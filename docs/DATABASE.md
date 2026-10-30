# 数据库设计文档

## 一、技术选型

- **开发环境**: SQLite + aiosqlite（零配置，文件即数据库）
- **生产环境**: PostgreSQL（仅需修改 `DATABASE_URL` 环境变量）
- **ORM**: SQLAlchemy 2.0 异步模式
- **迁移工具**: Alembic（async mode）

## 二、ER 图

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   projects   │ 1──N  │    specs     │ 1──N  │  endpoints   │
│              │       │              │       │              │
│ id (PK)      │       │ id (PK)      │       │ id (PK)      │
│ name         │       │ project_id   │       │ spec_id      │
│ description  │       │ name         │       │ path         │
│ base_url     │       │ version      │       │ method       │
│ created_at   │       │ spec_format  │       │ summary      │
│ updated_at   │       │ raw_content  │       │ parameters   │
└──────┬───────┘       │ parsed_json  │       │ request_body │
       │               │ parse_status │       │ responses    │
       │               │ parse_error  │       │ tags         │
       │               │ endpoint_..  │       │ security     │
       │               │ created_at   │       │ deprecated   │
       │               │ updated_at   │       │ analysis     │
       │               └──────────────┘       │ created_at   │
       │                                      │ updated_at   │
       │                                      └──────┬───────┘
       │                                             │
       │  ┌──────────────────────────────────────────┘
       │  │
       │  │  ┌──────────────────────┐
       │  │  │      testcases        │
       │  ├──│                      │
       │  │  │ id (PK)              │
       │  │  │ project_id (FK)      │
       │  │  │ endpoint_id (FK)     │
       │  │  │ spec_id (FK)         │
       │  │  │ name                 │
       │  │  │ description          │
       │  │  │ category (枚举)       │
       │  │  │   ├─ positive        │
       │  │  │   ├─ negative        │
       │  │  │   ├─ boundary        │
       │  │  │   ├─ security        │
       │  │  │   └─ schema          │
       │  │  │ severity (枚举)       │
       │  │  │ test_code (Text)     │
       │  │  │ input_params (JSON)  │
       │  │  │ expected_status      │
       │  │  │ expected_response    │
       │  │  │ llm_model            │
       │  │  │ llm_prompt_tokens    │
       │  │  │ llm_completion_tokens│
       │  │  │ status (枚举)         │
       │  │  │   ├─ draft           │
       │  │  │   ├─ reviewed        │
       │  │  │   ├─ approved        │
       │  │  │   └─ disabled        │
       │  │  │ review_notes         │
       │  │  │ created_at           │
       │  │  │ updated_at           │
       │  │  └──────────┬───────────┘
       │  │             │
       │  │  ┌──────────▼───────────┐
       │  │  │    test_results       │
       │  │  │                      │
       ├──│──│ execution_id (FK)    │
       │  │  │ testcase_id (FK)     │
       │  │  │ test_name            │
       │  │  │ status (枚举)         │
       │  │  │   ├─ passed          │
       │  │  │   ├─ failed          │
       │  │  │   ├─ error           │
       │  │  │   └─ skipped         │
       │  │  │ duration_ms          │
       │  │  │ error_message        │
       │  │  │ traceback (Text)     │
       │  │  │ captured_stdout      │
       │  │  │ captured_stderr      │
       │  │  │ recorded_at          │
       │  │  └──────────────────────┘
       │  │
       │  │  ┌──────────────────────┐
       ├──│──│    executions         │
       │  │  │                      │
       │  │  │ id (PK)              │
       │  │  │ project_id (FK)      │
       │  │  │ spec_id (FK)         │
       │  │  │ name                 │
       │  │  │ status (枚举)         │
       │  │  │ trigger (枚举)        │
       │  │  │ started_at           │
       │  │  │ completed_at         │
       │  │  │ total_tests          │
       │  │  │ passed               │
       │  │  │ failed               │
       │  │  │ errors               │
       │  │  │ skipped              │
       │  │  │ duration_ms          │
       │  │  │ environment (JSON)   │
       │  │  │ created_at           │
       │  │  │ updated_at           │
       │  │  └──────────┬───────────┘
       │  │             │
       │  │  ┌──────────▼───────────┐
       ├──│──│  defect_reports       │
       │  │  │                      │
       │  │  │ execution_id (FK)    │
       │  │  │ project_id (FK)      │
       │  │  │ title                │
       │  │  │ summary              │
       │  │  │ format (枚举)         │
       │  │  │ content              │
       │  │  │ file_path            │
       │  │  │ failed_count         │
       │  │  │ error_count          │
       │  │  │ total_count          │
       │  │  │ pass_rate            │
       │  │  │ created_at           │
       │  │  │ updated_at           │
       │  │  └──────────────────────┘
       │  │
       │  │  ┌──────────────────────┐
       ├──│──│ postman_collections   │
       │  │  │                      │
       │  │  │ project_id (FK)      │
       │  │  │ name                 │
       │  │  │ collection_json(JSON)│
       │  │  │ item_count           │
       │  │  │ created_at           │
       │  │  │ updated_at           │
       │  │  └──────────────────────┘
       │
       │  ┌──────────────────────┐
       │  │   llm_providers       │  (独立表，不关联Project)
       │  │                      │
       │  │ name (UNIQUE)        │
       │  │ provider_type (枚举)  │
       │  │   ├─ openai          │
       │  │   ├─ anthropic       │
       │  │   └─ openai_compat   │
       │  │ api_base             │
       │  │ api_key_encrypted    │
       │  │ default_model        │
       │  │ extra_params (JSON)  │
       │  │ is_active            │
       │  │ created_at           │
       │  │ updated_at           │
       │  └──────────────────────┘
```

## 三、表结构详细说明

### 3.1 projects — 项目表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | TEXT (UUID) | PK | 主键，自动生成 |
| `name` | VARCHAR(255) | NOT NULL | 项目名称 |
| `description` | TEXT | '' | 项目描述 |
| `base_url` | VARCHAR(1024) | '' | 目标 API 基础 URL |
| `created_at` | DATETIME | server_default=now() | 创建时间 |
| `updated_at` | DATETIME | onupdate=now() | 更新时间 |

### 3.2 specs — OpenAPI 文档表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | TEXT (UUID) | PK | 主键 |
| `project_id` | TEXT (UUID) | FK → projects, CASCADE | 所属项目 |
| `name` | VARCHAR(255) | NOT NULL | 文档名称 |
| `version` | VARCHAR(50) | 'unknown' | API 版本号 |
| `spec_format` | ENUM | 'json' / 'yaml' | 文档格式 |
| `raw_content` | TEXT | NOT NULL | 原始文档内容 |
| `parsed_json` | JSON | nullable | 解析后的结构化数据 |
| `parse_status` | ENUM | pending/parsed/error | 解析状态 |
| `parse_error` | TEXT | nullable | 解析错误信息 |
| `imported_at` | DATETIME | nullable | 导入时间 |

### 3.3 endpoints — 接口表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | TEXT (UUID) | PK | 主键 |
| `spec_id` | TEXT (UUID) | FK → specs, CASCADE | 所属文档 |
| `path` | VARCHAR(1024) | NOT NULL | 接口路径 |
| `method` | ENUM | GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS/TRACE | HTTP 方法 |
| `summary` | VARCHAR(500) | '' | 接口摘要 |
| `description` | TEXT | '' | 详细描述 |
| `operation_id` | VARCHAR(255) | '' | 操作 ID |
| `tags` | JSON | [] | 标签列表 |
| `parameters` | JSON | [] | 参数定义数组 |
| `request_body` | JSON | nullable | 请求体 Schema |
| `responses` | JSON | {} | 响应定义 |
| `security` | JSON | nullable | 安全配置 |
| `deprecated` | BOOLEAN | false | 是否已弃用 |
| `analyzed_at` | DATETIME | nullable | LLM 分析时间 |
| `analysis` | JSON | nullable | LLM 分析结果 |

### 3.4 testcases — 测试用例表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | TEXT (UUID) | PK | 主键 |
| `project_id` | TEXT (UUID) | FK → projects | 所属项目 |
| `endpoint_id` | TEXT (UUID) | FK → endpoints | 目标接口 |
| `spec_id` | TEXT (UUID) | FK → specs | 所属文档 |
| `name` | VARCHAR(500) | NOT NULL | 用例名称 |
| `description` | TEXT | '' | 用例描述 |
| `category` | ENUM | positive/negative/boundary/security/schema | 用例类别 |
| `severity` | ENUM | low/medium/high/critical | 严重程度 |
| `test_code` | TEXT | NOT NULL | pytest 可执行代码 |
| `input_params` | JSON | {} | 测试输入参数 |
| `expected_status` | INTEGER | nullable | 预期 HTTP 状态码 |
| `expected_response` | JSON | nullable | 预期响应结构 |
| `llm_model` | VARCHAR(100) | '' | 生成此用例的模型 |
| `llm_prompt_tokens` | INTEGER | 0 | Prompt Token 消耗 |
| `llm_completion_tokens` | INTEGER | 0 | 补全 Token 消耗 |
| `status` | ENUM | draft/reviewed/approved/disabled | 审核状态 |
| `review_notes` | TEXT | nullable | 审核备注 |

### 3.5 executions — 测试执行表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `status` | ENUM | pending/running/completed/failed/cancelled | 执行状态 |
| `trigger` | ENUM | manual/scheduled/ci | 触发方式 |
| `total_tests` | INTEGER | 0 | 总用例数 |
| `passed` | INTEGER | 0 | 通过数 |
| `failed` | INTEGER | 0 | 失败数 |
| `errors` | INTEGER | 0 | 错误数 |
| `skipped` | INTEGER | 0 | 跳过数 |
| `duration_ms` | INTEGER | nullable | 执行耗时(毫秒) |
| `environment` | JSON | {} | 环境变量快照 |

### 3.6 test_results — 测试结果表

| 字段 | 类型 | 说明 |
|------|------|------|
| `execution_id` | FK | 所属执行 |
| `testcase_id` | FK | 对应用例 |
| `test_name` | VARCHAR(500) | pytest node id |
| `status` | ENUM | passed/failed/error/skipped |
| `duration_ms` | INTEGER | 单个用例耗时 |
| `error_message` | TEXT | 错误信息 |
| `traceback` | TEXT | 完整堆栈 |

### 3.7 defect_reports — 缺陷报告表

| 字段 | 类型 | 说明 |
|------|------|------|
| `execution_id` | FK | 基于哪次执行 |
| `project_id` | FK | 所属项目 |
| `title` | VARCHAR(500) | 报告标题 |
| `format` | ENUM | markdown/html/pdf |
| `content` | TEXT | 报告内容 |
| `file_path` | VARCHAR(1024) | 生成的文件路径 |
| `pass_rate` | FLOAT | 通过率 |

### 3.8 llm_providers — LLM 提供商表

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | VARCHAR(100) UNIQUE | 提供商名称 |
| `provider_type` | ENUM | openai/anthropic/openai_compatible |
| `api_base` | VARCHAR(1024) | API 基础地址 |
| `api_key_encrypted` | VARCHAR(1024) | Fernet 加密的 API Key |
| `default_model` | VARCHAR(100) | 默认模型 |
| `extra_params` | JSON | 额外参数 (temperature等) |
| `is_active` | BOOLEAN | 是否启用 |

### 3.9 postman_collections — Postman 集合表

| 字段 | 类型 | 说明 |
|------|------|------|
| `project_id` | FK | 所属项目 |
| `name` | VARCHAR(500) | 集合名称 |
| `collection_json` | JSON | Postman v2.1 格式数据 |
| `item_count` | INTEGER | 请求条目数 |

## 四、索引建议（PostgreSQL 生产环境）

```sql
CREATE INDEX idx_specs_project ON specs(project_id);
CREATE INDEX idx_endpoints_spec ON endpoints(spec_id);
CREATE INDEX idx_endpoints_method ON endpoints(method);
CREATE INDEX idx_testcases_endpoint ON testcases(endpoint_id);
CREATE INDEX idx_testcases_project ON testcases(project_id);
CREATE INDEX idx_testcases_category ON testcases(category);
CREATE INDEX idx_executions_project ON executions(project_id);
CREATE INDEX idx_test_results_execution ON test_results(execution_id);
CREATE INDEX idx_defect_reports_project ON defect_reports(project_id);
```

## 五、迁移命令

```bash
# 生成迁移（自动检测模型变化）
cd backend
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1

# 查看迁移历史
alembic history
```
