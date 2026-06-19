"""Fetching layer: read RSS feeds and extract clean article text.

Uses RSS (feedparser) for incremental discovery and trafilatura for clean
main-content extraction. Falls back to raw HTML if trafilatura is missing.
"""

import urllib.request

import feedparser

try:
    import trafilatura
    _HAS_TRAF = True
except ImportError:  # pragma: no cover
    _HAS_TRAF = False

USER_AGENT = "ai-research-kb/1.0 (personal research digest; +https://github.com/A-ZHANG1)"


def parse_feeds(feeds):
    """Return a flat list of {url, title, published, source} from all feeds."""
    items = []
    for feed in feeds:
        parsed = feedparser.parse(feed)
        source = ""
        if getattr(parsed, "feed", None):
            source = parsed.feed.get("title", "") or feed
        for entry in parsed.entries:
            link = entry.get("link")
            if not link:
                continue
            items.append({
                "url": link,
                "title": entry.get("title", "(no title)"),
                "published": entry.get("published", entry.get("updated", "")),
                "source": source or feed,
            })
    return items


def extract_content(url, timeout=20):
    """Best-effort clean text extraction for a single article URL."""
    if _HAS_TRAF:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False)
            if text:
                return text
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return None
