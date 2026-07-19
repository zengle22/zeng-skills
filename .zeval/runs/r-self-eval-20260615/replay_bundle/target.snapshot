---
name: zeval-skill
description: "通用评估引擎。对 skill 设计 / agent run / 文档 / 代码 diff / prompt 输出 / 多轮对话执行多视角、可重放、带证据链的评估，输出可被 CI 消费的 gate 结果。"
argument-hint: "[--request request.json] [--rubric <id@version>] [--target <kind:ref>] [--judges correctness,safety,clarity] [--baseline compare|enforce|none] [--output-dir .zeval] [--replay-seed <seed>]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Agent
  - AskUserQuestion
---

# zeval-skill

通用评估引擎。本技能以**多角色并行评审 + 仲裁器统一出口**为核心执行模型，对"待评估对象"（skill 设计、agent run、文档、代码 diff、prompt 输出、多轮对话）执行结构化、可重放、带证据链的评估，输出**可被 CI 消费的 gate 结果**与**可对比的回归基线**。

> **TL;DR**
> `zeval-skill` 是"裁判"与"基线守护者"——它**不**直接修复问题、不**直接**产出代码。
> 修复动作由 `zcode-patrol` / `zcode-review-deep` / `zdoc-i2i` 等下游 skill 完成。

## Not Equal To

- **Not a source code fixer** — 评估产出**评分卡 + 修复建议**，不生成 patch
- **Not a replacement for human review** — 人类在 loop 中作为"最终仲裁"或"基线设定者"，不在 hot path
- **Not a real-time monitor** — 是**批/触发**型，不做 metrics dashboard
- **Not a training/eval benchmark** — 不读训练数据、不调权重、不替代 LM Evaluation Harness
- **Not opinionated on aesthetics** — 美学/品味/灵感等无客观证据的领域**不**进入 v1 rubric

## Execution Model

本技能采用**协作式执行架构**：

| 组件 | 职责 |
|------|------|
| **外层 AI Agent** | 完整流程编排：参数解析、Rubric 加载、Judge 并行调度、仲裁、报告生成、Baseline 对比 |
| **`agents/judge.*.md`** | 评审视角 prompt 定义（correctness / safety / clarity / completeness / efficiency / contract / style） |
| **`agents/adjudicator.md`** | 仲裁器 prompt 定义：汇总 N 个 Judge 评分，按 strategy 输出 Verdict |
| **`schemas/*.json`** | 输入/输出契约（强校验） |
| **`rubrics/*.yaml`** | 评分卡定义（维度、阈值、证据要求） |
| **`validate.py`** | 输出产物的 JSON Schema 契约验证（可选，确保产物质量） |
| **`.zeval/`（运行产物）** | 每次评估的 report、judgments、replay bundle、baseline 存储 |

> **注意**：本技能是**纯 SKILL.md + 外层 AI Agent** 实现，无独立 Python 运行时。
> `validate.py` 仅用于验证输出产物是否符合 JSON Schema 契约。
> 这与 `zcode-review-deep` v1.1 简化后的架构一致（参见 ADR-001 §12.1）。

## Top-Level Workflow

```
1. Loader        解析参数，加载 target / rubric / judges
2. Validator     Schema / Path / 权限校验（→ blocked if fail）
3. Dispatcher    并行调度 N 个 Judge Agent
4. Judges        独立评审，各输出 score + rationale + evidence_refs
5. Adjudicator   汇总冲突，按 strategy 产出 Verdict
6. Reporter      输出 EvalReport.json
7. Baseliner     与 baseline 对比，标记 regressed_dimensions
8. Replayer      持久化 replay bundle（保证可重放）
```

## Output Schema

所有输出产物必须符合以下 JSON Schema：

| 产物 | Schema | 路径约定 |
|------|--------|----------|
| EvalRequest | [`schemas/EvalRequest.schema.json`](./schemas/EvalRequest.schema.json) | `--request` 输入 |
| EvalReport  | [`schemas/EvalReport.schema.json`](./schemas/EvalReport.schema.json) | `{output_dir}/{run_id}/report.json` |
| Judgment    | [`schemas/EvalRequest.schema.json`](./schemas/EvalRequest.schema.json) §judges | `{output_dir}/{run_id}/judgments/<judge_id>.json` |

### Gate 退出码

| Gate.status | 退出码 | 含义 |
|-------------|--------|------|
| pass        | 0      | 全部通过 |
| warn        | 0      | 通过但有警告（仅返回非零 stderr） |
| fail        | 1      | 评估未通过 |
| blocked     | 2      | 输入/校验失败 |
| conflicted  | 3      | 多 judge 冲突无法收敛，升级人类 |

## Evaluation Target Matrix（v1）

| Target Kind   | Target 形态             | 主要 Rubric            | 状态 |
|---------------|-------------------------|------------------------|------|
| `skill-design`| `SKILL.md`              | `skill-design.v1`      | ✅ v1 |
| `document`    | 设计文档 / ADR / README | `document.v1`          | ✅ v1 |
| `agent-run`   | trajectory JSONL        | `agent-run.v1`         | ✅ v1 |
| `code-diff`   | unified diff            | `code-diff.v1`         | v1.x |
| `prompt-output` | LLM 响应              | `prompt-output.v1`     | v1.x |
| `conversation` | 多轮会话轨迹            | `conversation.v1`      | v1.x |

## Rubric System

### Rubric 形态（参见 `rubrics/_template.yaml`）

```yaml
id: skill-design
version: 1.0.0
target_kinds: [skill-design, skill-impl]

dimensions:
  - id: completeness
    weight: 1.0
    evidence_required: true
    levels:
      excellent: { min: 0.9, desc: "..." }
      good:      { min: 0.7, desc: "..." }
      # ...
    required_signals: ["..."]
    fail_if: ["..."]

adjudication:
  strategy: weighted-mean
  pass_threshold: 0.75
  fail_threshold: 0.45
  conflict_threshold: 0.4

baseline:
  regression_threshold: 0.10
  default_mode: compare
```

### Rubric 边界规则

1. **可观测**：每个维度必须有可被 Judge 看到的信号
2. **可证伪**：必须存在 Judge 能引用的"反例条件"
3. **不可评价**的维度（美学/品味）→ 不进 Rubric
4. **权重 > 0**，但不必和为 1

## Scoring Model

### 单维度评分

```
score ∈ [0, 1]    # Judge 输出 0.0~1.0
level ∈ {excellent, good, acceptable, poor, fail, skip}
```

- Judge 必带 `rationale`（≤500 字符） + ≥1 条 `evidence_refs`
- 缺证据 → 该维度直接 `level=fail`（除非 `evidence_required: false`）

### 仲裁策略

| 策略                | 适用 |
|---------------------|------|
| `weighted-mean`     | 默认 |
| `majority-vote`     | 安全类 |
| `any-fail-blocks`   | 安全性、契约类 |
| `unanimous-pass`    | 高门槛交付物 |

## Replay & Baseline

### Replay 三要素

```
Replay = Target.snapshot + Rubric.version + Model.config + Replay.seed
```

- Target 必须**内联快照**（不是路径），保证可重放
- Baseline 永久存储于 `.zeval/baselines/<rubric_id>/<target_hash>/`
- Baseline **不可自动覆盖**，升级须显式 `baseline promote`

### 回归检测

- 任一维度下降 > `regression_threshold`（rubric 内置，默认 0.10）→ 标 `regressed_dimensions`
- `baseline.mode: enforce` → 退化直接 fail；`compare` → 仅提示

## Execution Protocol

### 最小调用

```bash
# 1. 准备 EvalRequest（也可通过 CLI 参数自动生成）
cat > /tmp/eval.req.json <<EOF
{
  "target":  { "kind": "skill-design", "ref": "./skills/zdoc-i2i/SKILL.md" },
  "rubric":  { "id": "skill-design", "version": "1.0.0" },
  "judges":  [
    { "id": "j-corr", "role": "correctness" },
    { "id": "j-comp", "role": "completeness" },
    { "id": "j-clr",  "role": "clarity" }
  ]
}
EOF

# 2. 调用
/zeval-skill --request /tmp/eval.req.json

# 3. 读取结果
cat .zeval/runs/<run_id>/report.json
```

### 编排示例：被上层 skill 调用

```
用户: 设计文档 → zdoc-design-check → (通过)
                          ↓
                  zdoc-quality-loop
                          ↓
                    ┌─────────────┐
                    │  zeval-skill │   ← 本 skill（多视角评审阶段）
                    └──────┬──────┘
                           ↓
                      EvalReport
                           ↓
                    ┌──────────┐
                    │  Gate    │──→ pass / fail
                    └──────────┘
                           ↓ (pass)
                        zdoc-i2i
```

## Artifact Directory Structure

默认产物目录 `.zeval/`，结构：

```
.zeval/
├── runs/
│   └── <run_id>/
│       ├── report.json                    # 主报告（EvalReport）
│       ├── request.json                   # 输入快照（用于 replay）
│       ├── judgments/
│       │   ├── <judge_id_1>.json          # 单 judge 原始输出
│       │   ├── <judge_id_2>.json
│       │   └── ...
│       ├── replay_bundle/                 # 可重放 bundle
│       │   ├── target.snapshot
│       │   ├── rubric.snapshot.yaml
│       │   └── model.config.yaml
│       └── meta.yaml                      # 元信息（耗时、模型版本、seed）
└── baselines/
    └── <rubric_id>/
        └── <target_hash>/
            ├── baseline.json
            ├── meta.yaml
            └── replay_bundle/
```

可通过 `--output-dir <dir>` 覆盖。

## Validation

可选运行 `validate.py` 对产物做 JSON Schema 契约校验：

```bash
python3 skills/zeval-skill/validate.py \
    --report .zeval/runs/<run_id>/report.json \
    --rubric skills/zeval-skill/rubrics/skill-design.v1.yaml
```

- exit 0 = 全部 OK
- exit 1 = 存在 schema / rubric / 交叉引用不一致

## Non-Negotiable Rules

1. **不修代码** — 评估是裁判，修复是别人
2. **不省证据** — 没有 evidence 的评分自动 fail
3. **不混版本** — 同一 target 评估中途换 rubric 版本结果不可比
4. **不覆盖基线** — Baseline 一经建立须显式 promote
5. **不评价美学** — 无客观信号的维度不进 v1 rubric
6. **不背离宿主** — Judge 模型由宿主提供，不内置固定模型

## Usage

### 场景 1：评估一份 SKILL.md

```bash
/zeval-skill --target skill-design:./skills/zdoc-i2i/SKILL.md \
             --rubric skill-design@1.0.0 \
             --judges correctness,completeness,clarity
```

### 场景 2：评估一次 agent run

```bash
/zeval-skill --target agent-run:./trajectories/run-001.jsonl \
             --rubric agent-run@1.0.0 \
             --judges correctness,efficiency,safety,contract
```

### 场景 3：建立基线（首次跑某 target）

```bash
/zeval-skill --target document:./docs/my-design.md \
             --rubric document@1.0.0 \
             --baseline none   # 首次不对比

# 通过后手动 promote 为基线
python3 skills/zeval-skill/validate.py --promote-baseline .zeval/runs/<run_id>
```

### 场景 4：CI 模式（回归检测）

```bash
/zeval-skill --target code-diff:./pr-123.diff \
             --rubric code-diff@1.0.0 \
             --baseline enforce \
             --judges correctness,safety,style

# gate 退出码 1 = 退化阻断 CI
```

### 场景 5：被 zdoc-quality-loop / zcode-review-deep 调用

上层 skill 在"评审阶段"自动生成 EvalRequest 并调用本 skill；本 skill 输出 EvalReport 与 Gate 给上层 skill 决策。

## Relationship with Other Skills

| 调用方 | 调用意图 | 阶段 |
|--------|----------|------|
| `zdoc-quality-loop` | 把"评审阶段"换成多视角打分 + 冲突报告 | 评审 |
| `zdoc-design-check` | 复用其维度定义作为 eval rubric 子集 | 校验 |
| `zcode-review-deep` | 评估 review agent 自身输出的一致度、漏报率 | 元评估 |
| `zcode-patrol` | 评估巡检报告的误报率、漏报率 | 元评估 |
| `zdoc-i2i` | 评估 task pack 的覆盖率、可执行性 | 输出评估 |
| `zgsd-plan-phase` | 评估 plan 任务依赖正确性 | 输出评估 |
| `zgsd-bootstrap-milestone` | 评估阶段切分合理性 | 输出评估 |
| `zcode-safe-dev` | 作为自检环节检查硬约束符合度 | 编码期 |

## Pitfalls

- **不要把 eval 当真理** — 它是辅助判断，不是真理
- **不要在没有 baseline 时判定"退化"** — 退化需要参照
- **不要给"美/灵/巧"打分** — v1 无客观信号
- **不要追求"单 judge 准确率"** — 多视角 + 仲裁才是设计目标
- **不要在 hot path 频繁跑** — eval 是**批/触发**型

## Reference

- 基线 ADR：[`adr/ADR-006-评估技能-Eval-Skill-基线.md`](../../adr/ADR-006-评估技能-Eval-Skill-基线.md)
- 复用规范：[`docs/SKILL-USAGE-GUIDE.md`](../../docs/SKILL-USAGE-GUIDE.md)
- 关联 skill：`zdoc-quality-loop` / `zcode-review-deep` / `zcode-patrol`
