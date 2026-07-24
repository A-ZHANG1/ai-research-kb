"""Fetch NEW articles only (dedup against long-term memory) and dump them as
JSON -- without summarizing. Summarization is done externally by the calling
LLM agent (no separate Anthropic/OpenAI API key needed), then written back
via commit_and_notify.py.

Usage: python src/fetch_new.py [--out OUTPUT_PATH] [--limit-per-feed N]
       (--out defaults to new_items.json in the repo root, always written as
       UTF-8 so it isn't at the mercy of the Windows console's default
       codepage; --limit-per-feed caps how many entries per feed are
       considered -- mainly useful for the very first bootstrap run against
       an empty kb.db, where every current entry in every feed would
       otherwise count as "new" and take a long time to fetch)
"""
import argparse
import json
import pathlib

import yaml

from fetch import extract_content, parse_feeds
from memory import Memory

BASE = pathlib.Path(__file__).resolve().parent.parent


def load_feeds(path):
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data.get("feeds", [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(BASE / "new_items.json"))
    parser.add_argument("--limit-per-feed", type=int, default=None,
                         help="Only look at the N most recent entries per feed")
    args = parser.parse_args()

    feeds = load_feeds(BASE / "config" / "sources.yaml")
    mem = Memory(BASE / "kb.db")

    # Group parsed entries by feed so --limit-per-feed can cap each feed
    # independently (parse_feeds already flattens everything into one list,
    # but entries stay in feed order so a simple per-source counter works).
    per_feed_seen = {}
    new_items = []
    for item in parse_feeds(feeds):
        if args.limit_per_feed is not None:
            count = per_feed_seen.get(item["source"], 0)
            if count >= args.limit_per_feed:
                continue
            per_feed_seen[item["source"]] = count + 1

        url = item["url"]
        if mem.is_seen(url):  # long-term memory => only new posts
            continue
        item["content"] = extract_content(url)
        new_items.append(item)

    mem.close()
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(new_items, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(new_items)} new item(s) to {args.out}")


if __name__ == "__main__":
    main()
