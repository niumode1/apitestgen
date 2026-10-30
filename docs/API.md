# API 接口文档

Base URL: `http://localhost:8000/api/v1`

Swagger UI: `http://localhost:8000/docs`

---

## 通用说明

### 分页参数

所有列表接口支持分页：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | int | 1 | 页码（从1开始） |
| `page_size` | int | 20 | 每页条数（最大100） |

### 响应格式

**分页响应:**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

**错误响应:**
```json
{
  "detail": "Project xxx not found"
}
```

---

## 一、健康检查

### `GET /health`

```bash
curl http://localhost:8000/api/v1/health
```

**响应 (200):**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "development"
}
```

---

## 二、项目管理

### `GET /projects` — 获取项目列表

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `search` | string | 否 | 按名称搜索 |
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页条数 |

```bash
curl "http://localhost:8000/api/v1/projects?page=1&page_size=20"
```

**响应:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "宠物商店API",
      "description": "Petstore 示例项目",
      "base_url": "https://petstore.swagger.io/v2",
      "spec_count": 1,
      "testcase_count": 45,
      "execution_count": 3,
      "created_at": "2026-06-29T09:10:51",
      "updated_at": "2026-06-29T09:10:51"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### `POST /projects` — 创建项目

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的API项目",
    "description": "项目描述",
    "base_url": "https://api.example.com"
  }'
```

**请求体:**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 项目名称 (1-255字符) |
| `description` | string | 否 | 项目描述 |
| `base_url` | string | 否 | API 基础地址 |

**响应 (201):** 返回 ProjectResponse 对象

### `GET /projects/{project_id}` — 获取项目详情

```bash
curl http://localhost:8000/api/v1/projects/{project_id}
```

### `PUT /projects/{project_id}` — 更新项目

```bash
curl -X PUT http://localhost:8000/api/v1/projects/{project_id} \
  -H "Content-Type: application/json" \
  -d '{"name": "新名称", "base_url": "https://new-api.example.com"}'
```

所有字段可选，只更新传入的字段。

### `DELETE /projects/{project_id}` — 删除项目

```bash
curl -X DELETE http://localhost:8000/api/v1/projects/{project_id}
```

> ⚠️ 级联删除：会同时删除该项目下的所有 Spec、Endpoint、TestCase、Execution、Report。

---

## 三、OpenAPI 文档管理

### `GET /projects/{project_id}/specs` — 获取文档列表

```bash
curl "http://localhost:8000/api/v1/projects/{project_id}/specs"
```

**响应字段:**
| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | uuid | 文档ID |
| `name` | string | 文档名称（来自 `info.title`） |
| `version` | string | API 版本（来自 `info.version`） |
| `spec_format` | string | `json` 或 `yaml` |
| `parse_status` | string | `pending` / `parsed` / `error` |
| `endpoint_count` | int | 解析出的接口数量 |
| `imported_at` | datetime | 导入时间 |

### `POST /projects/{project_id}/specs` — 上传 OpenAPI 文档

```bash
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/specs \
  -F "file=@petstore.yaml"
```

支持格式: `.json` / `.yaml` / `.yml`

**限制:** 文件最大 10MB

**响应 (201):**
```json
{
  "id": "uuid",
  "name": "Swagger Petstore",
  "version": "1.0.0",
  "spec_format": "yaml",
  "parse_status": "parsed",
  "endpoint_count": 20,
  "message": "Imported 'Swagger Petstore' with 20 endpoints"
}
```

处理逻辑:
1. 检测文件格式（JSON / YAML）
2. 解析内容，校验 `openapi` 字段
3. 遍历 `paths` 下所有方法（GET/POST/PUT/DELETE/PATCH...）
4. 提取参数、请求体、响应定义
5. 合并 path-level 和 operation-level 参数
6. 存入 `OpenAPISpec` + 批量 `APIEndpoint` 记录

### `GET /projects/{project_id}/specs/{spec_id}` — 获取文档详情

```bash
curl http://localhost:8000/api/v1/projects/{project_id}/specs/{spec_id}
```

### `DELETE /projects/{project_id}/specs/{spec_id}` — 删除文档

```bash
curl -X DELETE http://localhost:8000/api/v1/projects/{project_id}/specs/{spec_id}
```

> ⚠️ 级联删除所有关联的 Endpoint 和 TestCase。

---

## 四、接口管理

### `GET /specs/{spec_id}/endpoints` — 获取接口列表

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `method` | string | 否 | 按 HTTP 方法过滤 (GET/POST...) |
| `tag` | string | 否 | 按标签过滤 |
| `search` | string | 否 | 搜索 path/summary/operationId |
| `deprecated` | bool | 否 | 是否已弃用 |

```bash
curl "http://localhost:8000/api/v1/specs/{spec_id}/endpoints?method=POST&tag=pet"
```

**响应:**
```json
{
  "items": [
    {
      "id": "uuid",
      "path": "/pet",
      "method": "POST",
      "summary": "Add a new pet to the store",
      "tags": ["pet"],
      "deprecated": false,
      "analyzed_at": null,
      "testcase_count": 5
    }
  ]
}
```

### `GET /specs/{spec_id}/endpoints/summary` — 接口统计

```bash
curl http://localhost:8000/api/v1/specs/{spec_id}/endpoints/summary
```

**响应:**
```json
{
  "total": 20,
  "by_method": {"GET": 8, "POST": 5, "PUT": 2, "DELETE": 5},
  "by_tag": {"pet": 8, "store": 4, "user": 8},
  "deprecated_count": 1
}
```

### `GET /specs/{spec_id}/endpoints/{endpoint_id}` — 接口详情

```bash
curl http://localhost:8000/api/v1/specs/{spec_id}/endpoints/{endpoint_id}
```

返回完整的接口定义，包括参数列表、请求体 Schema、响应定义、安全配置等。

---

## 五、LLM 提供商管理

### `GET /llm/providers` — 获取提供商列表

```bash
curl http://localhost:8000/api/v1/llm/providers
```

### `POST /llm/providers` — 添加提供商

```bash
curl -X POST http://localhost:8000/api/v1/llm/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My OpenAI",
    "provider_type": "openai",
    "api_base": "https://api.openai.com/v1",
    "api_key": "sk-...",
    "default_model": "gpt-4o-mini"
  }'
```

**provider_type 可选值:**
| 值 | 说明 |
|------|------|
| `openai` | OpenAI API |
| `anthropic` | Anthropic Claude API |
| `openai_compatible` | 兼容 OpenAI 格式 (Ollama, vLLM, OpenRouter 等) |

### `PUT /llm/providers/{provider_id}` — 更新提供商

```bash
curl -X PUT http://localhost:8000/api/v1/llm/providers/{provider_id} \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

### `DELETE /llm/providers/{provider_id}` — 删除提供商

```bash
curl -X DELETE http://localhost:8000/api/v1/llm/providers/{provider_id}
```

### `POST /llm/providers/{provider_id}/test` — 测试连接

```bash
curl -X POST http://localhost:8000/api/v1/llm/providers/{provider_id}/test
```

（完整实现在 Phase 2）

---

## 六、测试生成（Phase 2-3）

### `POST /specs/{spec_id}/generate` — 触发测试生成

```bash
curl -X POST http://localhost:8000/api/v1/specs/{spec_id}/generate \
  -H "Content-Type: application/json" \
  -d '{
    "spec_id": "uuid",
    "strategy": "all",
    "max_testcases_per_endpoint": 10,
    "review_enabled": true
  }'
```

**strategy 可选值:**
| 值 | 说明 |
|------|------|
| `all` | 生成全部类别 |
| `positive_only` | 仅正向用例 |
| `negative_only` | 仅负向用例 |
| `boundary_only` | 仅边界值测试 |
| `security_only` | 仅安全测试 |
| `schema_only` | 仅 Schema 校验 |

（完整实现在 Phase 2-3）

---

## 七、API 路由总览

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| `GET` | `/health` | 健康检查 | ✅ |
| `GET/POST` | `/projects` | 项目列表/创建 | ✅ |
| `GET/PUT/DELETE` | `/projects/{pid}` | 项目详情/更新/删除 | ✅ |
| `GET/POST` | `/projects/{pid}/specs` | 文档列表/上传 | ✅ |
| `GET/DELETE` | `/projects/{pid}/specs/{sid}` | 文档详情/删除 | ✅ |
| `GET` | `/specs/{sid}/endpoints` | 接口列表 | ✅ |
| `GET` | `/specs/{sid}/endpoints/summary` | 接口统计 | ✅ |
| `GET` | `/specs/{sid}/endpoints/{eid}` | 接口详情 | ✅ |
| `GET/POST` | `/llm/providers` | 提供商列表/添加 | ✅ |
| `GET/PUT/DELETE` | `/llm/providers/{pid}` | 提供商详情/更新/删除 | ✅ |
| `POST` | `/llm/providers/{pid}/test` | 测试连接 | 🔜 |
| `POST` | `/specs/{sid}/generate` | 触发生成 | 🔜 |
| `GET` | `/projects/{pid}/testcases` | 用例列表 | 🔜 |
| `GET` | `/projects/{pid}/executions` | 执行列表 | 🔜 |
| `GET` | `/projects/{pid}/reports` | 报告列表 | 🔜 |
| `POST` | `/postman/import` | Postman导入 | 🔜 |
| `GET` | `/dashboard/summary` | 仪表盘 | 🔜 |

> ✅ = Phase 0 已实现 &nbsp;&nbsp; 🔜 = 后续 Phase 实现
