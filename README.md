# Numper Ani 🐱

```
  /\_/\   Numper Ani
 ( o.o )  Your free, ad-free anime hub
  > ^ <   — Numper the orange cat, librarian of anime —
```

A local desktop anime player that pulls from multiple sources and streams everything through your own browser — no ads, no malicious sites, no risk.

---

## Features

- **Search across AllAnime + HiAnime** simultaneously
- **Auto-fallback** — if one source fails, it tries the next automatically
- **Dub / Sub toggle** with one click
- **Continue watching** — episode history saved locally
- **No login required** — completely free
- **HLS.js player** — handles both `.m3u8` and `.mp4` streams
- **CORS proxy** built-in — streams go through localhost, not third-party sites

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

That's it. No other setup needed.

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

1. **Type an anime name** in the search bar and hit Enter (or click Search)
2. **Toggle DUB** if you want the dubbed version
3. **Click an anime card** to see its episodes
4. **Click an episode number** to start watching
5. The player handles buffering automatically — no site visits, no ads

---

## How it works

```
You type a search
        ↓
Numper Ani queries AllAnime + HiAnime APIs simultaneously
        ↓
You pick an episode
        ↓
Backend fetches the encrypted source URL, decrypts it, resolves the stream
        ↓
If the stream needs JavaScript (Streamwish, Filemoon), Playwright handles it headlessly
        ↓
Stream is proxied through localhost → HLS.js plays it in your browser
```

No streaming site ever loads in your actual browser tab. All scraping happens invisibly in the backend.

---

## Sources

| Source | Type | Notes |
|--------|------|-------|
| AllAnime | API + decryption | Default, Filemoon, HiAnime providers |
| HiAnime (Zoro) | Web scrape | Reliable fallback with dub support |
| Playwright | JS extractor | Handles Streamwish, Filemoon embeds |

---

## Troubleshooting

**"Stream unavailable"** — The source's server may be temporarily down. Try toggling DUB/SUB or searching again. AllAnime's mp4 endpoints sometimes go down; the app automatically falls back to Filemoon/HiAnime.

**Slow to load** — Playwright (headless browser) adds a few seconds when scraping JS-protected embeds. This is normal.

**Browser doesn't open automatically** — Navigate to `http://localhost:6969` manually.

---

## Mascot

Meet **Numper** — an orange cat with round glasses who holds a library book. He catalogues every anime ever made and knows exactly where to find it.

---

*Built with FastAPI · Playwright · HLS.js · love for anime*
