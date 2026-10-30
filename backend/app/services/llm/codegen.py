"""Code Generator — extracts, validates, and writes pytest code from LLM output.

This is a critical module: LLM outputs are unreliable (may contain markdown,
explanations, malformed code). codegen sanitizes and validates everything.
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.utils.logger import logger


@dataclass
class ParsedTestCase:
    """A single test case extracted from LLM output."""
    function_name: str
    code: str
    description: str = ""
    expected_status: Optional[int] = None


@dataclass
class CodeGenResult:
    """Result of parsing LLM output."""
    test_cases: list[ParsedTestCase] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    raw_output: str = ""

    @property
    def success(self) -> bool:
        return len(self.test_cases) > 0


def extract_python_blocks(raw: str) -> list[str]:
    """Extract Python code from LLM output.

    Handles:
    - ```python ... ``` fenced blocks
    - ``` ... ``` blocks without language tag
    - Plain code (no fences at all)
    """
    # Try fenced blocks first
    pattern = r"```(?:python)?\s*\n(.*?)```"
    matches = re.findall(pattern, raw, re.DOTALL)

    if matches:
        return [m.strip() for m in matches]

    # No fences — return entire output as one block
    stripped = raw.strip()
    if stripped:
        return [stripped]
    return []


def parse_llm_output(raw: str) -> CodeGenResult:
    """Parse LLM output into validated test cases.

    1. Extract Python code blocks
    2. Parse with ast to verify syntax
    3. Extract individual test functions
    4. Return structured result
    """
    result = CodeGenResult(raw_output=raw)
    blocks = extract_python_blocks(raw)

    if not blocks:
        result.errors.append("No Python code blocks found in LLM output")
        return result

    for block_idx, block in enumerate(blocks):
        try:
            tree = ast.parse(block)
        except SyntaxError as e:
            result.errors.append(f"Block {block_idx}: syntax error: {e}")
            continue

        # Extract top-level async functions that look like tests
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_name = node.name
                if func_name.startswith("test_"):
                    try:
                        func_code = ast.unparse(node)
                    except Exception:
                        func_code = ast.get_source_segment(block, node) or ""

                    # Extract docstring as description
                    description = ""
                    if (
                        node.body
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)
                    ):
                        description = node.body[0].value.value.strip()

                    # Try to extract expected status from assertions
                    expected_status = None
                    for child in ast.walk(node):
                        if (
                            isinstance(child, ast.Compare)
                            and isinstance(child.left, ast.Attribute)
                            and child.left.attr == "status_code"
                            and isinstance(child.comparators[0], ast.Constant)
                        ):
                            expected_status = child.comparators[0].value
                            break

                    result.test_cases.append(ParsedTestCase(
                        function_name=func_name,
                        code=func_code,
                        description=description,
                        expected_status=expected_status,
                    ))

    if not result.test_cases and not result.errors:
        result.errors.append("No test functions (async def test_*) found in code blocks")

    return result


def validate_test_case(code: str) -> tuple[bool, str]:
    """Validate a single test case string is syntactically valid Python.

    Returns (is_valid, error_message).
    """
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, str(e)


def assemble_test_file(
    test_cases: list[ParsedTestCase],
    imports: str = "",
    module_docstring: str = "",
) -> str:
    """Assemble multiple test functions into a complete .py file.

    Args:
        test_cases: Extracted test functions
        imports: Import statements to prepend
        module_docstring: Module-level docstring

    Returns:
        Complete Python module content
    """
    lines = []

    if module_docstring:
        lines.append(f'"""{module_docstring}"""')
        lines.append("")

    # Default imports if none provided
    if not imports:
        imports = (
            "import pytest\n"
            "import httpx\n"
            "from conftest import BASE_URL\n"
        )
    lines.append(imports.strip())
    lines.append("")

    for tc in test_cases:
        lines.append("")
        lines.append(tc.code)
        lines.append("")

    return "\n".join(lines)


def write_test_file(content: str, filepath: Path) -> None:
    """Write generated test content to a file.

    Creates parent directories if needed.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")
    logger.info(f"Test file written: {filepath}")


def generate_conftest(base_url: str, extra_fixtures: str = "") -> str:
    """Generate a conftest.py file for a test suite.

    Args:
        base_url: The target API base URL
        extra_fixtures: Additional fixture code to include
    """
    return f'''"""Auto-generated conftest for API test generation platform."""

import pytest
import httpx

BASE_URL = "{base_url}"


@pytest.fixture
async def async_client() -> httpx.AsyncClient:
    """Async HTTP client fixture with proper lifecycle."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest.fixture
def base_url() -> str:
    """Target API base URL."""
    return BASE_URL

{extra_fixtures}
'''


def slugify_path(path: str) -> str:
    """Convert an API path to a safe filename slug.

    Example: /pet/{petId} → pet__petId_
    """
    slug = path.strip("/").replace("/", "_").replace("{", "_").replace("}", "_")
    slug = re.sub(r"[^a-zA-Z0-9_]", "_", slug)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "root"
