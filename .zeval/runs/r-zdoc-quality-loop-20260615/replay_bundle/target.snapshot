---
name: zdoc-quality-loop
description: "多文档质量收敛流水线。Review 阶段采用 BMAD 多角色评审团（选角→并行评审→合并→讨论→共识/升级人类）。Fix/Verify 阶段不变。过程审计和结果报告由独立 Agent 从磁盘重建，无共享上下文。"
argument-hint: "<doc1> [doc2 doc3 ...] [--ssot <path>] [--rubric <path>] [--max-rounds 5] [--p1-threshold 3] [--parallel] [--p2 always|never|low-risk] [--no-verify] [--output-dir .quality-loop]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Agent
  - AskUserQuestion
---

<Purpose>
zdoc-quality-loop 是一条有界、可追溯的文档质量收敛流水线，包含三个核心设计：

1. **BMAD 多角色评审团**：每份文档开始前分析内容并邀请 2-4 个专业角色并行评审，各角色输出独立意见，由主持人（Moderator）合并、检测冲突，冲突通过结构化讨论（最多 2 轮）解决，无法解决则暂停升级为人类决策，最终输出共识问题清单。

2. **全程落盘**：每个 Agent 动作（选角 / 各角色评审 / 合并 / 讨论 / 共识 / 修复 / 验证）的原始输出立即写文件，支持中断恢复。

3. **独立 Agent 审计和报告**：过程审计和结果报告由单独 spawn 的 Agent 完成，该 Agent 无任何共享上下文，仅通过磁盘文件了解全过程，确保客观性。
</Purpose>

<Use_When>
- 用户说"review and fix"、"质量循环"、"zdoc-quality-loop"、"多角色审核"
- 需要多视角评审确保文档质量，且要求可事后审计
- 一份或多份文档需要系统性修复并输出正式质量报告
</Use_When>

<Do_Not_Use_When>
- 目标是代码文件 → 用 `gsd-code-review` + `gsd-code-fixer`
- 只需要单轮评审无需修复 → 用 `code-reviewer`
- 文档尚未写好 → 先写文档再运行
</Do_Not_Use_When>

---

## 输出目录结构

所有产物写入 `{output_dir}/{batch_id}/`，默认 `.quality-loop`。

```
.quality-loop/
└── {batch_id}/
    ├── rubric-locked.md               ← Rubric 锁定版（全程不变）
    ├── batch-state.json               ← 实时状态（每阶段后更新）
    ├── batch-summary.md               ← 最终批次汇总（独立 Agent 生成）
    └── {alias}/                       ← 每份文档独立目录
        ├── role-panel.json            ← 选角结果（文档开始前生成，全轮复用）
        ├── r{n}/
        │   ├── reviews/
        │   │   ├── {role1}-review.json    ← 各角色原始输出
        │   │   ├── {role2}-review.json
        │   │   └── {role3}-review.json
        │   ├── consolidated-review.json   ← Moderator 合并去重后
        │   ├── review-conflicts.json      ← 检测到的冲突（可为空数组）
        │   ├── discussion/
        │   │   ├── conflict-{id}-r1.json  ← 讨论第 1 轮
        │   │   └── conflict-{id}-r2.json  ← 讨论第 2 轮（如需要）
        │   ├── review-human-decisions.json ← 升级人类决策的记录（如有）
        │   ├── review-consensus.json      ← 最终共识问题清单（权威来源）
        │   ├── fix-log.json
        │   ├── draft.md
        │   ├── verdicts.json
        │   ├── escalation.json            ← 修复引入新 P0 时（如有）
        │   └── round-audit.json
        ├── final.md                   ← Verifier 确认后的正式文档（或 --no-verify 时 P0=0）
        ├── audit-manifest.json        ← 过程审计 Agent 的输入清单
        ├── audit-report.json          ← 独立审计 Agent 输出（含所有 check）
        ├── audit-findings.json        ← 审计发现的异常（仅有问题时存在）
        ├── report-manifest.json       ← 报告 Agent 的输入清单
        └── quality-report.md          ← 独立报告 Agent 输出
```

**写入时机总览**：

| 文件 | 何时写入 | 写入方 |
|------|---------|-------|
| `role-panel.json` | 文档第一轮开始前 | 选角 Agent |
| `r{n}/reviews/{role}.json` | 各角色 Agent 返回后立即 | 主流程 |
| `r{n}/consolidated-review.json` | Moderator 返回后立即 | 主流程 |
| `r{n}/review-conflicts.json` | Moderator 返回后立即 | 主流程 |
| `r{n}/discussion/conflict-{id}-r{k}.json` | 每轮讨论返回后立即 | 主流程 |
| `r{n}/review-human-decisions.json` | 用户回答 AskUserQuestion 后 | 主流程 |
| `r{n}/review-consensus.json` | 所有冲突解决后 | 主流程 |
| `r{n}/fix-log.json` + `r{n}/draft.md` | Fixer 返回后立即 | 主流程 |
| `r{n}/verdicts.json` | Verifier 返回后立即 | 主流程 |
| `r{n}/round-audit.json` | 本轮结束前 | 主流程 |
| `final.md` | --no-verify 时 P0=0，或 Verifier 确认 P0 全清后 | 主流程 |
| `r{n}/escalation.json` | Fix Pass 检测到 introduced_risk.severity=P0 时 | 主流程 |
| `audit-manifest.json` | 进入审计阶段前 | 主流程 |
| `audit-report.json` + `audit-findings.json` | 审计 Agent 返回后 | 审计 Agent |
| `report-manifest.json` | 进入报告阶段前 | 主流程 |
| `quality-report.md` | 报告 Agent 返回后 | 报告 Agent |
| `batch-summary.md` | 所有文档报告完成后 | 主流程 |

---

## 标准 Rubric（每轮固定，初始化时锁定）

| # | 维度 | 检查内容 |
|---|------|---------|
| R01 | 需求完整性 | 所有用户故事/功能点是否都已陈述？有无遗漏场景？ |
| R02 | 主流程可执行性 | 开发人员能否仅凭此文档实现 Happy Path？步骤是否完整？ |
| R03 | 数据模型一致性 | 实体名称、字段、关系在文档内部是否前后一致？ |
| R04 | 边界与异常情况 | 空值、零值、超限、并发冲突等边界是否定义？ |
| R05 | 异常处理路径 | 失败模式和恢复路径是否明确？错误码/消息是否指定？ |
| R06 | UI/API/状态流一致性 | UI 状态 ↔ API 响应 ↔ 状态机转换是否三者对齐？ |
| R07 | 测试可验证性 | 验收标准是否可直接转换为自动化测试用例？ |
| R08 | SSOT 对齐 | 此文档是否与项目 SSOT / 宪法冲突？ |
| R09 | Mock/伪闭环风险 | 是否有标注 TBD、存根实现、"后续补充"等未完成内容？ |
| R10 | 范围漂移 | 文档内容是否超出了声明的目标范围？ |

---

## 角色池（Role Pool）

选角 Agent 从以下角色中选 2-4 个组成评审团，并指定 1 个 Moderator：

| 角色 ID | subagent_type | 主要负责 Rubric | 视角专长 |
|---------|--------------|--------------|---------|
| `product-manager` | `product-manager` | R01, R07, R10 | 需求完整性、用户价值、范围边界 |
| `architect` | `architect` | R02, R03, R06 | 技术可行性、数据模型、系统设计 |
| `developer` | `code-reviewer` | R02, R04, R05, R09 | 实现细节、边界、异常、伪闭环 |
| `ux-designer` | `ux-designer` | R06, R04 | UI 状态流、交互一致性 |
| `analyst` | `analyst` | R01, R08, R10 | 需求歧义、SSOT 对齐、逻辑一致性 |
| `security` | `security-reviewer` | R05, R04, R09 | 安全边界、失败路径、伪实现 |

> **注意**：`product-manager` 和 `ux-designer` 的 subagent_type 对应 Claude Code 内置 agent 类型（`product-manager`、`ux-designer`）。`documentation-analyst-writer`（阶段 3 报告 Agent）使用的是 `documentation-analyst-writer` 类型。审计 Agent（`verifier`）与报告 Agent（`documentation-analyst-writer`）是流水线级独立 Agent，与评审角色池无关，不参与选角。若目标系统不支持这些 subagent_type，可映射为：`product-manager`→`analyst`，`ux-designer`→`analyst`，`documentation-analyst-writer`→`writer`。

**Moderator**（固定用 `analyst` subagent，model=opus）：负责合并、去重、检测冲突、主持讨论。

> **analyst 双重身份说明**：当 `analyst` 同时被选为评审角色和 Moderator 时，Step A 中的评审 Agent 与 Step B 中的 Moderator Agent 是两个独立 spawn 的实例（不共享上下文），以保证角色独立性。

**冲突触发条件**：
- 严重级别分歧 ≥ 2 级（如 P0 vs P2，P1 vs P3）→ 必须讨论
- 同一问题，某角色给 P0/P1，另一角色明确标注"非问题" → 必须讨论
- 相邻级别分歧（P0 vs P1，P1 vs P2）→ Moderator 直接取高级别，无需讨论

---

## 数据结构

### Role Panel Schema（`role-panel.json`）
```json
{
  "alias": "spec",
  "document_type": "<Moderator 判断的文档类型，如 API Spec | PRD | 技术设计文档>",
  "selected_roles": [
    {
      "role_id": "product-manager",
      "subagent_type": "product-manager",
      "justification": "<选择理由>",
      "primary_dimensions": ["R01", "R07", "R10"]
    }
  ],
  "moderator_subagent": "analyst",
  "selected_at": "<ISO>"
}
```

### Problem Schema（`{role}-review.json` 中每条问题）
```json
{
  "id": "{alias}-{role_id}-R{round}-{severity}-{seq:03d}",
  "file": "<文档路径>",
  "severity": "P0 | P1 | P2 | P3",
  "dimension": "<如 R02-主流程可执行性>",
  "module": "<章节或模块名>",
  "problem": "<问题描述>",
  "evidence": "<文档精确原文，不允许改写>",
  "impact": "<不修复会导致的具体失败>",
  "fix_suggestion": "<具体修复建议>",
  "verification": "<修复后如何验证>",
  "found_by": ["<role_id>"],
  "merged_from_ids": []
}
```

### Problem Schema（`review-consensus.json` 中每条合并后问题）
```json
{
  "id": "{alias}-R{round}-{severity}-{seq:03d}",
  "file": "<文档路径>",
  "severity": "P0 | P1 | P2 | P3",
  "dimension": "<如 R02-主流程可执行性>",
  "module": "<章节或模块名>",
  "problem": "<问题描述>",
  "evidence": "<文档精确原文，不允许改写>",
  "impact": "<不修复会导致的具体失败>",
  "fix_suggestion": "<具体修复建议>",
  "verification": "<修复后如何验证>",
  "found_by": ["<role_id1>", "<role_id2>"],
  "merged_from_ids": ["<原始角色 issue id>"]
}
```

### Fix Schema（`r{n}/fix-log.json` 中每条修复记录）
```json
{
  "issue_id": "<被修复的问题 ID>",
  "action": "FIXED | SKIPPED | PARTIAL",
  "change_summary": "<描述做了什么修改>",
  "changed_sections": ["<章节名或行号范围>"],
  "introduced_risk": {
    "severity": "P0 | P1 | P2 | P3 | null",
    "description": "<若引入新风险，描述具体内容；无则 null>"
  }
}
```

### Verify Schema（`r{n}/verdicts.json` 中每条验证结果）
```json
{
  "issue_id": "<被验证的问题 ID>",
  "verdict": "RESOLVED | PARTIAL | NOT_RESOLVED",
  "evidence": "<从更新后文档精确引用，证明修复是否有效>",
  "verifier": "independent-verifier | skipped",
  "notes": "<可选备注>"
}
```

### Batch State Schema（`batch-state.json`）
```json
{
  "batch_id": "<batch_id>",
  "started_at": "<ISO>",
  "config": {
    "max_rounds": 5,
    "p1_threshold": 3,
    "p2_policy": "low-risk",
    "parallel": false,
    "no_verify": false,
    "ssot_paths": [],
    "rubric": "standard"
  },
  "files": [
    {
      "path": "<原始文档路径>",
      "alias": "<alias>",
      "output_dir": "<输出目录>",
      "status": "pending | running | fixing | verifying | auditing | reporting | APPROVED | PARTIAL_CONVERGENCE | NOT_CONVERGED | ESCALATED | HUMAN_BLOCKED",
      "current_round": 1,
      "open_issue_ids": ["<issue_id>"],
      "closed_issue_ids": ["<issue_id>"],
      "stop_reason": null,
      "last_updated": "<ISO>"
    }
  ],
  "batch_status": "running | completed | failed"
}
```

### Round Audit Schema（`r{n}/round-audit.json`）
```json
{
  "alias": "<alias>",
  "round": 1,
  "started_at": "<ISO>",
  "completed_at": "<ISO>",
  "review": {
    "role_panel": ["<role_id1>", "<role_id2>"],
    "per_role_files": {
      "<role_id1>": "r1/reviews/<role_id1>-review.json",
      "<role_id2>": "r1/reviews/<role_id2>-review.json"
    },
    "consolidated_file": "r1/consolidated-review.json",
    "conflicts_file": "r1/review-conflicts.json",
    "discussion_files": ["r1/discussion/conflict-<id>-r1.json"],
    "human_decisions_file": "r1/review-human-decisions.json",
    "consensus_file": "r1/review-consensus.json",
    "conflict_count": 0,
    "human_escalations": 0,
    "issue_count": { "P0": 0, "P1": 0, "P2": 0, "P3": 0 },
    "new_count": 0,
    "persistent_count": 0,
    "candidate_closed_count": 0
  },
  "fix": {
    "fix_log_file": "r1/fix-log.json",
    "draft_file": "r1/draft.md",
    "issues_fixed": 0,
    "issues_skipped": 0,
    "introduced_risks": []
  },
  "verify": {
    "verdicts_file": "r1/verdicts.json",
    "resolved_count": 0,
    "partial_count": 0,
    "not_resolved_count": 0,
    "verifier": "skipped"
  },
  "stop_condition_met": false,
  "stop_reason": null
}
```

### Conflict Schema（`review-conflicts.json` 中每条冲突）
```json
{
  "conflict_id": "{alias}-R{round}-conflict-{seq:03d}",
  "description": "<冲突描述：谁和谁在哪个问题上有分歧>",
  "section": "<涉及的文档章节>",
  "positions": [
    {
      "role_id": "product-manager",
      "proposed_severity": "P0",
      "evidence": "<该角色引用的原文>",
      "rationale": "<该角色的判断理由>"
    },
    {
      "role_id": "architect",
      "proposed_severity": "P2",
      "evidence": "<该角色引用的原文>",
      "rationale": "<该角色的判断理由>"
    }
  ],
  "status": "OPEN | RESOLVED_BY_DISCUSSION | RESOLVED_BY_HUMAN",
  "final_severity": null,
  "resolution_round": null,
  "human_decision": null
}
```

### Discussion Round Schema（`discussion/conflict-{id}-r{k}.json`）
```json
{
  "conflict_id": "...",
  "discussion_round": 1,
  "responses": [
    {
      "role_id": "product-manager",
      "response": "<对其他角色观点的回应>",
      "maintains_position": true,
      "willing_to_accept": "P1",
      "new_evidence": "<null 或补充引用>"
    },
    {
      "role_id": "architect",
      "response": "<回应>",
      "maintains_position": false,
      "willing_to_accept": "P0",
      "new_evidence": null
    }
  ],
  "moderator_synthesis": "<主持人综合意见>",
  "resolved": true,
  "agreed_severity": "P0",
  "next_action": "RESOLVED | NEXT_ROUND | ESCALATE_TO_HUMAN"
}
```

> **说明**：`responses` 为 N 长度数组，包含所有参与冲突的角色回应（不仅两方）。每个冲突的 `conflict-{id}-r{k}.json` 单文件包含整个 Discussion Round Schema（responses 数组 + moderator_synthesis），由主流程在所有角色 + Moderator 全部返回后一次性写入。

---

## 停止条件（任一满足即停止，按表格自上而下短路求值，先匹配先赢）

| 优先级 | 条件 | 触发行为 | batch-state status |
|--------|------|---------|-------------------|
| 最高 | 某轮修复引入新 P0（introduced_risk.severity=P0） | 立即停止 | ESCALATED |
| 最高 | 共识达不成，人类选择"阻塞" | 停止当前文档 | HUMAN_BLOCKED |
| 高 | P0=0 且 P1 ≤ 阈值 | 正常收敛 | APPROVED |
| 高 | P0=0 且 P1 > 阈值 | 部分收敛 | PARTIAL_CONVERGENCE |
| 中 | 已达最大轮次 | 强制停止 | NOT_CONVERGED |
| 中 | 连续 2 轮无新增 P0 且 P0 > 0 | 无法自动收敛 | NOT_CONVERGED |
| 低 | 最近 2 轮问题总数下降 < 20% | 收益递减 | NOT_CONVERGED |

> **检查时机**：停止条件在每轮 Review Pass 的 Step D（生成共识清单后）和 Verify Pass 结束后各检查一次。P0/P1 计数来自当轮 review-consensus.json（Review 阶段检查）或 verdicts.json 中 NOT_RESOLVED/PARTIAL 的统计（Verify 阶段检查）。

---

<Steps>

## 阶段 0：初始化

### 0.1 参数解析

```
位置参数（可多个）：<doc1> [doc2 ...]
  支持直接路径、glob、混合

命名参数：
  --ssot <path>           SSOT 文件（可多个，重复使用 --ssot）
  --rubric <path>         自定义 Rubric（必须含 R01-R10）
  --max-rounds N          默认 5
  --p1-threshold N        默认 3
  --parallel              并行处理所有文档
  --p2 always|never|low-risk  默认 low-risk
  --no-verify             跳过 Verifier
  --output-dir <path>     默认 .quality-loop
  --resume <batch_id>     恢复未完成的 batch（可选）
```

### 0.2 文件展开与验证

```
1. 展开 glob → files[]
2. 每个 path：存在性 + 可读性 + 大小 > 0 且 < 500KB（UTF-8 文本）
   - 非 UTF-8 / 非 .md/.txt 扩展名 → 报警告跳过（除非 --allow-binary）
   - 单个文件验证失败 → 警告并跳过，仅全部失败时终止
3. files[] 为空 → 报告错误，停止
4. 验证 --ssot 和 --rubric 文件
```

### 0.3 初始化输出目录

```
若有 --resume <batch_id>：
  检查 {output_dir}/{batch_id}/batch-state.json 是否存在
  若存在且 status 不是终态 → 读取 batch-state 恢复到中断位置继续执行
  若不存在 → 报错停止

否则（新 batch）：
  batch_id = {YYYYMMDD}-{HHMMSS}-{4位随机字母数字}
  output_root = {output_dir}/{batch_id}/

  Bash: mkdir -p {output_root}
  每个 file：
    alias = 文件名去扩展名，重复加数字后缀（碰撞规则：name, name-2, name-3, ...）
    Bash: mkdir -p {output_root}/{alias}/

  锁定 rubric → 写 {output_root}/rubric-locked.md
  写 {output_root}/batch-state.json（初始状态）
```

### 0.4 宣告启动

```
zdoc-quality-loop 启动
══════════════════════════════════════════════
Batch ID：{batch_id}  输出目录：{output_root}
文档：{N} 份，模式：{串行 | 并行}
配置：max-rounds={n}  p1-threshold={n}  p2={policy}
══════════════════════════════════════════════
```

---

## 阶段 1：评审轮次循环

**串行模式**：逐文档完整跑完。
**并行模式**（`--parallel`）：同时 spawn 所有文档，`run_in_background=true`。

---

### 1.0 选角（Role Panel Selection）— 每份文档仅执行一次

**触发时机**：该文档第一轮开始前（之后所有轮次复用同一 role-panel.json）。

Spawn `analyst` agent（model=haiku）：

```
你是评审团选角专家。根据文档内容为本次评审选择 2-4 个最合适的角色，并指定 1 个 Moderator。

【文档内容】
{document_content}

【可用角色池】
- product-manager：需求完整性、用户价值、范围定义（主管 R01 R07 R10）
- architect：技术可行性、数据模型、系统设计（主管 R02 R03 R06）
- developer：实现细节、边界、异常、伪闭环（主管 R02 R04 R05 R09）
- ux-designer：UI 状态流、交互一致性（主管 R06 R04）
- analyst：需求歧义、SSOT 对齐（主管 R01 R08 R10）
- security：安全边界、失败路径（主管 R05 R04 R09）

【选角规则】
1. 选 2-4 个，不多不少
2. 覆盖文档最关键的质量风险维度
3. Moderator 固定为 analyst（负责合并主持）
4. 选角不包含 analyst 时，额外加入 analyst 专职主持
5. 判断文档类型（PRD/技术设计/API 规范/前端设计等），以此指导选角

输出 JSON（Role Panel Schema），不输出说明文字
```

**完成后**：
```
解析输出 → role_panel
若解析失败 → 使用 fallback panel：
  selected_roles = [
    {role_id:"analyst", subagent_type:"analyst", primary_dimensions:["R01","R08","R10"]},
    {role_id:"developer", subagent_type:"code-reviewer", primary_dimensions:["R02","R04","R05","R09"]}
  ]
  moderator_subagent = "analyst"
  document_type = "unknown(fallback)"
  fallback_reason = "<解析失败原因>"
Write("{output_root}/{alias}/role-panel.json", role_panel)
更新 batch-state.json

展示：
  [{alias}] 评审团确定：{role_id_1} / {role_id_2} / ... + Moderator={moderator}
  依据：{document_type}，主要风险维度：{primary_dimensions}
  → {output_root}/{alias}/role-panel.json
```

---

### 1.1 Review Pass（多角色并行 → 合并 → 讨论 → 共识）

**读取**：
- 当前文档（`r{round-1}/draft.md` 优先，否则 `final.md`，否则原始 `file.path`）
- `role-panel.json`（本文档的角色配置）
- `rubric-locked.md`
- 上轮 `open_issues_json`（第 1 轮为空；第 2 轮起 = 上轮 verdicts.json 中 verdict ∈ {PARTIAL, NOT_RESOLVED} 的条目）

#### Step A：并行角色评审

对 `role_panel.selected_roles` 中每个角色，**同时** spawn（`run_in_background=true`）对应 subagent_type 的 Agent（model=opus）：

```
你是文档评审团成员，角色：{role_name}。

【你的评审视角】
{role_perspectives[role_id]}  ← 见下方角色视角库

【你主要负责（须深入评审）】
{primary_dimensions 对应的 Rubric 条目}

【你也须覆盖（基本评审）】
其余 Rubric 维度

【待审核文档】
---
{document_content}
---

【SSOT 参考】{ssot_content | 无}

【固定 Rubric（所有 10 个维度）】
{LOCKED_RUBRIC}

【严重级别】
P0：阻塞实现  P1：高歧义  P2：中风险  P3：低风险

【规则】
1. evidence 必须是文档精确原文
2. 不捏造问题
3. 风格类问题不得标注 P0/P1
4. ID 格式：{alias}-{role_id}-R{round}-{severity}-{seq:03d}
5. 只输出 JSON 数组

【上轮已知开放问题（第 2 轮起）】
{open_issues_json}
规则：若问题仍存在，保持原 issue_id，在 found_by 中添加本角色；若问题已解决，不重复上报。

输出：JSON 数组，每条符合 Problem Schema（found_by=["{role_id}"]）
```

**角色视角库**：
```
product-manager: 从产品和用户角度评审。关注：这个文档能否让团队对齐要构建什么？需求是否完整？验收标准是否可测？目标范围是否清晰？
architect:       从系统设计角度评审。关注：数据模型是否一致？API 设计是否合理？状态流是否完整？技术决策是否可执行？
developer:       从实现角度评审。关注：我能凭此文档直接开始编码吗？Happy Path 步骤是否完整？异常处理是否覆盖？有无伪实现？
ux-designer:     从用户体验角度评审。关注：UI 状态与 API 是否对齐？交互流程是否有遗漏状态？错误提示是否定义？
analyst:         从逻辑一致性角度评审。关注：需求有无歧义？与 SSOT 是否冲突？逻辑自洽性？范围是否漂移？
security:        从安全和健壮性角度评审。关注：失败路径是否完整？边界是否严格？有无被忽略的安全风险？伪实现是否会造成漏洞？
```

**各角色返回后立即**：
```
Bash: mkdir -p {output_root}/{alias}/r{round}/reviews/
Write("{output_root}/{alias}/r{round}/reviews/{role_id}-review.json", role_output)
```

**异常处理**：
```
- 各角色返回后立即做 JSON Schema 校验，失败则重试 1 次
- 单角色超时（reviewer 10min / moderator 5min / fixer 15min）→ 重试 1 次后仍超时则：
  Write("{role_id}.timeout", "超时详情")，记入 round-audit.json
- 至少 2 个角色返回有效结果才能继续 Step B，否则 batch-state status=ROUND_FAILED
```

**等待所有角色完成**（并行模式需 join）。

#### Step B：Moderator 合并与冲突检测

Spawn `analyst` agent（model=opus）作为 Moderator：

```
你是评审主持人（MODERATOR）。合并所有角色的评审结果，去重，并检测需要讨论的冲突。

【各角色评审输出】
{for each role_id: role_id 名称 + JSON 内容}

【合并规则】
1. 识别指向同一问题的条目（必要条件：module 完全一致 OR evidence 子串重合度 ≥ 70%，AND dimension 一致）→ 合并为一条
   - severity 取所有贡献角色中的最高级别（如 P0 vs P1 → P0）
   - evidence 取最精确、引用最完整的那个
   - found_by 列出所有贡献角色
   - merged_from_ids 记录所有原始 ID
   - merge_score: 合并置信度 0.0-1.0
   - 边界情况（0.5 ≤ merge_score < 0.8）须填写 merge_rationale 字段
2. 不同问题各自保留
3. 为每条分配新 ID：{alias}-R{round}-{severity}-{seq:03d}，seq 全局递增

【冲突检测规则】
定义冲突（需要讨论的情况）：
- 同一问题，不同角色 severity 相差 ≥ 2 级（P0 vs P2，P1 vs P3）
- 同一问题，某角色标注 P0/P1，另一角色明确在评审中标注"非问题"或给 P3
不构成冲突（Moderator 直接取高级别）：
- 相邻级别分歧（P0 vs P1，P1 vs P2，P2 vs P3）

【输出格式失败重试规则（仅在 Moderator 自我检查时参考）】
若输出中缺少任一分隔符，整体重新生成

输出两个部分：
===CONSOLIDATED_START===
[合并后的完整问题 JSON 数组]
===CONSOLIDATED_END===

===CONFLICTS_START===
[冲突 JSON 数组，符合 Conflict Schema；无冲突则输出空数组 []]
===CONFLICTS_END===
```

**Moderator 返回后立即**：
```
从 ===CONSOLIDATED_START/END=== 提取 → consolidated_issues[]
从 ===CONFLICTS_START/END=== 提取 → conflicts[]

若提取失败（缺少分隔符）→ 重新 spawn Moderator 一次（带强提示"必须包含完整分隔符"）
若二次失败 → 将各角色 review 求并集做兜底合并、不做冲突检测，在 round-audit.json 中标记 moderator_fallback=true

Write("{output_root}/{alias}/r{round}/consolidated-review.json", consolidated_issues)
Write("{output_root}/{alias}/r{round}/review-conflicts.json", conflicts)

若 conflicts 为空 → review_consensus = consolidated_issues，跳到 Step D（写共识）
若 conflicts 非空 → 进入 Step C（讨论）
```

#### Step C：冲突讨论（最多 2 轮）

**对每个 conflict in conflicts[]**，按以下逻辑处理：

**讨论轮（最多 2 轮）**：

为每个冲突的每轮讨论，对各冲突方角色分别 spawn Agent（model=opus）：

```
你是文档评审团成员，角色：{role_id}。
当前有一个评审分歧需要你回应。

【冲突内容】
{conflict.description}
文档位置：{conflict.section}

【所有角色立场列表】
{for each position in conflict.positions:
  {role_id}：严重级别 {proposed_severity}，理由：{rationale}，原文引用：{evidence}
}

【你的原立场】
严重级别：{你的 severity}，理由：{你的 rationale}

【本轮任务】
1. 回应其他角色的理由（是否有说服力？）
2. 明确表态：是否维持原立场，或接受妥协到哪个级别
3. 若有新的文档原文支持你的观点，提供精确引用

输出 JSON（Discussion Round Schema 中该角色的 response 部分）
```

各角色回应后，spawn Moderator（`analyst`，model=opus）综合：

```
你是评审主持人。根据本轮各方回应，判断冲突是否已解决。

【冲突原始描述】{conflict}
【本轮各方回应】{responses_json}

判断规则：
- 至少 N-1 方接受同一级别（含中间妥协）→ RESOLVED，记录 agreed_severity
- 多方让步但级别不一致 → 若这是第 1 轮 → NEXT_ROUND
- 第 2 轮仍不一致 → ESCALATE_TO_HUMAN
- 所有角色均维持原立场 → 若这是第 2 轮 → ESCALATE_TO_HUMAN，否则 → NEXT_ROUND
- 剩余分歧为相邻级别（P0 vs P1，P1 vs P2）→ RESOLVED，取高级别

第 2 轮 prompt 必须包含第 1 轮所有 response 摘要。

输出 JSON（Discussion Round Schema 的完整结构），包含 next_action
```

```
Write("{output_root}/{alias}/r{round}/discussion/conflict-{id}-r{k}.json", discussion_round)

若 next_action = RESOLVED → 更新 conflict.status = RESOLVED_BY_DISCUSSION，final_severity = agreed_severity
若 next_action = NEXT_ROUND → 进行下一轮（k+1）
若 next_action = ESCALATE_TO_HUMAN → 进入人类决策
```

**人类决策（ESCALATE_TO_HUMAN）**：

```
AskUserQuestion：

"文档 {alias} 第 {round} 轮评审发现一个分歧无法自动解决，需要您决定。

【冲突内容】
{conflict.description}
文档章节：{conflict.section}

【各角色立场】
{for each position: role_id / severity / rationale / evidence}

请选择此问题的处理方式："

选项：
  A. 采纳 P0 —— 必须修复
  B. 采纳 P1 —— 高风险，必须修复
  C. 采纳 P2 —— 中风险，按策略修复
  D. 采纳 P3 —— 低风险，仅记录
  E. 忽略此问题 —— 不纳入问题清单
  F. 阻塞此文档 —— 暂停流水线直到人工审核
  （取消/超时/非法输入 → 默认 F）
```

```
根据用户选择：
  A/B/C/D → conflict.status = RESOLVED_BY_HUMAN，final_severity = 选择的级别
  E       → conflict.status = RESOLVED_BY_HUMAN，final_severity = null（从清单移除）
  F / 取消/超时 → 更新 batch-state（status=HUMAN_BLOCKED），跳到阶段 2

写入 review-human-decisions.json（先 Read 旧文件解析为数组，append 新条目后整体写回）：
  [{conflict_id, choice, final_severity, rationale: "human_decision", decided_at: <ISO>}]
  取消/超时时额外记录 reason=USER_ABANDONED
```

#### Step D：生成共识清单

```
基于 consolidated-review.json 和所有 conflict 的 final_severity：
1. 对每个已解决冲突：用 final_severity 更新对应 issue 的 severity
2. 移除所有 final_severity = null 的 issue（人类决策"忽略"）
3. 重新排序（P0 → P1 → P2 → P3）
4. 持续性问题（与上轮 open_issue_ids 匹配）保留原 issue_id；仅新增问题重新分配 seq
   - 匹配依据：issue_id 直接匹配，或 (module + evidence 关键片段 ≥ 70% 相似) 语义匹配

Write("{output_root}/{alias}/r{round}/review-consensus.json", consensus_issues)
```

**问题分类**（与上轮 open_issue_ids 比对）：
```
new[]              = consensus_issues 中 ID 不在 open_issue_ids 的条目
persistent[]       = consensus_issues 中 ID 在 open_issue_ids 的条目
candidate_closed[] = open_issue_ids 中未出现在 consensus_issues 的 ID

更新 batch-state.json（open_issue_ids = consensus 中所有 issue_id）
```

**停止条件检查**（按优先级短路求值，P0/P1 计数来自 consensus_issues）：
```
满足 → 跳到阶段 2（Convergence Gate）
不满足 → 继续 1.2 Fix Pass
```

**Review 阶段完成后展示**：
```
[{alias}] 第 {round}/{max} 轮 - Review 完成
  角色：{role1} / {role2} / {role3}  Moderator：analyst
  ─────────────────────────────────────────────
  各角色问题数：{role1}={n}  {role2}={n}  {role3}={n}
  合并后：P0={n}  P1={n}  P2={n}  P3={n}
  冲突：{n} 个（讨论解决 {n} 个，人类决策 {n} 个）
  共识清单：{output_root}/{alias}/r{round}/review-consensus.json
  新增 +{new}  持续 ={persistent}  候选关闭 -{candidate_closed}
  {stop? "⚑ 停止：{reason}" : "→ 继续 Fix Pass"}
```

---

### 1.2 Fix Pass

**读取**：`r{round}/review-consensus.json`

按严重级别分组：P0/P1 → 必须修复；P2 → 按策略（low-risk：仅修复明显无副作用的问题）；P3 → 不处理。

Spawn `executor` agent（model=sonnet）：

```
角色：你是文档靶向修复专家（TARGETED DOCUMENT FIXER）。

【绝对禁止】
- 不得修改不在问题清单中的任何段落
- 不得改变文档结构、章节顺序或整体范围
- 不得添加超出修复所需的新内容
- 每个 issue_id 只修复一次
- 不得把多个问题合并成一次大改动

【当前文档】
{document_content}

【必须修复（P0）】{p0_issues_json}
【必须修复（P1）】{p1_issues_json}
【按策略处理（P2，策略={p2_policy}）】{p2_issues_json}
【不处理（P3，仅记录）】{p3_issues_json}

输出格式：
第一部分：Fix 日志 JSON 数组（Fix Schema）
第二部分：
===DOCUMENT_START===
{更新后完整文档}
===DOCUMENT_END===
```

**Fix 返回后立即**：
```
提取 fix_log[] → Write("r{round}/fix-log.json", fix_log)
提取 draft_content → Write("r{round}/draft.md", draft_content)

若提取 draft_content 失败：
  重试 1 次（带强提示"必须包含 ===DOCUMENT_START/END=== 分隔符"）
  重试仍失败 → 使用上一版文档作为 draft.md，fix-log 标记 action=PARSE_FAILED，记入 round-audit.json

扫描引入风险（fix_log.some(e => e.introduced_risk?.severity === 'P0')）：
  若触发：Write("r{round}/escalation.json", {introduced_by: issue_id, description: ...})，标记 ESCALATED，跳阶段 2

更新 batch-state.json
```

**文件写入异常处理**：
```
所有 Write 操作失败 → 重试 2 次（指数退避：1s, 2s）
仍失败 → 写 {alias}.write-error.log，batch-state status=IO_ERROR
并行模式下 batch-state.json 使用单写者模型（串行写入，不并发覆盖）
```

---

### 1.3 Verify Pass

前提：`--no-verify` 未设置。

Spawn `verifier` agent（model=sonnet），读取 `r{round}/draft.md`：

```
角色：你是独立验证专家（INDEPENDENT VERIFIER）。
你不是写修复的人，只核实修复是否有效。

【本轮共识问题清单（修复前）】{issues_json}
【Fixer 修复日志】{fix_log_json}
【修复后文档】{draft_content}

验证规则：
1. RESOLVED：文档有明确内容证明问题消除
2. PARTIAL：改善但未完全解决
3. NOT_RESOLVED：问题仍存在
4. evidence 必须引用更新文档原文
5. action=SKIPPED → verdict=NOT_RESOLVED

只输出 JSON 数组（Verify Schema，verifier="independent-verifier"）
```

**Verify 返回后立即**：
```
Write("r{round}/verdicts.json", verdicts)
处理裁定：RESOLVED → closed_issue_ids；PARTIAL/NOT_RESOLVED → open_issue_ids
若所有 P0 RESOLVED（或 --no-verify 时 P0 consensus count = 0）→ Write("{alias}/final.md", draft_content)
  - PARTIAL_CONVERGENCE 状态下也写 final.md，但在文件开头添加 <!-- WARNING: PARTIAL_CONVERGENCE 状态，P1 未全清 -->
  - NOT_CONVERGED 不写 final.md，保留最后 draft.md
写 round-audit.json（含完整多角色 review 信息）
更新 batch-state.json
停止条件检查 → 满足则阶段 2，否则 round+=1 回到 1.1
```

**--no-verify 分支**：
```
跳过 Verifier；
把 fix-log.json 中 action=FIXED 视为 RESOLVED 等价，自动构造 verdicts.json
（每条：verdict=RESOLVED, verifier="skipped", evidence="fix-log action=FIXED"）
当 review-consensus 中 P0=0 时写 final.md
```

---

## 阶段 2：独立过程审计（Independent Audit Agent）

**触发条件**：文档满足停止条件，进入报告前。

**目的**：由一个完全独立、无共享上下文的 Agent 从磁盘重建全过程，验证数据一致性。

> **说明**：`verifier` Agent 在此作为审计专家使用，与评审角色池无关，不参与选角。

### 2.1 准备审计清单

```
Write("{output_root}/{alias}/audit-manifest.json", {
  "alias": alias,
  "batch_id": batch_id,
  "output_dir": "{output_root}/{alias}/",
  "total_rounds": current_round,
  "round_files": {
    "r1": {
      "role_panel": "role-panel.json",
      "reviews_dir": "r1/reviews/",
      "consolidated": "r1/consolidated-review.json",
      "conflicts": "r1/review-conflicts.json",
      "discussion_dir": "r1/discussion/",
      "human_decisions": "r1/review-human-decisions.json",
      "consensus": "r1/review-consensus.json",
      "fix_log": "r1/fix-log.json",
      "draft": "r1/draft.md",
      "verdicts": "r1/verdicts.json",
      "round_audit": "r1/round-audit.json",
      "escalation": "r1/escalation.json"
    },
    ...
  },
  "final_doc": "final.md",
  "batch_state": "../batch-state.json",
  "rubric": "../rubric-locked.md",
  "checks_to_run": [
    "file_completeness",
    "issue_id_continuity",
    "fix_coverage",
    "verdict_coverage",
    "closed_issue_reconstruction",
    "introduced_risk_tracking",
    "consensus_vs_individual_consistency",
    "human_decision_coverage",
    "escalation_tracking"
  ]
})
```

### 2.2 Spawn 独立审计 Agent

Spawn `verifier` agent（model=opus），**无任何共享上下文**：

```
你是独立过程审计专家。你对本次评审流水线的过程完全不了解。

【你的任务】
根据以下审计清单中指定的文件路径，从磁盘读取所有相关文件，
对整个评审过程进行独立的一致性验证。

【审计清单路径】
{output_root}/{alias}/audit-manifest.json

【审计项目】
请逐一执行 audit-manifest.json 中 checks_to_run 列出的检查：

1. file_completeness（文件完整性）
2. issue_id_continuity（问题 ID 连续性）
3. fix_coverage（修复覆盖率：P0/P1 must have fix record）
4. verdict_coverage（验证覆盖率：action=FIXED must have verdict）
5. closed_issue_reconstruction（关闭列表重建）
6. introduced_risk_tracking（引入风险追踪）
7. consensus_vs_individual_consistency（共识与角色输出一致性）
8. human_decision_coverage（人类决策可追溯性）
9. escalation_tracking（escalation.json 与停止条件对齐验证）

【输出格式】
===AUDIT_REPORT_START===
{ "alias": "...", "audited_at": "<ISO>", ... }
===AUDIT_REPORT_END===

===AUDIT_FINDINGS_START===
[{ "check_id": "...", "severity": "ERROR|WARNING", ... }]
===AUDIT_FINDINGS_END===
```

**审计 Agent 返回后**：
```
提取 audit_report → Write("{output_root}/{alias}/audit-report.json", audit_report)
若提取失败（malformed JSON）→ 重试 1 次，仍失败 →
  Write("{alias}/audit-report.json", {status:"AUDIT_FAILED", alias, audited_at})
  audit_status = "AUDIT_FAILED"（不阻塞阶段 3，但报告 Agent 需标红）
若 findings 非空 → Write("{output_root}/{alias}/audit-findings.json", findings)
展示：
  [{alias}] 独立审计完成（无共享上下文）
  结果：{PASSED | FINDINGS（{n} 项）| AUDIT_FAILED}
  → {output_root}/{alias}/audit-report.json
```

---

## 阶段 3：独立结果报告（Independent Report Agent）

**触发条件**：审计完成（无论是否有 findings）。

**目的**：由完全独立的 Agent 从磁盘读取所有产物，生成客观的收敛报告。

> **说明**：`documentation-analyst-writer` Agent 在此作为报告专家使用，与评审角色池无关，不参与选角。若系统不支持该 subagent_type，可映射为 `writer`。

### 3.1 准备报告清单

```
Write("{output_root}/{alias}/report-manifest.json", {
  "alias": alias,
  "batch_id": batch_id,
  "original_doc": file.path,
  "output_dir": "{output_root}/{alias}/",
  "role_panel": "role-panel.json",
  "rubric": "../rubric-locked.md",
  "round_dirs": ["r1", "r2", ...],
  "final_doc": "final.md",
  "audit_report": "audit-report.json",
  "audit_findings": "audit-findings.json",
  "batch_state": "../batch-state.json",
  "report_output_path": "quality-report.md",
  "report_requirements": {
    "include_role_panel_section": true,
    "include_conflict_summary": true,
    "include_per_role_coverage": true,
    "include_process_artifact_index": true,
    "include_audit_section": true,
    "note_independent_generation": true,
    "embed_rubric_content": true
  }
})
```

### 3.2 Spawn 独立报告 Agent

Spawn `documentation-analyst-writer` agent（model=sonnet），**无任何共享上下文**：

```
你是独立文档报告专家。你对本次评审流水线的过程完全不了解。

【你的任务】
根据以下报告清单，从磁盘读取所有相关文件，
综合分析整个评审过程，生成完整的质量收敛报告。

【报告清单路径】
{output_root}/{alias}/report-manifest.json

请按以下步骤执行：
1. 读取 report-manifest.json，了解所有文件位置
2. 读取 role-panel.json，了解评审团组成
3. 读取每一轮的 review-consensus.json、fix-log.json、verdicts.json、round-audit.json
4. 读取 audit-report.json（和 audit-findings.json 若存在）
5. 读取 batch-state.json，了解最终收敛状态
6. 读取 rubric-locked.md，将内容内嵌到报告 Rubric 章节（不仅显示路径）
7. 综合以上信息，生成完整报告

报告必须包含以下章节，输出完整 Markdown：

# 质量收敛报告：{alias}

## 文档信息
- 原始路径、最终版本、Batch ID、处理时间、轮次、停止原因
- **本报告由独立报告 Agent 生成，仅凭磁盘文件，无共享评审上下文**

## 收敛结论

## 评审团组成

## 各角色问题发现统计

## 冲突与解决摘要

## 问题轨迹（从磁盘重建）

## 已关闭问题

## 仍开放问题

## 过程产物索引

## 过程审计结论

## 引入风险记录

## 剩余风险与建议

## Rubric 锁定内容
{此处内嵌 rubric-locked.md 全文，不仅显示路径}

将报告写入 {output_root}/{alias}/quality-report.md
```

**报告 Agent 返回后**：
```
展示：
  [{alias}] 独立报告生成完成（无共享上下文）
  → {output_root}/{alias}/quality-report.md
```

---

## 阶段 4：批次汇总

**触发条件**：所有文档的审计和报告均完成。

写入 `{output_root}/batch-summary.md` 并向用户展示：

```
zdoc-quality-loop 完成
══════════════════════════════════════════════
Batch ID：{batch_id}  输出根目录：{output_root}/

批次结果（{N} 份文档）：
  文档          别名     收敛状态                P0  P1  轮次  角色数  冲突  审计    报告
  ─────────────────────────────────────────────────────────────────────────────────
  spec.md       spec    ✓ APPROVED              0   2   3     3     0    PASSED  spec/quality-report.md
  design.md     design  ⚠ PARTIAL_CONVERGENCE   0   5   5     4     2    PASSED  design/quality-report.md
  prd.md        prd     ✗ NOT_CONVERGED         2   4   5     3     1    FINDINGS prd/quality-report.md
  auth.md       auth    ⛔ ESCALATED             1   2   2     3     0    PASSED  auth/quality-report.md
  api.md        api     ⏸ HUMAN_BLOCKED         0   3   1     2     1    PASSED  api/quality-report.md

全局残留风险：
  ...

需要人工关注：...
══════════════════════════════════════════════
```

---

## 阶段 5：人工闸门

`AskUserQuestion`：

**问题**："质量收敛完成。请选择下一步操作："

**选项**：
1. **全部接受** — 使用 final.md，承认剩余风险
2. **手动修复残留** — 用户自行处理 P0/P1
3. **扩展轮次继续** — 对 NOT_CONVERGED / ESCALATED / PARTIAL_CONVERGENCE 文档再跑 N 轮
4. **仅接受已收敛文档** — APPROVED 继续，其余暂停
5. **全部阻塞** — 直到 P0/P1=0

选择"扩展轮次"：
```
询问新增轮次数（默认 +3）
NOT_CONVERGED / ESCALATED / PARTIAL_CONVERGENCE 参与重跑（用户可选）
HUMAN_BLOCKED 需先解除阻塞才能重跑
ESCALATED 续跑前必须展示 escalation.json 内容并要求用户确认，防止死循环
APPROVED 不重跑
复用同一 batch_id 目录，新轮次写 r6/、r7/...
rubric-locked.md 在 batch 生命周期内永不变；role-panel.json 默认复用
重新生成 audit-manifest.json（加入新轮次文件）
重新 spawn 独立审计 Agent 和报告 Agent
```

</Steps>

---

<Anti_Patterns>
| 反模式 | 预防机制 |
|--------|---------|
| 自嗨收敛（Fixer 自我评价"已修复"） | Verifier 独立核对 + evidence 强制引用原文 |
| 标准漂移（每轮 Rubric 变化） | 初始化时锁定 rubric-locked.md，每轮从文件读取传入 |
| 角色互相认可（评审团互吹） | 讨论时每角色独立响应，Moderator 综合判断，人类作为最终裁判 |
| 多数暴政（2 对 1 压倒少数角色） | 冲突判断基于证据质量，不基于角色数量；差异 ≥ 2 级必须讨论 |
| 假共识（P0 被讨论降为 P1） | ID 追踪，审计 check 5 重建 closed_issue_ids；降级决策记录在 discussion/conflict-{id}-r{k}.json 中，agreed_severity 字段可追溯（仅人类升级决策写 human-decisions.json） |
| 报告与实际不符 | 独立报告 Agent 无共享上下文，只读磁盘；报告中注明生成方式 |
| 审计被流水线污染 | 独立审计 Agent 仅收到文件路径清单，无任何流水线上下文 |
| 中断丢失状态 | 每阶段立即落盘，所有状态可从磁盘文件重建；支持 --resume <batch_id> 恢复 |
| Token 爆炸 | 第 2 轮起 Reviewer 只传 open_issues JSON；各角色并行，不共享上下文 |
</Anti_Patterns>

---

<File_Path_Quick_Reference>
运行 `/zdoc-quality-loop spec.md prd.md` 后，以 spec 为例：

```
.quality-loop/20260508-143022-a3f2/
├── rubric-locked.md
├── batch-state.json
├── batch-summary.md
└── spec/
    ├── role-panel.json                  ← 选角结果（全轮复用）
    ├── r1/
    │   ├── reviews/
    │   │   ├── product-manager-review.json
    │   │   ├── architect-review.json
    │   │   └── developer-review.json
    │   ├── consolidated-review.json     ← Moderator 合并去重
    │   ├── review-conflicts.json        ← 冲突列表
    │   ├── discussion/
    │   │   └── conflict-001-r1.json     ← 讨论轮次记录
    │   ├── review-human-decisions.json  ← 人类裁决（如有）
    │   ├── review-consensus.json        ← 权威问题清单
    │   ├── fix-log.json
    │   ├── draft.md
    │   ├── verdicts.json
    │   ├── escalation.json              ← 修复引入新 P0 时（如有）
    │   └── round-audit.json
    ├── r2/ ...
    ├── final.md
    ├── audit-manifest.json              ← 审计 Agent 输入清单
    ├── audit-report.json                ← 独立审计 Agent 输出
    ├── audit-findings.json              ← 审计异常（如有）
    ├── report-manifest.json             ← 报告 Agent 输入清单
    └── quality-report.md                ← 独立报告 Agent 输出
```
</File_Path_Quick_Reference>

---

<Final_Checklist>
阶段 0：
- [ ] output_root 和所有 alias/ 目录已创建
- [ ] rubric-locked.md 已写入
- [ ] batch-state.json 已写入（running）

阶段 1.0（每文档一次）：
- [ ] role-panel.json 已写入
- [ ] 角色数 2-4，Moderator 指定

每轮 Review（1.1）：
- [ ] 各角色 reviews/{role}-review.json 已写入（并行返回后立即）
- [ ] consolidated-review.json 已写入
- [ ] review-conflicts.json 已写入（空数组也写）
- [ ] 所有冲突已处理（讨论 or 人类决策）
- [ ] review-human-decisions.json 已写入（如有人类决策，先 Read 后 append）
- [ ] review-consensus.json 已写入（最终权威清单）

每轮 Fix（1.2）：
- [ ] fix-log.json 已写入（Fix 返回后立即）
- [ ] draft.md 已写入（Fix 返回后立即）
- [ ] escalation.json 已写入（若 introduced_risk.severity=P0）
- [ ] 数据一致性：P0/P1 issue_id 在 fix-log 中均有对应记录

每轮 Verify（1.3）：
- [ ] verdicts.json 已写入（Verify 返回后立即，--no-verify 时自动构造）
- [ ] final.md 已更新（P0 全清时，PARTIAL_CONVERGENCE 附警告注释）
- [ ] round-audit.json 已写入（本轮结束前，含多角色信息）
- [ ] batch-state.json 已更新
- [ ] 数据一致性：action=FIXED 的 issue_id 在 verdicts 中均有对应 verdict

阶段 2（独立审计）：
- [ ] audit-manifest.json 已写入（含 escalation_tracking 检查项）
- [ ] 独立审计 Agent 已 spawn（无共享上下文）
- [ ] audit-report.json 已写入
- [ ] audit-findings.json 已写入（若有异常）

阶段 3（独立报告）：
- [ ] report-manifest.json 已写入
- [ ] 独立报告 Agent 已 spawn（无共享上下文）
- [ ] quality-report.md 已写入
- [ ] 报告含"独立 Agent 生成"声明
- [ ] 报告含角色发现统计、冲突摘要、过程产物索引、审计结论、Rubric 内嵌内容

阶段 4/5：
- [ ] batch-summary.md 已写入（含所有 status 符号）
- [ ] 人工闸门通过 AskUserQuestion 呈现
</Final_Checklist>

Task: {{ARGUMENTS}}
