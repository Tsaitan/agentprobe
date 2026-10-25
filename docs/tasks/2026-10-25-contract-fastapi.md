# AgentProbe 每日开发任务｜2026-10-25

今日主题：使用 FastAPI 实现第一个合同查询 HTTP API。

当前阶段：v0.2，AI Agent 全栈后端开发。预计投入：120 分钟。

来源：[AgentProbe AI Agent 全栈开发训练](chatgpt-conversation://6add5520-d9c4-83ec-9f1c-f16d1511fd8a)。本文依据引用对话的完整任务整理。应用工厂、健康检查、ContractRead 和合同查询路由已就绪；下一步编写正式 HTTP 接口测试。

## 1. 前置进度与当前起点

已经具备的能力：

- Contract 领域模型、内存仓储、ContractService。
- ContractRepository Protocol、六个 Mock 测试，以及真实仓储协作测试。
- GitHub Actions CI，运行 Pytest、Ruff 静态与格式检查。
- 最近已验证的测试基线为 70 条通过。本次未重新运行已有测试。

本次本地检查：

| 项目 | 结果 |
| --- | --- |
| 当前分支 | `feat/contract-fastapi` |
| 开发基线 | `e8e5461`，已核对与 origin/main 一致 |
| 当前阶段 | 合同查询路由已实现，正式测试待补 |
| FastAPI API 包 | 已有 create_app()、模块级 app、/health 和 /contracts/{contract_id} |
| 根目录 main.py | 仍为初始化示例 |
| 已声明的相关依赖 | FastAPI、HTTPX、Pydantic Settings、Uvicorn |

已通过 git fetch 更新远端信息，确认当前分支基线与 origin/main 同为 `e8e5461`，复用已有的 FastAPI 功能分支。PR #10、Issue #9 和 main CI 的具体状态本次未逐项查询。

应用工厂创建时装配一次 ContractService，保存在 app.state.contract_service。临时 TestClient 检查已确认 /health 返回 200 和约定 JSON，/docs、/openapi.json 返回 200，OpenAPI 包含 /health；外部仓储按原实例注入，不同默认应用的仓储相互独立。

上述检查尚未保存为正式 API 测试，tests/test_contract_api.py 目前仅有说明。检查过程中出现当前 Starlette 对 HTTPX TestClient 的弃用提示，检查结果仍通过；本步未调整依赖。

ContractRead 已在 schemas.py 中定义七个字段，并配置 from_attributes=True。临时检查已确认可通过 model_validate(contract) 从领域对象读取字段；Python 模型中金额、日期保留 Decimal 和 date 类型，model_dump(mode="json") 与 model_dump_json() 均输出完整约定字段，金额为 "50000.00"，日期为 ISO 字符串。响应模型文件的 Ruff 静态和格式检查通过。

合同查询路由已接入 ContractRead，通过 Depends(get_contract_service) 获取当前应用保存的 Service，再调用 service.get_contract()。临时 TestClient 检查已验证：存在的 ID 返回 200 和完整约定 JSON，不存在的正整数 ID 返回 404 及 {"detail": "合同不存在"}，0、负数和非数字 ID 返回 422 且没有调用 Service 查询方法；OpenAPI 包含路径正整数约束和 ContractRead 响应结构。入口文件的 Ruff 静态与格式检查通过。本步尚未新增正式测试、未重新运行原有测试，未启动真实 HTTP 服务器。

## 2. 今天的业务目标与分层

让调用方通过 HTTP 查询合同：

```http
GET /contracts/1001
```

处理流程：HTTP 请求进入 FastAPI，路由通过 Depends 获取 ContractService，由 Service 调用 Repository，再将结果转换为响应模型和 JSON。

| 层次 | 本次职责 |
| --- | --- |
| FastAPI 路由 | 接收请求、校验路径参数、调用 Service、返回 HTTP 状态 |
| ContractRead | 定义响应字段，完成响应校验和 JSON 序列化 |
| ContractService | 复用已有查询流程 |
| Repository | 复用已有数据访问能力 |
| Contract | 复用已有领域规则 |

路由不直接查询仓储，也不重复合同业务规则。今天只实现健康检查和按合同 ID 查询，不扩展客户列表或到期查询接口。

## 3. 文件安排

新增以下文件：

```text
agentprobe/
└── api/
    ├── __init__.py
    ├── main.py
    └── schemas.py
tests/
└── test_contract_api.py
```

`agentprobe/api/main.py` 是本次应用入口，与仓库根目录的 `main.py` 不同。无需为了新增 API 覆盖原有根目录示例。

实现和测试时使用现有项目环境；依赖有变更才更新 `pyproject.toml` 和锁文件。

## 4. 创建应用与健康检查

在 API main 模块提供 `create_app()` 应用工厂，并暴露模块级 `app` 供 Uvicorn 启动。

建议工厂接收可选的仓储依赖：

```python
def create_app(repository: ContractRepository | None = None) -> FastAPI: ...
```

应用装配约定：

- 未传仓储时，为该应用创建内存仓储，并装配 ContractService。
- 传入仓储时使用该实例，供测试控制数据。
- 同一个应用运行期间复用已装配的仓储，避免每次请求重新创建空仓储。
- 不同 create_app() 调用的默认仓储应彼此独立。
- 可通过闭包或 app.state 保存已装配的服务，由依赖提供函数交给路由。
- 路由使用 Depends 注入 Service，不在路由内查询 Repository。

首先实现：

```http
GET /health
```

响应为 HTTP 200：

```json
{"status": "ok"}
```

启动命令：

```bash
uv run uvicorn agentprobe.api.main:app --reload
```

手动访问：

- [健康检查](http://127.0.0.1:8000/health)
- [Swagger 文档](http://127.0.0.1:8000/docs)

这些链接用于本地启动后验证，生成文档并不代表服务已经运行。

## 5. 定义 ContractRead 响应模型

在 `agentprobe/api/schemas.py` 中定义 `ContractRead(BaseModel)`：

| 字段 | Python 类型 |
| --- | --- |
| id | int |
| customer_id | int |
| name | str |
| amount | Decimal |
| start_date | date |
| end_date | date |
| status | str |

配置 `model_config = ConfigDict(from_attributes=True)`，允许从 Contract 对象的属性读取字段。

需要理解：Domain 的 Contract 负责业务规则，API 的 ContractRead 负责对外响应结构。两个模型职责不同，不把 HTTP 处理逻辑放入 Domain。

在合同查询路由中使用 `response_model=ContractRead`。响应约定：

- Decimal 金额以十进制字符串返回，例如 `"50000.00"`。
- 日期以 ISO 日期字符串返回，例如 `"2026-11-10"`。
- 测试应断言实际 JSON 类型和值，避免把金额转换为 float 后再比较。

预期响应示例：

```json
{
  "id": 1001,
  "customer_id": 101,
  "name": "设备采购合同",
  "amount": "50000.00",
  "start_date": "2026-01-01",
  "end_date": "2026-11-10",
  "status": "active"
}
```

这只是响应格式示例，不要求所有测试或默认数据都使用同一金额和日期。

## 6. 实现合同查询接口

接口：`GET /contracts/{contract_id}`。

| 输入场景 | HTTP 状态 | 行为 |
| --- | --- | --- |
| 正整数 ID，合同存在 | 200 | 返回符合 ContractRead 的 JSON |
| 正整数 ID，合同不存在 | 404 | 返回明确的不存在提示 |
| 负数或 0 | 422 | 参数校验失败 |
| 非数字路径参数 | 422 | 参数类型校验失败 |

实现要求：

- `contract_id` 声明为 int，通过 `Path(gt=0)` 或等价写法约束为正整数。
- 使用 Depends 获取 ContractService。
- 调用 `service.get_contract(contract_id)`。
- 返回 None 时，通过 HTTPException 返回 404；不要把 None 作为成功响应。
- 查询成功时，通过响应模型输出合同。
- 非法 ID 的 422 由框架参数校验处理，不进入业务查询。

404 错误消息在实现时选定并保持一致，测试检查对应 JSON，不依赖整段框架默认错误文案。

可以为手动演示添加虚构合同，但应明确种子数据的装配位置。测试自行向独立仓储准备数据，不依赖默认演示数据；应用工厂收到测试仓储时，不额外注入演示合同。

## 7. HTTP 接口测试

在 `tests/test_contract_api.py` 中使用 `fastapi.testclient.TestClient`，不需要启动真实网络服务器，也不需要 Mock HTTP 请求。

建议 Fixture：

- repository：为每条测试创建独立内存仓储。
- contract：提供合法的虚构合同数据。
- client：调用 create_app(repository)，使用 TestClient 上下文管理器提供客户端。

至少覆盖以下五个场景：

| 编号 | 场景 | 核心断言 |
| --- | --- | --- |
| TC01 | GET /health | 200，JSON 等于 {"status": "ok"} |
| TC02 | 预先添加合同，GET /contracts/1001 | 200，完整 JSON 字段和值正确，金额和日期为字符串 |
| TC03 | 查询没有添加的正整数 ID | 404，错误 JSON 正确 |
| TC04 | GET /contracts/-1 | 422，返回参数校验错误 |
| TC05 | GET /contracts/abc | 422，返回参数类型错误 |

可选加强：

- [ ] ID 为 0 时也返回 422。
- [ ] 同一应用中连续查询合同，确认没有每次请求重建空仓储。
- [ ] 创建两个独立应用，向其中一个的仓储添加合同，另一个应用查询不到。
- [ ] GET /docs 返回成功，OpenAPI 中可以找到新增业务路由。

TestClient 示例：

```python
def test_health(client: TestClient):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

每条测试添加中文 Docstring，说明场景和预期。已有 Mock 单元测试与真实仓储测试保留，不因新增 API 而删除或替换。

## 8. 学习重点与时间安排

| 时间 | 开发任务 | 学习重点 |
| --- | --- | --- |
| 15 分钟 | 理解 HTTP GET、路由和状态码 | 网络请求如何调用 Python 函数 |
| 25 分钟 | 建立应用工厂与健康检查 | FastAPI 实例、模块入口、Swagger |
| 30 分钟 | 定义响应模型，实现合同查询 | Pydantic、response_model、Depends、HTTPException |
| 35 分钟 | 编写五个核心 HTTP 用例 | TestClient、Fixture、序列化和错误响应 |
| 15 分钟 | 检查、提交、创建 PR | Pytest、Ruff、CI |

完成后应能解释：

1. Contract dataclass 和 ContractRead 分别负责什么？
2. Depends 如何为路由提供 Service，与构造函数注入有什么联系？
3. 仓储在哪创建，为什么不能每次请求创建一个空仓储？
4. 为什么合同不存在返回 404，而非法 ID 返回 422？
5. TestClient 为什么无需真实监听端口也能测试接口？

阅读资料：[FastAPI 教程](https://fastapi.tiangolo.com/tutorial/)、[TestClient 测试指南](https://fastapi.tiangolo.com/tutorial/testing/)。

## 9. Issue、分支和检查流程

已创建 [Issue #11：使用 FastAPI 实现合同查询 HTTP API](https://github.com/Tsaitan/agentprobe/issues/11)，状态为 open，负责人为 `Tsaitan`，无需重复创建。

中文标题：

`[v0.2] 使用 FastAPI 实现合同查询 HTTP API`

Issue 描述已包含本文件的应用装配、响应模型、接口状态、五个测试场景和验收要求。

确认已有改动得到保留，再从最新 main 准备引用任务指定的分支：

```bash
git switch main
git pull origin main
git switch -c feat/contract-fastapi
```

分支已存在则切换继续，不重复创建。开发完成后检查：

```bash
uv run python -m pytest tests/test_contract_api.py -v
uv run python -m pytest -v
uv run ruff check .
uv run ruff format --check .
```

提交相关 API、测试与任务文档，推送分支，创建以 main 为目标的 PR，使用 `Closes #11` 关联 Issue，并记录实际验证结果。

已有 70 条测试，加至少 5 个 HTTP 测试，目标为至少 75 条通过。这是计划数量，不是当前实际执行结果。

## 10. 验收清单与范围

- [x] 新增 API 包和约定文件，正式测试内容待补。
- [x] create_app() 支持独立仓储注入，同一应用复用仓储，临时检查通过。
- [x] /docs、/openapi.json 通过 TestClient 检查，健康检查已出现在文档定义中。
- [ ] 实际启动 Uvicorn 并通过浏览器验证，补全合同路由后核对业务接口文档。
- [x] /health 返回 200 和约定 JSON，临时 TestClient 检查通过。
- [x] 存在的合同返回 200 和完整正确的响应，临时 TestClient 检查通过。
- [x] 不存在的合同返回 404，临时 TestClient 检查通过。
- [x] 非法合同 ID 返回 422，正整数约束有效，临时 TestClient 检查通过。
- [x] 定义 ContractRead，临时验证从领域对象读取字段及金额、日期序列化。
- [x] 在合同路由中使用 ContractRead 响应模型，临时验证 HTTP JSON 响应。
- [x] 路由通过 Depends 注入 Service，并调用 Service 查询。
- [ ] 至少五个 HTTP API 测试通过，数据独立。
- [ ] 原有 70 条测试保持通过，全量测试通过。
- [ ] Ruff 静态和格式检查通过。
- [ ] PR 最新 GitHub Actions 检查通过，完成 Code Review。

今天不实现客户合同列表、到期查询 API、数据库、鉴权、前端或 AI Agent。时间不足时优先完成应用启动、合同查询和 200/404 测试，未完成项如实记录。

本次 API 验收后，再暴露客户合同与到期查询能力，逐步进入 CRM Agent、Tool Calling、前端交互和 Agent 自动化评测。
