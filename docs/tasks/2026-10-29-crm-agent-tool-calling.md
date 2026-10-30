# AgentProbe 每日开发任务｜2026-10-29

今日主题：实现第一个 CRM Agent，完成合同查询工具调用闭环。

预计投入：120 分钟。当前阶段：从 v0.2 业务 API 进入 v0.3 CRM Agent。

来源：[AgentProbe AI Agent 全栈开发训练](chatgpt-conversation://6add5520-d9c4-83ec-9f1c-f16d1511fd8a)。引用对话目前能读取的完整日任务截至 10 月 26 日，之后包括当日条目仅返回引用占位。本文依据其“客户合同与到期 API → 第一个 CRM Agent → Tool Calling”路线，结合 10 月 29 日已核实的项目进度续排；这是本地执行方案，不是未能读取的当日正文转录。

任务准备阶段已完成：创建 Issue #15，复用已准备好的功能分支，并核对本地已安装的 SDK 与锁文件。AgentContext、普通合同查询适配函数和 SDK 工具包装已完成，Agent 工厂、正式测试及真实模型调用待完成。

## 1. 当前起点

| 项目 | 已核实状态 |
| --- | --- |
| PR #14：客户合同与即将到期查询 API | 已合并，北京时间 10 月 28 日 23:48 |
| Issue #13 | 已关闭 |
| origin/main | `3227d55`，已通过 git fetch 核对 |
| 已有查询能力 | 按合同 ID 查询、客户合同列表、即将到期合同查询 |
| 已有 HTTP 测试 | 28 个实例 |
| 最近确认的测试基线 | 本地及 PR CI 均为 98 passed |
| 最近确认的 PR CI | `e56518c` 的 CI #14 成功 |
| 当前本地分支 | codex/crm-agent-tool-calling，HEAD、main、origin/main 均为 `3227d55` |
| 现有依赖 | FastAPI、HTTPX、Pydantic Settings、Uvicorn，以及测试工具 |
| Agents SDK | 已声明、锁定并安装 openai-agents 0.24.0 |
| 本阶段 Issue | #15，open，负责人 Tsaitan |
| Agent 代码 | 已有 AgentContext、query_expiring_contracts 和 SDK 工具，Agent 工厂及演示待补 |

链接：[已合并的 PR #14](https://github.com/Tsaitan/agentprobe/pull/14)、[已关闭的 Issue #13](https://github.com/Tsaitan/agentprobe/issues/13)、[上一阶段 PR CI](https://github.com/Tsaitan/agentprobe/actions/runs/40719453151)。

初始生成文档时沿用上一阶段 98 passed 记录；准备 SDK 后已重新执行本地全量测试，仍为 98 passed，没有进行真实模型请求。本次没有重新确认合并后 main Push 的 CI。不重复开发已有查询接口，不重开 Issue #13。

## 2. 今天的最小业务目标

让用户能够提出：

> 以 2026-10-29 为基准，帮我查询客户 101 未来 30 天内到期的合同，并列出合同编号和到期日期。

预期过程：模型理解问题，发出合同查询工具调用；应用执行工具，调用 ContractService；工具将实际查询结果交回模型，模型据此生成中文回答。

今天只做一个 Agent、一个只读工具、一个命令行演示。工具选择 list_expiring_contracts，复用已有 Service 和领域规则。同一 Python 进程内可以直接调用 Service，不要求 Agent 再绕 HTTP 请求自己的 FastAPI。

OpenAI 官方 Quickstart 展示了 Python 的 Agent、Runner 和 function_tool：函数工具加入 Agent 的 tools，Runner 执行并返回 final_output。参见[官方 Quickstart](https://developers.openai.com/api/docs/guides/agents/quickstart?lang=python)。本任务使用这条 SDK 路线，不另行搭建托管 Agents API 会话。

## 3. 准备 Issue、分支和依赖

已创建 [Issue #15：CRM Agent 合同到期查询工具与最小调用闭环](https://github.com/Tsaitan/agentprobe/issues/15)，负责人为 Tsaitan。中文标题：

`[v0.3] 实现 CRM Agent 合同到期查询工具与最小调用闭环`

创建前已查询相关任务，未发现重复；Issue 已包含工具契约、离线测试、真实模型验收和交付清单。

确认并保留当前改动后，准备新分支：

```bash
git status
git switch main
git pull --ff-only origin main
git switch -c codex/crm-agent-tool-calling
```

上述命令供流程参考，当前已经位于 codex/crm-agent-tool-calling，无需重复创建或切换。本次 git fetch 后确认 HEAD、main、origin/main 同为 3227d55，直接复用现有分支，保留 pyproject.toml、uv.lock 和本任务文档的改动。

添加 SDK 的命令如下，当前已经完成，无需重复安装：

```bash
uv add openai-agents
```

安装包名为 openai-agents，Python 导入名为 agents，参见[官方安装与导入示例](https://developers.openai.com/api/docs/guides/agents/quickstart?lang=python)。本次只读核对结果：pyproject.toml 声明 openai-agents>=0.24.0，uv.lock 锁定 0.24.0，本地安装元数据也为 0.24.0；SDK 声明支持 Python>=3.10，当前环境为 3.12.11。提交时保留实际更新的依赖文件。

依赖准备后，使用现有虚拟环境重新执行全量 Pytest，结果为 98 passed。准备阶段没有重复安装或重写用户已有依赖改动。第 4 节的本地上下文、第 5 节的普通工具适配及 SDK 包装已实现，下一步创建 Agent 工厂并注册工具。本阶段尚未发起模型调用。

真实模型运行从环境读取 OPENAI_API_KEY 和 OPENAI_MODEL。模型名称按当前账号可用且支持工具调用的型号配置，不在普通测试中依赖默认线上模型。密钥只在本地配置，不写入代码、日志、任务文档或 Git。

可以新增 .env.example，仅保留空值或说明；若选择 .env 文件，需要显式实现加载并确认其被 Git 忽略，不能假设 SDK 会自动读取任意 .env 文件。配置检查放在演示入口，普通模块导入和离线测试不应因缺少密钥而失败。

## 4. 文件与职责

建议结构如下，具体文件可随实现保持精简：

```text
agentprobe/agents/
├── __init__.py
├── context.py       # 保存本地 Service 依赖
├── tools.py         # 普通业务适配函数与 SDK 工具包装
├── crm_agent.py     # Agent 工厂与指令
└── demo.py          # 构造虚构数据，执行一次演示
tests/
├── test_agent_tools.py
└── test_crm_agent.py
```

本地上下文可以用 dataclass 保存 ContractService，通过 RunContextWrapper 在工具中取得。模型只提供业务参数，不提供 service、repository 或数据库对象。SDK 的本地上下文用于应用依赖，不会自动成为模型可见事实，参见[官方本地上下文说明](https://developers.openai.com/api/docs/guides/agents/define-agents#keep-local-context-separate-from-model-context)。

先保留可直接调用的普通适配函数，便于独立测试；SDK 包装层使用 function_tool，将本地上下文中的 Service 交给该函数。避免在工具模块导入时创建共享仓储、读取真实密钥或发起模型请求。

当前实现：已新增 agents/__init__.py 与 agents/context.py，使用 dataclass 定义 AgentContext，字段为 contract_service: ContractService。创建时显式传入已有 Service，例如 AgentContext(contract_service=service)，上下文保存该实例的引用，不自行创建 Service 或仓储。

临时本地检查已确认：模块可导入，传入的 Service 和仓储保持原实例；分别传入两个独立 Service 时，各上下文保留各自依赖。新增包的 Ruff 静态和格式检查通过。本步未新增正式测试、未重复运行此前 98 条测试，未导入 SDK、读取密钥或调用模型。

## 5. 定义合同到期查询工具

工具公开给模型的业务参数：

| 参数 | 工具接口约定 |
| --- | --- |
| customer_id | int，必须大于 0 |
| days | int，默认 30，必须大于等于 0 |
| on_date | ISO 日期字符串或 None；None 表示服务端当天 |

普通适配函数负责校验业务参数，将日期字符串解析为 date，确定本次实际判断日期，再调用现有 service.list_expiring_contracts()。返回结果中的判断日期应与传给 Service 的日期一致。SDK 工具包装负责接收模型参数、取得本地 Service、返回结构化结果，不复制合同筛选逻辑。

HTTP 的 Path、Query 校验不会作用于直接调用的 Python 工具，因此工具入口仍需要处理非法客户 ID、负数窗口和非法日期。Python 的 int 类型注解本身也不能替代这些业务校验。

建议的成功输出格式如下，内容仅为测试数据示例，不代表实际已经查询：

```json
{
  "ok": true,
  "customer_id": 101,
  "days": 30,
  "on_date": "2026-10-29",
  "count": 1,
  "contracts": [
    {
      "id": 1001,
      "name": "设备采购合同",
      "end_date": "2026-11-10",
      "amount": "50000.00"
    }
  ]
}
```

约定：

- count 来自实际结果长度；金额使用十进制字符串，日期使用 ISO 字符串。
- 无匹配结果为 ok=true、count=0、contracts=[]。
- 非法参数返回明确的工具错误，例如 ok=false、error.code=invalid_arguments；不能将执行失败伪装成“没有合同”。
- 普通适配函数的参数错误抛 InvalidToolArgumentsError（ValueError 子类），由工具包装识别并转换为参数错误；Service 执行异常应保留失败语义，不使用笼统的 except Exception 返回空列表。
- 工具说明写明用途、参数含义、判断日期和空结果语义，让模型知道何时及如何调用。

函数工具的作用是执行应用代码并把结果交回模型，参见[官方工具说明](https://developers.openai.com/api/docs/guides/tools#usage-in-the-agents-sdk)。工具的参数类型声明与领域规则分别验证，不假设装饰器会自动理解“必须为正数”等自然语言要求。

### 当前普通适配函数的实现与检查

已新增 agents/tools.py，提供 query_expiring_contracts(service, customer_id, days=30, on_date=None)。该函数保留为普通 Python 函数，SDK 包装另行定义；普通适配函数不读取模型配置或密钥。

- customer_id 和 days 校验运行时整数类型及取值范围，明确拒绝 bool；非法参数在 Service 调用前抛出 InvalidToolArgumentsError。
- on_date 必须是有效 ISO 日期字符串或 None。None 时确定当天，字符串时解析为 date，并将同一个有效日期用于查询和返回元数据。
- 调用现有 Service，输出 ok、客户、窗口、判断日期、实际 count 和合同列表；金额转字符串，结束日期转 ISO 字符串。
- 无匹配结果仍是成功空结果。Service 的 RuntimeError、ValueError 等执行异常不被捕获或改成成功响应；后续包装层只将 InvalidToolArgumentsError 映射为 invalid_arguments，避免把 Service 的 ValueError 误判成输入错误。

临时检查通过：实际仓储查询与完整结构化输出、JSON 序列化、空结果、参数透传、days=0、非法类型及日期不执行查询、受控当天日期、RuntimeError 和 ValueError 原异常传递。文件的 Ruff 静态与格式检查通过。

上述场景尚未保存为正式测试，本步未重复运行原有 98 条测试。SDK 包装已在同一模块添加，见下文。

### 当前 SDK 包装的实现与检查

已定义 list_expiring_contracts 函数工具，使用 function_tool 装饰器和 RunContextWrapper[AgentContext]。工具从 context.context.contract_service 取得本地 Service，调用普通适配函数，再将结果转换为 JSON 文本。普通函数返回字典，SDK 工具返回序列化后的文本，内容契约保持一致。

- 公开参数仅为 customer_id、days、on_date，本地上下文及 Service 不进入工具参数 Schema。
- customer_id 和 days 使用 Pydantic StrictInt，防止 SDK 参数解析将布尔值或数字字符串静默转换成整数后绕过普通函数的类型校验。
- 自定义 failure_error_function 处理 InvalidToolArgumentsError 和 SDK 的 ModelBehaviorError，返回 ok=false、error.code=invalid_arguments 的 JSON；意外执行异常继续抛出，不转换成成功空列表。
- 已核对安装版本的严格参数 Schema：三个业务字段均列为 required。Python 函数仍有 days=30、on_date=None 的默认值，但模型遵循严格 Schema 时应显式给出窗口和日期，使用当天时传 on_date=null。

临时验证直接调用 SDK FunctionTool 的 on_invoke_tool，使用 ToolContext 注入 AgentContext，并在验证进程中禁用 tracing，没有创建模型请求或启动 Runner。已验证成功与空结果、日期解析及参数透传、非法参数与无效 JSON、严格整数类型、默认值、上下文注入，以及 RuntimeError、普通 ValueError 原异常传递。生成的 Schema 只含三个业务字段，Ruff 静态与格式检查通过。

直接在 Runner 外测试错误路径时，SDK 出现 No active span 的日志提示，验证仍通过；这不是模型调用结果。上述调用检查尚未保存为正式测试，原有 98 条测试本步未重复运行。下一步创建 crm_agent.py 中的 Agent 工厂并注册此工具。

## 6. 创建 Agent 与演示入口

提供可测试的 Agent 工厂，接收明确的模型配置，注册上述工具。指令至少覆盖：

- 涉及具体合同事实时必须查询工具，回答以实际工具结果为依据。
- 缺少客户 ID 时先询问，不猜测公司名称与 ID 的映射。
- 空结果说明在本次判断日期和窗口下没有匹配合同。
- 参数错误或工具失败时说明问题，不声称查询成功，也不编造编号、金额或日期。

演示入口自行创建独立内存仓储，加入少量虚构合同，装配 Service 和本地上下文，再运行一次 Agent。不要为演示修改 FastAPI 默认应用的数据。

使用 async main()、await Runner.run(...) 和 asyncio.run(main()) 组织命令行入口；不要在已有异步事件循环中再次嵌套 asyncio.run。SDK 最小运行形式参见[官方运行示例](https://developers.openai.com/api/docs/guides/agents/quickstart?lang=python)。

演示应设置合理的请求等待与执行限制，限制配置按实际安装 SDK 的公开接口确认；不添加无限自动重试。输出或保存工具名、业务参数、工具返回以及最终回答，避免把认证信息输出到日志。

## 7. 离线测试清单

普通 Pytest 和 CI 不调用真实模型、不需要真实密钥。使用独立仓储测试业务适配函数，使用 Mock 检查 Service 交互，检查 Agent 的工具注册和配置；需要模拟 Runner 时替换项目自己的调用入口，不把 Mock 的回答当成模型效果证据。

| 场景 | 核心验证 |
| --- | --- |
| 工具查询成功 | 实际合同字段、数量、金额和日期格式正确 |
| 业务参数透传 | Service 收到正确客户、days 和解析后的 date |
| 无匹配客户或合同 | 成功空结果，count=0、contracts=[] |
| 非法客户 ID | 返回参数错误，不执行 Service 查询 |
| days=-1 | 参数错误，不执行 Service 查询 |
| days=0 | 合法，调用 Service 时窗口为 0 |
| on_date 非法 | 参数错误，不执行 Service 查询 |
| 省略 on_date | 使用受控当天，输出日期与查询日期一致 |
| 执行异常 | 保持错误语义，不转成成功空结果 |
| Agent 注册 | 包含约定工具，公开业务参数不混入本地依赖对象 |
| 缺少真实运行配置 | 演示给出明确提示，普通导入和离线测试仍可工作 |

固定日期测试使用 date(2026, 10, 29)。不要再穷举已有领域层全部日期组合，重点检查新工具的参数转换、输出契约和错误处理。保留原有 98 条测试，新增数量以实际收集结果为准。

## 8. 真实模型闭环验收

完成离线实现后，配置本地密钥和模型，执行命令行演示，例如：

```bash
uv run python -m agentprobe.agents.demo
```

这个命令是计划中的新增入口，文件实现并配置后才能运行。真实运行会使用所配置账号的 API，不加入默认 CI，也不因缺少配置而偷偷换用其他模型或供应商。

至少核对一次正常查询和一次无匹配查询：

- 用户问题明确指定客户、窗口和判断日期。
- 运行记录中有模型产生的正确工具名和业务参数。
- 应用实际执行工具，取得预置虚构数据的正确结果。
- 模型读取结果后给出中文回答，数量、编号、到期日期与工具一致。

只成功调用普通 Python 函数、或只拿到一段流畅回答，都不足以证明工具调用闭环已完成。若无法执行真实请求，如实保留这一项未完成，离线测试与真实模型验收分别记录。

## 9. 时间安排与提交

| 时间 | 任务 |
| --- | --- |
| 15 分钟 | 同步 main、准备新任务与分支、安装 SDK |
| 35 分钟 | 本地上下文、普通工具适配、SDK 包装 |
| 20 分钟 | Agent 工厂与命令行演示 |
| 30 分钟 | 离线测试与错误场景 |
| 10 分钟 | 真实模型演示并核对调用记录 |
| 10 分钟 | 质量检查、文档、PR |

开发后运行：

```bash
uv run python -m pytest -v
uv run ruff check .
uv run ruff format --check .
```

提交相关模块、测试、配置样例、依赖锁文件和本文。创建新的 PR，使用 Closes #15 关联本阶段任务，不复用已关闭的 #13；核对 PR 最新提交的 CI。

## 10. 验收清单

- [x] 核对 PR #14 已合并、Issue #13 已关闭及 main 新基线。
- [x] 依据可读取的路线和当前进度生成执行任务，注明原始正文限制。
- [x] 创建 Issue #15，复用已准备的功能分支，核对 SDK 声明、锁定和安装版本，安装依赖后原有 98 条测试通过。
- [x] 创建 AgentContext，显式保存 ContractService，临时检查依赖引用及 Ruff 通过。
- [x] 实现普通 query_expiring_contracts 参数适配与结构化输出，临时检查和 Ruff 通过。
- [x] 合同查询工具通过本地上下文取得 Service，参数与返回格式明确，SDK 离线调用检查通过。
- [x] 成功、空结果、参数错误、执行失败均有正确行为，临时检查通过，正式测试待补。
- [ ] Agent 注册工具，具备依据工具结果回答的指令。
- [ ] 命令行入口和本地配置提示可用。
- [ ] 新增离线测试和原有 98 条测试通过，记录实际数量。
- [ ] Ruff 静态与格式检查通过。
- [ ] 真实模型确实产生工具调用，执行结果回传后完成回答，保存验证记录。
- [ ] 创建新 PR，关联正确 Issue，最新 CI 通过。

若两小时不足，优先完成工具适配、Agent 注册和离线测试，真实闭环单独标记待验证，后续继续，不宣称已交付完整 Agent。

今天不增加多 Agent、RAG、向量库、前端、数据库或 Agent HTTP 接口。先把一个合同查询问题的完整过程跑通，再扩展工具数量和对话交互。
