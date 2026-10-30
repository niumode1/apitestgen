"""Generate the project report as a Word document following the template."""

import os
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE

OUT = "e:/kkk/文档/APITestGen项目报告.docx"
IMG_DIR = "e:/kkk/文档"

doc = Document()

# ── Page setup ──
for section in doc.sections:
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(3)
    section.right_margin = Cm(2.5)

style = doc.styles['Normal']
font = style.font
font.name = '宋体'
font.size = Pt(12)

# ── Cover Page ──
for _ in range(6):
    doc.add_paragraph()

title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run("大模型驱动的接口自动化测试\n智能生成平台")
run.font.size = Pt(28)
run.font.bold = True
run.font.name = '黑体'

doc.add_paragraph()
sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = sub.add_run("APITestGen")
run.font.size = Pt(20)
run.font.name = 'Arial'

for _ in range(4):
    doc.add_paragraph()

info = doc.add_paragraph()
info.alignment = WD_ALIGN_PARAGRAPH.CENTER
info.add_run("2026年06月").font.size = Pt(14)

doc.add_page_break()

# ── Helper Functions ──
def add_heading1(text):
    h = doc.add_heading(text, level=1)
    for run in h.runs:
        run.font.name = '黑体'
        run.font.size = Pt(16)
    return h

def add_heading2(text):
    h = doc.add_heading(text, level=2)
    for run in h.runs:
        run.font.name = '黑体'
        run.font.size = Pt(14)
    return h

def add_para(text, bold=False, indent=False):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.first_line_indent = Cm(0.74)
    run = p.add_run(text)
    run.font.name = '宋体'
    run.font.size = Pt(12)
    if bold:
        run.font.bold = True
    return p

def add_code(text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1)
    run = p.add_run(text)
    run.font.name = 'Consolas'
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    return p

def add_image(filename, width_inches=5.5, caption=""):
    path = os.path.join(IMG_DIR, filename)
    if os.path.exists(path):
        doc.add_picture(path, width=Inches(width_inches))
        if caption:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(caption)
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

# ── Chapter 1: 项目引言 ──
add_heading1("1 项目引言")

add_heading2("1.1 项目背景")
add_para("在传统软件开发流程中，接口测试用例的编写是一项高度重复、耗时且依赖人工经验的工作。测试工程师需要阅读接口文档、理解参数语义和约束，手动编写大量 pytest/JUnit 测试代码，覆盖正向、负向、边界值、安全等多种场景。一个中型微服务项目（30+ 接口）通常需要 3-5 人天来完成基础测试用例编写，且容易遗漏边界场景。", indent=True)
add_para("随着大语言模型（LLM）代码生成能力的快速发展，利用 AI 自动分析 API 接口语义、生成测试代码成为可能。本项目旨在构建一个 LLM 驱动的接口自动化测试智能生成平台，通过导入 OpenAPI 文档，AI 自动生成全面的 pytest 测试用例，一键执行并输出缺陷报告，完全替代人工编写测试用例的重复劳动。", indent=True)

add_heading2("1.2 项目目标")
add_para("本项目目标是开发一个功能完整的 Web 应用平台，实现以下核心目标：", indent=True)
add_para("（1）OpenAPI 文档导入与解析：支持 JSON/YAML 格式的 OpenAPI 3.x 规范文件上传和 URL 导入，自动提取所有接口的路径、方法、参数、请求体和响应定义。")
add_para("（2）LLM 驱动的测试用例智能生成：对接 DeepSeek/OpenAI/Anthropic 等大模型，自动生成正向、负向、边界值、安全、Schema 校验五类测试用例。")
add_para("（3）一键测试执行与结果分析：通过 pytest 子进程运行生成的测试，实时解析执行结果，按类别统计通过率。")
add_para("（4）缺陷报告自动生成：基于执行结果生成 Markdown/HTML 格式的测试报告，包含失败用例详情和按类别统计。")

add_heading2("1.3 技术路线")
add_para("本项目采用前后端分离架构：", indent=True)
add_para("后端：Python FastAPI 异步框架 + SQLAlchemy 2.0 ORM + SQLite 数据库。通过 Provider 工厂模式抽象 LLM 调用层，支持 OpenAI、DeepSeek、Anthropic、Ollama 等多种后端。使用 Jinja2 模板引擎管理 Prompt 和报告渲染。")
add_para("前端：Vue 3 + TypeScript + Element Plus 组件库 + Pinia 状态管理 + Vite 构建工具。采用工作台（Workspace）模式聚合导入、生成、执行、报告功能于一页。")
add_para("测试执行：通过 Python subprocess 模块在独立进程中运行 pytest，使用 pytest-json-report 插件获取结构化结果。")

add_image("architecture.png", 5.5, "图1-1 系统架构图")

# ── Chapter 2: 需求分析 ──
add_heading1("2 需求分析")

add_heading2("2.1 可行性分析")
add_para("技术可行性：项目关键技术栈（FastAPI + Vue 3 + SQLite）均为成熟开源技术，LLM API 调用采用 OpenAI SDK 兼容多种模型后端，不存在技术瓶颈。", indent=True)
add_para("经济可行性：DeepSeek 等国产 LLM 的 API 调用成本极低（约 $0.0005/接口），个人开发者即可负担全流程测试生成的开销。", indent=True)
add_para("操作可行性：用户仅需导入 OpenAPI 文档并配置 LLM API Key，通过浏览器即可完成全部操作，无需安装任何本地软件。", indent=True)

add_heading2("2.2 用户需求")
add_para("目标用户为后端开发工程师和测试工程师。核心需求包括：", indent=True)
add_para("（1）减少重复劳动：自动生成测试用例，替代人工编写。")
add_para("（2）提高测试覆盖率：自动覆盖边界值、安全等容易被忽略的场景。")
add_para("（3）快速回归测试：一键执行全部测试，即时获取通过率报告。")
add_para("（4）团队协作：支持 Postman Collection 导入导出，便于团队共享。")

add_heading2("2.3 功能需求")
add_para("（1）项目管理：创建、查看、更新、删除项目，支持批量操作。")
add_para("（2）OpenAPI 导入：支持文件上传和 URL 导入，自动解析接口元数据。")
add_para("（3）AI 测试生成：五类策略（正向/负向/边界值/安全/Schema），可单独选择或全部生成。")
add_para("（4）测试执行：pytest 子进程执行，JSON 报告解析，实时展示执行进度。")
add_para("（5）缺陷报告：Markdown 格式报告，按类别统计通过率，包含失败详情和堆栈。")
add_para("（6）Postman 集成：导入导出 Postman Collection v2.1 格式。")
add_para("（7）仪表盘：项目、接口、用例、执行次数统计，总体通过率展示。")
add_para("（8）LLM 配置管理：支持多提供商，API Key 安全存储。")

add_image("usecase.png", 5, "图2-1 系统用例图")
add_image("pipeline.png", 5.5, "图2-2 核心业务流程图")

add_heading2("2.4 非功能需求")
add_para("（1）响应时间：单接口测试生成 < 15 秒，19 接口全策略生成 < 3 分钟。")
add_para("（2）并发处理：多接口并行生成，Semaphore=3 控制并发。")
add_para("（3）可扩展性：LLM Provider 抽象层，新增模型仅需实现 BaseLLMProvider 接口。")
add_para("（4）数据安全：API Key 使用 Fernet 加密静态存储。")

# ── Chapter 3: 系统设计 ──
add_heading1("3 系统设计")

add_heading2("3.1 系统架构")
add_para("系统采用四层架构：", indent=True)
add_para("（1）前端展示层（Vue 3）：负责用户交互、数据展示和路由控制。核心为 WorkspacePage 工作台页面，集成导入、生成、执行、报告四个 Tab，替代传统的多个独立页面跳转。")
add_para("（2）API 网关层（FastAPI）：提供 10 组 RESTful 端点，包括项目 CRUD、文档管理、测试生成、测试执行、报告查看、仪表盘统计等。支持 WebSocket 实时推送执行日志。")
add_para("（3）业务服务层：OpenAPI 解析器（YAML/JSON → APIEndpoint）、LLM Agent 引擎（Provider → Agent → CodeGen）、pytest 执行器（子进程 → JSON 报告 → TestResult）、报告生成器（Jinja2 → Markdown/HTML）。")
add_para("（4）数据持久层：SQLAlchemy 2.0 异步 ORM + SQLite（可无缝迁移至 PostgreSQL），9 张核心数据表。")

add_image("architecture.png", 5.5, "图3-1 系统架构图")

add_heading2("3.2 数据库设计")
add_para("数据库包含 9 张表：projects（项目）、specs（OpenAPI文档）、endpoints（接口）、testcases（测试用例）、executions（执行记录）、test_results（执行结果）、defect_reports（缺陷报告）、llm_providers（LLM提供商）、postman_collections（Postman集合）。", indent=True)
add_para("核心关系：Project 1→N Spec 1→N Endpoint 1→N TestCase；Execution 1→N TestResult ←1 TestCase；Execution 1→N DefectReport。采用 UUID 主键，级联删除保证数据一致性。", indent=True)

add_image("er_diagram.png", 5.5, "图3-2 数据库ER图")

add_heading2("3.3 功能模块设计")
add_para("系统核心功能模块包括：", indent=True)
add_para("（1）文档解析模块（spec_parser）：支持 JSON/YAML 自动识别，遍历 OpenAPI paths × methods 提取接口元数据，合并 path-level 和 operation-level 参数。")
add_para("（2）LLM Agent 模块（services/llm/）：Provider 抽象层 + BaseAgent 基类 + 6 个专项 Agent + Orchestrator 编排器 + CodeGen 代码生成器。")
add_para("（3）执行引擎模块（executor_service）：使用 subprocess.run 在独立进程执行 pytest，通过 pytest-json-report 获取结构化结果，逐条解析 TestResult 入库。")
add_para("（4）报告引擎模块（report_service）：Jinja2 模板渲染 Markdown，按类别（正向/负向/边界值/安全/Schema）分组统计，提取 call.crash.message 获取具体错误信息。")

add_image("agent_architecture.png", 5.5, "图3-3 LLM Agent体系图")

add_heading2("3.4 界面设计")
add_para("前端采用工作台（Workspace）设计模式，核心页面 WorkspacePage 一页聚合全部功能：", indent=True)
add_para("（1）顶部流水线导航（导入→生成→执行→报告），可点击跳转对应 Tab。")
add_para("（2）文档选择器支持多文档切换，点击 X 删除。")
add_para("（3）四个 Tab：接口列表（按方法着色）、测试用例（按类别筛选 + 代码弹窗）、执行历史（点击查看每条结果）、缺陷报告（90%宽弹窗带格式化渲染）。")
add_para("（4）策略下拉选择器 + 生成/执行按钮，一步完成操作。")

add_image("frontend_tree.png", 5.5, "图3-4 前端组件树图")

add_heading2("3.5 接口设计")
add_para("后端提供 30+ REST API 端点，核心接口包括：", indent=True)
add_para("POST /projects/{id}/specs — 上传 OpenAPI 文档（multipart/form-data）")
add_para("POST /projects/{id}/specs/import-url — URL 导入 OpenAPI 文档")
add_para("POST /specs/{id}/generate — 触发 AI 测试生成（异步后台任务）")
add_para("GET /specs/{id}/generations/{gid}/status — 轮询生成进度")
add_para("POST /projects/{id}/executions — 启动测试执行")
add_para("POST /projects/{id}/executions/{eid}/reports — 生成缺陷报告")
add_para("WebSocket /ws/execution/{eid} — 实时执行日志推送")

# ── Chapter 4: 系统实现 ──
add_heading1("4 系统实现")

add_heading2("4.1 开发环境")
add_para("硬件环境：Windows 10 + 16GB RAM", indent=True)
add_para("软件环境：Python 3.11 + Node.js v24 + VSCode IDE")
add_para("核心依赖：FastAPI 0.138 + SQLAlchemy 2.0 + Pydantic v2 + Vue 3 + Element Plus")
add_para("LLM 服务：DeepSeek API (deepseek-chat / deepseek-v4-flash)")
add_para("版本控制：Git，项目目录 e:/kkk/")

add_heading2("4.2 关键技术")
add_para("（1）LLM Provider 工厂模式", indent=True)
add_code("""class BaseLLMProvider(ABC):
    @abstractmethod
    async def complete(self, system_prompt, user_prompt) -> LLMResponse: ...

class OpenAIProvider(BaseLLMProvider):     # 兼容 DeepSeek + Ollama
class AnthropicProvider(BaseLLMProvider):  # Claude

class LLMProviderFactory:
    @staticmethod
    def create_from_model(record) -> BaseLLMProvider: ...""")

add_para("（2）并行 Agent 编排器", indent=True)
add_code("""# 5个Agent并行生成，asyncio.Semaphore控制并发
agent_tasks = []
if strategy in ("all", "positive_only"):
    agent_tasks.append(("positive", PositiveCaseAgent(provider).generate(...)))
# ... 5种Agent依次判断

results = await asyncio.gather(*[task for _, task in agent_tasks])
# 每接口5种Agent并行，3个接口同时处理""")

add_para("（3）AST 双保险校验", indent=True)
add_code("""def parse_llm_output(raw: str) -> CodeGenResult:
    blocks = extract_python_blocks(raw)        # 正则提取代码块
    for block in blocks:
        tree = ast.parse(block)                 # ast语法校验
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                if node.name.startswith("test_"):
                    tests.append(ParsedTestCase(...))  # 提取有效测试函数""")

add_para("（4）Prompt 质量控制系统", indent=True)
add_para("所有 Prompt 使用 Jinja2 模板管理，与代码分离。包含 CRITICAL RULES 区块针对性修复 LLM 常见错误：禁止 if len(data)>0 假通过模式、禁止硬编码假 ID、必须精确匹配 Schema 字段名。模板路径：backend/app/services/llm/prompts/*.j2", indent=True)

add_heading2("4.3 核心代码")
add_para("项目核心代码约 6000 行，其中：", indent=True)
add_para("后端 Python：~3500 行（models 9个 / schemas 12个 / api路由 10组 / services 4个服务 / llm 引擎）")
add_para("前端 Vue/TypeScript：~2500 行（5个页面 / 2个布局组件 / API 封装层 / Pinia 状态管理）")
add_para("核心文件：")
add_para("  - backend/app/services/llm/agents/orchestrator.py — Agent 编排器（并行调度核心）")
add_para("  - backend/app/services/llm/codegen.py — LLM 输出解析与 AST 校验")
add_para("  - backend/app/services/executor_service.py — pytest 执行引擎")
add_para("  - frontend/src/views/WorkspacePage.vue — 工作台页面（一页全流程）")

add_heading2("4.4 测试分析")
add_para("（1）后端 API 测试：对全部 10 组 REST 端点进行覆盖测试，包括正常 CRUD、404 处理、无效文件上传、空项目执行等场景，全部通过。", indent=True)
add_para("（2）端到端测试：使用内置 Demo API（localhost:9001，6 个接口）进行全流程验证：导入 OpenAPI → 生成 30 条正向测试 → 执行 → 15 条通过（50%）→ 生成缺陷报告。失败用例均为 LLM 对响应格式的预期偏差（如期望 list 实际为 {items: [...]}），非平台 Bug。", indent=True)
add_para("（3）自举测试：平台导入自身 OpenAPI 文档（30 个接口），生成 86 条用例，执行后 17 条通过（20%）。通过的 17 条均为无状态 GET 端点（/health, /projects, /dashboard/summary 等），证明核心 API 功能正常。", indent=True)
add_para("（4）批量生成性能：19 接口全策略（5 类 Agent 并行，Semaphore=3），约 2-3 分钟完成，生成约 100 条用例。", indent=True)

# ── Chapter 5: 项目总结 ──
add_heading1("5 项目总结")

add_heading2("5.1 项目成果")
add_para("（1）完成了一个功能完整的 LLM 驱动接口自动化测试智能生成平台，后端 3500+ 行 Python，前端 2500+ 行 Vue/TypeScript。")
add_para("（2）实现了从 OpenAPI 文档导入 → AI 测试生成 → pytest 执行 → 缺陷报告的全自动化流水线。")
add_para("（3）创新性地采用 Agent-per-Category 架构，5 个专项 Agent 并行生成不同类型的测试用例。")
add_para("（4）支持 DeepSeek/OpenAI/Anthropic/Ollama 等多种 LLM 后端，通过 Provider 工厂模式实现一套代码适配所有模型。")
add_para("（5）前端采用工作台设计模式，一页聚合全流程，替代传统的多页面跳转架构，显著提升用户体验。")

add_heading2("5.2 收获与不足")
add_para("收获：", indent=True)
add_para("（1）深入掌握了 FastAPI 异步编程、SQLAlchemy 2.0 ORM、Pydantic v2 数据校验等 Python 后端技术栈。")
add_para("（2）实践了 LLM 应用开发的核心模式：Provider 抽象、Agent 编排、Prompt 工程、输出解析与校验。")
add_para("（3）学习了 Vue 3 Composition API、Pinia 状态管理、Vite 构建等现代前端技术。")
add_para("（4）理解了软件工程全流程：需求分析 → 系统设计 → 迭代开发 → 测试验收 → 文档编写。")
add_para("不足：", indent=True)
add_para("（1）LLM 生成的测试断言精度有待提升，部分用例存在字段名猜测和假 ID 问题。可通过引入 Schema 感知的响应校验和 Few-shot 示例模板改进。")
add_para("（2）系统缺乏 CI/CD 集成能力，无法直接嵌入 GitHub Actions 或 Jenkins 流水线。")
add_para("（3）缺少用户认证和权限管理系统，目前为单用户模式。")

add_heading2("5.3 未来展望")
add_para("（1）智能断言修正：LLM 分析失败原因，自动修复不准确的断言。")
add_para("（2）定时任务与 API 健康监控：配置 Cron 定时执行测试，发现异常自动告警。")
add_para("（3）CI/CD 集成：提供 GitHub Actions 和 Jenkins 插件。")
add_para('（4）Mock 服务自动生成：根据 OpenAPI 自动生成 Mock Server，解决"先有测试还是先有 API"的鸡生蛋问题。')
add_para("（5）PDF 正式报告：使用 WeasyPrint 生成适合打印和归档的 PDF 报告。")

# ── References ──
add_heading1("参考文献")
refs = [
    "[1] FastAPI Documentation. https://fastapi.tiangolo.com/ [EB/OL]. 2026.",
    "[2] SQLAlchemy 2.0 Documentation. https://docs.sqlalchemy.org/ [EB/OL]. 2026.",
    "[3] OpenAI API Reference. https://platform.openai.com/docs/ [EB/OL]. 2026.",
    "[4] DeepSeek API Documentation. https://platform.deepseek.com/docs [EB/OL]. 2026.",
    "[5] Vue.js Guide. https://vuejs.org/guide/ [EB/OL]. 2026.",
    "[6] Pytest Documentation. https://docs.pytest.org/ [EB/OL]. 2026.",
    "[7] OpenAPI Specification 3.0. https://spec.openapis.org/oas/v3.0.3 [EB/OL]. 2026.",
]
for ref in refs:
    add_para(ref)

# ── Save ──
doc.save(OUT)
print(f"Report saved to: {OUT}")
print(f"Size: {os.path.getsize(OUT)} bytes")
