"""AllAnime source backend — mirrors ani-cli's AllAnime implementation."""
import base64
import hashlib
import json
import re
import httpx
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

BASE = "https://api.allanime.day"
REFERER = "https://allmanga.to"
AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
HEADERS = {"User-Agent": AGENT, "Referer": REFERER}

_AES_KEY = hashlib.sha256(b"Xot36i3lK3:v1").digest()

# Substitution table from ani-cli's provider_init sed chain
_SUB = {
    "79": "A", "7a": "B", "7b": "C", "7c": "D", "7d": "E", "7e": "F", "7f": "G",
    "70": "H", "71": "I", "72": "J", "73": "K", "74": "L", "75": "M", "76": "N", "77": "O",
    "68": "P", "69": "Q", "6a": "R", "6b": "S", "6c": "T", "6d": "U", "6e": "V", "6f": "W",
    "60": "X", "61": "Y", "62": "Z",
    "59": "a", "5a": "b", "5b": "c", "5c": "d", "5d": "e", "5e": "f", "5f": "g",
    "50": "h", "51": "i", "52": "j", "53": "k", "54": "l", "55": "m", "56": "n", "57": "o",
    "48": "p", "49": "q", "4a": "r", "4b": "s", "4c": "t", "4d": "u", "4e": "v", "4f": "w",
    "40": "x", "41": "y", "42": "z",
    "08": "0", "09": "1", "0a": "2", "0b": "3", "0c": "4", "0d": "5", "0e": "6", "0f": "7",
    "00": "8", "01": "9",
    "15": "-", "16": ".", "67": "_", "46": "~",
    "02": ":", "17": "/", "07": "?", "1b": "#",
    "63": "[", "65": "]", "78": "@",
    "19": "!", "1c": "$", "1e": "&",
    "10": "(", "11": ")", "12": "*", "13": "+", "14": ",",
    "03": ";", "05": "=", "1d": "%",
}

SEARCH_GQL = (
    "query($search:SearchInput $limit:Int $page:Int $translationType:VaildTranslationTypeEnumType"
    " $countryOrigin:VaildCountryOriginEnumType){"
    "shows(search:$search limit:$limit page:$page translationType:$translationType"
    " countryOrigin:$countryOrigin){edges{_id name availableEpisodes __typename}}}"
)

EPISODE_GQL = (
    "query($showId:String! $translationType:VaildTranslationTypeEnumType! $episodeString:String!){"
    "episode(showId:$showId translationType:$translationType episodeString:$episodeString)"
    "{episodeString sourceUrls}}"
)

EPISODE_QUERY_HASH = "d405d0edd690624b66baba3068e0edc3ac90f1597d898a1ec8db4e5c43c00fec"


def _decode_hex_url(hex_str: str) -> str:
    """Decode a hex-encoded URL using the AllAnime substitution cipher."""
    chunks = [hex_str[i:i+2] for i in range(0, len(hex_str), 2)]
    return "".join(_SUB.get(c, c) for c in chunks).replace("/clock", "/clock.json")


def _decrypt_tobeparsed(blob: str) -> list[dict]:
    """Decrypt a tobeparsed blob → list of {name, url} source dicts."""
    try:
        raw = base64.b64decode(blob + "==")
        iv = raw[1:13]
        ct = raw[13:len(raw) - 16]
        ctr_iv = iv + b"\x00\x00\x00\x02"
        cipher = Cipher(algorithms.AES(_AES_KEY), modes.CTR(ctr_iv), backend=default_backend())
        dec = cipher.decryptor()
        plain = (dec.update(ct) + dec.finalize()).decode("utf-8", errors="ignore")
    except Exception:
        return []

    sources = []
    for chunk in plain.replace("{", "\n").replace("}", "\n").split("\n"):
        m = re.search(r'"sourceUrl":"--([^"]+)".*?"sourceName":"([^"]+)"', chunk)
        if not m:
            m = re.search(r'"sourceName":"([^"]+)".*?"sourceUrl":"--([^"]+)"', chunk)
            if m:
                name, hex_url = m.group(1), m.group(2)
            else:
                continue
        else:
            hex_url, name = m.group(1), m.group(2)
        sources.append({"name": name, "url": _decode_hex_url(hex_url)})
    return sources


async def search(query: str, dub: bool = False) -> list[dict]:
    mode = "dub" if dub else "sub"
    variables = {
        "search": {"allowAdult": False, "allowUnknown": False, "query": query},
        "limit": 40,
        "page": 1,
        "translationType": mode,
        "countryOrigin": "ALL",
    }
    async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
        r = await client.post(
            f"{BASE}/api",
            json={"variables": variables, "query": SEARCH_GQL},
        )
        data = r.json()

    results = []
    for edge in data.get("data", {}).get("shows", {}).get("edges", []):
        ep_count = edge.get("availableEpisodes", {}).get(mode, 0)
        if ep_count:
            results.append({
                "id": edge["_id"],
                "title": edge["name"],
                "episodes": ep_count,
                "source": "allanime",
            })
    return results


async def get_episode_sources(show_id: str, ep: str, dub: bool = False) -> list[dict]:
    """Return list of {name, clock_url} for a given episode."""
    mode = "dub" if dub else "sub"

    import urllib.parse
    variables = json.dumps({"showId": show_id, "translationType": mode, "episodeString": ep})
    extensions = json.dumps({"persistedQuery": {"version": 1, "sha256Hash": EPISODE_QUERY_HASH}})

    async with httpx.AsyncClient(timeout=15) as client:
        # Try persisted query first
        r = await client.get(
            f"{BASE}/api",
            params={"variables": variables, "extensions": extensions},
            headers={**HEADERS, "Origin": "https://youtu-chan.com", "Referer": "https://youtu-chan.com"},
        )
        resp_text = r.text

        if "tobeparsed" not in resp_text:
            # Fallback to POST
            r = await client.post(
                f"{BASE}/api",
                json={"variables": {"showId": show_id, "translationType": mode, "episodeString": ep},
                      "query": EPISODE_GQL},
                headers=HEADERS,
            )
            resp_text = r.text

    data = {}
    try:
        data = r.json()
    except Exception:
        pass

    blob_match = re.search(r'"tobeparsed":"([^"]+)"', resp_text)
    if blob_match:
        return _decrypt_tobeparsed(blob_match.group(1))

    # Parse sourceUrls directly (non-encrypted fallback)
    sources = []
    for chunk in resp_text.replace("{", "\n").replace("}", "\n").split("\n"):
        m = re.search(r'"sourceUrl":"--([^"]+)".*?"sourceName":"([^"]+)"', chunk)
        if not m:
            m = re.search(r'"sourceName":"([^"]+)".*?"sourceUrl":"--([^"]+)"', chunk)
            if m:
                name, hex_url = m.group(1), m.group(2)
            else:
                continue
        else:
            hex_url, name = m.group(1), m.group(2)
        clean = hex_url.replace("\\u002F", "/").replace("\\", "")
        sources.append({"name": name, "url": _decode_hex_url(clean)})
    return sources


async def resolve_clock(clock_path: str) -> str | None:
    """Fetch a clock.json URL and extract the direct stream URL."""
    if not clock_path.startswith("http"):
        url = f"https://allanime.day{clock_path}"
    else:
        url = clock_path
    async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
        try:
            r = await client.get(url)
            data = r.json()
            # Wixmp / default format
            links = data.get("links", [])
            if links:
                return links[0].get("link") or links[0].get("hls")
            # mp4 format
            if data.get("mp4"):
                return None  # broken mp4 endpoint
        except Exception:
            pass
    return None
