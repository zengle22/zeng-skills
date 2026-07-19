# ADR-006：评估技能（Eval Skill）基线

> **SSOT ID**: ADR-006
> **Title**: 建立通用评估引擎 `zeval-skill`，对 skill 设计 / agent run / 文档 / 代码 diff / prompt 输出 / 多轮对话执行多视角、可重放、带证据链的评估，输出可被 CI 消费的 gate 结果与回归基线
> **Status**: Draft
> **Version**: v1.0
> **Effective Date**: TBD
> **Scope**: 评估治理 / Skill 元评估 / 跨 skill 质量可比性 / CI Gate 集成 / 回归基线守护
> **Owner**: 架构 / Skill 治理 / AI 辅助质量工程
> **Governance Kind**: NEW
> **Audience**: AI 实施代理、Skill 维护者、Agent 编排者、Benchmark 维护者
> **Depends On**: 无
> **Supersedes**: 无

状态：Draft
日期：2026-06-10
相关 ADR：—

---

## 1. 背景

### 1.1 One-Sentence Summary

> **现有 8 个 skill 中，无一专门负责"评估输出质量 + 维护基线"，导致评审类 skill（zcode-review-deep / zdoc-quality-loop）的输出**自身**无打分、跨 run 输出不可比、rubric 一致性没有客观尺子、prompt / model 改动后的"是否变差"无法量化。**

### 1.2 现有能力与缺口

当前 `zeng-skills` 仓库的 8 个 skill 形成 3 条能力线：

| 能力线 | 现有 skill | 缺失环节 |
|--------|-----------|----------|
| **设计与实施流水线** | zdoc-design-check、zdoc-i2i、zgsd-bootstrap-milestone、zgsd-plan-phase | I2I 输出（task pack）质量无客观评分 |
| **文档质量** | zdoc-quality-loop | BMAD 评审团输出无统一分数、冲突仅靠共识 |
| **代码质量** | zcode-safe-dev、zcode-patrol、zcode-review-deep | 巡检/审查的**输出**无元评估（漏报率/误报率） |

共性缺口：
1. **评审类 skill 的输出没有打分** — review agent 自身质量靠人工
2. **跨 run 不可比** — 一次跑 80 还是 90 没有客观尺子
3. **没有回归基线** — 改 rubric 后老 baseline 不能用；改 prompt 后老输出不可比
4. **多视角冲突无指标** — 三个 judge 严重冲突时只能人工看

### 1.3 为什么现在做

- ✅ zcode-review-deep v1.1 简化后（参见 ADR-001 §12.1）已稳定"纯 SKILL.md + validate.py"范式
- ✅ zdoc-quality-loop 的 BMAD 评审团已验证"多角色并行"在 Claude Code / Codex 上的可行性
- ✅ 8 个 skill 已基本成熟，可被"评估"做元评估
- ❗ 下一个规模化的关键节点（v2.x）需要"评估引擎"做质量门禁

---

## 2. 决策

**采纳 `zeval-skill` 作为通用评估引擎**，并遵循以下七条核心决策。

### 决策 D1：定位为"裁判 + 基线守护者"，不直接修复

- 评估 skill **不**修改、不重写、不修复被评估对象
- 只输出 EvalReport + Gate 信号
- 修复动作仍由 `zcode-patrol` / `zcode-review-deep` / `zdoc-i2i` 等下游 skill 完成

**理由**：避免与"修复类" skill 产生职责重叠与循环依赖。

### 决策 D2：强 Schema、强协议、强可重放

- 所有输入输出走 JSON Schema，versioned（见 `schemas/EvalRequest.schema.json` / `EvalReport.schema.json`）
- 重放三要素 = Target.snapshot + Rubric.version + Model.config + Replay.seed
- 不允许"路径式" target（必须内联快照）以保证可重放

**理由**：评估结果若不能重放，等同于不可信。

### 决策 D3：多 Judge 并行 + 仲裁器统一出口

- 单维度允许多 judge 并行评审（见 `agents/judge.*.md`）
- Adjudicator 是唯一产生 Verdict 的组件（见 `agents/adjudicator.default.md`）
- 默认 `weighted-mean` 策略；安全类用 `any-fail-blocks`

**理由**：避免单 judge 视角偏差；统一出口降低上层 skill 接入成本。

### 决策 D4：Rubric 必带证据

- 每个评分必带 ≥1 条 evidence ref
- 缺证据的评分自动 fail（除非 `evidence_required: false`）
- v2 引入 evidence ref 自动回查（防"幻觉引用"）

**理由**：评估的核心价值是"可证伪"，没有证据就没有评估。

### 决策 D5：Baseline 不可覆盖、显式 promote

- 一旦 baseline 建立，永不自动覆盖
- 升级 baseline 须显式 `validate.py --promote-baseline <run_dir>`
- baseline 与 rubric 版本绑定（`baseline/<rubric_id>/<target_hash>/`）

**理由**：基线是回归检测的参照，自动化覆盖会让回归检测失去意义。

### 决策 D6：v1 范围收敛三类 Target

- v1 支持 T1 (skill 设计)、T3 (agent run)、T5 (文档) 三类
- T2/T4/T6/T7 留 v1.x 阶段（见 `SKILL.md` § Evaluation Target Matrix）

**理由**：v1 必须可交付、可验证；目标越多越容易失焦。

### 决策 D7：执行模型 = 纯 SKILL.md + validate.py（与 zcode-review-deep v1.1 一致）

- 无独立 Python 运行时
- 所有流程逻辑由外层 AI Agent 执行
- `validate.py` 仅用于输出契约验证 + baseline promote

**理由**：与 zcode-review-deep v1.1 简化后范式一致（参见 ADR-001 §12.1）；降低维护成本。

---

## 3. 架构概览

### 3.1 组件协作

```
┌──────────────────────────────────────────────────────────────┐
│                     zeval-skill 执行模型                       │
├──────────────────────────────────────────────────────────────┤
│  ① Loader        → 解析参数 / 加载 target+Rubric            │
│  ② Validator     → Schema / Path / 权限校验（→ blocked）   │
│  ③ Dispatcher    → 并行调度 N 个 Judge Agent               │
│  ④ Judges        → 多视角独立评议，输出 evidence           │
│  ⑤ Adjudicator   → 汇总冲突，产出 Verdict                  │
│  ⑥ Reporter      → 输出 EvalReport.json                    │
│  ⑦ Baseliner     → 与 baseline 对比，标 regressed          │
│  ⑧ Replayer      → 持久化 replay bundle                    │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 目录结构（落地后）

```
skills/zeval-skill/
├── SKILL.md                              # 核心定义
├── schemas/
│   ├── EvalRequest.schema.json
│   └── EvalReport.schema.json
├── rubrics/
│   ├── _template.yaml
│   └── skill-design.v1.yaml
├── agents/
│   ├── judge.correctness.md
│   └── adjudicator.default.md
├── examples/
│   ├── request.skill-design.json
│   └── report.skill-design.json
└── validate.py                            # 契约校验 + baseline promote
```

### 3.3 评估对象矩阵

| Target Kind   | Target 形态             | 主要 Rubric        | 状态 |
|---------------|-------------------------|--------------------|------|
| `skill-design`| `SKILL.md`              | `skill-design.v1`  | ✅ v1 |
| `document`    | 设计文档 / ADR / README | `document.v1`      | ✅ v1 |
| `agent-run`   | trajectory JSONL        | `agent-run.v1`     | ✅ v1 |
| `code-diff`   | unified diff            | `code-diff.v1`     | v1.x |
| `prompt-output` | LLM 响应              | `prompt-output.v1` | v1.x |
| `conversation` | 多轮会话轨迹            | `conversation.v1`  | v1.x |

---

## 4. 协议契约

### 4.1 输入契约

```json
{
  "target":   { "kind": "skill-design", "ref": "..." },
  "rubric":   { "id": "skill-design", "version": "1.0.0" },
  "judges":   [ { "id": "j-corr", "role": "correctness" } ],
  "adjudicator": { "strategy": "weighted-mean" },
  "baseline":    { "mode": "compare" },
  "replay":      { "seed": "..." }
}
```

### 4.2 输出契约（节选）

```json
{
  "run_id": "r-2026-06-10-001",
  "rubric_id": "skill-design",
  "rubric_version": "1.0.0",
  "scores":  [ { "judge_id": "...", "dimension": "...", "score": 0.82, "level": "good", "evidence_refs": [...] } ],
  "verdict": { "verdict": "pass", "score": 0.79, "rationale": "..." },
  "gate":    { "status": "pass", "code": "G000" }
}
```

完整定义见 `schemas/EvalRequest.schema.json` / `EvalReport.schema.json`。

### 4.3 Gate 退出码

| Gate.status | 退出码 | 含义 |
|-------------|--------|------|
| pass        | 0      | 全部通过 |
| warn        | 0      | 通过但有警告（stderr 非零） |
| fail        | 1      | 评估未通过 |
| blocked     | 2      | 输入/校验失败 |
| conflicted  | 3      | 多 judge 冲突无法收敛 |

---

## 5. 与现有 skill 的关系

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

**关键约束**：`zeval-skill` 永远**只读**上层 skill 的产物，**不**改写。eval 输出**只**写到 `.zeval/` 目录。

---

## 6. 后果

### 6.1 正面

- ✅ 第一次有**客观尺子**衡量 skill 质量
- ✅ 评审类 skill 自身也可被评估，**闭环**
- ✅ 跨 run 回归基线让"我是不是改坏了"成为可量化问题
- ✅ 多视角冲突可被结构化记录、推动架构改进
- ✅ CI 可直接消费 `gate` 退出码

### 6.2 负面 / 成本

- ⚠️ **Token 成本上升**：每个评估 N 个 judge × M 个维度 → 多倍 token
  - 缓解：max_parallel 控制 + rubric 可关 judge
- ⚠️ **评审延迟**：单次评估从"读 → 评"变成"读 → 多视角评 → 仲裁"
  - 缓解：v1 默认同步；v2 引入流式中间态
- ⚠️ **LLM 评审不稳定**：相同输入两次跑分差可能 > 0.1
  - 缓解：多 judge 取均 + 强制 replay seed + model 版本绑定
- ⚠️ **Rubric 维护成本**：rubric 本身需要元评估
  - 缓解：v1 暂不做 meta-eval，靠人工 review rubric 变更

### 6.3 维护负担

- 仓库 skill 总数 8 → 9
- 增加 5 份 schemas/rubrics/examples 资产需维护
- 增加 1 份 validate.py 需 Python 依赖管理（jsonschema / pyyaml）

---

## 7. 备选方案

### 备选 A：把评估内嵌到每个 skill 自身

- 拒绝理由：① 重复实现 N 套评估 ② rubric 无法统一 ③ 跨 skill 不可比
- **否决**

### 备选 B：纯人工评估 + 表格记录

- 拒绝理由：① 不可重放 ② 不可自动化 ③ 不可被 CI 消费
- **否决**

### 备选 C：复用某个外部评估库（如 promptfoo、inspect）

- 拒绝理由：① 与 zeng-skills 自有 skill 协议不通 ② 强依赖外部工程 ③ Rubric 体系不通用
- **暂否决**（v3+ 可考虑通过适配层引入）

### 备选 D：仅实现"评估 SKILL.md 自身"的窄定义版本

- 拒绝理由：① 价值局限于 skill 治理，无法覆盖 agent run、文档、代码 diff
- **否决**（但 v1 优先落地 skill-design 维度，作为示范）

---

## 8. 实施路径

### 8.1 落地步骤

| 步骤 | 内容 | 状态 |
|------|------|------|
| 1 | 起 SKILL.md + 7 份 schema/rubric/agent/example 资产 | ✅ 本 ADR |
| 2 | validate.py 落地（schema 校验 + baseline promote） | ✅ 本 ADR |
| 3 | 起 ADR-006（本文档） | ✅ 本 ADR |
| 4 | README 增加 zeval-skill 入口、badge 改 8→9 | 🔜 |
| 5 | 实测：用 zeval-skill 评估 zdoc-i2i 的 SKILL.md，验证 end-to-end 可行 | ⏳ |
| 6 | 补全 `document.v1` / `agent-run.v1` rubric | ⏳ v1.x |
| 7 | zdoc-quality-loop 接入 zeval-skill 作为"评审阶段" | ⏳ v1.x |
| 8 | zcode-review-deep 接入 zeval-skill 做元评估 | ⏳ v1.x |

### 8.2 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| R1. LLM 评审不稳定 | 同 input 跑两次分差大 | 多 judge 取均 + replay seed + 记录 model 版本 |
| R2. Rubric 漂移 | 改后历史 baseline 不可比 | 强制语义版本 + baseline 绑定版本 |
| R3. 评估成本膨胀 | N judge × M 维度 → token 爆炸 | max_parallel 控制 + rubric 可关 judge |
| R4. 证据链"伪造" | Judge 编造 line number | v2 引入 evidence ref 自动回查 |
| R5. 评估=评价偏好 | 用户把 eval 结果当真理 | SKILL.md / 文档明确"eval 是辅助判断，不是真理" |

### 8.3 开放问题

- **Q1**. eval 自身用哪个模型？倾向"跟随宿主"（D1 已隐含）
- **Q2**. human_in_loop 的物理形态？v1 通过 PR 评论/留 review notes；v2 考虑 web UI
- **Q3**. 多轮对话的 turn 边界如何切分？倾向按 user turn 切
- **Q4**. Rubric 是否允许继承？倾向支持 `extends: skill-design.v1`
- **Q5**. 评估报告保留多久？默认永久；超 1GB 触发归档压缩
- **Q6**. eval 自身有 meta-eval 吗？v1 不做；v2 引入"judge 一致性指标"

---

## 9. 演进路径

### v1.0（当前）— 单 rubric + 同步执行

- ✅ Skill 设计、agent run、文档 三类 Target
- ✅ 1 个生产 rubric（`skill-design.v1`）
- ✅ validate.py 落地
- ⏳ 实测 end-to-end

### v1.x — 多 rubric + 编排接入

- 补全 `document.v1` / `agent-run.v1` / `code-diff.v1`
- zdoc-quality-loop / zcode-review-deep 接入
- 引入 human_in_loop 显式 PR 评论通道

### v2.0 — 元评估 + 流式

- 引入"judge 一致性指标"
- 流式中间态
- evidence ref 自动回查
- Rubric 继承机制

### v3.0 — 外部适配（备选）

- 通过适配层接入 promptfoo / inspect / lm-eval-harness
- 与外部 benchmark 对齐

---

## 10. 实施入口

- **设计文档**：本文档
- **Skill 目录**：[`skills/zeval-skill/`](../skills/zeval-skill/SKILL.md)
- **Schema 入口**：[`schemas/EvalRequest.schema.json`](../skills/zeval-skill/schemas/EvalRequest.schema.json)
- **第一个生产 rubric**：[`rubrics/skill-design.v1.yaml`](../skills/zeval-skill/rubrics/skill-design.v1.yaml)
- **校验脚本**：[`validate.py`](../skills/zeval-skill/validate.py)
- **关联 ADR**：ADR-001（Deep Code Review，zcode-review-deep v1.1 简化范式参考）

---

*文档版本：v1.0*
*创建日期：2026-06-10*
*更新日期：2026-06-10*
