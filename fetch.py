#!/usr/bin/env python3
"""Standalone fetch module for vibereader-menubar.

This module is a self-contained copy of the fetch orchestration logic from the
vibereader plugin. It exposes `async def run_fetch()` as the public API so that
the menubar web server and tray app can import and invoke it directly, with no
dependency on the plugin directory.

Usage as a module:
    from fetch import run_fetch
    await run_fetch()

Usage as a script:
    python3 fetch.py
"""
import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from dataclasses import asdict

try:
    import feedparser
    _FEEDPARSER_AVAILABLE = True
except ImportError:
    _FEEDPARSER_AVAILABLE = False

try:
    import aiohttp
    _AIOHTTP_AVAILABLE = True
except ImportError:
    _AIOHTTP_AVAILABLE = False

try:
    from vibereader.config import load_config
    from vibereader.feeds.hn import fetch_hn
    from vibereader.feeds.rss import fetch_rss
    _VIBEREADER_AVAILABLE = True
except ImportError:
    print("vibereader not installed. Run: pip install vibereader", file=sys.stderr)
    _VIBEREADER_AVAILABLE = False

ARTICLES_PATH = os.path.expanduser("~/.vibereader/articles.json")
PREFERENCES_PATH = os.path.expanduser("~/.vibereader/preferences.json")

SOURCE_FEEDS = {
    'hn': None,  # Special: uses fetch_hn(), not RSS
    'hnrss': 'https://hnrss.org/newest?points=100',
    'techcrunch': 'https://techcrunch.com/feed/',
    'theverge': 'https://www.theverge.com/rss/index.xml',
    'arstechnica': 'https://feeds.arstechnica.com/arstechnica/technology-lab',
    'wired': 'https://www.wired.com/feed/rss',
    'techmeme': 'https://www.techmeme.com/feed.xml',
    'slashdot': 'https://rss.slashdot.org/Slashdot/slashdotMain',
    'coindesk': 'https://www.coindesk.com/arc/outboundfeeds/rss',
    'cointelegraph': 'https://cointelegraph.com/rss',
    'newscientist': 'https://www.newscientist.com/section/news/feed/',
    'quanta': 'https://www.quantamagazine.org/feed/',
    'sciencedaily': 'https://www.sciencedaily.com/rss/top.xml',
    'producthunt': 'https://www.producthunt.com/feed',
    'reddit-prog': 'https://www.reddit.com/r/programming/.rss',
}

LEGACY_SOURCE_MAP = {
    'rss-google': ['techcrunch', 'theverge', 'wired'],
    'rss-hnrss': ['hnrss'],
}

CATEGORY_KEYWORDS = {
    'ai-ml': ['ai', 'llm', 'gpt', 'machine learning', 'neural', 'openai', 'anthropic', 'model', 'ml', 'deep learning', 'transformer', 'claude', 'gemini'],
    'web-dev': ['javascript', 'react', 'css', 'frontend', 'node', 'typescript', 'browser', 'web', 'html', 'vue', 'svelte', 'nextjs'],
    'systems': ['linux', 'kernel', 'rust', 'c++', 'os', 'infrastructure', 'distributed', 'database', 'postgres', 'redis'],
    'crypto': ['crypto', 'blockchain', 'bitcoin', 'ethereum', 'web3', 'defi', 'nft', 'token'],
    'science': ['research', 'paper', 'study', 'physics', 'biology', 'math', 'climate', 'space', 'nasa'],
    'devtools': ['git', 'ide', 'vscode', 'editor', 'cli', 'terminal', 'docker', 'kubernetes', 'ci/cd', 'devtool'],
    'security': ['security', 'vulnerability', 'hack', 'exploit', 'privacy', 'encryption', 'malware', 'cve'],
    'open-source': ['open source', 'github', 'oss', 'foss', 'mit license', 'apache', 'contributor'],
}


def load_preferences():
    """Load preferences from ~/.vibereader/preferences.json, return None if not present."""
    if not os.path.exists(PREFERENCES_PATH):
        return None
    try:
        with open(PREFERENCES_PATH) as f:
            return json.load(f)
    except Exception as e:
        print(f"[vibe] Failed to load preferences: {e}", file=sys.stderr)
        return None


def tag_article(title, url):
    """Return list of matching category strings based on title and url."""
    text = (title + ' ' + url).lower()
    matched = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                matched.append(category)
                break
    return matched


def score_article(article_dict, prefs):
    """Return a float score for an article based on HN points, recency, and preferences."""
    # Base score from HN points (capped at 1.0)
    base = min(article_dict.get('score', 0) / 100, 1.0)

    # Recency bonus based on fetched_at
    fetched_at = article_dict.get('fetched_at', '')
    recency = 0.0
    if fetched_at:
        try:
            if isinstance(fetched_at, str):
                # Parse ISO format; handle both offset-aware and naive
                if fetched_at.endswith('Z'):
                    fetched_dt = datetime.fromisoformat(fetched_at.replace('Z', '+00:00'))
                else:
                    fetched_dt = datetime.fromisoformat(fetched_at)
                    if fetched_dt.tzinfo is None:
                        fetched_dt = fetched_dt.replace(tzinfo=timezone.utc)
            else:
                fetched_dt = fetched_at
                if fetched_dt.tzinfo is None:
                    fetched_dt = fetched_dt.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            age_seconds = (now - fetched_dt).total_seconds()
            if age_seconds < 3600:
                recency = 1.0
            elif age_seconds < 21600:
                recency = 0.5
        except Exception:
            pass

    # Preference match bonus (only if prefs provided)
    pref_bonus = 0.0
    if prefs is not None:
        preferred_categories = set(prefs.get('categories', []))
        article_categories = set(article_dict.get('categories', []))
        matches = len(preferred_categories & article_categories)
        pref_bonus = min(matches * 0.5, 1.0)

    return base + recency + pref_bonus


def serialize_article(a):
    d = asdict(a)
    for k, v in d.items():
        if isinstance(v, datetime):
            d[k] = v.isoformat()
    return d


async def safe_fetch(coro, source_name):
    """Run a fetch coroutine, return empty list on failure."""
    try:
        return await coro
    except Exception as e:
        print(f"[vibe] {source_name} fetch failed: {e}", file=sys.stderr)
        return []


# Module-level cache of url -> summary string, populated during run_fetch()
_summaries = {}


async def fetch_rss_with_summaries(url):
    """Fetch an RSS feed and return a dict mapping article URL -> summary string.

    Extracts the summary/description field from each entry, strips HTML tags,
    and truncates to 150 characters. Returns {} on any failure or if feedparser
    is not installed.
    """
    if not _FEEDPARSER_AVAILABLE:
        return {}
    try:
        raw = None
        if _AIOHTTP_AVAILABLE:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                        raw = await resp.text()
            except Exception:
                raw = None
        if raw is None:
            # Fallback: feedparser can fetch synchronously; run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, url)
        else:
            feed = feedparser.parse(raw)

        result = {}
        for entry in feed.get('entries', []):
            entry_url = entry.get('link', '')
            if not entry_url:
                continue
            raw_summary = entry.get('summary', '') or entry.get('description', '')
            # Strip HTML tags
            clean = re.sub(r'<[^>]+>', '', raw_summary).strip()
            # Truncate to 150 chars
            if len(clean) > 150:
                clean = clean[:150] + '...'
            result[entry_url] = clean
        return result
    except Exception as e:
        print(f"[vibe] Summary fetch failed for {url[:40]}: {e}", file=sys.stderr)
        return {}


async def run_fetch() -> None:
    """Fetch articles from all configured sources and save to ~/.vibereader/articles.json.

    This is the public API for this module. Equivalent to main() in the plugin's
    fetch-and-save.py script.
    """
    global _summaries

    if not _VIBEREADER_AVAILABLE:
        print("[vibe] Cannot fetch: vibereader package not installed. Run: pip install vibereader", file=sys.stderr)
        return

    prefs = load_preferences()

    # Resolve active sources
    if prefs and prefs.get('sources'):
        active_sources = set()
        for s in prefs['sources']:
            if s in LEGACY_SOURCE_MAP:
                active_sources.update(LEGACY_SOURCE_MAP[s])
            elif s in SOURCE_FEEDS:
                active_sources.add(s)
        # Always include 'hn' if it was in the original pref or legacy mapped
        if not active_sources:
            active_sources = set(SOURCE_FEEDS.keys())
    else:
        active_sources = set(SOURCE_FEEDS.keys())

    article_tasks = []
    rss_urls = []

    if 'hn' in active_sources:
        article_tasks.append(safe_fetch(fetch_hn(limit=20), "HackerNews"))

    for name, url in SOURCE_FEEDS.items():
        if name == 'hn' or url is None:
            continue
        if name in active_sources:
            article_tasks.append(safe_fetch(fetch_rss(url, limit=10), f"RSS({name})"))
            rss_urls.append(url)

    summary_tasks = [fetch_rss_with_summaries(url) for url in rss_urls]

    # Run article fetches and summary fetches in parallel
    all_results = await asyncio.gather(
        asyncio.gather(*article_tasks),
        asyncio.gather(*summary_tasks),
    )
    results, summary_results = all_results

    # Merge all url->summary dicts into the module-level cache
    for sd in summary_results:
        _summaries.update(sd)

    articles = []
    seen = set()
    for batch in results:
        for a in batch:
            if a.id not in seen:
                seen.add(a.id)
                articles.append(a)

    serialized = []
    for a in articles:
        d = serialize_article(a)
        d['categories'] = tag_article(d.get('title', ''), d.get('url', ''))
        d['score'] = score_article(d, prefs)
        d['summary'] = _summaries.get(d.get('url', ''), '')
        serialized.append(d)

    serialized.sort(key=lambda d: d['score'], reverse=True)

    data = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(serialized),
        "articles": serialized[:50],
    }

    os.makedirs(os.path.dirname(ARTICLES_PATH), exist_ok=True)
    tmp = ARTICLES_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, default=str)
    os.replace(tmp, ARTICLES_PATH)

    print(f"Saved {len(serialized)} articles to {ARTICLES_PATH}")


if __name__ == "__main__":
    asyncio.run(run_fetch())
