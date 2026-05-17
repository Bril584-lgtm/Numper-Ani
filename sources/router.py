"""Source router — tries AllAnime first, then HiAnime, with auto-fallback."""
import asyncio
from . import allanime, hianime, playwright_extractor


async def search_all(query: str, dub: bool = False) -> list[dict]:
    results_aa, results_hi = await asyncio.gather(
        allanime.search(query, dub=dub),
        hianime.search(query, dub=dub),
        return_exceptions=True,
    )
    seen_titles = set()
    merged = []
    for r in (results_aa if not isinstance(results_aa, Exception) else []):
        key = r["title"].lower()
        if key not in seen_titles:
            seen_titles.add(key)
            merged.append(r)
    for r in (results_hi if not isinstance(results_hi, Exception) else []):
        key = r["title"].lower()
        if key not in seen_titles:
            seen_titles.add(key)
            merged.append(r)
    return merged


async def get_stream(source: str, show_id: str, ep: int, dub: bool = False) -> dict:
    """
    Return {"url": "...", "type": "hls"|"mp4", "source": "..."} or {"error": "..."}.
    Tries multiple providers within the source with auto-fallback.
    """
    if source == "allanime":
        return await _resolve_allanime(show_id, str(ep), dub)
    elif source == "hianime":
        return await _resolve_hianime(show_id, ep, dub)
    return {"error": "Unknown source"}


_CLOCK_PREFIXES = ("/apivtwo/", "/clock", "allanime.day/")
_DIRECT_STREAM = (".m3u8", ".mp4", "cdnfile", "cdn.plyr", "storage.googleapis")


def _is_clock_url(url: str) -> bool:
    return any(p in url for p in _CLOCK_PREFIXES)


def _is_direct_stream(url: str) -> bool:
    return any(p in url for p in _DIRECT_STREAM)


async def _resolve_allanime(show_id: str, ep: str, dub: bool) -> dict:
    try:
        sources = await allanime.get_episode_sources(show_id, ep, dub=dub)
    except Exception as e:
        return {"error": f"AllAnime fetch failed: {e}"}

    if not sources:
        return {"error": "No sources found on AllAnime"}

    # Priority: Filemoon/Vid-mp4 (reliable m3u8), then OK.ru, then others
    priority = ["Default", "Vid-mp4", "Fm-mp4", "Luf-Mp4", "S-mp4", "Ok", "Yt-mp4"]

    def source_rank(s):
        try:
            return priority.index(s["name"])
        except ValueError:
            return 99

    sources.sort(key=source_rank)

    for src in sources:
        url = src.get("url", "")
        name = src.get("name", "unknown")
        if not url:
            continue

        # If it's already a direct stream, serve it
        if _is_direct_stream(url):
            stream_type = "hls" if ".m3u8" in url else "mp4"
            return {"url": url, "type": stream_type, "source": f"allanime:{name}"}

        # If it's a clock.json path, resolve via API
        if _is_clock_url(url):
            direct = await allanime.resolve_clock(url)
            if direct:
                stream_type = "hls" if ".m3u8" in direct else "mp4"
                return {"url": direct, "type": stream_type, "source": f"allanime:{name}"}
            # clock failed → try Playwright on it
            try:
                stream = await playwright_extractor.extract_from_allanime_source(url)
                if stream:
                    stream_type = "hls" if ".m3u8" in stream else "mp4"
                    return {"url": stream, "type": stream_type, "source": f"allanime:{name} (pw)"}
            except Exception:
                continue
        else:
            # Embed URL (iframe): use Playwright to extract stream
            try:
                stream = await playwright_extractor.extract_stream(url)
                if stream:
                    stream_type = "hls" if ".m3u8" in stream else "mp4"
                    return {"url": stream, "type": stream_type, "source": f"allanime:{name} (pw)"}
            except Exception:
                continue

    return {"error": "All AllAnime sources failed"}


async def _resolve_hianime(show_slug: str, ep_num: int, dub: bool) -> dict:
    try:
        ep_id = await hianime.get_episode_id(show_slug, ep_num)
        if not ep_id:
            return {"error": "Episode not found on HiAnime"}
        url = await hianime.get_stream_url(ep_id, dub=dub)
        if url:
            stream_type = "hls" if ".m3u8" in url else "mp4"
            return {"url": url, "type": stream_type, "source": "hianime"}
    except Exception as e:
        return {"error": f"HiAnime failed: {e}"}
    return {"error": "HiAnime: no stream found"}
