# APITestGen 产品文档

## 一、产品定位

**大模型驱动的接口自动化测试智能生成平台** — 导入 OpenAPI 文档，AI 自动分析接口语义、生成 pytest 测试用例、一键执行并输出缺陷报告，替代人工编写接口测试。

适用场景：后端 API 开发完成后的接口测试阶段，适合微服务、RESTful API、对外接口等需要大量测试用例覆盖的项目。

---

## 二、核心功能

### 2.1 OpenAPI 文档导入

上传 JSON/YAML 格式的 OpenAPI 3.x 规范文件，系统自动解析所有接口的路径、方法、参数、请求体、响应定义。

- 支持本地文件上传和 URL 导入
- 自动识别 JSON/YAML 格式
- 解析后展示接口列表，按标签和方法筛选

### 2.2 AI 测试用例生成

对接 DeepSeek / OpenAI / Anthropic 等大模型，根据接口定义自动生成 pytest 测试代码。

| 策略 | 说明 | 每接口生成 |
|------|------|------|
| 正向用例 | 合法参数，预期返回成功 | 2-4 条 |
| 负向用例 | 缺参数、错类型、非法值 | 3-5 条 |
| 边界值 | min/max/零值/空值/超长 | 3-5 条 |
| 安全测试 | SQLi / XSS / 路径穿越 / 超大输入 | 2-3 条 |
| Schema 校验 | 响应字段类型、必填、格式 | 2-3 条 |

特点：
- 5 个 Agent 并行生成，19 个接口约 40 秒
- 生成代码经过 AST 语法校验后才入库
- Prompt 模板持续优化，禁止"假通过"模式

### 2.3 测试执行引擎

一键运行生成的 pytest 测试，实时查看执行进度和结果。

- pytest 子进程执行，隔离安全
- JSON 报告自动解析入库
- 实时显示 pass/fail/error 统计
- 支持按类别查看通过率

### 2.4 缺陷报告

基于执行结果自动生成 Markdown 格式缺陷报告。

- 按类别统计通过率（正向/负向/边界值/安全/Schema）
- 失败用例详情含错误信息和堆栈
- 支持 HTML 渲染预览和文件下载

### 2.5 Postman 导入导出

- 导入：上传 Postman Collection v2.1 JSON，自动创建项目和接口
- 导出：将项目中的接口导出为 Postman Collection

### 2.6 仪表盘

- 项目/接口/用例/执行次数统计
- 总体通过率
- 用例分类分布
- 最近活动记录

---

## 三、技术架构

```
前端 (Vue 3 + Element Plus)
    ↕ HTTP / REST
后端 (FastAPI + SQLAlchemy async)
    ├── API 路由层
    ├── 服务层
    │   ├── LLM 引擎 (Provider → Agent → CodeGen)
    │   ├── 执行引擎 (pytest 子进程)
    │   └── 报告引擎 (Jinja2 → Markdown/HTML)
    └── 数据层 (SQLite / PostgreSQL)
    ↕
LLM (DeepSeek / OpenAI / Anthropic / Ollama)
```

---

## 四、使用流程

### 首次使用

1. **启动** — 双击 `start.bat`，自动启动三个服务
2. **配置 LLM** — 打开 http://localhost:5173 → LLM 配置 → 添加提供商（填入 API Key）
3. **新建项目** — 项目管理 → 新建 → 填入名称和 API 基础地址
4. **导入文档** — 上传 OpenAPI JSON/YAML 文件
5. **生成测试** — 点文档 → 查看接口 → 生成测试 → 选策略 → 开始生成
6. **执行测试** — 项目页 → 执行测试
7. **查看报告** — 项目页 → 缺陷报告 → 查看/下载

### 已有文档快速测试

```bash
# 使用内置 Demo API
项目名称: Demo Users API
Base URL:  http://localhost:9001
文档:      e:/kkk/demo_openapi.json
```

### 测试你自己的 API

```
1. 把你的 API 部署到可访问的地址（如 localhost:8080）
2. 导入你项目的 OpenAPI 文档
3. Base URL 填你的 API 地址
4. 生成 → 执行 → 看报告
```

---

## 五、支持的 LLM

| 提供商 | 类型 | 配置示例 |
|------|------|------|
| DeepSeek | openai_compatible | `https://api.deepseek.com` |
| OpenAI | openai | `https://api.openai.com/v1` |
| Anthropic | anthropic | 自动寻址 |
| Ollama | openai_compatible | `http://localhost:11434/v1` |
| vLLM | openai_compatible | 自部署地址 |

---

## 六、项目结构

```
e:/kkk/
├── start.bat                # 一键启动
├── stop.bat                 # 一键停止
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI 入口
│   │   ├── config.py        # 配置项
│   │   ├── api/v1/          # 10 组 REST 路由
│   │   ├── models/          # 9 个 ORM 模型
│   │   ├── schemas/         # Pydantic 校验
│   │   └── services/        # 业务逻辑
│   │       ├── llm/         # LLM 引擎
│   │       ├── executor_service.py
│   │       └── report_service.py
│   ├── demo_api.py          # 本地演示 API
│   ├── generated_tests/     # 运行时生成的测试
│   └── reports/             # 生成的报告文件
├── frontend/
│   └── src/
│       ├── views/           # 10 个页面
│       ├── components/      # 布局组件
│       ├── api/             # Axios 封装
│       └── stores/          # Pinia 状态
├── docs/                    # 文档
└── test_specs/              # 测试用 OpenAPI 文档
```

---

## 七、开发路线

| Phase | 功能 | 状态 |
|------|------|------|
| 0 | 项目基础 + ORM + 前端壳 | ✅ |
| 1 | OpenAPI 导入解析 | ✅ |
| 2 | LLM 集成 + 正向 Agent | ✅ |
| 3 | 全类型 5 Agent 并行 | ✅ |
| 4 | 测试执行引擎 | ✅ |
| 5 | 缺陷报告 Markdown | ✅ |
| 6 | Postman 导入导出 | ✅ |
| 7 | 仪表盘统计 | ✅ |
| 8 | 启动脚本 + 文档 | ✅ |
| 9 | 批量操作 + Prompt 优化 | ✅ |

### 后续方向

- **定时任务** — 定时执行测试，监控 API 健康
- **CI/CD 集成** — GitHub Actions / Jenkins 插件
- **断言智能修正** — LLM 分析失败原因，自动修复测试
- **多环境支持** — 开发/测试/生产环境切换
- **PDF 报告** — WeasyPrint 生成 PDF
- **性能测试** — 集成 Locust/k6
- **Mock 服务** — 根据 OpenAPI 自动生成 Mock
- **用户系统** — 多用户 + 权限管理
