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


async def _resolve_allanime(show_id: str, ep: str, dub: bool) -> dict:
    try:
        sources = await allanime.get_episode_sources(show_id, ep, dub=dub)
    except Exception as e:
        return {"error": f"AllAnime fetch failed: {e}"}

    if not sources:
        return {"error": "No sources found on AllAnime"}

    # Priority order: Default (wixmp, m3u8), Luf-Mp4 (HiAnime), then Filemoon, S-mp4
    priority = ["Default", "Luf-Mp4", "Fm-mp4", "S-mp4", "Yt-mp4"]

    def source_rank(s):
        try:
            return priority.index(s["name"])
        except ValueError:
            return 99

    sources.sort(key=source_rank)

    for src in sources:
        clock_path = src["url"]
        if not clock_path:
            continue

        # Try direct resolution first
        direct = await allanime.resolve_clock(clock_path)
        if direct:
            stream_type = "hls" if ".m3u8" in direct else "mp4"
            return {"url": direct, "type": stream_type, "source": f"allanime:{src['name']}"}

        # Try Playwright for JS-protected embeds
        try:
            stream = await playwright_extractor.extract_from_allanime_source(clock_path)
            if stream:
                stream_type = "hls" if ".m3u8" in stream else "mp4"
                return {"url": stream, "type": stream_type, "source": f"allanime:{src['name']} (playwright)"}
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
