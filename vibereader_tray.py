"""
vibereader_tray.py — System tray app for tech news (vibereader).
Reads articles from ~/.vibereader/articles.json and shows them in a tray menu.
"""

import asyncio
import json
import sys
import threading
import time
import webbrowser
from datetime import datetime, timezone
from functools import partial
from pathlib import Path

import pystray
from PIL import Image, ImageDraw

from fetch import run_fetch

ARTICLES_PATH = Path.home() / ".vibereader" / "articles.json"
PREFS_PATH = Path.home() / ".vibereader" / "preferences.json"
TITLE_MAX_LEN = 60
TOP_N = 15
REFRESH_ARTICLES_INTERVAL = 60   # seconds between menu refreshes
REFRESH_FETCH_INTERVAL = 300     # seconds between cache fetches
ICON_SIZE = 64
ORANGE = (255, 140, 0, 255)
GRAY = (128, 128, 128, 255)


def load_prefs():
    try:
        data = json.loads(PREFS_PATH.read_text())
        return data
    except Exception:
        return {"categories": [], "sources": [], "style": ""}


def load_articles():
    try:
        data = json.loads(ARTICLES_PATH.read_text())
        return data
    except Exception:
        return {"fetched_at": None, "count": 0, "articles": []}


def is_fresh(fetched_at_str):
    if not fetched_at_str:
        return False
    try:
        fetched_at = datetime.fromisoformat(fetched_at_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age = (now - fetched_at).total_seconds()
        return age < REFRESH_FETCH_INTERVAL
    except Exception:
        return False


def make_icon_image(fresh):
    color = ORANGE if fresh else GRAY
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 4
    draw.ellipse(
        [margin, margin, ICON_SIZE - margin, ICON_SIZE - margin],
        fill=color,
    )
    return img


def truncate_title(title):
    if len(title) > TITLE_MAX_LEN:
        return title[:TITLE_MAX_LEN] + "..."
    return title


def filter_articles(articles, prefs):
    pref_cats = set(prefs.get("categories", []))
    if pref_cats:
        filtered = [
            a for a in articles
            if set(a.get("categories", [])) & pref_cats
        ]
    else:
        filtered = list(articles)

    if len(filtered) < 5:
        filtered = list(articles)

    filtered.sort(key=lambda a: a.get("score", 0), reverse=True)
    return filtered[:TOP_N]


def open_url(url, icon, item):
    webbrowser.open(url)


def build_items(ref):
    data = load_articles()
    prefs = load_prefs()
    articles = filter_articles(data.get("articles", []), prefs)

    items = []
    for article in articles:
        url = article.get("url", "")
        if not url:
            continue
        title = truncate_title(article.get("title", "(no title)"))
        items.append(pystray.MenuItem(title, partial(open_url, url)))

    items.append(pystray.MenuItem("Refresh Now", lambda icon, item: refresh_now(ref)))
    items.append(pystray.MenuItem("Quit", lambda icon, item: icon.stop()))

    return items


def refresh_now(icon_ref):
    def _run():
        asyncio.run(run_fetch())
        update_icon_and_menu(icon_ref)
    threading.Thread(target=_run, daemon=True).start()


def update_icon_and_menu(icon_ref):
    data = load_articles()
    fresh = is_fresh(data.get("fetched_at"))
    icon_ref.icon = make_icon_image(fresh)
    icon_ref.update_menu()


def background_loop(icon_ref):
    last_fetch = time.monotonic() - REFRESH_FETCH_INTERVAL
    while True:
        time.sleep(REFRESH_ARTICLES_INTERVAL)
        now = time.monotonic()
        update_icon_and_menu(icon_ref)
        if now - last_fetch >= REFRESH_FETCH_INTERVAL:
            threading.Thread(target=lambda: asyncio.run(run_fetch()), daemon=True).start()
            last_fetch = now


def main():
    data = load_articles()
    fresh = is_fresh(data.get("fetched_at"))
    img = make_icon_image(fresh)

    class IconRef:
        """Thin proxy so background_loop and build_items share one mutable ref."""
        def __init__(self):
            self._icon = None

        # Proxy attribute access to the underlying pystray.Icon
        def __getattr__(self, name):
            return getattr(self._icon, name)

        def __setattr__(self, name, value):
            if name == "_icon":
                object.__setattr__(self, name, value)
            else:
                setattr(self._icon, name, value)

    ref = IconRef()

    icon = pystray.Icon("vibereader", img, "Vibereader",
                        menu=pystray.Menu(lambda: build_items(ref)))
    ref._icon = icon

    t = threading.Thread(target=background_loop, args=(ref,), daemon=True)
    t.start()

    icon.run()


if __name__ == "__main__":
    main()
