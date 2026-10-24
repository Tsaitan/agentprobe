# AgentProbe 每日开发任务｜2026-10-24

今日主题：继续完成 Repository Protocol 与 MagicMock 隔离测试。

当前阶段：v0.1，Python 工程基础。预计投入：120 分钟。

来源：[AgentProbe 每日开发任务](chatgpt-conversation://6ad30ce1-7ba8-83ec-9777-b00b105890ce)。本文根据 10 月 24 日的完整任务整理，延续 10 月 23 日的学习目标。Protocol 与 Service 依赖类型调整已完成，下一步建立 Mock 测试 Fixture 和首条隔离测试。

## 1. 当前进度与起点

本次本地检查确认：

| 检查项 | 当前本地情况 |
| --- | --- |
| 当前分支 | `refactor/contract-repository-protocol` |
| 开发基线 | `218f982`，已同步 origin/main |
| 当前改动 | Service 类型调整及任务文档更新 |
| ContractService | 构造函数已依赖 ContractRepository Protocol |
| ContractRepository Protocol | 已声明两个读取方法 |
| Service Mock 测试 | 未发现对应文件 |
| 当前测试结果 | 64 passed，其中真实仓储的 Service 测试为 14 个实例 |

已通过 git fetch 更新远端分支信息，将本地 main 快进到 `218f982`，并从该基线创建开发分支。引用对话记录的 PR #8、Issue #7 及 main CI 状态本次未逐项查询。

Service 类型调整后，全量测试 64 passed；Ruff 静态和格式检查通过。mypy 验证 `repository: ContractRepository = InMemoryContractRepository()` 以及将其传给 ContractService 均无类型错误，确认内存仓储结构符合协议要求。

今天延续尚未实现的 Protocol 和 Mock 任务，不推进 FastAPI。

## 2. 今天要解决的问题

改造前 Service 虽然接收外部传入的 Repository，但类型注解写为 `InMemoryContractRepository`；目前已改为 `ContractRepository`。

目标是让它依赖仓储具备的能力，而不是某一种存储实现：

| 概念 | 解决的问题 |
| --- | --- |
| 依赖注入 | 仓储对象由谁创建、从哪里传入 |
| Protocol | Service 对仓储有哪些方法和签名要求 |
| MagicMock | 如何在没有真实仓储时，控制返回值并验证依赖调用 |

原有真实仓储测试继续保留，用来验证真实对象协作；新增 Mock 测试验证 Service 的返回结果与调用行为。两者互相补充。

## 3. 文件与修改范围

新增：

```text
agentprobe/repositories/protocol.py
tests/test_contract_service_mock.py
```

修改：

```text
agentprobe/services/contract_service.py
```

保留：

- `InMemoryContractRepository` 的现有实现和继承关系。
- 原有 64 条测试，包括 `tests/test_contract_service.py` 的真实仓储测试。
- Contract 的状态、日期和到期业务规则。

`Protocol` 来自 `typing`，`MagicMock` 来自 `unittest.mock`，本次不需要新增第三方依赖。

## 4. 实现 ContractRepository Protocol

在 `agentprobe/repositories/protocol.py` 中定义 `ContractRepository(Protocol)`，只声明当前 Service 使用的两个读取方法：

| 方法 | 返回与约定 |
| --- | --- |
| `get_by_id(self, contract_id: int) -> Contract \| None` | 返回指定合同，不存在时返回 None |
| `list_by_customer(self, customer_id: int) -> list[Contract]` | 返回指定客户的全部合同，无匹配时返回空列表 |

要求：

- [x] 使用 `from typing import Protocol`。
- [x] 导入 Contract，并保持方法参数名、类型与现有仓储一致。
- [x] 协议方法只声明接口，不实现存储或查询逻辑。
- [x] 本阶段不加入 `add()`，因为 Service 当前不使用写入能力。
- [x] 内存仓储保持原继承关系，无须显式继承该 Protocol。

结构化类型的含义：某个对象只要具有符合协议要求的方法签名，就可以满足该类型约束，不要求显式继承。

Protocol 主要表达静态类型约束，不会因为写了类型注解就在运行时自动检查传入对象。今天无需为了 `isinstance()` 添加 `runtime_checkable`。

## 5. 修改 Service 的依赖类型

将构造函数改为：

```python
def __init__(self, repository: ContractRepository) -> None:
    self.repository = repository
```

- [x] 将 Service 中具体仓储的 import 替换为 Protocol 的 import。
- [x] 不再用具体内存仓储作为构造参数类型。
- [x] 保持三个业务方法及其行为不变。
- [x] 现有真实仓储仍可传入 Service，原有 14 个 Service 测试保持通过。

这一步改变的是依赖声明。现有内存仓储已经有两个符合要求的方法，不需要为了满足协议新增业务代码。

## 6. MagicMock 的使用与测试组织

在新测试文件中准备函数作用域 Fixture：

- `mock_repository`：返回 `MagicMock(spec=ContractRepository)`。
- `service`：接收该 Mock 并传给 ContractService。
- 合同数据：继续使用真实 Contract，可用 Fixture 或 `replace()` 构造不同场景。

核心用法示例：

```python
mock_repository = MagicMock(spec=ContractRepository)
mock_repository.get_by_id.return_value = contract

service = ContractService(mock_repository)
result = service.get_contract(1001)

assert result == contract
mock_repository.get_by_id.assert_called_once_with(1001)
```

理解两种断言：

- 返回结果断言：Service 是否返回预期对象或列表。
- 交互断言：是否调用了正确仓储方法、调用次数和参数是否正确。

`spec` 限制 Mock 可访问的属性名称，但不自动校验每个调用参数的 Python 类型，也不等于完整的函数签名约束。今天先理解 `spec`；`autospec` 可留作后续加强项。

每条测试显式设置仓储方法的 `return_value`。列表查询应设置真实的合同列表或 `[]`，不要依赖 MagicMock 默认返回的另一个 Mock。

## 7. 至少六个 Mock 测试场景

统一使用固定基准日 `date(2026, 10, 24)`。30 天后为 2026-11-23，31 天后为 2026-11-24。

| 编号 | 场景与准备 | 返回结果断言 | 交互断言 |
| --- | --- | --- | --- |
| TC01 | get_by_id 返回指定 Contract，调用 get_contract(1001) | 返回该合同 | get_by_id 恰好调用一次，参数为 1001 |
| TC02 | get_by_id 返回 None，查询不存在的 ID | 返回 None | get_by_id 恰好调用一次，参数为查询 ID |
| TC03 | list_by_customer 返回客户 101 的全部合同 | Service 原样返回该客户的合同列表，不过滤状态 | list_by_customer 恰好调用一次，参数为 101 |
| TC04 | 返回同客户、不同日期和状态的真实合同，执行到期查询 | 仅包含窗口内有效合同 | list_by_customer 恰好调用一次，参数为 101 |
| TC05 | list_by_customer 返回空列表，执行到期查询 | 返回 [] | list_by_customer 恰好调用一次，参数为 101 |
| TC06 | days=-1，调用到期查询 | 抛出 ValueError，消息包含 days | list_by_customer 没有被调用 |

TC04 可以包含当天到期、窗口内、30 天边界、31 天、已取消等数据。Mock 的列表模拟仓储已按客户筛选的返回结果，Service 负责复用 Domain 的有效性和到期规则。

### 重点：校验非法参数时不能访问仓储

```python
with pytest.raises(ValueError, match="days"):
    service.list_expiring_contracts(
        customer_id=101,
        days=-1,
        on_date=date(2026, 10, 24),
    )

mock_repository.list_by_customer.assert_not_called()
```

异常断言和“不调用”断言都必须保留。不要只检查 Mock 对象本身是否被调用，应检查具体的数据访问方法。

每个用例添加简短中文 Docstring。原有 Fixture 以真实仓储为依赖，新的 Fixture 以 Mock 为依赖，分文件组织即可，不必强行合并。

## 8. 可选增强与学习问题

优先完成六个核心场景，再考虑：

- [ ] `days=0`：一份合同当天到期，一份次日到期，结果只包含当天到期合同。
- [ ] 了解 `side_effect` 如何让 Mock 抛出异常；如新增异常传播测试，应先明确期望行为，不擅自改变 Service 的异常语义。
- [ ] 理解使用真实仓储的测试和隔离 Mock 测试各自能发现哪些问题。

完成后应能回答：

1. 已经使用依赖注入，为什么还要引入 Protocol？
2. 没有显式继承 Protocol，内存仓储为什么仍满足约束？
3. `return_value` 和普通方法返回值有什么关系？
4. 为什么结果正确，还要断言调用次数和参数？
5. 为什么 Mock 测试不能替代真实仓储测试？

## 9. 开发流程与检查

先检查本地是否已有对应分支或未提交实现；已有则继续使用，避免重复创建。

已创建 [Issue #9：使用 Protocol 解耦合同仓储并补充 Mock 单元测试](https://github.com/Tsaitan/agentprobe/issues/9)，状态为 open，负责人为 `Tsaitan`，无需重复创建。

Issue 标题：

`[v0.1] 使用 Protocol 解耦合同仓储并补充 Mock 单元测试`

Issue 已包含两个协议方法、Service 类型调整、六个 Mock 测试及验收要求。

工作区干净时同步 main，再创建引用对话指定的分支：

```bash
git switch main
git pull origin main
git switch -c refactor/contract-repository-protocol
```

若分支已存在，则直接切换继续。新任务文档尚未提交时，应先安排保留或提交，不为切换分支丢弃改动。

检查命令：

```bash
uv run python -m pytest tests/test_contract_service_mock.py -v
uv run python -m pytest -v
uv run ruff check .
uv run ruff format --check .
```

确认通过后，提交相关实现、测试及任务文档，推送分支并创建 PR。PR 使用 `Closes #9` 关联 Issue，记录实际验证结果，确认最新 GitHub CI 通过后进入代码审查。

64 条原有测试加至少 6 个新测试实例，目标是至少 70 条通过；这是计划数量，不是当前执行结果。可选增强完成后数量可以增加。

## 10. 时间安排与验收清单

| 时间 | 开发任务 | 学习重点 |
| --- | --- | --- |
| 15 分钟 | 检查已有本地进度和分支 | Git 状态、避免重复开发 |
| 25 分钟 | 定义 ContractRepository Protocol | 结构化类型、接口约定 |
| 20 分钟 | 修改 Service 依赖类型 | 依赖倒置、行为兼容 |
| 40 分钟 | 编写六个 Mock 测试 | return_value、结果和交互断言 |
| 20 分钟 | 检查、提交、创建 PR | 本地验证与 GitHub CI |

- [x] 定义仅含两个读取方法的 ContractRepository Protocol。
- [x] ContractService 改为依赖 Protocol，移除具体仓储类型依赖。
- [x] 内存仓储无须显式继承 Protocol，原有真实仓储测试继续有效。
- [ ] 至少六个 Mock 测试实例通过。
- [ ] 结果、调用次数和参数均有断言。
- [ ] 负数 days 抛出异常，且不触发仓储查询。
- [x] 原有 64 条测试保持通过，当前全量 64 passed；新增 Mock 测试后需重跑。
- [x] 当前 Ruff 静态与格式检查通过；后续修改后需重跑。
- [ ] 创建 PR 并确认最新 GitHub Actions 结果。
- [ ] 完成 Code Review 后，再按项目流程合并和核对 Issue。

今天不开发 FastAPI、不连接数据库、不接入 AI Agent。完成本次任务后，再学习路由、Pydantic 数据模型和 HTTP 接口测试。
