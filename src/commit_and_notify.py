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
from summary_quality import rejection_reason

BASE = pathlib.Path(__file__).resolve().parent.parent


def main():
    items_path = sys.argv[1]
    with open(items_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    mem = Memory(BASE / "kb.db")
    publishable = []
    rejected = []
    for it in items:
        reason = rejection_reason(it.get("summary"))
        if reason:
            rejected.append((it, reason))
            mem.add_article(
                it["url"], source=it.get("source"), title=it.get("title"),
                published=it.get("published"), content=it.get("content"),
                summary=None, category="skipped",
            )
            continue

        mem.add_article(
            it["url"], source=it.get("source"), title=it.get("title"),
            published=it.get("published"), content=it.get("content"),
            summary=it.get("summary"),
        )
        publishable.append(it)

    if not publishable:
        mem.close()
        raise SystemExit("No publishable summaries; digest was not generated.")

    mem.log_run(len(publishable))

    digest_md = build_digest(publishable)
    out = deliver(digest_md, out_dir=str(BASE / "digests"))

    for it, reason in rejected:
        print(f"[quality] omitted {it.get('title')!r}: {reason}")
    print(f"[ai-research-kb] {len(publishable)} published, "
          f"{len(rejected)} omitted. Digest: {out}")
    print(f"[ai-research-kb] memory: {mem.stats()}")
    mem.close()


if __name__ == "__main__":
    main()
