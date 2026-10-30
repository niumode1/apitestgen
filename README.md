# APITestGen — 大模型驱动的接口自动化测试智能生成平台

## 一键启动

双击 `start.bat`，自动启动三个服务：

| 服务 | 端口 | 地址 |
|------|------|------|
| 前端界面 | 5173 | http://localhost:5173 |
| 后端 API | 8000 | http://localhost:8000/docs |
| Demo API | 9001 | http://localhost:9001/docs |

## 使用流程

```
1. 打开 http://localhost:5173
2. 侧边栏 → 项目管理 → 新建项目（Base URL 填 http://localhost:9001）
3. 导入 OpenAPI 文档（或上传 e:/kkk/demo_openapi.json）
4. 点文档 → 生成测试 → 选策略 → 开始生成
5. 项目页 → 执行测试 → 查看 pass/fail
6. 项目页 → 缺陷报告 → 查看/下载
```

## 功能

| 模块 | 说明 |
|------|------|
| 仪表盘 | 项目/接口/用例/执行次数统计 |
| 项目管理 | OpenAPI 导入、接口预览 |
| AI 生成 | 正向/负向/边界值/安全/Schema，5类 Agent 并行 |
| 执行引擎 | pytest 子进程运行，JSON 报告解析 |
| 缺陷报告 | Markdown 格式，失败用例汇总 |
| Postman | 导入导出 v2.1 格式 |

## 支持的 LLM

- OpenAI (GPT-4o, GPT-4o-mini)
- Anthropic (Claude)
- DeepSeek
- Ollama / vLLM / 任何兼容 OpenAI 的 API

## 技术栈

| 层 | 技术 |
|------|------|
| 后端 | FastAPI + SQLAlchemy async + Pydantic v2 |
| 数据库 | SQLite / PostgreSQL |
| 测试 | Pytest + httpx + pytest-asyncio |
| LLM | OpenAI SDK (多后端兼容) |
| 前端 | Vue 3 + TypeScript + Element Plus + Pinia |
| 构建 | Vite + Axios |
