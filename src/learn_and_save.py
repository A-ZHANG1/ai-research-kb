"""Save a piece of knowledge learned ad hoc (while answering a question, not
from the daily RSS pipeline) into the long-term memory kb.db, so future
questions can find it via `query.py` / `Memory.search()` instead of
re-searching the web every time.

This is the "self-learning" half of the self-learn-kb skill: after a live
web search turns up something genuinely new and substantive about an AI
Agent / AI Infra / Lakehouse topic, save it here.

Usage:
    python src/learn_and_save.py --url URL --title TITLE --category CATEGORY \
        --summary "..." [--source SOURCE] [--content-file PATH]

Categories (informal, freeform but keep it to one of these for consistency):
    architecture | error-code | api | session-insight | general
"""
import argparse
import pathlib

from memory import Memory

BASE = pathlib.Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--summary", required=True,
                         help="Concise Chinese summary of what was learned and why it matters")
    parser.add_argument("--category", default="general",
                         choices=["architecture", "error-code", "api", "session-insight", "general"])
    parser.add_argument("--source", default="self-learn",
                         help="Where this came from, e.g. a site name or 'session-insight'")
    parser.add_argument("--content-file", default=None,
                         help="Optional path to a file with the full fetched content")
    args = parser.parse_args()

    content = None
    if args.content_file:
        with open(args.content_file, "r", encoding="utf-8") as f:
            content = f.read()

    mem = Memory(BASE / "kb.db")
    already_seen = mem.is_seen(args.url)
    mem.add_article(
        args.url, source=args.source, title=args.title,
        published=None, content=content, summary=args.summary,
        category=args.category,
    )
    stats = mem.stats()
    mem.close()

    if already_seen:
        print(f"Already in kb.db (not re-added): {args.url}")
    else:
        print(f"Learned and saved: {args.title} [{args.category}]")
    print(f"memory stats: {stats}")


if __name__ == "__main__":
    main()
