# AgentProbe

> Enterprise AI Agent & Automated Evaluation Platform  
> 企业业务 AI Agent 与自动化质量评测平台

## 项目目标

围绕 **CRM 客户与合同管理** 构建一个可实际调用业务工具的 AI Agent，再开发测试用例管理、Agent 执行轨迹检查、自动化评测和回归报告。

本项目同时作为 Python 进阶、后端开发与 AI Agent 测试开发的实战练习：优先保证代码可理解、可测试、可维护，不追求一开始就引入大量框架。

## 开发阶段

| 版本 | 目标 | 核心知识 |
| --- | --- | --- |
| v0.1 | 客户/合同领域模型、业务服务和单元测试 | dataclass、类型注解、异常处理、Pytest |
| v0.2 | FastAPI 接口及单个 CRM Agent | Pydantic、依赖注入、Function Calling |
| v0.3 | Agent 自动化测试 | Mock、工具调用校验、权限与故障测试 |
| v0.4 | Agent 评测引擎 | Benchmark、Trace、评测指标、报告 |
| v0.5 | 工程化与部署 | PostgreSQL、Docker、CI/CD、质量门禁 |

**当前阶段：v0.1 — Python 工程与领域模型。**

## 已配置技术

- Python 3.12
- uv
- FastAPI / HTTPX / Pydantic Settings
- Pytest / pytest-asyncio
- Ruff / mypy

其他依赖按开发阶段引入，避免一开始增加无关复杂度。

## 本地启动

安装 [uv](https://docs.astral.sh/uv/) 后：

```bash
git clone https://github.com/Tsaitan/agentprobe.git
cd agentprobe
uv sync
uv run python main.py
```

当前 `main.py` 仅为 `uv init` 生成的示例，**AI Agent 尚未实现**。

当单元测试添加后：

```bash
uv run python -m pytest
uv run ruff check .
```

## 如何参与开发

1. 在 [Issues](https://github.com/Tsaitan/agentprobe/issues) 中选择任务。
2. 基于 `main` 新建功能分支（例如 `feat/contract-domain`）。
3. 独立实现功能与 Pytest 测试。
4. 本地执行测试、代码检查。
5. 提交 Pull Request，经过 Code Review 后合并。

第一个任务：**Implement Contract Domain Model**。这是项目的第一块业务代码，重点练习 Python 面向对象、`dataclass`、`Decimal`、日期计算与边界测试。

## 开发原则

- 业务规则放在领域模型和服务层，避免把逻辑全部塞进 API 或 Agent 提示词。
- Agent 只能通过明确授权的工具访问业务数据。
- 对可以确定的业务事实使用规则断言；自然语言质量另用模型辅助评测。
- 不上传真实客户数据、令牌或 `.env` 等敏感文件。
- 学习阶段先实现单个 Agent，暂不急于引入多 Agent、RAG、MCP 或前端。

## 许可

当前尚未添加开源许可证；公开可查看不等于自动授权第三方复用。
