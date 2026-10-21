# AgentProbe 每日开发任务｜2026-10-21

今日主题：添加 GitHub Actions 自动化测试工作流。

当前阶段：v0.1，Python 工程化基础。预计投入：120 分钟。

来源：[AgentProbe 每日开发任务](chatgpt-conversation://6ad30ce1-7ba8-83ec-9777-b00b105890ce)。本文根据引用对话的完整任务整理，执行进度见第 6 节。

## 1. 当前进度与验证基线

Contract 领域模型、内存合同仓储及其单元测试已实现。今天先让现有检查在 GitHub 上自动运行，再继续 ContractService。

2026-10-21 本地实际复核结果：

| 检查项 | 结果 |
| --- | --- |
| Pytest | 50 passed |
| Ruff 静态检查 | All checks passed |
| Ruff 格式检查 | 11 files already formatted |
| `.python-version` | 3.12 |
| `pyproject.toml` | Python >=3.12，已配置 Pytest、Ruff 等开发依赖 |
| `uv.lock` | 已纳入 Git 跟踪 |
| GitHub Actions YAML | 本地未发现 |
| 当前本地分支 | `feat/contract-repository` |

上述检查使用本地 `.venv/bin/python -m pytest -q`、`.venv/bin/ruff check .`、`.venv/bin/ruff format --check .` 执行。

引用对话记录 PR #4 已合并、Issue #3 已关闭；本次未重新核实远端状态。本地测试通过也不代表 GitHub CI 已通过，远端结果需要在创建 PR 后实际确认。

## 2. 今日目标与交付文件

新增一个工作流文件：

```text
.github/
└── workflows/
    └── ci.yml
```

工作流自动完成以下步骤：

1. 检出仓库代码。
2. 安装 uv 并准备 Python 3.12。
3. 使用已有锁文件安装项目和开发依赖。
4. 执行全部 Pytest 测试。
5. 执行 Ruff 静态检查。
6. 执行 Ruff 格式检查。

第一版使用一个 Job、`ubuntu-latest` 运行环境。将依赖安装、测试、静态检查和格式检查分别命名为独立 Step，方便在日志中定位失败。

## 3. 触发条件

需要明确区分两种事件：

| 事件 | 触发范围 | 用途 |
| --- | --- | --- |
| `push` | 提交推送到 `main` | 检查主分支最新代码，包括 PR 合并后的结果 |
| `pull_request` | 创建或更新以 `main` 为目标的 PR | 合并前验证变更 |

触发器提示：

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

这里 `pull_request.branches` 指目标分支。只向功能分支 Push、尚未创建 PR 时，不满足上述触发条件；创建 PR 后，继续向其来源分支 Push 会触发 PR 更新检查。

## 4. 环境与依赖要求

- [x] 已配置 `actions/checkout` 检出仓库。
- [x] 已配置 `astral-sh/setup-uv` 安装 uv。
- [x] 已配置 `uv python install 3.12` 显式准备 Python。
- [x] 已配置并在本地通过 `uv sync --locked --dev`。
- [x] 本地 uv 环境可运行 Pytest 和 Ruff；远端 Job 的实际执行待 PR 验证。

当前工作流固定 uv 为 `0.7.19`，与本地实际验证使用的版本一致；Action 按官方资料固定到提交 SHA，并在注释中注明版本。工作流只请求 `contents: read` 权限。

实现时查阅 [uv 官方 GitHub Actions 指南](https://docs.astral.sh/uv/guides/integration/github/)，确认所用 Action 的版本和参数，本文不预设具体版本号。

`--locked` 要求锁文件与项目声明一致：不一致时应失败，便于发现遗漏提交的依赖变更。`--dev` 明确安装测试和检查所需的开发依赖。

若依赖同步失败，检查 `pyproject.toml`、`uv.lock` 和日志。需要更新锁文件时在本地完成并提交，不要在 CI 中取消锁定来掩盖问题。

## 5. 自动化检查命令

工作流必须包含以下三个检查：

```bash
uv run python -m pytest -v
uv run ruff check .
uv run ruff format --check .
```

| 检查 | 验证内容 |
| --- | --- |
| Pytest | 业务逻辑和测试断言 |
| Ruff check | 静态代码问题和已启用的规范规则 |
| Ruff format --check | 文件格式是否符合要求 |

CI 中使用格式检查命令，不使用会修改文件的 `ruff format .`。发现格式问题后，在本地格式化并提交。

保留命令的失败状态，不设置 `continue-on-error: true` 或追加 `|| true`。前一步失败时，后续步骤默认可能跳过，应先定位最早失败的步骤。

## 6. GitHub 实际验证流程

### 当前执行记录（2026-10-21）

- [x] 已确认复用 [Issue #5：为 AgentProbe 添加 GitHub Actions 自动化测试工作流](https://github.com/Tsaitan/agentprobe/issues/5)，状态为 open，负责人为 `Tsaitan`。
- [x] 已拉取远端分支信息，并将本地 `main` 快进到 `7d070f4`。
- [x] 已从最新 `main` 创建并切换到 `chore/add-github-actions-ci`。
- [x] 新增 `.github/workflows/ci.yml`，配置触发器、运行环境、锁定依赖安装及三项检查。
- [x] YAML 解析及本地配置检查通过，依赖同步与三项检查全部通过。
- [x] 工作流和任务文档已在本地提交，提交为 `3acca29`。
- [x] 更新令牌权限后，CI 分支推送成功。
- [x] 创建 [PR #6：添加 Pytest 和 Ruff 的 GitHub Actions 自动检查](https://github.com/Tsaitan/agentprobe/pull/6)，通过 `Closes #5` 关联 Issue。
- [x] GitHub Actions 首次 PR 检查通过：[CI #1](https://github.com/Tsaitan/agentprobe/actions/runs/39628775386)，对应工作流提交 `3acca29`。

本地验证记录：`uv sync --locked --dev` 成功；`uv run python -m pytest -v` 为 50 passed；`uv run ruff check .` 通过；`uv run ruff format --check .` 为 12 files already formatted。

已完成工作流配置、本地验证、分支推送和 PR 创建。GitHub 托管 Ubuntu runner 上的依赖安装、Pytest、Ruff 静态检查及格式检查均成功。PR 保持打开，合并和合并后的 Push 工作流验证尚未进行。

权限问题已解决：首次推送曾因认证令牌缺少 `workflow` 权限而被 GitHub 拒绝，更新令牌后重试成功。此权限属于 Git 认证令牌，与 `ci.yml` 中控制运行时令牌的 `permissions` 配置不同，无需修改工作流来解决。

### 操作步骤

1. 检查是否已有 CI Issue，没有则使用第 9 节草稿创建，分配给自己。
2. 确认工作区干净，切回 `main` 并同步代码。
3. 创建功能分支；引用对话建议的名称如下：

```bash
git switch main
git pull origin main
git switch -c chore/add-github-actions-ci
```

若分支已存在，切换到该分支继续，不重复创建。

4. 编写工作流，在本地执行依赖同步与三项检查，查看差异。
5. 提交并推送相关文件，创建以 `main` 为目标的 PR。
6. 在 PR 的 Checks 或仓库 Actions 页面查看实际运行。
7. 失败时查看对应 Step 日志，修复后再次推送，确认新提交的结果通过。
8. PR 合并后，确认 `main` 的 Push 事件也触发了工作流。

本地验证建议：

```bash
uv sync --locked --dev
uv run python -m pytest -v
uv run ruff check .
uv run ruff format --check .
git diff --check
```

不要只根据本地命令成功、YAML 文件存在或工作流配置截图判断完成。需要记录一次 PR 对应的实际 Actions 运行结果；条件允许时，把运行链接写入 PR 描述。

## 7. 学习重点与排障

| 概念 | 需要理解的问题 |
| --- | --- |
| CI | 为什么每次变更都需要自动验证？ |
| Workflow | 一个 YAML 文件如何描述自动化流程？ |
| Job | 运行环境是什么，各个 Job 是否共享环境？ |
| Step | 同一个 Job 内的步骤如何依次执行？ |
| YAML | 缩进、键值、列表和 `run` 命令如何表达？ |
| Event | Push 与 PR 事件有什么区别？ |
| Exit code | 为什么非零退出码会让检查失败？ |
| 锁文件 | 为什么依赖版本一致有助于重现测试结果？ |

失败时按日志分类：

- 工作流没有出现：检查文件路径、YAML 语法、事件与目标分支。
- 依赖安装失败：检查 Python 版本、Action 参数、锁文件和依赖安装日志。
- Pytest 失败：检查断言、导入路径、日期依赖，以及 Linux 与本地 macOS 的文件名大小写差异。
- Ruff 失败：先在本地运行相同命令修正，再提交。

遇到失败应修复原因，不通过删除测试或忽略退出码来获得绿色结果。

## 8. 时间安排与验收

| 时间 | 任务 |
| --- | --- |
| 15 分钟 | 理解 CI、Workflow、Job、Step |
| 35 分钟 | 编写触发器与 Job 结构 |
| 20 分钟 | 配置 Python、uv 与锁定依赖安装 |
| 20 分钟 | 添加三项检查，完成本地验证 |
| 20 分钟 | 创建 PR，查看并修复 GitHub Checks |
| 10 分钟 | 补充文档、验证记录和 PR 说明 |

验收清单：

- [x] 已有对应 Issue #5 和 CI 功能分支 `chore/add-github-actions-ci`。
- [x] 新增 `.github/workflows/ci.yml`。
- [x] 已配置 Push 到 `main` 和以 `main` 为目标的 PR 触发器，PR 触发已验证，main Push 待合并后验证。
- [x] 已配置 `ubuntu-latest` 和 Python 3.12。
- [x] 已配置 uv 及锁文件安装项目和开发依赖。
- [x] 已配置运行全部 Pytest 测试的步骤。
- [x] 已配置 Ruff 静态检查和格式检查步骤。
- [x] 本地依赖同步、50 条测试和 Ruff 检查通过。
- [x] PR 对应的 GitHub Checks 实际通过，运行结果见 PR 描述和上述 Actions 链接。
- [ ] 合并后确认 `main` 的 Push 工作流运行情况。

新增工作流本身不要求新增业务测试；现有 50 条测试作为本次验证基线。

## 9. 中文 Issue 草稿

标题：`[v0.1] 为 Pytest 和 Ruff 添加 GitHub Actions 自动检查`

描述：

> 当前项目依赖手动执行测试与代码检查，需要在 GitHub 上自动验证每次主分支更新和 PR。
>
> 新增 `.github/workflows/ci.yml`，在 Push 到 main、创建或更新以 main 为目标的 PR 时触发；使用 Ubuntu、Python 3.12 和 uv，通过 `uv sync --locked --dev` 安装依赖，依次执行 Pytest、Ruff 静态检查和格式检查。
>
> 验收以 PR 中实际通过的 GitHub Checks 为准，记录对应运行结果，并在合并后确认 main 的 Push 工作流。
>
> 本次范围为持续集成，不包括服务器部署、Docker 镜像发布或 CD；不修改 Contract 和 Repository 的业务逻辑。

已确认本任务对应 Issue #5，后续 PR 描述中使用 `Closes #5` 关联，无需重复创建 Issue。

## 10. 后续任务

CI 验收完成后继续 ContractService：学习依赖注入、Repository 与 Service 职责划分、`Protocol` 和 `MagicMock`。今天先完成可实际运行的自动化检查流程。
