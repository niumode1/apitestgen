# APITestGen 快速上手

## 启动

双击 `start.bat`，打开 http://localhost:5173

## 5 分钟体验

**1. 配 LLM** → 侧边栏 LLM 配置 → 添加：
```
名称: DeepSeek
类型: 兼容 OpenAI
API:  https://api.deepseek.com
Key:  sk-your-api-key-here
模型: deepseek-chat
```

**2. 建项目** → 侧边栏项目管理 → 新建：
```
名称: 测试项目
Base URL: http://localhost:9001
```

**3. 导文档** → 点进项目 → 右上角导入 → 选 `e:/kkk/demo_openapi.json`

**4. 生成测试** → 点文档名 → 右上角生成测试 → 开始生成（约 30 秒）

**5. 执行** → 返回项目页 → 执行测试 → 看 pass/fail

**6. 报告** → 项目页 → 缺陷报告 → 生成 → 查看

## 测试你自己的 API

把 Base URL 和 OpenAPI 文档换成你自己的就行。没有文档？告诉我接口长什么样，AI 帮你写。

## 其他测试文档

`e:/kkk/test_specs/` 下还有三套：Blog API、Task API、Shop API，每套都有不同特色的接口设计。
