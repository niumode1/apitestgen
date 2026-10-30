"""Test Execution Service — runs pytest as subprocess with live streaming."""

import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.events import EventBus, EventType, ExecutionEvent
from app.models.execution import (
    ExecutionStatus,
    ExecutionTrigger,
    TestExecution,
    TestOutcome,
    TestResult,
)
from app.models.project import Project
from app.models.spec import OpenAPISpec
from app.models.testcase import TestCase, TestCaseStatus
from app.utils.logger import logger


async def run_test_execution(
    project_id: str,
    event_bus: Optional[EventBus] = None,
    spec_id: Optional[str] = None,
    environment: Optional[dict] = None,
    name: Optional[str] = None,
    trigger: str = "manual",
) -> TestExecution:
    """Run pytest for a project's generated tests. Creates its own DB session."""

    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        return await _do_run(project_id, db, event_bus, spec_id, environment, name, trigger)


async def _do_run(
    project_id: str,
    db: AsyncSession,
    event_bus: Optional[EventBus],
    spec_id: Optional[str],
    environment: Optional[dict],
    name: Optional[str],
    trigger: str,
) -> TestExecution:
    # ── Create execution record ──
    project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    execution = TestExecution(
        project_id=project_id,
        spec_id=spec_id,
        name=name or f"Run {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        status=ExecutionStatus.RUNNING,
        trigger=ExecutionTrigger(trigger),
        started_at=datetime.utcnow(),
        environment=environment or {},
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    exec_id = execution.id

    async def emit(etype: EventType, payload: dict):
        if event_bus:
            await event_bus.publish(ExecutionEvent(resource_id=exec_id, event_type=etype, payload=payload))

    await emit(EventType.EXECUTION_STARTED, {"execution_id": exec_id, "project_id": project_id})

    # ── Find test files ──
    tests_dir = settings.generated_tests_path / project_id
    if spec_id:
        tests_dir = tests_dir / spec_id

    if not tests_dir.exists() or not list(tests_dir.rglob("test_*.py")):
        logger.warning(f"No test files found in {tests_dir}")
        execution.status = ExecutionStatus.COMPLETED
        execution.total_tests = 0
        execution.completed_at = datetime.utcnow()
        await db.commit()
        await emit(EventType.EXECUTION_COMPLETED, {"execution_id": exec_id, "total": 0, "passed": 0, "failed": 0})
        return execution

    # ── Run pytest subprocess ──
    report_file = (tests_dir / ".pytest_report.json").resolve()
    backend_dir = Path(__file__).parent.parent.parent.resolve()  # e:/kkk/backend/

    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir.resolve()),
        "-v",
        "--tb=short",
        "--json-report",
        f"--json-report-file={report_file}",
        "--continue-on-collection-errors",
    ]

    env = os.environ.copy()
    if environment:
        env.update({k: str(v) for k, v in environment.items()})

    logger.info(f"Running: {' '.join(cmd)}")
    logger.info(f"cwd: {backend_dir}")

    try:
        # Run pytest in thread pool (more reliable than async subprocess on Windows)
        import subprocess

        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            cwd=str(backend_dir),
            env=env,
            timeout=120,
        )

        # Stream output via EventBus
        for line in result.stdout.split('\n'):
            if line.strip():
                await emit(EventType.LOG_LINE, {"line": line, "stream": "stdout"})
        for line in result.stderr.split('\n'):
            if line.strip():
                await emit(EventType.LOG_LINE, {"line": line, "stream": "stderr"})

        logger.info(f"Pytest exit code: {result.returncode}")

    except subprocess.TimeoutExpired:
        logger.error("Pytest timed out after 120s")
        execution.status = ExecutionStatus.FAILED
        execution.completed_at = datetime.utcnow()
        await db.commit()
        return execution
    except Exception as e:
        logger.error(f"Pytest failed: {e}")
        execution.status = ExecutionStatus.FAILED
        execution.completed_at = datetime.utcnow()
        await db.commit()
        return execution

    # ── Parse JSON report ──
    results_data = _parse_pytest_report(report_file)

    # ── Create TestResult records ──
    total = 0
    passed = 0
    failed = 0
    errors = 0
    skipped = 0
    total_duration_ms = 0

    for test in results_data:
        outcome = test.get("outcome", "error")
        test_name = test.get("nodeid", test.get("name", "unknown"))
        duration_sec = test.get("duration", 0)

        # Extract error details from pytest-json-report format
        crash = test.get("crash", {})
        call_result = test.get("call", {})
        setup_result = test.get("setup", {})
        teardown_result = test.get("teardown", {})

        error_msg = ""
        traceback_text = ""
        stdout_text = ""
        stderr_text = ""

        # Top-level crash
        if crash:
            error_msg = crash.get("message", "")
            traceback_text = crash.get("longrepr", "")

        # Check call phase — error may be in call.crash or call.longrepr
        for phase in [setup_result, call_result, teardown_result]:
            phase_crash = phase.get("crash", {})
            if phase_crash:
                msg = phase_crash.get("message", "")
                if msg:
                    error_msg = error_msg or msg
                    traceback_text = traceback_text or msg
            longrepr = phase.get("longrepr", "")
            if longrepr:
                # longrepr contains the full failure detail
                error_msg = error_msg or longrepr.split("\n")[0] if "\n" in longrepr else longrepr[:200]
                traceback_text = traceback_text or longrepr

        # Capture stdout/stderr
        for phase in [setup_result, call_result, teardown_result]:
            stdout_text = stdout_text or phase.get("stdout", "") or phase.get("capstdout", "")
            stderr_text = stderr_text or phase.get("stderr", "") or phase.get("capstderr", "")

        if not error_msg and outcome == "failed":
            error_msg = "Test assertion failed"

        tr = TestResult(
            execution_id=exec_id,
            testcase_id="",
            test_name=test_name,
            status=TestOutcome(outcome),
            duration_ms=int(duration_sec * 1000) if duration_sec else None,
            error_message=error_msg[:2000] if error_msg else "",
            traceback=traceback_text[:5000] if traceback_text else "",
            captured_stdout=stdout_text[:2000] if stdout_text else "",
            captured_stderr=stderr_text[:2000] if stderr_text else "",
            recorded_at=datetime.utcnow(),
        )
        db.add(tr)

        total += 1
        total_duration_ms += int(duration_sec * 1000) if duration_sec else 0
        if outcome == "passed":
            passed += 1
        elif outcome == "failed":
            failed += 1
        elif outcome == "error":
            errors += 1
        elif outcome == "skipped":
            skipped += 1

    # ── Update execution record ──
    execution.status = ExecutionStatus.COMPLETED
    execution.total_tests = total
    execution.passed = passed
    execution.failed = failed
    execution.errors = errors
    execution.skipped = skipped
    execution.duration_ms = total_duration_ms if total_duration_ms > 0 else int((datetime.utcnow() - execution.started_at).total_seconds() * 1000) if execution.started_at else 0
    execution.completed_at = datetime.utcnow()

    await db.commit()

    await emit(EventType.EXECUTION_COMPLETED, {
        "execution_id": exec_id,
        "total": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
        "duration_ms": total_duration_ms,
        "pass_rate": round((passed / total * 100), 1) if total > 0 else 0,
    })

    logger.info(f"Execution {exec_id} complete: {passed}/{total} passed")
    return execution


def _parse_pytest_report(report_file: Path) -> list[dict]:
    """Parse pytest-json-report output."""
    if not report_file.exists():
        logger.warning(f"No pytest report found at {report_file}")
        return []

    try:
        data = json.loads(report_file.read_text(encoding="utf-8"))
        tests = data.get("tests", [])
        # Also check for "collectors" or flat format
        if not tests and isinstance(data, list):
            tests = data
        return tests
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse pytest report: {e}")
        return []


def _extract_pytest_results_from_stdout(stdout: str) -> list[dict]:
    """Fallback: parse results from pytest stdout if JSON report unavailable."""
    results = []
    pattern = r"(PASSED|FAILED|ERROR|SKIPPED)\s+([\w./:\[\]-]+)"
    for match in re.finditer(pattern, stdout):
        outcome = match.group(1).lower()
        nodeid = match.group(2).strip()
        results.append({"nodeid": nodeid, "outcome": outcome, "duration": 0})
    return results
