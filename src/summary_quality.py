"""Quality gate for summaries that are safe to publish in a digest."""

PLACEHOLDER_PHRASES = (
    "摘录仅包含",
    "无可靠内容",
    "材料不足",
    "无法总结",
    "抓取失败",
    "摘要暂缺",
    "no extractable content",
    "与 ai agent、ai infra 或 lakehouse 无关",
    "与ai/技术关系较弱",
    "与 ai/技术关系较弱",
    "本期从略",
    "why it matters：无",
    "无相关技术实践价值",
)


def rejection_reason(summary):
    text = (summary or "").strip()
    if not text:
        return "summary is empty"
    for phrase in PLACEHOLDER_PHRASES:
        if phrase.lower() in text.lower():
            return f"placeholder phrase: {phrase}"
    lines = [line.strip() for line in text.splitlines()]
    if not any(line.startswith("- Why it matters：") for line in lines):
        return "missing standalone Why it matters bullet"
    return None
