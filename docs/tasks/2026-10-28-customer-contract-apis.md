# AgentProbe 每日开发任务｜2026-10-28

今日主题：新增客户合同列表与即将到期合同查询 API。

当前阶段：v0.2，FastAPI 业务接口开发。预计投入：120 分钟。

来源：[AgentProbe AI Agent 全栈开发训练](chatgpt-conversation://6add5520-d9c4-83ec-9f1c-f16d1511fd8a)。当前可读取的完整日任务截至 10 月 26 日，后续条目仅返回引用占位。本文依据该任务明确提出的下一阶段路线，结合 10 月 28 日核实的仓库进度整理；新增参数约定和测试清单属于本地执行方案，并非未能读取的当日原文。

## 1. 当前进度：上一阶段已经交付

| 检查项 | 已确认结果 |
| --- | --- |
| PR #12：合同查询 HTTP API | 已合并，北京时间 10 月 27 日 23:38 |
| Issue #11 | 已关闭 |
| origin/main 最新提交 | `6285514`，已通过 git fetch 核对 |
| 已有接口 | GET /health、GET /contracts/{contract_id}、GET /customers/{customer_id}/contracts |
| 已有 Service 方法 | get_contract、list_customer_contracts、list_expiring_contracts |
| 已有 HTTP 测试 | 6 个实例 |
| 最近确认的 PR CI | 提交 `8c8966a` 的 CI #11 成功，76 个测试通过 |
| 本地所在分支 | codex/customer-contract-apis，已准备就绪 |
| 分支基线 | HEAD、main、origin/main 均为 `6285514`，已重新 fetch 核对 |
| 工作区 | 保留本任务文档，API 入口已新增客户合同列表路由 |
| 本阶段 Issue | #13，open，负责人 Tsaitan |

链接：[已合并的 PR #12](https://github.com/Tsaitan/agentprobe/pull/12)、[已关闭的 Issue #11](https://github.com/Tsaitan/agentprobe/issues/11)、[上一阶段 PR CI](https://github.com/Tsaitan/agentprobe/actions/runs/40522219824)。

76 passed 来自已确认的上一阶段执行结果；本阶段已新增客户合同列表接口，重新运行的原有 HTTP 测试为 6 passed，未重新执行全量 76 条。即将到期查询接口和新增正式测试待完成；本次未核验合并后 main Push 的 CI，不重复创建旧 PR 或重开 Issue #11。

## 2. 今天要完成什么

新增两个接口，让调用方能够查询客户的全部合同，并进一步筛选即将到期的合同：

```http
GET /customers/101/contracts
GET /customers/101/contracts/expiring?days=30&on_date=2026-10-28
```

继续使用现有调用关系：HTTP 路由通过 Depends 获取 ContractService，由 Service 查询仓储并调用 Contract 的领域规则。

本次主要修改：

- `agentprobe/api/main.py`：新增两个路由，导入 Query。
- `tests/test_contract_api.py`：复用现有 Fixture，新增接口测试。
- 本任务文档：逐步记录实际进度与验证结果。

复用 ContractRead、Service、Protocol 和内存仓储。当前需求不要求新增领域模型、Repository 方法或响应包装对象。

## 3. 第一步：准备新任务和分支

已创建 [Issue #13：新增客户合同列表与即将到期查询 API](https://github.com/Tsaitan/agentprobe/issues/13)，状态为 open，负责人为 Tsaitan。中文标题为：

`[v0.2] 新增客户合同列表与即将到期查询 API`

Issue 已包含本文的接口约定、核心测试、可选加强和验收标准，无需重复创建。

开始开发前检查并保留未提交改动，再准备新分支：

```bash
git status
git switch main
git pull --ff-only origin main
git switch -c codex/customer-contract-apis
```

上述命令供流程参考，当前分支已经存在且已切换到 codex/customer-contract-apis，本次复用它，没有重复创建或切换分支。准备阶段重新 git fetch 后确认 HEAD 与 main、origin/main 均为 6285514，本任务文档完整保留。后续接口实现进度见第 4 节。

第一步已经完成，客户合同列表接口也已实现，下一步从第 5 节的即将到期查询接口开始。

## 4. 客户合同列表接口

接口：`GET /customers/{customer_id}/contracts`。

| 项目 | 约定 |
| --- | --- |
| customer_id | 路径参数，int，使用 Path(gt=0) 约束为正整数 |
| Service 调用 | service.list_customer_contracts(customer_id) |
| 成功响应 | 200，JSON 数组，response_model=list[ContractRead] |
| 没有匹配合同 | 200，返回 [] |
| customer_id 为 0、负数、非数字 | 422 |

列表接口返回该客户的全部合同，不按合同状态或日期过滤。其他客户的合同不能混入结果。

目前没有客户实体或客户存在性查询，因此“没有匹配合同”统一返回空数组；不自行推断客户不存在并返回 404。

列表中的每个元素仍有 ContractRead 的七个字段，金额是十进制字符串，日期是 ISO 字符串。无需新增 total、items 等包装字段，也不承诺额外排序规则。

实现时可逐个调用 ContractRead.model_validate(contract) 组装响应列表，与现有单合同接口保持一致。FastAPI 支持使用模型列表作为响应结构，参见[官方响应模型说明](https://fastapi.tiangolo.com/tutorial/response-model/#list-of-models)。

当前实现与验证：已在 API main.py 中新增上述路由，通过 Depends 获取 Service，调用 list_customer_contracts()，再逐个转换为 ContractRead。临时 TestClient 检查已验证：客户 101 的两份合同正常返回，其他客户的数据被排除；已取消且日期已过期的合同仍保留；完整 JSON 中金额、日期序列化正确；无匹配客户返回 200 和 []；0、-1、abc 返回 422 且未调用 Service 查询方法。OpenAPI 中响应定义为 ContractRead 数组。

本步重新运行原有 HTTP 测试，结果为 6 passed；API 入口 Ruff 静态、格式检查通过。仍有一条已知 TestClient 弃用提示，未调整依赖。上述新增场景目前只经过临时检查，尚未写入正式测试文件，也未实现到期查询路由。

## 5. 即将到期合同查询接口

接口：`GET /customers/{customer_id}/contracts/expiring`。

| 参数 | 来源 | 类型和默认值 | 约束 |
| --- | --- | --- | --- |
| customer_id | Path | int，必填 | 大于 0 |
| days | Query | int，默认 30 | 大于等于 0 |
| on_date | Query | date 或 None，默认 None | 提供时应为可解析日期，文档示例使用 YYYY-MM-DD |

参数声明可以沿用 Annotated 风格：

```python
customer_id: Annotated[int, Path(gt=0)]
days: Annotated[int, Query(ge=0)] = 30
on_date: Annotated[date | None, Query()] = None
```

这些是单独的参数声明示例，不是完整可执行路由。使用规则参考 [FastAPI 查询参数说明](https://fastapi.tiangolo.com/tutorial/query-params-str-validations/)。

将解析后的参数传给已有 Service：

```python
service.list_expiring_contracts(
    customer_id=customer_id,
    days=days,
    on_date=on_date,
)
```

路由负责参数校验和 HTTP 响应，不重新实现合同筛选。即将到期的合同必须同时满足：

- 属于目标客户。
- status 为 active。
- start_date <= on_date <= end_date，即判断当天有效。
- 剩余天数在闭区间 [0, days] 内。

成功统一返回 200 和 list[ContractRead]，没有匹配项返回 []。days=0 合法，只匹配判断当天到期且有效的合同。

不传 on_date 时，将 None 交给 Service，由现有逻辑使用当天。HTTP 查询字符串中的 on_date=null 或 on_date=None 并不表示 Python 的 None；调用方应省略该参数。

days 为负数或无法解析成整数、customer_id 非法、on_date 为明显非法日期时，由 FastAPI 返回 422。Service 中原有 days < 0 抛 ValueError 的规则保留，路由不需要通过广泛捕获 ValueError 来代替参数校验。

## 6. 核心 HTTP 测试清单

继续复用函数级 repository、contract、client Fixture。新增测试使用固定的判断日期，例如 date(2026, 10, 28)，构造合同日期时可以使用 timedelta。

### 6.1 客户合同列表

| 场景 | 数据准备和核心断言 |
| --- | --- |
| 只返回指定客户 | 客户 101 两份、102 一份；查询 101，返回 200，长度为 2，ID 集合准确 |
| 保留全部业务状态 | 101 的 active 与 cancelled 合同都能返回，证明没有错误套用到期筛选 |
| 序列化正确 | 至少一个元素断言完整七字段 JSON，金额和日期是约定字符串 |
| 没有匹配客户 | 仓储中有其他客户合同，查询无匹配客户，返回 200 和 [] |
| 非法客户 ID | 参数化覆盖 0、-1、abc，均返回 422，错误位置为 path/customer_id |

前三个维度可以合理合并到一个混合数据测试中，不需要机械拆成重复测试。

### 6.2 即将到期查询

| 场景 | 预期与目的 |
| --- | --- |
| 混合数据过滤 | 仅返回目标客户窗口内有效合同；排除其他客户、已取消、已过期、未开始和超出窗口的合同 |
| 剩余 0、30、31 天，days=30 | 分别包含、包含、不包含，验证窗口两端 |
| pending、expired 状态，日期满足窗口 | 均不返回，补齐状态过滤 |
| days=1，分别明天和后天到期 | 只返回明天到期的合同，验证自定义窗口传入 Service |
| days=0，分别当天和明天到期 | 只返回当天到期的合同 |
| 不传 days，分别剩余 30 和 31 天 | 只返回 30 天的合同，验证接口默认值为 30 |
| 无匹配结果 | 目标客户有合同但全部不满足条件，返回 200 和 [] |
| 无匹配客户 | 仓储有其他客户数据，查询无匹配客户，返回 200 和 [] |
| days=-1 或 days=abc | 返回 422，错误位置为 query/days |
| 非法客户 ID | 参数化覆盖 0、-1、abc，返回 422，错误位置为 path/customer_id |
| on_date=2026-02-30 或 on_date=invalid | 返回 422，错误位置为 query/on_date |

可通过参数化或一个混合数据集覆盖多个业务维度。检查长度和 ID 集合，避免只断言“存在一份结果”而漏掉错误混入的合同。不要在预期值中调用被测筛选方法来计算应返回的合同。

HTTP 非法参数用例检查状态码、错误位置和适当的错误类型，不匹配整段默认错误文案。非法参数不应调用 Service 的业务查询方法；如补充交互断言，可复用 monkeypatch 或 Mock 知识。

### 6.3 可选加强

- [ ] 不传 on_date 时，monkeypatch `agentprobe.services.contract_service` 模块中的 date，使 today() 返回受控日期，验证默认当天行为。
- [ ] 同一个应用连续两次查询已有合同，均返回相同的正确结果。
- [ ] 分别 create_app() 创建两个默认应用，只向第一个的仓储添加合同；第一个查询成功，第二个查询不到。
- [ ] 检查 /docs 成功加载，OpenAPI 包含两个新增路由及参数默认值、范围和列表响应结构。

后面三项延续上一阶段的可选加强；本阶段核心优先级是两个新接口及其业务边界测试。不通过共享全局数据来准备测试环境。

## 7. 时间安排和学习重点

| 时间 | 任务 | 学习重点 |
| --- | --- | --- |
| 15 分钟 | 同步 main、创建新任务与分支 | 已合并功能的后续开发流程 |
| 20 分钟 | 客户合同列表 API | 路径参数、列表响应、空集合语义 |
| 25 分钟 | 到期查询 API | Query、默认参数、date 解析、参数透传 |
| 40 分钟 | HTTP 测试与边界覆盖 | 参数化、固定日期、完整 JSON 断言 |
| 10 分钟 | Swagger 验证 | 请求参数和响应文档 |
| 10 分钟 | 检查、提交、PR | 本地结果和最新 PR CI |

完成后应能解释：Path 和 Query 的区别；days 参数与实际剩余天数的区别；空列表为什么返回 200；HTTP 参数校验与领域规则的职责；为什么 API 路由不重复实现到期判断。

## 8. 检查与交付流程

实现后运行：

```bash
uv run python -m pytest tests/test_contract_api.py -v
uv run python -m pytest -v
uv run ruff check .
uv run ruff format --check .
```

原有 76 条应继续通过，新增实例数量以实际收集结果为准，不为凑数量增加重复测试。本文没有把计划中的新测试标记为已通过。

手动验证时先检查 8000 端口是否已有开发服务，避免重复启动。需要启动时使用：

```bash
uv run uvicorn agentprobe.api.main:app --reload
```

通过 [Swagger 文档](http://127.0.0.1:8000/docs) 查看并执行新接口。默认仓储为空时，两个列表接口返回 [] 是正常结果；成功的非空列表由注入测试数据的自动化测试验证，不强行向默认应用加入演示合同。

提交相关代码、测试和本文，创建新的 PR，目标分支为 main。描述使用 Closes #13 关联本阶段任务，不引用已关闭的 #11。等待该 PR 最新提交的 CI 通过，再进行审阅合并。

## 9. 今日验收清单

- [x] 核对 PR #12 已合并、Issue #11 已关闭，确定新的开发起点。
- [x] 生成今日任务文档；明确引用可读范围与本地执行方案。
- [x] 创建 Issue #13，复用已准备好的 codex/customer-contract-apis 分支，并核对最新 main 基线。
- [x] 客户合同列表仅返回目标客户的全部合同，空结果返回 200 和 []，临时 TestClient 检查通过。
- [ ] 即将到期接口复用 Service 和 Contract 规则，不在路由中重写筛选。
- [ ] customer_id、days、on_date 的参数声明与 422 行为正确。
- [ ] 两个接口均使用 list[ContractRead]，字段和序列化正确。
- [ ] 固定日期验证到期边界、自定义窗口和默认窗口。
- [ ] 原有测试与新增测试全部通过，记录实际数量。
- [ ] Ruff 静态与格式检查通过。
- [ ] Swagger 能展示新增接口、查询参数和列表响应。
- [ ] 创建新 PR，关联正确 Issue，最新提交 CI 通过。

本次不扩展数据库、写入接口、鉴权、前端、LLM 或 Agent。两个查询接口完成后，再将已有业务能力封装为 Agent 工具。
