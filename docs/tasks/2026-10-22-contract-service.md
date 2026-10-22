# AgentProbe 每日开发任务｜2026-10-22

今日主题：实现 `ContractService` 合同业务服务层。

当前阶段：v0.1，Python 工程基础。预计投入：120 分钟。

来源：[AgentProbe 每日开发任务](chatgpt-conversation://6ad30ce1-7ba8-83ec-9777-b00b105890ce)。本文按引用对话中的完整要求整理。三个业务方法、Service 测试 Fixture 和十四个测试实例已完成，计划中的十二类测试场景均已覆盖，待代码审查和 PR 验证。

## 1. 前置进度

当前已有：

- Contract 领域模型，包含创建校验、有效性判断和到期判断。
- InMemoryContractRepository，包含添加、按合同 ID 查询、按客户 ID 查询。
- GitHub Actions CI，运行 Pytest、Ruff 静态检查和格式检查。
- 2026-10-22 实现三个 Service 方法后，原有 50 条测试保持通过。
- 新增十四个 Service 测试实例后，全量测试为 64 passed，Ruff 静态和全项目格式检查通过。
- 到期边界、客户和有效性筛选、负数窗口及查询不修改数据等计划场景，现已保存为正式 Service 测试。

引用对话记录 PR #6 已合并、Issue #5 已关闭，main 的 CI 成功。以上远端状态本次未重新查询，不能把引用记录当作本次实时验证结果。开始开发前应同步最新 main。

当前使用独立分支 `feat/contract-service`。2026-10-22 拉取远端分支信息后，确认其开发基线与 `origin/main` 一致，均为 `6d33494`。

## 2. 今天要解决的业务问题

用户希望查询：

> 客户 101 有哪些合同将在未来 30 天内到期？

完成这个需求需要协调两个已有能力：

1. Repository 获取客户的全部合同。
2. 对每份 Contract 调用 `is_expiring_soon()`。

Service 负责组织上述流程，为后续 FastAPI 路由和 Agent 工具提供可复用的业务入口。

| 层次 | 职责 | 今日安排 |
| --- | --- | --- |
| Domain：Contract | 判断合同是否合法、有效、即将到期 | 复用 |
| Repository | 保存和检索合同数据 | 复用 |
| Service：ContractService | 协调仓储查询与合同业务判断 | 新增 |
| FastAPI / Agent | 接收外部请求，调用 Service | 后续实现 |

Service 不自行访问仓储的 `_contracts`，也不重新计算合同的剩余天数。

## 3. 文件安排

新增以下文件：

```text
agentprobe/
└── services/
    ├── __init__.py
    └── contract_service.py
tests/
└── test_contract_service.py
```

已有 Domain、Repository 和相关测试保持可用，不需要为本次任务引入新框架。

当前进度：构造函数和三个业务方法已实现。Service 测试合计十四个实例，计划场景已覆盖。最后新增的测试通过 asdict() 保存独立字段快照，查询后检查原对象、按 ID 查询结果及两个客户的合同集合，确认未被修改。下一步代码审查、同步 Issue 进度，并提交 PR 验证 CI。

## 4. 构造函数与依赖注入

定义 `ContractService`，通过构造函数接收 `InMemoryContractRepository`：

```python
def __init__(self, repository: InMemoryContractRepository) -> None:
    self.repository = repository
```

使用方式：

```python
repository = InMemoryContractRepository()
service = ContractService(repository)
```

这是依赖注入：调用者决定把哪个仓储交给 Service。Service 使用传入的对象，不在内部重新创建仓储，也不要求继承 Repository。

学习问题：如果先向外部仓储添加数据，Service 却在内部创建另一个仓储，会查到什么？

本阶段先使用具体仓储类型，不要求新增 `Protocol` 或抽象基类。

## 5. 三个接口与业务规则

### 5.1 查询单份合同

```python
def get_contract(self, contract_id: int) -> Contract | None: ...
```

- 调用注入仓储的 `get_by_id()`。
- 找到时返回对应 Contract。
- 找不到时返回 `None`，不新增异常语义。

### 5.2 查询客户全部合同

```python
def list_customer_contracts(self, customer_id: int) -> list[Contract]: ...
```

- 调用仓储的 `list_by_customer()`。
- 返回该客户的全部合同，不过滤状态和日期。
- 客户无合同时返回 `[]`。

### 5.3 查询客户即将到期的有效合同

```python
def list_expiring_contracts(
    self,
    customer_id: int,
    days: int = 30,
    on_date: date | None = None,
) -> list[Contract]: ...
```

必须满足：

1. `days < 0` 时抛出 `ValueError`，即使客户没有合同也一样。
2. 从仓储获取指定客户的全部合同。
3. 使用 `Contract.is_expiring_soon(days=days, on_date=on_date)` 筛选。
4. 返回符合条件的合同列表，无匹配时返回 `[]`。
5. 不修改原合同的字段，也不修改仓储数据。

实现顺序提示：先校验窗口参数，再查询和筛选。仅依靠循环中 Contract 方法的校验，会在列表为空时漏掉负数 `days`。

`days` 是查询窗口，不是某份合同的实际剩余天数。默认窗口为 30 天，省略 `on_date` 或传入 None 表示以当天为基准。建议一次查询只确定一次基准日期，然后把同一天传给每份合同，避免跨午夜时不同合同使用不同日期。

到期规则已在 Domain 中实现，不在 Service 内重复编写状态检查或日期差计算。

## 6. Pytest 测试设计

测试统一使用固定基准日 `date(2026, 10, 22)`。对应边界是：当天为 10-22，30 天后为 11-21，31 天后为 11-22。

至少完成引用任务中的 8 个核心场景，并优先补充空列表和参数校验的关键边界：

| 编号 | 测试场景 | 关键断言 |
| --- | --- | --- |
| TC01 | 查询已添加的合同 | 返回正确 Contract |
| TC02 | 查询没有添加过的合同 ID | 返回 None |
| TC03 | 客户 101 有两份不同状态的合同，客户 102 有一份 | 客户全部合同查询只返回 101 的两份，不过滤状态 |
| TC04 | 多客户、多状态、多到期日期的混合数据 | 到期查询仅返回目标客户在窗口内的有效合同 |
| TC05 | active 合同恰好 30 天后到期 | 结果包含该合同 |
| TC06 | active 合同 31 天后到期 | 结果不包含该合同 |
| TC07 | cancelled 合同的日期满足到期窗口 | 结果不包含该合同 |
| TC08 | 客户有合同时传 days=-1 | 抛出 ValueError |
| TC09 | 客户没有合同，执行全部合同和到期查询 | 两种查询均返回 [] |
| TC10 | active 合同在基准日当天到期 | 到期结果包含该合同 |
| TC11 | 客户没有合同时传 days=-1 | 仍抛出 ValueError，防止遗漏入口校验 |
| TC12 | 调用到期查询前后比较合同字段及仓储内容 | 原合同和仓储数据不变 |

执行进度：TC01 至 TC06 已有独立测试通过；TC07 的 cancelled 合同排除行为由混合数据用例覆盖；TC08 和 TC11 由负数窗口参数化测试覆盖；TC09 由两种列表查询各两个实例覆盖；TC10 已验证当天到期的有效合同被包含；TC12 已通过字段快照和仓储公共查询验证数据不变。十二类计划场景全部覆盖，共十四个测试实例。Service Fixture 与测试数据准备使用同一个仓储实例。

可选增强：覆盖 `days=0`、自定义窗口、已过期、未开始、pending/expired 状态，以及默认日期分支。默认日期测试可复用已经学习的 `monkeypatch` 思路，替换实际读取当天日期的模块名称。

### 测试组织建议

- 使用真实 `InMemoryContractRepository`，今天不要求 MagicMock。
- 用函数作用域 Fixture 分别提供仓储和依赖该仓储的 Service，保证各场景数据隔离。
- 向注入 Service 的同一个仓储添加数据，避免准备与查询用了不同实例。
- 使用 Factory 或 `dataclasses.replace()` 构造多份合法合同，不为测试准备非法日期组合。
- 多份合同使用不同 ID，避免重复 ID 错误干扰 Service 测试。
- 多结果查询可以比较 ID 集合，并同时检查数量，不依赖顺序。
- 验证不修改数据时保存字段快照；只比较指向同一个可变对象的两个引用，不能发现字段被修改。
- 每个测试添加简短中文 Docstring，说明场景和预期。

## 7. 学习重点与时间安排

| 时间 | 开发任务 | 学习重点 |
| --- | --- | --- |
| 20 分钟 | 理解 Domain、Repository、Service 职责 | 分层与业务规则归属 |
| 25 分钟 | 构造函数和两个基本查询方法 | 类、对象组合、依赖注入 |
| 25 分钟 | 实现到期合同查询 | 参数校验、列表推导式、复用模型方法 |
| 35 分钟 | 编写 Fixture、核心和边界用例 | 数据准备与流程断言 |
| 15 分钟 | 运行检查、提交并查看 CI | Git 和工程质量 |

完成后应能解释：

- [ ] 为什么 Service 接收外部仓储，而不是自己创建？
- [ ] 为什么 Service 与 Repository 是组合关系？
- [ ] 为什么不能只依赖 Contract 来校验负数窗口？
- [ ] 为什么到期判断继续放在 Domain？
- [ ] 如何验证 Service 没有修改原合同？

## 8. Issue、分支与 PR

已创建 [Issue #7：实现 ContractService 合同业务服务层及单元测试](https://github.com/Tsaitan/agentprobe/issues/7)，状态为 open，负责人为 `Tsaitan`。无需重复创建。

中文标题：

`[v0.1] 实现 ContractService 合同业务服务层及单元测试`

Issue 描述已包含本文第 4、5、6 节的接口、规则与测试要求，以及第 9 节验收标准。

工作区干净时同步 main，再创建引用任务指定的功能分支：

```bash
git switch main
git pull origin main
git switch -c feat/contract-service
```

若分支已存在，切换到该分支继续开发。完成检查后按需提交相关文件：

```bash
git add agentprobe/services tests/test_contract_service.py
git commit -m "feat: 实现 ContractService 及单元测试"
git push -u origin feat/contract-service
```

任务文档有更新时，将对应文档一并提交。PR 描述记录实现行为、测试结果，并使用 `Closes #7` 关联 Issue。创建 PR 后确认最新提交的 GitHub Checks，不只看本地结果。

## 9. 验收标准

- [x] 新增约定的 services 包、实现文件和测试文件。
- [x] 通过构造函数注入仓储实例。
- [x] 实现 get_contract()。
- [x] 实现 list_customer_contracts()。
- [x] 实现 list_expiring_contracts()，复用 Domain 的到期判断。
- [x] 负数 days 在有数据和无数据时均抛出 ValueError，两个正式参数化测试实例通过。
- [x] 查询不修改原合同或仓储数据，字段快照与客户合同集合对比的正式回归测试通过。
- [x] 至少 8 个 Service 测试实例通过，目前共 14 个。
- [x] 补齐空客户的两种列表查询测试，覆盖空仓储和仅有其他客户数据。
- [x] 补齐当天到期的正式测试。
- [x] 补齐不修改数据的正式测试。
- [x] 原有 50 条测试与新增 14 个 Service 测试实例全部通过，当前全量 64 passed；后续修改后需重跑。
- [x] 当前 Ruff 静态和全项目格式检查通过；后续修改后需重跑。
- [ ] PR 对应的最新 GitHub Actions 检查通过。
- [ ] 完成 Code Review 后，再按项目流程合并和核对 Issue。

检查命令：

```bash
uv run python -m pytest tests/test_contract_service.py -v
uv run python -m pytest -v
uv run ruff check .
uv run ruff format --check .
```

50 条原有测试加上 14 个新增 Service 测试实例，当前实际全量结果为 64 passed。计划场景与本地检查均已完成；远端 Issue 勾选、PR 的实际 CI 和代码审查仍需另行核对，不能据此直接判定整个 Issue 已验收。

## 10. 今日范围与下一阶段

今天只实现 ContractService、相关测试和验证记录。不开发 FastAPI、不接入 AI Agent、不连接数据库，不要求 Protocol 或 MagicMock。

优先保证到期查询与边界测试正确，未完成部分如实记录。下一阶段再学习 Protocol、MagicMock 和替换 Service 依赖，随后逐步接入 FastAPI。
