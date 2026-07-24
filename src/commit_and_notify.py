"""Take new items (with `summary` already filled in by the calling LLM agent)
from a JSON file, persist them into long-term memory (kb.db), build the
Markdown digest, and write it to disk. Email delivery is handled separately
(by AI-Builders-Digest's Resend-based send_digest_email.py), not here.

Usage: python src/commit_and_notify.py items_with_summaries.json
"""
import json
import pathlib
import sys

from digest import build_digest
from memory import Memory
from notify import deliver

BASE = pathlib.Path(__file__).resolve().parent.parent


def main():
    items_path = sys.argv[1]
    with open(items_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    mem = Memory(BASE / "kb.db")
    for it in items:
        mem.add_article(
            it["url"], source=it.get("source"), title=it.get("title"),
            published=it.get("published"), content=it.get("content"),
            summary=it.get("summary"),
        )
    mem.log_run(len(items))

    digest_md = build_digest(items)
    out = deliver(digest_md, out_dir=str(BASE / "digests"))

    print(f"[ai-research-kb] {len(items)} new article(s). Digest: {out}")
    print(f"[ai-research-kb] memory: {mem.stats()}")
    mem.close()


if __name__ == "__main__":
    main()
