"""Quality gate for summaries that are safe to publish in a digest."""

PLACEHOLDER_PHRASES = (
    "摘录仅包含",
    "无可靠内容",
    "材料不足",
    "无法总结",
    "抓取失败",
    "摘要暂缺",
    "no extractable content",
)


def rejection_reason(summary):
    text = (summary or "").strip()
    if not text:
        return "summary is empty"
    for phrase in PLACEHOLDER_PHRASES:
        if phrase.lower() in text.lower():
            return f"placeholder phrase: {phrase}"
    if "Why it matters：" not in text:
        return "missing Why it matters"
    return None
