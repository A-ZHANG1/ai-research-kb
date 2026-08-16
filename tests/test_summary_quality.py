import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from summary_quality import rejection_reason  # noqa: E402


def test_rejects_placeholder_summary():
    summary = (
        "- 摘录仅包含网页 HTML，除标题外无可靠内容可总结。\n"
        "Why it matters：现有材料不足以判断具体影响。"
    )
    assert rejection_reason(summary) is not None


def test_rejects_missing_why_it_matters():
    assert (
        rejection_reason("- 一个没有结论的摘要")
        == "missing standalone Why it matters bullet"
    )


def test_rejects_non_bullet_why_it_matters():
    summary = (
        "- 一条实质摘要。\n"
        "Why it matters：这一行没有使用 bullet。"
    )
    assert rejection_reason(summary) == "missing standalone Why it matters bullet"


def test_rejects_irrelevant_omission_summary():
    summary = (
        "- 与 AI Agent、AI Infra 或 Lakehouse 无关，略过。\n"
        "Why it matters：无相关技术实践价值。"
    )
    assert rejection_reason(summary) is not None


def test_accepts_substantive_summary():
    summary = (
        "- dbt State 用缓存减少重复解析和仓库计算。\n"
        "- Why it matters：缩短运行时间并降低数据仓库成本。"
    )
    assert rejection_reason(summary) is None
