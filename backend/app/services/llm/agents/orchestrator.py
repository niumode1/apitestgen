"""Agent Orchestrator — coordinates multi-agent test generation pipeline.

Processes endpoints in parallel batches for speed.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.events import EventBus, EventType, ExecutionEvent
from app.models.endpoint import APIEndpoint, HTTPMethod
from app.models.project import Project
from app.models.spec import OpenAPISpec
from app.models.testcase import TestCase, TestCaseStatus, TestCategory
from app.services.llm.agents.analyzer import EndpointAnalyzerAgent
from app.services.llm.agents.positive import PositiveCaseAgent
from app.services.llm.agents.negative import NegativeCaseAgent
from app.services.llm.agents.boundary import BoundaryValueAgent
from app.services.llm.agents.security import SecurityPayloadAgent
from app.services.llm.agents.schema_v import SchemaValidationAgent
from app.services.llm.codegen import (
    CodeGenResult,
    ParsedTestCase,
    assemble_test_file,
    generate_conftest,
    parse_llm_output,
    slugify_path,
    write_test_file,
)
from app.services.llm.provider import BaseLLMProvider, LLMProviderFactory
from app.services.llm.token_counter import estimate_cost, estimate_tokens
from app.utils.logger import logger

ProgressCallback = Callable[[str, str, int, int, int], Any]

# Number of concurrent endpoint tasks — balances speed vs API rate limits
# "all" strategy runs 5 agents per endpoint, so use lower concurrency
MAX_CONCURRENT = 3


class AgentOrchestrator:
    """Orchestrates the test generation pipeline for a spec."""

    def __init__(
        self,
        provider: BaseLLMProvider,
        db: AsyncSession,
        event_bus: Optional[EventBus] = None,
    ):
        self.provider = provider
        self.db = db
        self.event_bus = event_bus
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async def _emit_event(self, resource_id: str, event_type: EventType, payload: dict[str, Any]) -> None:
        if self.event_bus:
            await self.event_bus.publish(ExecutionEvent(
                resource_id=resource_id, event_type=event_type, payload=payload,
            ))

    async def generate_for_spec(
        self,
        spec_id: str,
        endpoint_ids: Optional[list[str]] = None,
        strategy: str = "positive_only",
        max_testcases_per_endpoint: int = 10,
        review_enabled: bool = False,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> dict[str, Any]:
        generation_id = str(uuid4())

        spec = (await self.db.execute(select(OpenAPISpec).where(OpenAPISpec.id == spec_id))).scalar_one_or_none()
        if not spec:
            raise ValueError(f"Spec {spec_id} not found")

        project = (await self.db.execute(select(Project).where(Project.id == spec.project_id))).scalar_one_or_none()
        base_url = project.base_url if project else "http://localhost"

        query = select(APIEndpoint).where(APIEndpoint.spec_id == spec_id)
        if endpoint_ids:
            query = query.where(APIEndpoint.id.in_(endpoint_ids))
        endpoints = (await self.db.execute(query)).scalars().all()

        if not endpoints:
            return {"error": "No endpoints found", "testcases_generated": 0}

        # Output dir + conftest
        tests_dir = settings.generated_tests_path / project.id / spec_id
        tests_dir.mkdir(parents=True, exist_ok=True)
        write_test_file(generate_conftest(base_url), tests_dir / "conftest.py")

        # ── Process endpoints in parallel with semaphore ──
        total = 0
        prompt_tokens_total = 0
        completion_tokens_total = 0
        all_errors: list[str] = []
        by_category: dict[str, int] = {}
        completed = 0
        lock = asyncio.Lock()

        async def process_one(endpoint: APIEndpoint) -> tuple[int, dict[str, int], int, int, list[str]]:
            nonlocal completed, total
            tc_count = 0
            cat_count: dict[str, int] = {}
            pt = 0
            ct = 0
            errs: list[str] = []

            ep_path = f"{endpoint.method.value} {endpoint.path}"

            async with self.semaphore:
                # Step 1: Analyze
                try:
                    ep_ctx = self._build_endpoint_context(endpoint)
                    # Create a fresh agent per endpoint (avoids shared state issues)
                    analyzer = EndpointAnalyzerAgent(self.provider)
                    analysis = await analyzer.analyze(ep_ctx)
                    pt += analysis.pop("_meta", {}).get("prompt_tokens", 0)
                    ct += analysis.pop("_meta", {}).get("completion_tokens", 0)
                    endpoint.analysis = analysis
                    endpoint.analyzed_at = datetime.utcnow()
                except Exception as e:
                    logger.error(f"Analysis failed: {ep_path}: {e}")
                    errs.append(f"Analysis: {ep_path}: {e}")
                    async with lock:
                        completed += 1
                        if progress_callback:
                            await progress_callback("error", ep_path, completed, len(endpoints), total)
                    return 0, {}, pt, ct, errs

                # Step 2: Run selected agent(s) in parallel per endpoint
                agent_tasks: list[tuple[str, Any]] = []
                count = min(3, max_testcases_per_endpoint)

                if strategy in ("all", "positive_only"):
                    agent_tasks.append(("positive", PositiveCaseAgent(self.provider).generate(
                        endpoint=ep_ctx, analysis=analysis, count=count)))

                if strategy in ("all", "negative_only"):
                    agent_tasks.append(("negative", NegativeCaseAgent(self.provider).generate(
                        endpoint=ep_ctx, analysis=analysis, count=count)))

                if strategy in ("all", "boundary_only"):
                    agent_tasks.append(("boundary", BoundaryValueAgent(self.provider).generate(
                        endpoint=ep_ctx, analysis=analysis, count=count)))

                if strategy in ("all", "security_only"):
                    agent_tasks.append(("security", SecurityPayloadAgent(self.provider).generate(
                        endpoint=ep_ctx, analysis=analysis, count=count)))

                if strategy in ("all", "schema_only"):
                    agent_tasks.append(("schema", SchemaValidationAgent(self.provider).generate(
                        endpoint=ep_ctx, analysis=analysis, count=count)))

                # Run selected agents in parallel
                agent_results = await asyncio.gather(
                    *[task for _, task in agent_tasks], return_exceptions=True
                )

                category_map = {
                    "positive": TestCategory.POSITIVE,
                    "negative": TestCategory.NEGATIVE,
                    "boundary": TestCategory.BOUNDARY,
                    "security": TestCategory.SECURITY,
                    "schema": TestCategory.SCHEMA,
                }

                for idx, (cat_name, _) in enumerate(agent_tasks):
                    result = agent_results[idx]
                    if isinstance(result, Exception):
                        logger.error(f"{cat_name} gen failed: {ep_path}: {result}")
                        errs.append(f"{cat_name}: {ep_path}: {result}")
                        continue
                    try:
                        code, p, c = result
                        pt += p
                        ct += c
                        parsed = parse_llm_output(code)
                        cat_enum = category_map.get(cat_name, TestCategory.POSITIVE)
                        saved = await self._save_testcases(
                            endpoint, parsed, cat_enum, project.id, spec_id)
                        tc_count += saved
                        cat_count[cat_name] = cat_count.get(cat_name, 0) + saved
                    except Exception as e:
                        logger.error(f"{cat_name} parse/save failed: {ep_path}: {e}")
                        errs.append(f"{cat_name}: {ep_path}: {e}")

                self.db.add(endpoint)

                async with lock:
                    completed += 1
                    if progress_callback:
                        await progress_callback("done", ep_path, completed, len(endpoints), total + tc_count)

                return tc_count, cat_count, pt, ct, errs

        # Fire all tasks concurrently (limited by semaphore)
        results = await asyncio.gather(*[process_one(ep) for ep in endpoints])

        # Aggregate from return values only (no more double counting)
        for tc, cats, p, c, errs in results:
            total += tc
            prompt_tokens_total += p
            completion_tokens_total += c
            all_errors.extend(errs)
            for cat, cnt in cats.items():
                by_category[cat] = by_category.get(cat, 0) + cnt

        await self.db.commit()

        status = "failed" if (total == 0 and all_errors) else "completed"

        summary = {
            "generation_id": generation_id,
            "spec_id": spec_id,
            "status": status,
            "endpoints_processed": len(endpoints),
            "total_testcases_generated": total,
            "by_category": by_category,
            "total_prompt_tokens": prompt_tokens_total,
            "total_completion_tokens": completion_tokens_total,
            "estimated_cost_usd": estimate_cost(prompt_tokens_total, completion_tokens_total, self.provider.model),
            "errors": all_errors,
            "completed_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Generation complete: {summary}")
        return summary

    async def _save_testcases(
        self, endpoint: APIEndpoint, parsed: CodeGenResult,
        category: TestCategory, project_id: str, spec_id: str,
    ) -> int:
        count = 0
        for tc in parsed.test_cases:
            testcase = TestCase(
                project_id=project_id, endpoint_id=endpoint.id, spec_id=spec_id,
                name=f"[{category.value}] {tc.function_name}",
                description=tc.description or f"{category.value} test for {endpoint.method.value} {endpoint.path}",
                category=category, test_code=tc.code, input_params={},
                expected_status=tc.expected_status,
                llm_model=self.provider.model,
                status=TestCaseStatus.DRAFT,
            )
            self.db.add(testcase)
            count += 1
        return count

    def _build_endpoint_context(self, endpoint: APIEndpoint) -> dict[str, Any]:
        return {
            "path": endpoint.path,
            "method": endpoint.method.value,
            "summary": endpoint.summary,
            "description": endpoint.description,
            "operation_id": endpoint.operation_id,
            "tags": endpoint.tags or [],
            "parameters": endpoint.parameters or [],
            "request_body": endpoint.request_body,
            "responses": endpoint.responses or {},
            "security": endpoint.security,
            "deprecated": endpoint.deprecated,
        }


async def write_endpoint_test_files(db: AsyncSession, project_id: str, spec_id: str) -> int:
    """Write all generated test cases to .py files grouped by endpoint."""
    from app.models.endpoint import APIEndpoint
    from app.models.testcase import TestCase, TestCaseStatus

    result = await db.execute(select(OpenAPISpec).where(OpenAPISpec.id == spec_id))
    spec = result.scalar_one_or_none()
    if not spec:
        return 0

    tests_dir = settings.generated_tests_path / project_id / spec_id
    tests_dir.mkdir(parents=True, exist_ok=True)

    tc_result = await db.execute(
        select(TestCase).where(
            TestCase.spec_id == spec_id,
            TestCase.status.in_([TestCaseStatus.DRAFT, TestCaseStatus.APPROVED]),
        )
    )
    testcases = tc_result.scalars().all()

    by_endpoint: dict[str, list[TestCase]] = {}
    for tc in testcases:
        by_endpoint.setdefault(tc.endpoint_id, []).append(tc)

    files_written = 0
    for endpoint_id, cases in by_endpoint.items():
        ep = (await db.execute(select(APIEndpoint).where(APIEndpoint.id == endpoint_id))).scalar_one_or_none()
        if not ep:
            continue

        parsed = [
            ParsedTestCase(
                function_name=c.name.replace(f"[{c.category.value}] ", ""),
                code=c.test_code, description=c.description,
                expected_status=c.expected_status,
            )
            for c in cases
        ]
        slug = slugify_path(ep.path)
        method = ep.method.value.lower()
        filepath = tests_dir / f"test_{method}_{slug}.py"
        content = assemble_test_file(parsed, module_docstring=f"Tests for {ep.method.value} {ep.path}")
        write_test_file(content, filepath)
        files_written += 1

    return files_written
