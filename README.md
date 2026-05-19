# Numper Ani 🐱

```
  /\_/\   Numper Ani
 ( o.o )  Your free, ad-free anime hub
  > ^ <   — Numper the orange cat, librarian of anime —
```

A **local desktop anime player** that aggregates multiple streaming sources into one clean, ad-free interface — launched from your terminal, watched in your browser.

---

> ## ⚠️ Legal Disclaimer
>
> **Numper Ani does not host, store, distribute, or reproduce any copyrighted content.**
>
> This tool is a **client-side aggregator**. It queries publicly accessible third-party APIs and streaming embeds in the same way a browser would when you visit those sites directly. All video content is served from the original source servers — Numper Ani only resolves and proxies the stream URL through localhost to avoid CORS issues.
>
> - This project is intended for **personal, non-commercial, educational use only**.
> - Users are solely responsible for ensuring their use complies with the laws of their country and the terms of service of any third-party site accessed.
> - The developers of Numper Ani are **not affiliated** with AllAnime, GogoAnime, AniList, or any other streaming or metadata service.
> - If you are a rights holder and believe your content is being improperly accessed, please contact the third-party source sites directly. This tool contains no infringing content and cannot remove content from external servers.
> - **Use at your own risk.**

---

## Features

- **Netflix-style homepage** — hero banner, auto-rotating trending titles, horizontal scroll rows by genre
- **AniList integration** — Trending, Popular This Season, Top Rated, Action, Romance, Fantasy, Comedy, Sci-Fi rows with cover art, scores, and synopsis
- **Search across AllAnime + GogoAnime** simultaneously
- **Auto-source fallback** — tries every available source, picks the first that works
- **Dub / Sub toggle** with one click
- **Source switcher** — manually switch between Filemoon, Direct MP4, Streamwish, OK.ru, and more inside the player
- **Skip Intro / Skip Recap** buttons (powered by AniSkip)
- **Continue Watching** — episode history saved locally, shown on the homepage
- **Subtitle support** — load your own .srt/.vtt file, or auto-fetch via OpenSubtitles
- **No login required** — completely free
- **HLS.js player** — handles both `.m3u8` and `.mp4` streams
- **CORS proxy** built-in — all streams route through localhost

---

## Requirements

- **Python 3.10+** — [Download](https://www.python.org/downloads/)
- **pip** (comes with Python)
- A modern browser (Chrome, Firefox, Edge)

---

## Installation

### Step 1 — Clone the repo

```bash
git clone https://github.com/Bril584-lgtm/Numper-Ani.git
cd Numper-Ani
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Install Playwright browser (one-time)

```bash
python -m playwright install chromium
```

That's it. No API keys, no accounts, no other setup needed.

---

## Usage

### Launch (Windows — double-click)

Double-click **`run.bat`**.

### Launch (Terminal — any OS)

```bash
python main.py
```

Your browser will automatically open to `http://localhost:6969`.

---

## How to watch

1. **Browse the homepage** — scroll through trending, seasonal, and genre rows, or use the hero banner
2. **Search** — type an anime name and hit Enter for direct results
3. **Toggle DUB** if you want the dubbed version
4. **Click an anime card** to see its episodes
5. **Click an episode number** to start watching
6. **Switch sources** anytime using the source bar above the video if one source fails
7. **Skip intro/recap** using the buttons that appear at the right time

---

## How it works

```
Homepage loads
        ↓
AniList API returns trending / seasonal / genre metadata (cover art, scores, synopsis)
        ↓
You pick an anime (from homepage or search)
        ↓
AllAnime / GogoAnime APIs return episode source URLs (encrypted)
        ↓
Backend decrypts URLs — fast sources (clock.json, direct MP4) resolve instantly
        ↓
JS-protected embeds (Filemoon, Streamwish) use Playwright headlessly
        ↓
Stream is proxied through localhost → HLS.js plays it in your browser
```

No streaming site ever loads in your actual browser tab. All resolution happens invisibly in the backend.

---

## Sources

| Source | What it provides | Notes |
|--------|-----------------|-------|
| AllAnime (`api.allanime.day`) | Episode stream URLs (encrypted) | Primary source, supports dub/sub |
| GogoAnime | Episode stream URLs | Fallback / additional source |
| AniList (`graphql.anilist.co`) | Metadata only — covers, scores, genres | Homepage & search enrichment |
| AniSkip (`api.aniskip.com`) | Skip timestamps | Intro / recap buttons in player |
| OpenSubtitles | Subtitle files | Auto-fetched when available |
| Playwright (Chromium) | JS-protected embed extractor | Headless, runs locally |

**HiAnime (hianime.to) was permanently shut down in May 2026 and is disabled.**

---

## Project structure

```
Numper-Ani/
├── main.py                      # Entry point — starts server, opens browser
├── server.py                    # FastAPI: all /api/* endpoints + caching
├── sources/
│   ├── allanime.py              # AllAnime search, AES-256-CTR decryption, episode sources
│   ├── anilist_home.py          # AniList homepage data (trending, genres, metadata)
│   ├── gogoanime.py             # GogoAnime source
│   ├── hianime.py               # Disabled (site shut down)
│   ├── playwright_extractor.py  # Headless Chromium m3u8 extractor
│   ├── router.py                # Multi-source orchestration + auto-fallback
│   └── subtitles.py             # OpenSubtitles auto-fetch
├── static/
│   └── index.html               # Full SPA — homepage, search, player, source switcher
├── requirements.txt
├── run.bat                      # Windows double-click launcher
└── README.md
```

---

## Troubleshooting

**"No sources found"** — The episode may not be available in the selected dub/sub mode. Toggle DUB/SUB and try again.

**"All sources failed"** — Source servers are temporarily down. Try switching sources manually in the player, or come back later.

**Slow first load** — Playwright (headless Chromium) takes 5–15 seconds on JS-protected embeds. Subsequent plays are cached and instant.

**Browser doesn't open automatically** — Navigate to `http://localhost:6969` manually.

**Homepage shows no cover art** — AniList API may be temporarily unavailable. Search still works normally.

---

## Mascot

Meet **Numper** — an orange cat with round glasses who holds a library book. He catalogues every anime ever made and knows exactly where to find it.

---

## License

MIT — see [LICENSE](LICENSE).

*This project is provided as-is with no warranty. The author assumes no liability for misuse.*

---

*Built with FastAPI · Playwright · HLS.js · AniList · love for anime*
