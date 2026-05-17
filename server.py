"""Numper Ani — FastAPI backend server."""
import json
import os
import re
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from sources import router as source_router

app = FastAPI(title="Numper Ani", docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

STATIC_DIR = Path(__file__).parent / "static"
HISTORY_FILE = Path(__file__).parent / "history.json"


def _load_history() -> dict:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_history(h: dict):
    HISTORY_FILE.write_text(json.dumps(h, indent=2))


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
    result = await source_router.get_stream(source, id, ep, dub=dub)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return result


@app.get("/api/proxy")
async def proxy_stream(url: str = Query(...), referer: str = Query(default="")):
    """Proxy m3u8/mp4 to avoid CORS issues."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    }
    if referer:
        headers["Referer"] = referer

    async def stream_response():
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=30) as client:
            async with client.stream("GET", url) as r:
                async for chunk in r.aiter_bytes(chunk_size=8192):
                    yield chunk

    # Detect content type
    ctype = "application/vnd.apple.mpegurl" if ".m3u8" in url else "video/mp4"
    return StreamingResponse(stream_response(), media_type=ctype)


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
