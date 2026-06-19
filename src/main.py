"""Orchestrator — cron entrypoint.

Flow: load sources -> for each RSS item, skip if already in long-term memory,
else fetch + summarize + store -> build digest of NEW items -> deliver.
"""

import pathlib

import yaml

from digest import build_digest
from fetch import extract_content, parse_feeds
from memory import Memory
from notify import deliver
from summarize import summarize

BASE = pathlib.Path(__file__).resolve().parent.parent


def load_feeds(path):
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data.get("feeds", [])


def run():
    feeds = load_feeds(BASE / "config" / "sources.yaml")
    mem = Memory(BASE / "kb.db")

    new_items = []
    for item in parse_feeds(feeds):
        url = item["url"]
        if mem.is_seen(url):          # long-term memory => only new posts
            continue
        content = extract_content(url)
        summary = summarize(item["title"], content)
        mem.add_article(url, source=item.get("source"), title=item.get("title"),
                        published=item.get("published"), content=content,
                        summary=summary)
        item["summary"] = summary
        new_items.append(item)

    mem.log_run(len(new_items))
    digest = build_digest(new_items)
    out = deliver(digest, out_dir=str(BASE / "digests"))

    print(f"[ai-research-kb] {len(new_items)} new article(s). Digest: {out}")
    print(f"[ai-research-kb] memory: {mem.stats()}")
    mem.close()


if __name__ == "__main__":
    run()
