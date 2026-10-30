# 系统架构文档

## 一、项目概述

APITestGen 是一个大模型驱动的接口自动化测试智能生成平台。通过导入 OpenAPI 接口文档，LLM Agent 自动分析接口语义、生成覆盖全面的 pytest 测试用例（正向/负向/边界/安全/Schema校验），一键执行测试并输出缺陷报告，完全替代人工编写接口测试用例。

## 二、技术栈

| 层级 | 技术选型 | 版本 |
|------|---------|------|
| **后端框架** | FastAPI (async) | 0.136.0 |
| **ORM** | SQLAlchemy 2.0 (async) | 2.0.51 |
| **数据校验** | Pydantic v2 | 2.13.1 |
| **数据库** | SQLite (开发) / PostgreSQL (生产) | — |
| **异步驱动** | aiosqlite | 0.22.1 |
| **数据库迁移** | Alembic (async) | 1.18.5 |
| **测试框架** | Pytest + httpx | 9.0.3 |
| **LLM SDK** | OpenAI / Anthropic | 2.32.0 |
| **模板引擎** | Jinja2 | 3.1.6 |
| **报表** | WeasyPrint (PDF) / markdown-it-py | 69.0 |
| **前端框架** | Vue 3 + TypeScript | 3.x |
| **UI 组件库** | Element Plus | 2.x |
| **状态管理** | Pinia | 2.x |
| **图表** | ECharts (vue-echarts) | 5.x |
| **HTTP 客户端** | Axios | 1.x |
| **构建工具** | Vite | 6.x |

## 三、系统分层架构

```
┌─────────────────────────────────────────────────────┐
│                    前端 (Vue 3)                       │
│   Element Plus  UI  │  Pinia 状态管理  │  Axios      │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / WebSocket
┌──────────────────────▼──────────────────────────────┐
│                   API 层 (FastAPI)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐             │
│  │ Projects │ │  Specs   │ │Endpoints │  ... 10个路由 │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘             │
│       │             │            │                    │
│  ┌────▼─────────────▼────────────▼─────┐             │
│  │         依赖注入层 (deps.py)         │             │
│  │    get_db / pagination / 404检查    │             │
│  └────────────────┬───────────────────┘             │
└───────────────────┼─────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────┐
│                 服务层 (services/)                    │
│  ┌──────────┐ ┌──────────────┐ ┌──────────────┐     │
│  │SpecParser│ │ExecutorService│ │ReportService │     │
│  │  OpenAPI │ │  pytest子进程  │ │ Markdown/PDF │     │
│  └──────────┘ └──────────────┘ └──────────────┘     │
│  ┌──────────────────────────────────────────┐       │
│  │           LLM 引擎 (services/llm/)        │       │
│  │  ┌─────────┐  ┌──────────────────┐       │       │
│  │  │Provider │  │  Agent 编排器      │       │       │
│  │  │OpenAI   │  │  ┌──────┐┌──────┐│       │       │
│  │  │Anthropic│  │  │分析  ││正向  ││ ...   │       │
│  │  │Ollama   │  │  │Agent ││Agent ││ 7个   │       │
│  │  └─────────┘  │  └──────┘└──────┘│ Agent  │       │
│  │                └──────────────────┘       │       │
│  │  ┌─────────┐  ┌──────────────────┐       │       │
│  │  │CodeGen  │  │  Prompt 模板      │       │       │
│  │  │AST解析  │  │  Jinja2 (.j2)    │       │       │
│  │  └─────────┘  └──────────────────┘       │       │
│  └──────────────────────────────────────────┘       │
└───────────────────┬───────────────────────────────┘
                    │
┌───────────────────▼───────────────────────────────┐
│                数据层 (models/)                      │
│  ┌────────┐ ┌──────┐ ┌──────────┐ ┌──────────┐   │
│  │Project │ │Spec  │ │Endpoint  │ │TestCase  │   │
│  └────────┘ └──────┘ └──────────┘ └──────────┘   │
│  ┌────────────┐ ┌──────────┐ ┌──────────────┐     │
│  │Execution   │ │Report    │ │LLMProvider   │     │
│  │+ Result    │ │          │ │+ Postman     │     │
│  └────────────┘ └──────────┘ └──────────────┘     │
│                    SQLite / PostgreSQL              │
└───────────────────────────────────────────────────┘
```

## 四、核心流程

### 4.1 测试生成流水线

```
用户上传 OpenAPI YAML/JSON
        │
        ▼
┌──────────────────────┐
│  SpecParser          │  解析YAML/JSON
│  验证OpenAPI 3.x结构  │  展开 $ref 引用
│  提取接口元数据       │  存入 OpenAPISpec + APIEndpoint
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  AgentOrchestrator   │  对每个接口:
│  1. AnalyzerAgent    │    分析参数语义/约束/依赖
│  2. 并行生成(5选N)    │    Positive / Negative / Boundary
│  3. ReviewerAgent    │    / Security / Schema agents
│  4. CodeGen          │    AST解析 → 验证 → 写文件
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  TestCase 写入 DB    │  生成 conftest.py + test_*.py
│  generated_tests/    │  每条用例含代码/参数/预期状态码
└──────┬───────────────┘
       │
       ▼  (用户点击"执行")
┌──────────────────────┐
│  ExecutorService     │  pytest --json-report 子进程
│  EventBus → WS推送   │  实时日志流 → 前端展示
│  解析JSON报告        │  TestResult 入库
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  ReportService       │  聚合失败用例
│  LLM摘要(可选)       │  Jinja2 → Markdown/HTML/PDF
│  缺陷分类 + 建议     │  DefectReport 入库
└──────────────────────┘
```

### 4.2 事件总线架构

```
ExecutorService                WebSocket Handler
  │                                  │
  │ publish(ExecutionEvent)          │ subscribe(execution_id)
  │   ├─ EXECUTION_STARTED           │   └─ asyncio.Queue
  │   ├─ TEST_STARTED                │       │
  │   ├─ TEST_COMPLETED              │       ▼
  │   ├─ LOG_LINE                    │   async for event in queue:
  │   └─ EXECUTION_COMPLETED         │     await ws.send_json(event)
  │       │                          │
  └───────┼──────────────────────────┘
          │
     EventBus (内存 pub/sub)
     按 execution_id 分发
```

## 五、数据库 ER 图

```
Project (1) ──────< (N) OpenAPISpec
    │                      │
    │                      └──────< (N) APIEndpoint
    │                                      │
    │                                      └──< (N) TestCase
    │                                               │
    ├──< (N) TestExecution                          │
    │         │                                     │
    │         └──< (N) TestResult ─── (1) >─────────┘
    │
    ├──< (N) DefectReport ── (1) >── TestExecution
    │
    ├──< (N) PostmanCollection
    │
    └── (独立) LLMProvider

关键关系:
- Project 级联删除所有子资源
- TestCase 关联 Endpoint (1:N)
- TestResult 同时关联 Execution 和 TestCase
- DefectReport 归属于一次 Execution
```

## 六、LLM Agent 体系

| Agent | 职责 | 输出 |
|-------|------|------|
| **EndpointAnalyzer** | 分析接口参数语义、类型约束、依赖关系 | 结构化 JSON 分析报告 |
| **PositiveCase** | 生成 2-3 个正向测试用例 | pytest async function |
| **NegativeCase** | 生成 3-5 个异常测试（缺参数/错类型/非法值） | pytest async function |
| **BoundaryValue** | 边界值测试（min±1, max±1, 零值, 空值） | pytest async function |
| **SecurityPayload** | SQL注入/XSS/命令注入/JWT篡改等安全测试 | pytest async function |
| **SchemaValidation** | 验证响应体符合 OpenAPI Schema 定义 | pytest async function |
| **TestReviewer** | 代码正确性审查、逻辑错误检测、去重 | approve/revise + 修改意见 |

Agent 编排特点:
- 同接口内不同 Agent 可并行执行（`asyncio.gather`）
- LLM 输出经 `ast.parse()` 语法验证后才入库
- 支持分步流式推送进度到前端 WebSocket
- 可限制每个接口最大生成用例数，控制 Token 成本

## 七、安全设计

- LLM API Key: Fernet 对称加密静态存储
- 文件上传: 限制大小（默认 10MB），校验格式
- 数据库: SQLite WAL 模式，并发读友好
- CORS: 开发阶段允许所有来源，生产需白名单
- pytest 执行: 子进程隔离，超时可杀
