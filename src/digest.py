"""Build a daily Markdown digest from the new articles of a run."""

import datetime


def build_digest(new_items):
    today = datetime.date.today().isoformat()
    if not new_items:
        return f"# AI Research Digest — {today}\n\n今天没有新文章。\n"

    lines = [f"# AI Research Digest — {today}\n",
             f"共 **{len(new_items)}** 篇新文章。\n"]

    by_source = {}
    for it in new_items:
        by_source.setdefault(it.get("source") or "Unknown", []).append(it)

    for source, items in by_source.items():
        lines.append(f"\n## {source}\n")
        for it in items:
            lines.append(f"### [{it['title']}]({it['url']})")
            if it.get("published"):
                lines.append(f"*{it['published']}*\n")
            lines.append(it.get("summary") or "")
            lines.append("")
    return "\n".join(lines)
