"""Anikoto / Megaplay source — streams via AniList/MAL ID through megaplay.buzz CDN."""
import re
import httpx

MEGAPLAY = "https://megaplay.buzz"
ANILIST_URL = "https://graphql.anilist.co"
AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"

_SEARCH_GQL = """
query($s:String){Page(page:1,perPage:20){media(search:$s,type:ANIME,sort:SEARCH_MATCH){
  id idMal title{romaji english}coverImage{extraLarge large}
  format status averageScore episodes seasonYear
}}}
"""

_HEADERS = {
    "User-Agent": AGENT,
    "Referer": MEGAPLAY,
    "X-Requested-With": "XMLHttpRequest",
}


async def search(query: str, dub: bool = False) -> list[dict]:
    """Search via AniList; stream uses AniList or MAL ID on megaplay."""
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(
                ANILIST_URL,
                json={"query": _SEARCH_GQL, "variables": {"s": query}},
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            )
            media_list = r.json().get("data", {}).get("Page", {}).get("media") or []
    except Exception:
        return []

    results = []
    for m in media_list:
        anilist_id = m.get("id")
        if not anilist_id:
            continue
        titles = m.get("title") or {}
        title = titles.get("english") or titles.get("romaji") or ""
        if not title:
            continue
        cover = m.get("coverImage") or {}
        thumb = cover.get("extraLarge") or cover.get("large") or ""
        results.append({
            "id": str(anilist_id),          # AniList ID used for streaming
            "title": title,
            "episodes": m.get("episodes") or 0,
            "thumb": thumb,
            "source": "anikoto",
            "format": m.get("format") or "",
            "score": m.get("averageScore") or 0,
            "year": m.get("seasonYear") or 0,
            "mal_id": m.get("idMal") or 0,
        })
    return results


async def _extract_stream_from_embed(embed_url: str) -> str | None:
    """
    Two-step extraction:
    1. Fetch embed page → parse numeric file ID from <title>
    2. Call /stream/getSources?id={file_id} → return sources.file (m3u8)
    """
    try:
        async with httpx.AsyncClient(
            headers={**_HEADERS, "Referer": "https://anikoto.site/"},
            follow_redirects=True,
            timeout=20,
        ) as c:
            r = await c.get(embed_url)
            if r.status_code in (404, 410):
                return None

            # Parse file ID from <title>File 12345</title>
            title_m = re.search(r"<title[^>]*>File\s+(\d+)</title>", r.text, re.IGNORECASE)
            if not title_m:
                return None
            file_id = title_m.group(1)

            # Fetch sources
            sr = await c.get(
                f"{MEGAPLAY}/stream/getSources",
                params={"id": file_id},
                headers=_HEADERS,
            )
            if sr.status_code != 200:
                return None
            data = sr.json()
            sources = data.get("sources") or {}
            # sources can be a dict {"file": "url"} or a list [{"file": "url"}]
            if isinstance(sources, dict):
                return sources.get("file") or sources.get("url")
            if isinstance(sources, list) and sources:
                return sources[0].get("file") or sources[0].get("url")
    except Exception:
        pass
    return None


async def get_stream(anilist_id: str, ep: int, dub: bool = False) -> dict:
    lang = "dub" if dub else "sub"

    # Try AniList ID endpoint first, then MAL ID if we have it
    embed_candidates = [
        f"{MEGAPLAY}/stream/ani/{anilist_id}/{ep}/{lang}",
    ]

    for embed_url in embed_candidates:
        stream = await _extract_stream_from_embed(embed_url)
        if stream:
            return {"url": stream, "type": "hls" if ".m3u8" in stream else "mp4", "source": "anikoto"}

    # Playwright fallback on the watch page
    try:
        from . import playwright_extractor
        watch_url = f"https://anikoto.site/watch?id={anilist_id}&ep={ep}&lang={lang}"
        stream = await playwright_extractor.extract_stream(watch_url)
        if stream:
            return {"url": stream, "type": "hls" if ".m3u8" in stream else "mp4", "source": "anikoto (pw)"}
    except Exception:
        pass

    return {"error": f"Anikoto: not available (ep {ep} {lang}) — may be region/DMCA restricted"}
