"""Numper Ani — FastAPI backend server."""
import asyncio
import json
import re
import time
import urllib.parse
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse

from sources import router as source_router

app = FastAPI(title="Numper Ani", docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

STATIC_DIR = Path(__file__).parent / "static"
HISTORY_FILE = Path(__file__).parent / "history.json"

# In-memory stream cache: key → (result_dict, fetched_at_timestamp)
_stream_cache: dict[str, tuple[dict, float]] = {}
_CACHE_TTL = 2700  # 45 min — stream tokens last ~3h, refresh well before expiry

# Homepage data cache (AniList)
_home_cache: dict = {}
_HOME_CACHE_TTL = 1800  # 30 min

_PROXY_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
}


def _load_history() -> dict:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_history(h: dict):
    HISTORY_FILE.write_text(json.dumps(h, indent=2))


def _proxy_url(absolute_url: str) -> str:
    return f"/api/proxy?url={urllib.parse.quote(absolute_url, safe='')}"


def _rewrite_m3u8(content: str, base_url: str) -> str:
    """Rewrite all URLs in an m3u8 playlist to route through our proxy."""
    base = base_url.rsplit("/", 1)[0] + "/"
    lines = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append(line)
            continue

        if stripped.startswith("#"):
            # Rewrite URI="..." attributes (encryption keys, maps, etc.)
            def _replace_uri(m):
                uri = m.group(1)
                abs_uri = uri if uri.startswith("http") else base + uri
                return f'URI="{_proxy_url(abs_uri)}"'
            lines.append(re.sub(r'URI="([^"]+)"', _replace_uri, stripped))
        else:
            # Segment or sub-playlist URL
            abs_url = stripped if stripped.startswith("http") else base + stripped
            lines.append(_proxy_url(abs_url))
    return "\n".join(lines)


@app.get("/", response_class=HTMLResponse)
async def index():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/api/home")
async def api_home(nsfw: bool = False):
    """Homepage data: trending hero + all row sections from AniList."""
    from sources.anilist_home import fetch_home_data
    cache_key = "nsfw" if nsfw else "safe"
    cached = _home_cache.get(cache_key)
    if cached:
        data, ts = cached
        if time.time() - ts < _HOME_CACHE_TTL:
            return data
    data = await fetch_home_data(nsfw=nsfw)
    _home_cache[cache_key] = (data, time.time())
    return data


@app.get("/api/suggest")
async def api_suggest(q: str = Query(..., min_length=1)):
    gql = "query($s:String){Page(page:1,perPage:8){media(search:$s,type:ANIME,sort:SEARCH_MATCH){title{romaji english}coverImage{medium}format}}}"
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.post("https://graphql.anilist.co",
                json={"query": gql, "variables": {"s": q}},
                headers={"Content-Type": "application/json", "Accept": "application/json"})
            media = r.json().get("data", {}).get("Page", {}).get("media", [])
        results = []
        for m in media:
            t = m.get("title") or {}
            title = t.get("english") or t.get("romaji") or ""
            if title:
                results.append({"title": title, "thumb": (m.get("coverImage") or {}).get("medium", ""), "format": m.get("format", "")})
        return {"results": results}
    except Exception:
        return {"results": []}


_JIKAN_BASE = "https://api.jikan.moe/v4"
_JIKAN_BATCH = 3  # Jikan pages fetched per display page (3×25=75 candidates)


async def _jikan_page(c: httpx.AsyncClient, lup: str | None, jpage: int, sfw: bool = True) -> dict:
    params: dict = {"page": jpage, "limit": 25, "order_by": "popularity", "sort": "asc"}
    if lup and lup != "#":
        params["letter"] = lup
    if sfw:
        params["sfw"] = "true"
    try:
        r = await c.get(f"{_JIKAN_BASE}/anime", params=params)
        if r.status_code == 429:
            return {}
        return r.json()
    except Exception:
        return {}


@app.get("/api/browse")
async def api_browse(letter: str = Query(default="A"), page: int = Query(default=1, ge=1), nsfw: bool = False, dub: bool = False):
    lup = letter.upper() if letter.upper().isalpha() else "#"
    jikan_start = (page - 1) * _JIKAN_BATCH + 1

    sfw = not nsfw
    async with httpx.AsyncClient(timeout=20) as c:
        pages_data = await asyncio.gather(
            *[_jikan_page(c, lup, jikan_start + i, sfw=sfw) for i in range(_JIKAN_BATCH)]
        )

    # Ratings considered adult — filter out when nsfw=False
    _ADULT_RATINGS = {"rx - hentai", "r+ - mild nudity"}

    results = []
    has_next = False
    total = 0
    for data in pages_data:
        if not data:
            continue
        pagination = data.get("pagination") or {}
        if not total:
            total = (pagination.get("items") or {}).get("total", 0)
        has_next = pagination.get("has_next_page", False)
        for m in (data.get("data") or []):
            title = (m.get("title_english") or m.get("title") or "").strip()
            if not title:
                continue
            first = title[0].upper()
            if lup == "#":
                if first.isalpha():
                    continue
            elif first != lup:
                continue
            # Filter adult content when nsfw is off
            rating = (m.get("rating") or "").lower()
            is_adult = any(r in rating for r in _ADULT_RATINGS)
            if not nsfw and is_adult:
                continue
            images = m.get("images") or {}
            jpg = images.get("jpg") or {}
            thumb = jpg.get("large_image_url") or jpg.get("image_url") or ""
            score_raw = m.get("score") or 0
            results.append({
                "title": title,
                "thumb": thumb,
                "format": m.get("type") or "",
                "score": int(score_raw * 10) if score_raw else 0,
                "year": m.get("year") or 0,
            })

    return {"results": results, "has_next": has_next, "total": total}


@app.get("/api/search")
async def api_search(q: str = Query(..., min_length=1), dub: bool = False, nsfw: bool = False):
    results = await source_router.search_all(q, dub=dub, nsfw=nsfw)
    return {"results": results}


@app.get("/api/stream")
async def api_stream(
    source: str = Query(...),
    id: str = Query(...),
    ep: int = Query(..., ge=1),
    dub: bool = False,
):
    cache_key = f"{source}:{id}:{ep}:{dub}"
    cached = _stream_cache.get(cache_key)
    if cached:
        result, fetched_at = cached
        if time.time() - fetched_at < _CACHE_TTL:
            return result

    result = await source_router.get_stream(source, id, ep, dub=dub)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    _stream_cache[cache_key] = (result, time.time())
    return result


@app.get("/api/sources")
async def api_sources(
    source: str = Query(...),
    id: str = Query(...),
    ep: int = Query(..., ge=1),
    dub: bool = False,
):
    """Return all raw source URLs for an episode so the UI can show a switcher."""
    from sources import allanime
    if source == "allanime":
        srcs = await allanime.get_episode_sources(id, str(ep), dub=dub)
        return {"sources": [{"name": s["name"], "url": s["url"], "stype": s.get("stype", "")} for s in srcs]}
    return {"sources": []}


@app.get("/api/resolve")
async def api_resolve(embed_url: str = Query(...), name: str = Query(default="")):
    """Resolve a single embed/clock URL to a playable stream."""
    from sources import router as sr
    from sources import allanime, playwright_extractor

    url = embed_url
    _CLOCK = ("/apivtwo/", "/clock")
    _DIRECT_STREAM = (".m3u8", ".mp4")

    # Direct mp4 file (Yt-mp4 / fast4speed) — serve via proxy for CORS
    if "fast4speed" in url or (url.startswith("http") and any(url.endswith(x) for x in (".mp4",))):
        return {"url": f"/api/proxy?url={urllib.parse.quote(url, safe='')}", "type": "mp4", "source": name}

    if any(url.endswith(x) or x in url.split("?")[0] for x in _DIRECT_STREAM):
        stream_type = "hls" if ".m3u8" in url else "mp4"
        return {"url": url, "type": stream_type, "source": name}

    if any(p in url for p in _CLOCK):
        direct = await allanime.resolve_clock(url)
        if direct:
            return {"url": direct, "type": "hls" if ".m3u8" in direct else "mp4", "source": name}

    # Embed URL — Playwright
    try:
        stream = await playwright_extractor.extract_stream(embed_url)
        if stream:
            return {"url": stream, "type": "hls" if ".m3u8" in stream else "mp4", "source": name}
    except Exception:
        pass

    raise HTTPException(status_code=502, detail=f"Could not resolve source: {name}")


@app.get("/api/proxy")
async def proxy_stream(url: str = Query(...), request: Request = None):
    """Proxy any CDN URL — supports Range requests for seekable MP4 playback."""
    from fastapi import Request

    range_header = request.headers.get("range") if request else None
    req_headers = {**_PROXY_HEADERS}
    if range_header:
        req_headers["Range"] = range_header

    async with httpx.AsyncClient(
        headers=req_headers, follow_redirects=True, timeout=30
    ) as client:
        r = await client.get(url)

    ctype = r.headers.get("content-type", "application/octet-stream")
    resp_headers = {"Access-Control-Allow-Origin": "*"}

    # Pass through range-response headers so browser can seek
    for h in ("content-range", "accept-ranges", "content-length"):
        if h in r.headers:
            resp_headers[h] = r.headers[h]

    if ".m3u8" in url or "mpegurl" in ctype.lower():
        rewritten = _rewrite_m3u8(r.text, url)
        resp_headers["Cache-Control"] = "no-cache"
        return Response(
            content=rewritten.encode(),
            media_type="application/vnd.apple.mpegurl",
            headers=resp_headers,
        )

    status_code = r.status_code  # 200 or 206 Partial Content
    return Response(
        content=r.content,
        status_code=status_code,
        media_type=ctype,
        headers=resp_headers,
    )


@app.get("/api/skiptimes")
async def api_skiptimes(mal_id: int = Query(...), ep: int = Query(..., ge=1)):
    """Fetch intro/recap skip timestamps from AniSkip."""
    if not mal_id:
        return {"found": False, "results": []}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(
                f"https://api.aniskip.com/v2/skip-times/{mal_id}/{ep}",
                params={"types[]": ["op", "recap", "ed"]},
            )
            return r.json()
    except Exception:
        return {"found": False, "results": []}


@app.get("/api/subtitles")
async def api_subtitles(title: str = Query(...), ep: int = Query(..., ge=1)):
    from sources.subtitles import fetch as fetch_subs
    subs = await fetch_subs(title, ep)
    return {"subtitles": subs}


@app.get("/api/episodes")
async def api_episodes(source: str = Query(...), id: str = Query(...)):
    from sources import router as sr
    count = await sr.get_episode_count(source, id)
    return {"count": count}


@app.get("/api/history")
async def get_history():
    return _load_history()


@app.post("/api/history")
async def save_history(body: dict):
    h = _load_history()
    key = f"{body['source']}:{body['id']}"
    h[key] = {
        "title": body.get("title", ""),
        "source": body.get("source", ""),
        "id": body.get("id", ""),
        "ep": body.get("ep", 1),
        "dub": body.get("dub", False),
        "thumb": body.get("thumb", ""),
    }
    _save_history(h)
    return {"ok": True}
