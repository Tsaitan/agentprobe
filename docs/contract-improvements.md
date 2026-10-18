# AgentProbe v0.1 改进清单

整理日期：2026-10-18  
当前阶段：Contract 领域模型与单元测试  
来源：[AgentProbe 每日开发任务](chatgpt-conversation://6ad30ce1-7ba8-83ec-9777-b00b105890ce)，并结合本地代码复核。

本文件用于安排后续练习和记录验收，不表示下列改进已实施。业务代码和测试代码本次未修改。

## 1. 当前已完成的内容

- [x] 定义 Contract dataclass 与字段类型。
- [x] 创建时拒绝日期倒置、负金额、非法状态。
- [x] 允许零金额、起止日期相同、未来合同和历史合同。
- [x] 实现 `is_active()`，同时判断状态和日期闭区间。
- [x] 实现 `is_expiring_soon()`，复用有效性判断并检查剩余天数。
- [x] `days < 0` 抛出 `ValueError`。
- [x] 使用参数化测试和异常断言。
- [x] 为 `__post_init__()` 添加 `-> None`。这项已在本地完成，无需重复修改。

### 本地执行结果

| 检查 | 2026-10-18 复核结果 |
| --- | --- |
| Pytest | 23 passed |
| Ruff 静态检查 | All checks passed |
| Ruff 格式检查 | 未通过，2 个文件需要格式化 |
| 当前本地分支 | `feat/contract-domain` |

需要格式化的文件是 `agentprobe/domain/contract.py` 和 `tests/test_contract.py`。

以上结果通过本地 `.venv/bin/python -m pytest -q`、`.venv/bin/ruff check .` 和 `.venv/bin/ruff format --check .` 确认。修改代码后应重新检查。

原对话中的“测试通过情况尚未核实”和“Ruff 检查尚未核实”已由本次实际运行更新。远端 PR、合并和 Issue 状态本次未重新查询，不能按旧对话直接认定当前状态。

## 2. 本次提交前优先整理

### 2.1 清理注释并统一格式

涉及文件：`agentprobe/domain/contract.py`、`tests/test_contract.py`。

- [ ] 删除已实现功能上方的 `TODO`。
- [ ] 删除测试中的占位注释“这里放上面创建 contract 的代码”。
- [ ] 将逐行翻译代码的注释精简为业务说明；学习笔记可另存到文档。
- [ ] 为两个业务方法补充简短 Docstring，说明状态要求、日期边界和默认日期行为。
- [ ] 将 `zero-window-ends-tomorrow` 的中文注释改为“明天到期，超出零天窗口”。
- [ ] 执行格式化，并重新运行静态检查和测试。

示例：

```python
def is_active(self, on_date: date | None = None) -> bool:
    """判断合同在指定日期是否有效，包含开始日和结束日。"""
```

推荐命令：

```bash
uv run ruff format .
uv run ruff check .
uv run ruff format --check .
uv run python -m pytest -v
```

验收：三项检查通过，整理前后的业务行为保持一致。`ruff check` 通过不代表 `ruff format --check` 一定通过。

### 2.2 修改项目描述

涉及文件：`pyproject.toml`。

- [ ] 将默认描述 `Add your description here` 替换为实际项目描述，例如：

```toml
description = "Enterprise AI Agent and Automated Evaluation Platform"
```

## 3. 本阶段学习改进：Factory 与 Fixture

这部分解决测试数据重复问题，属于工程能力练习，不是当前业务逻辑缺陷，也不是原 Issue #1 的硬性验收条件。

### 3.1 抽取测试数据工厂

涉及文件：先放在 `tests/test_contract.py`，多个测试模块需要时再抽取公共模块。

- [ ] 实现 `make_contract(**overrides) -> Contract`。
- [ ] 在函数内部用字典准备默认合法数据。
- [ ] 用 `overrides` 覆盖本条用例需要改变的字段。
- [ ] 使用 `Contract(**data)` 创建并返回对象。
- [ ] 将重复的构造代码改为调用工厂，保留每条用例的关键输入。

目标调用方式：

```python
contract = make_contract(status="cancelled")
contract = make_contract(amount=Decimal("0"))

with pytest.raises(ValueError, match="amount"):
    make_contract(amount=Decimal("-0.01"))
```

学习重点：字典、`dict.update()`、`**kwargs` 收集关键字参数、`**data` 解包参数。

验收：每次调用返回新对象；非法字段在构造阶段触发校验；原有 23 条测试保持通过。不要先创建对象再修改字段来测试创建校验，因为属性赋值不会自动触发 `__post_init__()`。

### 3.2 使用 Fixture 管理默认合同

- [ ] 添加函数作用域的 `active_contract` Fixture，内部调用 `make_contract()`。
- [ ] 在适合使用同一组默认数据的测试中，通过函数参数获取 Fixture。
- [ ] 日期、金额或状态需要不同组合的测试继续使用工厂，不必强行改成 Fixture。

学习重点：工厂负责构造数据；Fixture 负责让 Pytest 管理和提供测试依赖。默认函数作用域可避免不同测试共享同一可变合同对象。

验收：能够解释 Pytest 如何按参数名注入 Fixture；测试可以单独执行，不依赖其他用例的运行顺序。

## 4. 可逐步补充的测试

主要业务场景已经覆盖，以下为加强项。

| 待补场景 | 预期与目的 |
| --- | --- |
| `days=1`，明天到期与后天到期 | 分别为 True、False，验证自定义窗口 |
| `pending`、`expired` 状态且日期满足到期范围 | 均为 False，补齐到期判断中的状态场景 |
| 不传 `days`，分别剩余 30 和 31 天 | 分别为 True、False，验证默认窗口确实为 30 |
| `is_active()` 不传 `on_date` 或显式传 None | 使用受控的当天日期判断 |
| `is_expiring_soon()` 不传 `on_date` 或显式传 None | 使用受控的当天日期判断 |

- [ ] 补充自定义窗口和默认窗口测试。
- [ ] 补充到期判断中的其他状态。
- [ ] 学习 `monkeypatch` 后补充默认日期分支。

默认日期测试应替换被测模块 `agentprobe.domain.contract` 中使用的 `date` 名称，让 `today()` 返回固定日期；不要直接修改内置 `date.today`，也不要让固定合同日期依赖真实当天时间。

可选探索：创建对象后把状态改为 `cancelled`，观察方法返回值变化，理解可变 dataclass。属性修改不会自动重新校验；是否限制属性修改属于后续设计选择，本阶段不要求改成不可变模型。

## 5. PR 收尾与验收

- [ ] 完成约定的代码整理后，重新运行 Pytest、Ruff 静态检查、格式检查。
- [ ] 查看 `git diff`，确认提交范围。
- [ ] 提交并推送本次修改。
- [ ] 检查是否已有对应 PR；没有则创建，已有则更新。
- [ ] 在 PR 中说明为什么金额使用 `Decimal`。
- [ ] 在 PR 中说明为什么日期判断支持 `on_date` 参数。
- [ ] 在 PR 中填写实际测试命令与执行结果。
- [ ] 完成代码审查后再按项目流程合并、核对 Issue #1 验收状态。

PR 说明要点：`Decimal` 适合表达十进制金额，避免二进制浮点表示带来的误差；`on_date` 允许指定业务基准日，使测试可重复，不随真实日期变化。

## 6. 后续工程化任务

本地未发现 GitHub Actions 工作流文件。以下内容安排在本地收尾后，不作为当前领域模型练习的阻塞条件。

- [ ] 增加 `.github/workflows/test.yml`，在提交和 PR 时执行测试与 Ruff 检查。
- [ ] CI 中同时运行格式检查，与本地检查保持一致。
- [ ] 后续接入 FastAPI 时，用 Pydantic 请求模型处理输入类型校验。

普通 dataclass 的类型注解不会自动完成运行时类型检查；当前不需要为所有字段增加手写类型校验。

## 7. 建议执行顺序

1. 清理注释、格式化、修改项目描述。
2. 学习字典解包和 `**kwargs`，抽取 `make_contract()`。
3. 学习 Fixture，将少量合适用例改为使用 `active_contract`。
4. 补自定义窗口、默认窗口与状态测试；默认日期测试可结合 Mock 练习继续推进。
5. 完成最终检查，整理 PR 说明并进入代码审查。

每完成一项再勾选清单。测试数量会随新增场景增长，验收重点是业务断言仍有效、原有场景不丢失和所有检查通过。
