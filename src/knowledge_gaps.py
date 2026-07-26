"""Knowledge-gap report: for a topic defined in config/knowledge_map.yaml,
check how much each concept has actually shown up in the kb.db corpus so far,
and flag genuine gaps vs. shallow vs. solid exposure.

This is deliberately a simple keyword-presence heuristic, not true semantic
understanding -- "exposure" (the concept appeared in something you were sent)
is a proxy for "you've had a chance to learn this", not proof you understood
it. Treat the report as a prompt for what to read up on, not a grade.

Usage: python src/knowledge_gaps.py [--out report.md]
"""
import argparse
import datetime
import email.utils
import pathlib

import yaml

from memory import Memory

BASE = pathlib.Path(__file__).resolve().parent.parent

# Thresholds for classifying exposure depth by number of distinct matching
# articles found across all of a concept's aliases.
GAP_MAX = 0        # 0 matches: never appeared at all
SHALLOW_MAX = 2     # 1-2 matches: shown up in passing


def load_knowledge_map(path):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("topic", "Untitled"), data.get("concepts", [])


def parse_published(value):
    """Best-effort parse of the `published` field, which mixes ISO 8601 and
    RFC 822 formats across feeds. Returns an aware/naive datetime, or None if
    unparseable (treated as "unknown, sort last" rather than crashing)."""
    if not value:
        return None
    try:
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pass
    try:
        return email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None


def find_matches(mem, aliases):
    """Search kb.db for any of a concept's aliases; dedupe by URL, most
    recently PUBLISHED first (not most recently fetched -- kb.db also holds a
    lot of old backlog that was only fetched/inserted recently)."""
    MIN_DT = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)

    def sort_key(row):
        dt = parse_published(row.get("published"))
        if dt is None:
            return MIN_DT
        if dt.tzinfo is None:  # normalize naive datetimes so comparisons don't crash
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt

    seen = {}
    for alias in aliases:
        for row in mem.search(alias, limit=50):
            seen[row["url"]] = row
    return sorted(seen.values(), key=sort_key, reverse=True)


def classify(count):
    if count <= GAP_MAX:
        return "gap"
    if count <= SHALLOW_MAX:
        return "shallow"
    return "solid"


LABELS = {
    "gap": ("\u274c", "从未出现"),
    "shallow": ("\u26a0\ufe0f", "浅提及"),
    "solid": ("\u2705", "多次深入提及"),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(BASE / "knowledge_gap_report.md"))
    args = parser.parse_args()

    topic, concepts = load_knowledge_map(BASE / "config" / "knowledge_map.yaml")
    mem = Memory(BASE / "kb.db")

    rows = []
    for c in concepts:
        name = c["name"]
        aliases = c.get("aliases", [name])
        matches = find_matches(mem, aliases)
        status = classify(len(matches))
        icon, label = LABELS[status]
        latest = matches[0]["published"] if matches else None
        rows.append({
            "name": name, "status": status, "icon": icon, "label": label,
            "count": len(matches), "latest": latest,
            "examples": matches[:3],
        })
    mem.close()

    today = datetime.date.today().isoformat()
    lines = [f"# 知识图谱状态 — {topic}（{today}）\n"]
    lines.append("基于 kb.db 语料库里出现过的次数做的粗略判断（关键词命中≠真正理解，仅供参考下一步该读什么）：\n")
    lines.append("| 状态 | 概念 | 命中次数 | 最近一次 |")
    lines.append("|---|---|---|---|")
    for r in rows:
        lines.append(f"| {r['icon']} {r['label']} | {r['name']} | {r['count']} | {r['latest'] or '-'} |")

    gaps = [r for r in rows if r["status"] == "gap"]
    shallow = [r for r in rows if r["status"] == "shallow"]
    if gaps:
        lines.append("\n## \u274c 完全没出现过（建议主动找资料补）\n")
        for r in gaps:
            lines.append(f"- {r['name']}")
    if shallow:
        lines.append("\n## \u26a0\ufe0f 只是浅提及（可能只是听过名字）\n")
        for r in shallow:
            lines.append(f"- **{r['name']}**（{r['count']}次）")
            for ex in r["examples"]:
                lines.append(f"  - [{ex['title']}]({ex['url']})")

    report = "\n".join(lines) + "\n"
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Wrote knowledge gap report to {args.out}")
    print(f"gap={len(gaps)} shallow={len(shallow)} solid={len(rows) - len(gaps) - len(shallow)}")


if __name__ == "__main__":
    main()
