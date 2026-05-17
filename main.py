"""Numper Ani — entry point. Run this to start the local anime server."""
import socket
import subprocess
import sys
import time
import threading
import webbrowser
import uvicorn
from server import app

PORT = 6969


def _ensure_playwright():
    """Install Playwright Chromium on first run (needed when running as .exe)."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch(headless=True).close()
    except Exception:
        print("  Installing Playwright Chromium (one-time, ~150MB)...")
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=False)


def _local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _open_browser():
    time.sleep(1.2)
    webbrowser.open(f"http://localhost:{PORT}")


def main():
    _ensure_playwright()
    ip = _local_ip()
    print(f"""
  /\\_/\\   Numper Ani
 ( o.o )  http://localhost:{PORT}
  > ^ <   http://{ip}:{PORT}  (local network)
""")
    t = threading.Thread(target=_open_browser, daemon=True)
    t.start()
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
