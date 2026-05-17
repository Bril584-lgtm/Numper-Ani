"""Numper Ani — FastAPI backend server."""
import json
import re
import time
import urllib.parse
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Query, Response
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


@app.get("/api/search")
async def api_search(q: str = Query(..., min_length=1), dub: bool = False):
    results = await source_router.search_all(q, dub=dub)
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


@app.get("/api/proxy")
async def proxy_stream(url: str = Query(...)):
    """Proxy any CDN URL through localhost — rewrites m3u8 playlists so all
    sub-requests also flow through here (fixes HLS.js cross-origin errors)."""
    is_m3u8 = ".m3u8" in url

    async with httpx.AsyncClient(
        headers=_PROXY_HEADERS, follow_redirects=True, timeout=20
    ) as client:
        r = await client.get(url)

    if is_m3u8 or "mpegurl" in r.headers.get("content-type", "").lower():
        rewritten = _rewrite_m3u8(r.text, url)
        return Response(
            content=rewritten.encode(),
            media_type="application/vnd.apple.mpegurl",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-cache",
            },
        )

    # Binary (ts segments, mp4, keys)
    ctype = r.headers.get("content-type", "application/octet-stream")
    return Response(
        content=r.content,
        media_type=ctype,
        headers={"Access-Control-Allow-Origin": "*"},
    )


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
