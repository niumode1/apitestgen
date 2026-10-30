# 开发指南

## 一、环境准备

### 系统要求
- Python >= 3.11
- Node.js >= 18
- Git (可选)

### 克隆项目
```bash
cd e:/kkk
```

### 后端配置
```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv .venv

# Windows PowerShell:
.venv\Scripts\Activate.ps1
# 如果报执行策略错误，先运行:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Windows CMD:
# .venv\Scripts\activate.bat

# Mac/Linux:
# source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（复制示例文件后编辑）
copy .env.example .env   # Windows
# cp .env.example .env   # Mac/Linux
# 编辑 .env 填入 LLM API Key
```

### 前端配置
```bash
cd frontend
npm install
```

---

## 二、开发启动

### 启动后端
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

访问:
- API 文档 (Swagger UI): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/api/v1/health

### 启动前端
```bash
cd frontend
npm run dev
```

访问: http://localhost:5173

前端自动代理 `/api` → `localhost:8000`，无需额外配置。

---

## 三、项目结构速览

```
backend/app/
├── main.py              # FastAPI 应用入口，生命周期管理
├── config.py            # 所有配置项（pydantic-settings）
├── database.py          # 异步 SQLAlchemy 引擎和会话工厂
├── events.py            # 事件总线（WebSocket 推送用）
│
├── models/              # ORM 数据模型（9个）
│   ├── base.py          #   UUIDMixin, TimestampMixin
│   ├── project.py       #   项目
│   ├── spec.py          #   OpenAPI 文档
│   ├── endpoint.py      #   API 接口
│   ├── testcase.py      #   测试用例
│   ├── execution.py     #   测试执行 + 测试结果
│   ├── report.py        #   缺陷报告
│   ├── llm.py           #   LLM 提供商
│   └── postman.py       #   Postman 集合
│
├── schemas/             # Pydantic 请求/响应 Schema（12个模块）
│
├── api/v1/              # REST API 路由（10个模块）
│   ├── router.py        #   路由聚合
│   ├── projects.py      #   ✅ CRUD 已实现
│   ├── specs.py         #   ✅ 上传/解析 已实现
│   ├── endpoints.py     #   ✅ 列表/详情 已实现
│   ├── llm_providers.py #   ✅ CRUD 已实现
│   ├── generation.py    #   🔜 Phase 2-3
│   ├── testcases.py     #   🔜 Phase 3
│   ├── executions.py    #   🔜 Phase 4
│   ├── reports.py       #   🔜 Phase 5
│   ├── postman.py       #   🔜 Phase 6
│   └── dashboard.py     #   🔜 Phase 7
│
├── services/            # 业务逻辑层
│   ├── spec_parser.py   #   🔜 OpenAPI 解析器
│   ├── postman_service.py # 🔜 Postman 导入导出
│   ├── executor_service.py # 🔜 Pytest 执行引擎
│   ├── report_service.py  # 🔜 报告生成
│   └── llm/             #   🔜 LLM 引擎
│       ├── provider.py  #     OpenAI/Anthropic/兼容
│       ├── codegen.py   #     LLM输出 → pytest 代码
│       ├── agents/      #     7个专项 Agent
│       └── prompts/     #     Jinja2 提示词模板
│
├── templates/           # Jinja2 模板
│   ├── report.html.j2   #   🔜 报告 HTML 模板
│   ├── test_module.py.j2 #  🔜 测试文件脚手架
│   └── conftest.py.j2   #   🔜 conftest 脚手架
│
└── utils/
    └── logger.py        # loguru 日志配置
```

---

## 四、开发规范

### 4.1 数据库操作

```python
# ✅ 正确：使用异步查询
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project import Project

async def get_projects(db: AsyncSession):
    result = await db.execute(select(Project))
    return result.scalars().all()

# ✅ 正确：依赖注入获取 session
from app.api.deps import get_session

@router.get("")
async def list_projects(db: AsyncSession = Depends(get_session)):
    ...
```

### 4.2 Schema 使用

```python
# 请求：使用 Create/Update Schema
from app.schemas.project import ProjectCreate

@router.post("")
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_session)):
    project = Project(**data.model_dump())
    ...

# 响应：使用 Response Schema，开启 ORM 模式
from app.schemas.project import ProjectResponse

@router.get("/{id}", response_model=ProjectResponse)
async def get_project(project: Project = Depends(get_project_or_404)):
    return ProjectResponse.model_validate(project)
```

### 4.3 资源存在性检查

```python
# 使用 deps.py 中预置的依赖检查
from app.api.deps import get_project_or_404, get_spec_or_404

@router.get("/{project_id}")
async def get_project(project: Project = Depends(get_project_or_404)):
    # project 保证存在，否则自动返回 404
    return project
```

### 4.4 新增路由

```python
# 1. 在 app/api/v1/ 下创建 new_resource.py
from fastapi import APIRouter
router = APIRouter()

@router.get("")
async def list_resources(...):
    ...

# 2. 在 app/api/v1/router.py 中注册
from app.api.v1 import new_resource
api_v1_router.include_router(new_resource.router, prefix="/new-resource", tags=["NewResource"])
```

### 4.5 新增模型

```python
# 1. 在 app/models/ 下创建 new_model.py
# 2. 在 app/models/__init__.py 中导出
# 3. 运行迁移
alembic revision --autogenerate -m "add new_model"
alembic upgrade head
```

---

## 五、数据库迁移

```bash
cd backend

# 修改模型后，生成迁移文件
alembic revision --autogenerate -m "描述你的改动"

# 查看生成的迁移文件
cat migrations/versions/xxx_描述你的改动.py

# 应用迁移
alembic upgrade head

# 回滚最近一次迁移
alembic downgrade -1
```

---

## 六、测试

```bash
# 运行平台自身的测试
cd backend
pytest tests/ -v

# 带覆盖率
pytest tests/ --cov=app --cov-report=html
```

---

## 七、实现阶段总览

| Phase | 内容 | 核心文件 | 状态 |
|-------|------|---------|------|
| 0 | 项目基础搭建 | models/, schemas/, api/v1/ | ✅ 完成 |
| 1 | OpenAPI 文档导入 | services/spec_parser.py | 🔜 下一步 |
| 2 | LLM 基础集成 | services/llm/provider.py, agents/ | 待开发 |
| 3 | 多 Agent 编排 | services/llm/agents/orchestrator.py | 待开发 |
| 4 | 测试执行引擎 | services/executor_service.py | 待开发 |
| 5 | 缺陷报告 | services/report_service.py | 待开发 |
| 6 | Postman 集成 | services/postman_service.py | 待开发 |
| 7 | 仪表盘分析 | services/analytics_service.py | 待开发 |
| 8 | 产品化完善 | tests/, CI/CD, Docker | 待开发 |

---

## 八、常用命令速查

```bash
# ── 后端 ──
cd backend
uvicorn app.main:app --reload                    # 启动开发服务器
python -c "from app.main import app; print('ok')" # 验证导入
alembic revision --autogenerate -m "msg"          # 生成迁移
alembic upgrade head                               # 执行迁移

# ── 前端 ──
cd frontend
npm run dev                 # 启动开发服务器
npm run build               # 生产构建
npx vue-tsc --noEmit        # 类型检查

# ── API 测试 ──
curl localhost:8000/api/v1/health
curl localhost:8000/api/v1/projects
curl -X POST localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"test"}'
```
