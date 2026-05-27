---
name: zeng-code-review-deep
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

# zeng-code-review-deep

多智能体深度代码审查技能。对单次 Commit/PR/模块执行多维度并行专项审查，合并去重后生成结构化修复任务与最终报告。

## Not Equal To

- Not a replacement for `bmad-code-review`（互补；bmad 用于快速扫描，deep 用于关键 PR）
- Not a source code auto-fixer（生成修复任务，人工决定是否执行）
- Not a gate decision maker（仅提供证据）

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

## Usage

在 Claude Code 中调用：

```
/zeng-code-review-deep --mode commit --ref HEAD~1
/zeng-code-review-deep --mode pr --base main --head feature/x
/zeng-code-review-deep --mode module --path src/services/order/
```
