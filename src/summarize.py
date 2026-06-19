"""Summarization layer: provider-agnostic.

Set LLM_PROVIDER + the matching API key for real summaries (Anthropic/OpenAI).
Without keys it falls back to a cheap extractive snippet so the pipeline still
runs end-to-end (useful for testing).
"""

import os
import re

SUMMARY_PROMPT = """You are a research assistant tracking AI agents, AI \
infrastructure, and data/AI platforms (Microsoft Fabric, Databricks, etc.).

Summarize the article below in 3-5 concise bullet points focused on what is \
new or notable. Then add one final line starting with "Why it matters:".

Title: {title}

Content:
{content}
"""


def summarize(title, content, max_chars=8000):
    content = (content or "")[:max_chars]
    if not content.strip():
        return "_(no extractable content)_"
    provider = os.getenv("LLM_PROVIDER", "").lower()
    if provider == "anthropic" and os.getenv("ANTHROPIC_API_KEY"):
        return _anthropic(title, content)
    if provider == "openai" and os.getenv("OPENAI_API_KEY"):
        return _openai(title, content)
    return _extractive(content)


def _anthropic(title, content):
    import anthropic

    client = anthropic.Anthropic()
    model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")
    msg = client.messages.create(
        model=model,
        max_tokens=400,
        messages=[{"role": "user",
                   "content": SUMMARY_PROMPT.format(title=title, content=content)}],
    )
    return msg.content[0].text.strip()


def _openai(title, content):
    from openai import OpenAI

    client = OpenAI()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    resp = client.chat.completions.create(
        model=model,
        max_tokens=400,
        messages=[{"role": "user",
                   "content": SUMMARY_PROMPT.format(title=title, content=content)}],
    )
    return resp.choices[0].message.content.strip()


def _extractive(content):
    sentences = re.split(r"(?<=[.!?])\s+", content.strip())
    snippet = " ".join(sentences[:3])[:500]
    return (f"- {snippet}\n"
            "- _(set LLM_PROVIDER + API key in .env for real LLM summaries)_")
