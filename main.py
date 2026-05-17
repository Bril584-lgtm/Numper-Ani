"""Numper Ani — entry point. Run this to start the local anime server."""
import sys
import time
import threading
import webbrowser
import uvicorn
from server import app

PORT = 6969
URL = f"http://localhost:{PORT}"


def _open_browser():
    time.sleep(1.2)
    webbrowser.open(URL)


def main():
    print(f"""
  /\\_/\\   Numper Ani
 ( o.o )  Your ad-free anime hub
  > ^ <   {URL}
""")
    t = threading.Thread(target=_open_browser, daemon=True)
    t.start()
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
