## Want Movies, TV, Spanish & Hentai too?

Check out **[Numper Hub](https://github.com/Bril584-lgtm/Numper-Hub)** — the all-in-one version that includes Numper Ani plus Movies & TV, Spanish content, and Hentai in a single launcher.

---

<p align="center">
  <img src="https://i.imgur.com/placeholder.png" alt="Numper Ani" width="120" style="display:none"/>
</p>

<h1 align="center">Numper Ani</h1>

<p align="center">
  A free, ad-free, locally-run anime hub — one interface, every show, zero subscriptions.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="MIT License"/>
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square" alt="Platform"/>
  <img src="https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square" alt="Status"/>
</p>

---

## What is Numper Ani?

Numper Ani is a **locally-hosted anime aggregator** that runs on your machine and opens in your browser. It pulls together anime metadata and streaming availability from multiple publicly accessible sources, presenting them in a single clean, Netflix-inspired interface — with no ads, no pop-ups, no account required, and no monthly fee.

You launch it once from your terminal or by double-clicking a script. Everything else happens at `localhost`.

---

## What it offers

### Discovery
- **Netflix-style homepage** with a hero banner and rotating trending titles
- **Genre rows** — Action, Romance, Fantasy, Comedy, Sci-Fi, and more
- **Seasonal spotlight** — what's popular right now
- **Top-rated all-time** rankings with cover art, scores, and synopsis
- **A–Z Browse** — scroll through the full anime catalog letter by letter, with pagination
- **NSFW toggle** — switch to an adult-oriented content view when enabled

### Search
- **Multi-source search** — queries several providers simultaneously and merges the results
- **Autocomplete** — live suggestions as you type, click to jump straight to episodes
- **Fuzzy correction** — handles typos and alternate titles gracefully
- **Dub / Sub toggle** — one click to switch modes before or during browsing

### Watching
- **Episode panel** — clean numbered grid for every episode of a show
- **Provider switcher** — if one source has trouble, switch to another with a single click, without leaving the player
- **Skip Intro / Skip Recap** buttons that appear automatically at the right moment
- **Continue Watching** — your episode progress is saved locally and shown on the homepage
- **Subtitle support** — load your own `.srt` / `.vtt` file, or let the app fetch them automatically
- **Seekable playback** — full scrubbing support on both HLS and direct MP4 streams
- **Source quality bar** — see which server is streaming and switch on the fly

### Technical
- Runs entirely on your local machine — nothing is uploaded or logged externally
- Streams are proxied through `localhost` to handle cross-origin restrictions
- No API keys, no accounts, no paid services required
- Works on Windows, macOS, and Linux

---

## Requirements

- **Python 3.10 or newer** — [python.org/downloads](https://www.python.org/downloads/)
- A modern web browser (Chrome, Firefox, Edge)

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/Bril584-lgtm/Numper-Ani.git
cd Numper-Ani

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install the headless browser (one-time, ~130 MB)
python -m playwright install chromium
```

No API keys. No configuration files. No accounts.

---

## Usage

**Windows — double-click launcher:**
```
run.bat
```

**Any platform — terminal:**
```bash
python main.py
```

Your default browser will open automatically. If it doesn't, navigate to `http://localhost:6969`.

---

## Quick start

1. The **homepage** loads with trending and seasonal rows — scroll or click anything to start
2. Use the **search bar** to find a specific title; autocomplete will suggest as you type
3. Toggle **DUB** or **NSFW** in the top bar as needed
4. Click an anime card → pick an episode → watch
5. If playback fails, use the **source switcher** above the video to try another provider
6. **Skip Intro / Recap** buttons appear automatically — click them or let them count down

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| "No sources found" | Toggle DUB/SUB — the episode may not be available in your selected mode |
| "All sources failed" | Switch providers using the source bar; external servers may be temporarily down |
| Slow first load on some episodes | Normal — certain sources require a few extra seconds to resolve. Cached after first play |
| Browser doesn't open | Go to `http://localhost:6969` manually |
| Homepage has no images | Metadata service may be temporarily unavailable — search still works normally |

---

## Legal Disclaimer

> **Numper Ani does not host, store, distribute, or reproduce any copyrighted content.**

This software is a **personal-use aggregation client**. It makes HTTP requests to third-party, publicly accessible APIs and streaming endpoints in the same manner any browser would when a user visits those services directly. All media content is served exclusively from the original third-party servers. Numper Ani does not cache, re-host, modify, or redistribute any video content.

- This project is intended solely for **personal, non-commercial, and educational use**.
- Users are solely responsible for ensuring their use complies with the applicable laws of their jurisdiction and the terms of service of any third-party services accessed.
- The developers and contributors of Numper Ani are **not affiliated with, endorsed by, or in partnership with** any streaming service, content provider, or rights holder referenced by this software.
- Third-party services accessed by this software are operated independently. Their availability, content, and legality are entirely outside the control of this project.
- If you are a rights holder and believe that a third-party service accessed by this tool is infringing your content, please contact that service directly. This repository contains no infringing content and has no ability to remove content from external servers.
- **This software is provided as-is, with no warranty of any kind. Use at your own risk.**

---

## License

[MIT](LICENSE) — free to use, modify, and distribute with attribution.

---

<p align="center">Built with FastAPI · HLS.js · Playwright · AniList &nbsp;·&nbsp; Made for anime lovers</p>

