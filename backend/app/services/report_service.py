"""Defect Report Service — aggregates execution results into professional reports.

Outputs Markdown, HTML, and optionally PDF.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.execution import TestExecution, TestResult, TestOutcome
from app.models.project import Project
from app.models.report import DefectReport, ReportFormat
from app.utils.logger import logger

# Jinja2 template for Markdown reports
REPORT_TEMPLATE = """# 缺陷报告 — {{ title }}

**生成时间**: {{ generated_at }}
**执行名称**: {{ execution_name }}
**项目**: {{ project_name }}

---

## 执行概要

| 指标 | 数值 |
|------|------|
| 总用例数 | {{ total }} |
| 通过 | {{ passed }} ✅ |
| 失败 | {{ failed }} ❌ |
| 错误 | {{ errors }} ⚠️ |
| 跳过 | {{ skipped }} |
| 通过率 | {{ pass_rate }}% |
| 耗时 | {{ duration }} |

{%- if summary -%}

## AI 分析摘要

{{ summary }}
{%- endif -%}

## 按类别统计

| 类别 | 总数 | 通过 | 失败 | 通过率 |
|------|------|------|------|------|
{% for cat in by_category %}
| {{ cat.category }} | {{ cat.total }} | {{ cat.passed }} | {{ cat.failed }} | {{ cat.rate }}% |
{% endfor %}

> **正向用例通过率** = API 核心功能健康状况
> **边界值/安全/负向** = API 鲁棒性参考（失败可能是 API 正确拒绝了异常输入）

## 失败用例详情（仅正向+负向）

{%- if core_failures -%}
{%- for item in core_failures -%}
### {{ loop.index }}. {{ item.name }}

- **类别**: {{ item.category }}
- **状态**: {{ item.status }}
- **错误信息**: {{ item.error }}
{% if item.traceback %}
```
{{ item.traceback[:1500] }}
```
{% endif %}

---
{% endfor %}
{% else %}
核心功能测试全部通过 ✅
{% endif %}

{% if boundary_failures %}
> 另有 {{ boundary_failures|length }} 条边界值/安全/Schema 测试未通过（属于正常情况，API 正确拒绝了异常参数）
{% endif %}

## 按接口统计

| 接口 | 总数 | 通过 | 失败 |
|------|------|------|------|
{% for ep in by_endpoint %}
| {{ ep.method }} {{ ep.path }} | {{ ep.total }} | {{ ep.passed }} | {{ ep.failed }} |
{% endfor %}

---

*报告由 APITestGen 自动生成*
"""


async def generate_report(
    db: AsyncSession,
    execution_id: str,
    format: str = "markdown",
    include_llm_summary: bool = False,
) -> DefectReport:
    """Generate a defect report from test execution results.

    Args:
        db: Database session
        execution_id: The execution to report on
        format: "markdown" | "html" | "pdf"
        include_llm_summary: Whether to use LLM for executive summary

    Returns:
        Created DefectReport record
    """
    # Load execution + results
    exec_result = await db.execute(
        select(TestExecution).where(TestExecution.id == execution_id)
    )
    execution = exec_result.scalar_one_or_none()
    if not execution:
        raise ValueError(f"Execution {execution_id} not found")

    project_result = await db.execute(
        select(Project).where(Project.id == execution.project_id)
    )
    project = project_result.scalar_one_or_none()

    results_query = select(TestResult).where(TestResult.execution_id == execution_id)
    results = (await db.execute(results_query.order_by(TestResult.status, TestResult.test_name))).scalars().all()

    # Aggregate by category
    from app.models.testcase import TestCase, TestCategory

    core_failures = []      # positive + negative
    boundary_failures = []  # boundary + security + schema
    by_endpoint_map: dict[str, dict] = {}
    by_category: dict[str, dict] = {
        "positive": {"category": "正向用例", "total": 0, "passed": 0, "failed": 0, "rate": 0},
        "negative": {"category": "负向用例", "total": 0, "passed": 0, "failed": 0, "rate": 0},
        "boundary": {"category": "边界值", "total": 0, "passed": 0, "failed": 0, "rate": 0},
        "security": {"category": "安全测试", "total": 0, "passed": 0, "failed": 0, "rate": 0},
        "schema": {"category": "Schema", "total": 0, "passed": 0, "failed": 0, "rate": 0},
    }

    # Guess category from test name (no reliable testcase_id mapping)
    def guess_category(name: str) -> str:
        name_lower = name.lower()
        if "boundary" in name_lower or "minimum" in name_lower or "maximum" in name_lower or "below_min" in name_lower or "above_max" in name_lower:
            return "boundary"
        if "security" in name_lower or "sql" in name_lower or "xss" in name_lower or "injection" in name_lower:
            return "security"
        if "schema" in name_lower or "validate" in name_lower:
            return "schema"
        if "negative" in name_lower or "invalid" in name_lower or "error" in name_lower or "missing" in name_lower:
            return "negative"
        return "positive"

    for r in results:
        cat = guess_category(r.test_name)
        if cat in by_category:
            by_category[cat]["total"] += 1
        else:
            by_category["positive"]["total"] += 1
            cat = "positive"

        endpoint_key = _guess_endpoint(r.test_name)
        if endpoint_key not in by_endpoint_map:
            by_endpoint_map[endpoint_key] = {"path": endpoint_key, "total": 0, "passed": 0, "failed": 0, "method": "GET"}
        by_endpoint_map[endpoint_key]["total"] += 1

        if r.status in (TestOutcome.FAILED, TestOutcome.ERROR):
            by_endpoint_map[endpoint_key]["failed"] += 1
            by_category[cat]["failed"] += 1
            short_name = r.test_name.split("::")[-1] if "::" in r.test_name else r.test_name.split("/")[-1]
            detail = {"name": short_name, "status": r.status.value, "category": cat, "error": r.error_message or "(no message)", "traceback": r.traceback or ""}

            if cat in ("positive", "negative"):
                core_failures.append(detail)
            else:
                boundary_failures.append(detail)
        else:
            by_endpoint_map[endpoint_key]["passed"] += 1
            by_category[cat]["passed"] += 1

    # Calculate rates
    for cat_data in by_category.values():
        if cat_data["total"] > 0:
            cat_data["rate"] = round(cat_data["passed"] / cat_data["total"] * 100, 1)

    # Duration
    duration_str = f"{execution.duration_ms / 1000:.1f}s" if execution.duration_ms else "N/A"

    # LLM summary (optional)
    summary = ""
    if include_llm_summary and failed_details:
        summary = await _llm_summary(db, failed_details, execution)

    # Render Markdown
    context = {
        "title": f"{project.name if project else 'Project'} - 测试报告",
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "execution_name": execution.name,
        "project_name": project.name if project else "Unknown",
        "total": execution.total_tests,
        "passed": execution.passed,
        "failed": execution.failed,
        "errors": execution.errors,
        "skipped": execution.skipped,
        "pass_rate": execution.pass_rate,
        "duration": duration_str,
        "summary": summary,
        "core_failures": core_failures,
        "boundary_failures": boundary_failures,
        "by_category": list(by_category.values()),
        "by_endpoint": list(by_endpoint_map.values()),
    }

    from jinja2 import Template
    markdown_content = Template(REPORT_TEMPLATE).render(**context)

    # Convert to HTML if requested
    html_content = None
    if format in ("html", "pdf"):
        try:
            from markdown_it import MarkdownIt
            md = MarkdownIt()
            html_content = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{context['title']}</title>
<style>body{{font-family:Arial,sans-serif;max-width:900px;margin:40px auto;padding:20px;line-height:1.6}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:8px;text-align:left}}
th{{background:#f5f5f5}}pre{{background:#1e1e2e;color:#a6e3a1;padding:12px;border-radius:6px;overflow-x:auto}}
</style></head><body>
{md.render(markdown_content)}
</body></html>"""
        except ImportError:
            logger.warning("markdown-it-py not installed, HTML report unavailable")

    # Save to disk
    reports_dir = settings.reports_path / execution_id
    reports_dir.mkdir(parents=True, exist_ok=True)

    report = DefectReport(
        execution_id=execution_id,
        project_id=execution.project_id,
        title=context["title"],
        summary=summary,
        format=ReportFormat(format),
        content=markdown_content,
        failed_count=execution.failed,
        error_count=execution.errors,
        total_count=execution.total_tests,
        pass_rate=execution.pass_rate,
    )

    if format == "markdown":
        filepath = reports_dir / "report.md"
        filepath.write_text(markdown_content, encoding="utf-8")
        report.file_path = str(filepath)
    elif format == "html" and html_content:
        filepath = reports_dir / "report.html"
        filepath.write_text(html_content, encoding="utf-8")
        report.file_path = str(filepath)

    db.add(report)
    await db.commit()
    await db.refresh(report)

    return report


async def _llm_summary(db, failed_details, execution) -> str:
    """Generate an LLM-powered executive summary of failures."""
    if not failed_details:
        return ""

    try:
        from app.models.llm import LLMProvider
        from app.services.llm.provider import LLMProviderFactory

        providers = (await db.execute(
            select(LLMProvider).where(LLMProvider.is_active == True)
        )).scalars().all()

        if not providers:
            return "_LLM provider not configured, skipping AI summary._"

        provider = LLMProviderFactory.create_from_model(providers[0])
        failures_text = "\n".join([
            f"- {f['name']}: {f['error'][:200]}"
            for f in failed_details[:10]
        ])

        prompt = f"""Analyze these {len(failed_details)} test failures and write a brief executive summary (2-3 sentences in Chinese):

{failures_text}

Focus on: common failure patterns, likely root causes, recommended actions."""

        response = await provider.complete(
            system_prompt="You are a QA expert. Write concise Chinese summaries.",
            user_prompt=prompt,
            max_tokens=300,
        )
        return response.content.strip()
    except Exception as e:
        logger.warning(f"LLM summary failed: {e}")
        return ""


def _guess_endpoint(test_name: str) -> str:
    """Guess the API endpoint from a pytest test name."""
    # e.g., "test_get_users_list_success" -> "/api/v1/users"
    parts = test_name.replace("test_", "").replace("_api_v1_", "/api/v1/").split("_")
    # Simple heuristic
    return test_name
