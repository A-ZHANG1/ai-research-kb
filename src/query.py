"""Query the long-term memory (the accumulated KB).

Usage:
    python src/query.py                 # show 15 most recent articles
    python src/query.py agent memory    # keyword search the corpus
"""

import pathlib
import sys

from memory import Memory

BASE = pathlib.Path(__file__).resolve().parent.parent


def main():
    mem = Memory(BASE / "kb.db")
    if len(sys.argv) < 2:
        print("# Recent articles in long-term memory\n")
        for a in mem.recent(15):
            print(f"- {a['fetched_at'][:10]} [{a['source']}] {a['title']}")
            print(f"  {a['url']}")
    else:
        keyword = " ".join(sys.argv[1:])
        results = mem.search(keyword)
        print(f"# {len(results)} result(s) for '{keyword}'\n")
        for a in results:
            print(f"- [{a['source']}] {a['title']}")
            print(f"  {a['url']}")
            if a.get("summary"):
                print(f"  {a['summary'][:200]}")
            print()
    print(f"\n[memory stats] {mem.stats()}")
    mem.close()


if __name__ == "__main__":
    main()
