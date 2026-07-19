---
name: zcode-review-deep
description: "多智能体深度代码审查技能。对单次 Commit/PR/模块执行 4+ 维度并行专项审查，合并去重后生成结构化修复任务与最终报告。"
argument-hint: "[--mode commit|pr|module|frz] [--ref REF] [--base BASE] [--head HEAD] [--path PATH] [--frz-ref FRZ_REF] [--output-dir .cr-deep]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Agent
  - AskUserQuestion
---

# zcode-review-deep

多智能体深度代码审查技能。对单次 Commit/PR/模块执行多维度并行专项审查，合并去重后生成结构化修复任务与最终报告。

## 1. 目标与非目标

### 1.1 目标

- 对单次 Commit/PR/模块执行 4+ 维度并行专项审查，捕获深层缺陷与架构风险
- 多 Agent 独立审查后合并去重，生成结构化问题清单与修复任务
- 提供带证据链的审查结论，支撑人工决策而非替代人工决策
- 产出可机器消费的 JSON 产物与可人工阅读的 Markdown 报告，支持 CI 集成

### 1.2 非目标

- 不替代 `bmad-code-review`（互补；bmad 用于快速扫描，deep 用于关键 PR）
- 不自动修改源代码（仅生成修复任务，人工决定是否执行）
- 不做合并/发布 Gate 决策（仅提供证据，决策权保留给人类）
- 不覆盖全量回归测试（聚焦变更范围，不保证无漏测）

## 2. 输入/输出

### 2.1 输入

| 参数 | 必填 | 说明 |
|------|------|------|
| `--mode` | 是 | 审查模式：`commit` / `pr` / `module` / `frz` |
| `--ref` | 条件 | 提交哈希或分支名（`commit` 模式必填） |
| `--base` | 条件 | PR 基分支（`pr` 模式必填） |
| `--head` | 条件 | PR 头分支（`pr` 模式必填） |
| `--path` | 条件 | 模块路径（`module` 模式必填） |
| `--frz-ref` | 条件 | 冻结版本引用（`frz` 模式必填） |
| `--output-dir` | 否 | 输出根目录，默认 `.cr-deep` |

### 2.2 输出

| 产物 | 路径 | 说明 |
|------|------|------|
| `role-panel.json` | `{output_dir}/{batch_id}/role-panel.json` | Agent 选择结果 |
| `batch-state.json` | `{output_dir}/{batch_id}/batch-state.json` | 批次运行状态 |
| `reviews/` | `{output_dir}/{batch_id}/reviews/{agent}-review.json` | 各 Agent 审查结果 |
| `consolidated-review.json` | `{output_dir}/{batch_id}/consolidated-review.json` | 合并后的问题清单 |
| `review-conflicts.json` | `{output_dir}/{batch_id}/review-conflicts.json` | 冲突记录 |
| `review-consensus.json` | `{output_dir}/{batch_id}/review-consensus.json` | 最终共识问题清单 |
| `fix-tasks.json` | `{output_dir}/{batch_id}/fix-tasks.json` | 修复任务清单 |
| `final-report.md` | `{output_dir}/{batch_id}/final-report.md` | 人工可读最终报告 |

### 2.3 退出码

| 退出码 | 含义 |
|--------|------|
| `0` | 审查完成，无 P0 问题 |
| `1` | 审查完成，发现 P0 问题 |
| `2` | 参数错误或环境不满足 |
| `3` | 执行过程中发生异常 |

## 3. 执行步骤

1. **Initialize** — 解析参数，生成 `batch_id`，创建输出目录，捕获输入快照
2. **Role Selection** — 根据变更内容选择 2-4 个专业 Agent + 1 个 Moderator，写入 `role-panel.json`
3. **Parallel Review** — 并行 Spawn 各 Agent 执行审查，每个 Agent 写入 `{agent_id}-review.json`
4. **Merge & Conflict Detection** — Moderator 合并去重，检测严重级别冲突，写入 `consolidated-review.json` + `review-conflicts.json`
5. **Consensus Build** — 相邻级别冲突自动取高级别，写入 `review-consensus.json`
6. **Fix Task Generation** — 为 P0/P1 问题生成修复任务，写入 `fix-tasks.json`
7. **Report Synthesis** — 生成 `final-report.md`

> 详细执行逻辑见下方 `## Execution Protocol` 章节。

## Execution Model

本技能采用**协作式执行架构**：

| 组件 | 职责 |
|------|------|
| **外层 AI Agent** | 完整流程编排：参数解析、角色选择、并行审查、合并、报告生成 |
| **validate.py** | 输出产物的 JSON Schema 契约验证（可选，用于确保输出质量） |

> **注意**：本技能是纯 SKILL.md 实现，所有流程逻辑由外层 AI Agent 执行。
> `validate.py` 仅用于验证输出产物是否符合 JSON Schema 契约。

## Output Schema

所有输出产物必须符合以下 JSON Schema：

| 产物 | Schema | 说明 |
|------|--------|------|
| `role-panel.json` | `role-panel.schema.json` | Agent 选择结果 |
| `batch-state.json` | `batch-state.schema.json` | 批次运行状态 |
| `reviews/{agent}-review.json` | `problem.schema.json` | 各 Agent 审查结果 |
| `consolidated-review.json` | `problem.schema.json`（数组） | 合并后的问题清单 |
| `review-conflicts.json` | `conflict.schema.json`（数组） | 冲突记录 |
| `review-consensus.json` | `problem.schema.json`（数组） | 最终共识问题清单 |
| `fix-tasks.json` | `fix-task.schema.json`（数组） | 修复任务清单 |

## Issue Schema（每条问题）

```json
{
  "issue_id": "{batch_id}-{agent_id}-{severity}-{seq:03d}",
  "severity": "P0 | P1 | P2 | P3",
  "dimension": "如 C01-Consistency, C03-Logic",
  "file": "相对文件路径",
  "line_range": [10] 或 [10, 20],
  "evidence": "精确代码片段（带行号）",
  "description": "问题描述",
  "found_by": ["agent_id1", "agent_id2"]
}
```

## Severity 级别

| 级别 | 含义 | 说明 |
|------|------|------|
| P0 | Blocker | 必须立即修复 |
| P1 | High | 应在合并前修复 |
| P2 | Medium | 建议修复 |
| P3 | Low | 可选修复 |

## Execution Protocol

1. **Initialize**
   - 解析参数，生成 `batch_id`
   - 创建输出目录结构
   - 捕获输入快照（git diff, PR description）

2. **Role Selection**
   - 根据变更内容选择 2-4 个专业 Agent + 1 个 Moderator
   - 写入 `role-panel.json`

3. **Parallel Review**
   - 并行 Spawn 各 Agent 执行审查
   - 每个 Agent 写入 `{agent_id}-review.json`

4. **Merge & Conflict Detection**
   - Moderator 合并去重
   - 检测严重级别冲突（≥2 级或 P0 vs "none"）
   - 写入 `consolidated-review.json` + `review-conflicts.json`

5. **Consensus Build**
   - 相邻级别冲突自动取高级别
   - 写入 `review-consensus.json`

6. **Fix Task Generation**
   - 为 P0/P1 问题生成修复任务
   - 写入 `fix-tasks.json`

7. **Report Synthesis**
   - 生成 `final-report.md`

## Artifact Directory Structure

```
{output_dir}/{batch_id}/
├── batch-state.json
├── role-panel.json
├── reviews/
│   ├── {agent1}-review.json
│   └── {agent2}-review.json
├── consolidated-review.json
├── review-conflicts.json
├── review-consensus.json
├── fix-tasks.json
└── final-report.md
```

## Validation

使用 `validate.py` 验证输出产物是否符合 Schema 契约：

```bash
# 验证整个批次
python validate.py .cr-deep/CR-20260527-001

# 安装依赖
pip install jsonschema
```

## Non-Negotiable Rules

- 审查阶段不修改源文件
- 不捏造问题 — 每个发现必须有精确代码证据
- 纯风格问题不得标记为 P0/P1
- 所有产物立即写入磁盘，不保留内存状态

## Pitfalls / 常见坑与规避

| 坑点 | 影响 | 规避措施 |
|------|------|----------|
| **Agent 选择过少（<2）** | 审查维度不足，深层缺陷漏检 | 变更 >100 行或涉及跨模块时至少启用 3 个 Agent |
| **Moderator 合并时过度去重** | 不同位置相似问题被误判为同一问题，导致遗漏 | 合并规则要求 `file` + `line_range` 同时匹配才去重；保留 `found_by` 多 Agent 标记 |
| **P0 问题缺乏代码证据** | 误报导致开发者信任下降，或漏报导致生产故障 | 强制 `evidence` 字段包含精确代码片段与行号；Moderator 二次校验 P0 证据链 |
| **输出产物未写入磁盘即中断** | 审查结果丢失，需重新运行，浪费 Token 与时间 | 每步完成后立即 `Write` 产物；`batch-state.json` 记录阶段状态，支持断点续跑 |
| **纯风格问题标记为 P0/P1** | 阻塞合并流程，降低团队效率 | 规则明确：P0/P1 仅限功能缺陷、安全漏洞、性能陷阱；风格问题最高 P2 |

## Usage

在 Claude Code 中调用：

```
/zcode-review-deep --mode commit --ref HEAD~1
/zcode-review-deep --mode pr --base main --head feature/x
/zcode-review-deep --mode module --path src/services/order/
```

预期输出路径：

| 命令 | 预期输出目录 |
|------|-------------|
| `--mode commit --ref HEAD~1` | `.cr-deep/CR-{YYYYMMDD}-{NNN}/` |
| `--mode pr --base main --head feature/x` | `.cr-deep/CR-{YYYYMMDD}-{NNN}/` |
| `--mode module --path src/services/order/` | `.cr-deep/CR-{YYYYMMDD}-{NNN}/` |
