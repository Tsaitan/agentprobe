# AgentProbe 每日开发任务｜2026-10-19

今日主题：实现 `InMemoryContractRepository`，学习 Python 数据访问层设计。  
当前阶段：v0.1，从 Contract 领域模型过渡到业务服务层。  
预计投入：120 分钟。  
来源：[AgentProbe 每日开发任务](chatgpt-conversation://6ad30ce1-7ba8-83ec-9777-b00b105890ce)。

本文件整理引用对话中的今日任务，作为独立实现和代码审查的依据。本次仅生成任务文档，不实现 Repository，也不创建 Issue 或 PR。

## 1. 前置进度

此前已实现 Contract 模型、创建校验、有效性判断和到期判断，已学习 Factory、Fixture、参数化测试及 `monkeypatch`。最近一次本地验证记录为 43 条测试通过。

引用对话记录 PR #2 已合并、Issue #1 已关闭；这些远端状态本次未重新核实。生成本文档时，本地分支为 `main`，工作区干净。

今天继续复用已有 Contract 模型，重点练习数据存取职责，不重复开发合同业务规则。

## 2. 开发目标与职责

实现一个内存版合同仓储，负责保存合同、根据合同 ID 查询，以及按客户 ID 查询合同列表。

| 层次 | 职责 | 本次范围 |
| --- | --- | --- |
| Contract 领域模型 | 描述合同，校验字段业务规则，判断有效性和到期情况 | 复用已有代码 |
| Repository 数据访问层 | 保存与检索合同 | 今天实现 |
| ContractService 服务层 | 组织合同查询和业务操作 | 后续任务 |
| FastAPI / Agent 工具 | 接收外部请求并调用业务能力 | 后续任务 |

先用字典保存对象，为后续学习数据库访问层建立基础。本次不要求增加抽象基类、Protocol 或数据库适配器。

## 3. 文件安排

新增以下文件：

```text
agentprobe/
└── repositories/
    ├── __init__.py
    └── memory_contract_repository.py
tests/
└── test_contract_repository.py
```

仓储类名称：`InMemoryContractRepository`。

在 `__init__()` 中为每个实例初始化独立字典：

```python
self._contracts: dict[int, Contract] = {}
```

思考：为什么应该在实例初始化时创建字典，而不是把它放成所有实例共享的类属性？

## 4. 接口与业务约定

| 方法签名 | 行为 | 边界处理 |
| --- | --- | --- |
| `add(contract: Contract) -> None` | 保存合同，以合同 ID 作为字典键 | ID 已存在时抛出 `ValueError`，保留原合同 |
| `get_by_id(contract_id: int) -> Contract \| None` | 查询指定 ID 的合同 | 不存在时返回 `None` |
| `list_by_customer(customer_id: int) -> list[Contract]` | 返回该客户的所有合同 | 无匹配结果时返回空列表 |

实现提示：

- `add()` 先判断键是否已存在，再写入字典，避免静默覆盖。
- 重复以 ID 判断，即使是两个不同的 Contract 对象，只要 ID 相同也属于重复。
- `get_by_id()` 可以思考字典的 `get()` 与方括号取值在缺失键时有什么区别。
- `list_by_customer()` 可以遍历字典的值，使用列表推导式筛选。
- 客户查询只按 `customer_id` 过滤，不额外过滤状态、日期或金额。
- 查询结果顺序本次不作要求，测试不要把排序作为隐含约束。

本阶段不提供更新或删除功能，不引入并发控制、分页、持久化或深拷贝策略。添加时对象的字段合法性由现有 Contract 构造校验负责。

## 5. 测试设计

在 `tests/test_contract_repository.py` 中至少覆盖以下 7 个场景：

| 场景 | 准备与操作 | 关键断言 |
| --- | --- | --- |
| 成功添加合同 | 新仓储添加一份合法合同 | `add()` 返回 `None`，随后能够查到该合同 |
| 按 ID 查询已存在合同 | 添加 ID 为 1001 的合同，再查询 1001 | 返回正确合同 |
| 查询不存在的合同 | 查询没有添加过的 ID | 返回 `None` |
| 重复合同 ID | 添加一份合同，再添加同 ID、其他字段不同的合同 | 抛出 `ValueError`，原数据未被覆盖 |
| 查询指定客户 | 客户 101 添加两份合同，客户 102 添加一份 | 查询 101 只返回该客户的两份合同 |
| 查询不存在的客户 | 仓储已有其他客户的数据，查询一个无匹配客户 | 返回 `[]` |
| 添加多个不同 ID | 添加多份不同 ID 的合同 | 每份均可独立按 ID 查询，互不覆盖 |

测试组织建议：

- 使用函数作用域的 `repository` Fixture，每条测试创建新的仓储实例。
- 沿用 Factory 思路构造合法合同，每个场景只覆盖关注的字段。
- 多份合同应使用不同 ID，除非该用例专门验证重复 ID。
- 列表查询可比较 ID 集合并同时断言结果数量，避免依赖顺序或漏掉重复项。
- 异常断言使用 `pytest.raises(ValueError)`；如检查消息，选择稳定的字段或关键词。
- 不依赖测试执行顺序，也不让用例共享全局仓储实例。

可选增强：再写一条测试，创建两个仓储实例，只向其中一个添加合同，确认另一个仍为空。这能直接验证字典是否正确隔离在各个实例中。

若两个测试模块都需要同一个合同工厂，可后续整理到公共测试工具或通过 `conftest.py` 提供工厂 Fixture；本次不要为复用而大幅重构已有测试。

## 6. Python 学习重点

- [ ] 理解 `__init__()` 与实例属性。
- [ ] 掌握字典按键添加、检查和查询，以及 `.values()` 遍历。
- [ ] 理解 `Contract | None` 表示查询结果可能不存在。
- [ ] 理解 `list[Contract]` 和列表推导式。
- [ ] 区分模型中的业务规则与仓储的数据访问职责。
- [ ] 用 Fixture 保证测试数据隔离。

动手前先回答：

1. ID 不存在返回 `None`，为什么不直接使用字典的方括号取值？
2. 为什么重复 ID 应抛异常，而不是覆盖之前的数据？
3. 没有匹配客户时，为什么返回空列表而不是 `None`？

## 7. 建议时间安排

| 时间 | 任务 | 产出 |
| --- | --- | --- |
| 15 分钟 | 理解 Repository 职责和接口约定 | 能解释三个方法的输入、输出和边界 |
| 35 分钟 | 实现初始化与三个方法 | 可独立使用的内存仓储 |
| 40 分钟 | 编写 Fixture 和测试 | 至少 7 个可独立运行的测试场景 |
| 20 分钟 | 跑测试、Ruff，修复问题 | 检查通过 |
| 10 分钟 | 查看差异，提交并整理 PR | 说明实现和验证结果 |

## 8. 验收清单

- [x] 新增约定的包和文件（已创建，仓储实现及测试用例待编写）。
- [ ] 三个 Repository 方法完成，签名与边界符合本任务约定。
- [ ] 重复 ID 不会覆盖原数据。
- [ ] 至少 7 个测试场景通过。
- [ ] 原有 Contract 测试继续通过。
- [ ] 完整 Pytest 测试通过。
- [ ] Ruff 静态检查通过。
- [ ] Ruff 格式检查通过。
- [ ] 创建对应 PR 并完成 Code Review。

检查命令：

```bash
uv run python -m pytest tests/test_contract_repository.py -v
uv run python -m pytest -v
uv run ruff check .
uv run ruff format --check .
```

需要整理格式时执行 `uv run ruff format .`，然后复跑检查。43 是此前的测试数量，不是今天的目标上限；新增仓储测试后总数应相应增加。

## 9. GitHub 开发流程

1. 检查是否已有本任务 Issue，避免重复创建；没有则新建并分配给自己。
2. Issue 标题建议为 `[v0.1] Implement InMemoryContractRepository`，记录实际分配的编号。
3. 在工作区干净时同步 `main` 并创建功能分支：

```bash
git switch main
git pull origin main
git switch -c feat/contract-repository
```

若该功能分支已存在，使用 `git switch feat/contract-repository` 继续开发，不重复创建。分支名称沿用引用对话给出的名称。

4. 实现后检查差异，只提交本任务相关文件，推送功能分支并创建 PR。
5. PR 描述填写功能行为、检查结果，并使用 `Closes #实际编号` 关联 Issue；将“实际编号”替换为真正的数字，不能假定一定是 #3。
6. Code Review 通过后，再按项目流程合并并核对 Issue 状态。

## 10. 开发范围

今天优先独立实现，遇到问题时结合具体代码进行讲解和审查。暂不接入真实数据库、不引入 SQLAlchemy、不实现 ContractService、不开发 FastAPI 接口或 Agent 调用。
