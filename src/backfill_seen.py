"""Utility: mark OLD backlog entries as seen without summarizing (fast, no
network calls). Useful whenever a feed's current RSS window has old entries
that were never processed (e.g. right after adding a new source, or after a
capped bootstrap like --limit-per-feed).

IMPORTANT: only entries OLDER than --max-age-days are touched. Anything more
recent is left alone so the normal fetch_new.py -> summarize -> commit flow
picks it up and actually surfaces it to the user. (The first version of this
script had no age cutoff and silently swallowed 20 genuinely recent articles,
including a same-day model release announcement -- see the incident fixed on
2026-07-26. Do not remove the cutoff.)
"""
import argparse
import datetime
import pathlib
import time

import feedparser
import yaml

from memory import Memory

BASE = pathlib.Path(__file__).resolve().parent.parent


def load_feeds(path):
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data.get("feeds", [])


def entry_age_days(entry):
    """Return how many days old an entry is, or None if no parseable date."""
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    entry_time = time.mktime(parsed)
    return (time.time() - entry_time) / 86400


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-age-days", type=float, default=3.0,
                         help="Only silently mark entries older than this as seen; "
                              "leave anything more recent for the normal summarize flow")
    args = parser.parse_args()

    feeds = load_feeds(BASE / "config" / "sources.yaml")
    mem = Memory(BASE / "kb.db")

    marked = 0
    skipped_recent = 0
    for feed in feeds:
        parsed_feed = feedparser.parse(feed)
        source = ""
        if getattr(parsed_feed, "feed", None):
            source = parsed_feed.feed.get("title", "") or feed
        for entry in parsed_feed.entries:
            url = entry.get("link")
            if not url or mem.is_seen(url):
                continue

            age = entry_age_days(entry)
            if age is None or age < args.max_age_days:
                # Unknown date, or too recent: don't swallow it silently --
                # let it flow through fetch_new.py/summarize/commit instead.
                skipped_recent += 1
                continue

            mem.add_article(
                url, source=source or feed,
                title=entry.get("title", "(no title)"),
                published=entry.get("published", entry.get("updated", "")),
                content=None,
                summary="_(backlog, older than cutoff, not summarized)_",
            )
            marked += 1

    mem.close()
    print(f"Marked {marked} backlog article(s) (older than {args.max_age_days} days) as seen.")
    print(f"Left {skipped_recent} more recent (or undated) article(s) untouched for the normal flow.")


if __name__ == "__main__":
    main()
