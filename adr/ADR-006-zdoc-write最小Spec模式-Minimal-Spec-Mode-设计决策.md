---
title: "zdoc-write 最小 Spec 模式设计决策"
doc_id: "ADR-006"
status: draft
created: "2026-06-15"
updated: "2026-06-15"
doc_type: spec
module_id: "zdoc-write"
related_docs:
  - "../skills/zdoc-write/SKILL.md"
  - "../skills/zdoc-write/templates/document.md"
  - "../skills/zdoc-write/templates/decision-summary.md"
  - "../skills/zdoc-write/templates/minimal-spec.md"
  - "../skills/zdoc-write/templates/review-card.md"
  - "../skills/zdoc-write/references/doc-type-requirements.md"
  - "../docs/DOC-WRITING-GUIDE.md"
  - "../docs/ITERATION-DOCUMENT-CHECKLIST.md"
---

# ADR-006：zdoc-write 最小 Spec 模式设计决策

# Goal

`zdoc-write` 当前默认倾向生成完整 SSOT 文档，容易把 PRD、API、TECH、TESTSET、实现设计和评审摘要混在一起。

在 Agent 协作、人类审核、AI 实施场景中，默认文档目标应改为：

```text
人类 3 分钟能审核，AI 能稳定执行，长期维护成本低。
```

本 ADR 决定：`zdoc-write` 在用户未显式指定详细文档类型时，默认生成 **Minimal Spec**，只保存长期有价值的业务意图、边界、规则、约束和验收标准。

# Scope

## In Scope

- 约束 `zdoc-write` 的默认写作模式。
- 新增 `spec` 作为默认文档类型。
- 定义 Minimal Spec 的最小结构、禁止项、长度限制和 Review Card。
- 明确详细 SSOT 文档类型继续保留，但必须显式 opt-in。
- 明确 AI 不得把自行推断的关键业务内容写成正式事实。

## Out of Scope

- 不废弃现有 `prd/api/tech/testset/data/ddd/skill/adapter/job/impl` 等详细文档能力。
- 不在本 ADR 中重写 `zdoc-write` 的完整实现流程。
- 不定义 API、数据库、类、函数或任务拆解细节。
- 不替代 `zdoc-design-check`、`zdoc-i2i`、`zdoc-quality-loop` 的职责。
- 不直接批准新的 SSOT 目录；`docs/mvp-lite/specs/` 需先进入 `DOC-WRITING-GUIDE`。

# Context Diagram

```text
用户输入 / 需求讨论
        ↓
zdoc-write
        ↓
Minimal Spec（默认）
        ↓
人类 3 分钟审核
        ↓
AI 实施 / 详细 SSOT 文档（按需生成）
```

# Business Rules

R1

当用户未显式指定文档类型时，`zdoc-write` 默认生成 `spec`，不得根据输入中出现的技术词自动推断为 `prd`、`api`、`tech` 或 `testset`。

R2

类型识别优先级固定为：类型代码前缀 > 用户明确要求某类详细文档 > 默认 `spec`。

明确 opt-in 信号包括：

| 用户表达 | 类型 |
|----------|------|
| `api`、`API 契约`、`接口文档`、`端点定义` | `api` |
| `tech`、`技术设计`、`实现设计` | `tech` |
| `testset`、`测试用例集`、`测试策略文档` | `testset` |
| `prd`、`完整 PRD`、`产品需求文档` | `prd` |
| `arch`、`架构设计` | `arch` |
| `ux`、`UX 规范`、`交互规范` | `ux` |

非 opt-in 信号：普通需求中提到“可能需要 API / 数据库 / 测试 / 技术方案”，仍默认 `spec`。

R3

Minimal Spec 固定结构为：

```markdown
# Goal
# Scope
# Context Diagram
# Business Rules
# Constraints
# Acceptance
# Risks（可选）
```

R4

Minimal Spec 只保存长期资产：目标、边界、规则、约束、验收和风险；不得混入一次性实现方案。

R5

所有现有详细文档类型继续支持，包括 `req/business/prd/ux/ux-proto/api/arch/tech/testset/data/ddd/skill/adapter/job/stg/review/impl`，但只有用户显式指定时才生成。

支持类型的调整方案如下：

| 类型 | 调整方案 |
|------|----------|
| `spec` | 新增默认类型；输出 Minimal Spec。 |
| `req` | 保留为需求来源文档；不承载 PRD、AC、API 或实现方案。 |
| `business` | 保留为商业设计；压缩为目标、用户、范围、指标、风险，成本/JTBD/漏斗为可选。 |
| `prd` | 保留为完整 PRD；默认不再由普通需求自动推断生成。 |
| `ux` | 保留为 UX 规范；普通 Spec 只保留用户可见流程和状态约束。 |
| `ux-proto` | 保留为显式原型输出；不参与 Minimal Spec 默认流程。 |
| `api` | 保留为 API Contract；仅显式要求接口/契约/端点时生成。 |
| `arch` | 保留为架构设计；仅显式要求架构方案时生成。 |
| `tech` | 保留为 Technical Design；从默认 Spec 中移除实现细节。 |
| `testset` | 保留为测试策略与用例集；Minimal Spec 中只保留 Acceptance。 |
| `data` | 保留为数据流/数据契约；Minimal Spec 只记录数据边界和不可违反约束。 |
| `ddd` | 保留为领域设计；不进入默认 Spec。 |
| `skill` | 保留为 AI Skill 设计；不进入默认 Spec。 |
| `adapter` | 保留为外部适配器契约；不进入默认 Spec。 |
| `job` | 保留为后台任务设计；不进入默认 Spec。 |
| `stg` | 保留为战略/商业宪法；不由普通功能需求自动生成。 |
| `review` | 保留为审查与对齐报告；不作为 Spec 默认输出。 |
| `impl` | 保留为实施设计；必须显式指定，且不得混入 Minimal Spec。 |

R6

AI 可以补格式、整理表达、提出问题；不得把自行推断的 Goal、Scope、Business Rules、Constraints、Acceptance 写成正式事实。

R7

缺失关键内容时的处理规则：

| 缺失内容 | 处理方式 |
|----------|----------|
| Goal | 停止并询问 |
| Scope | 在 Review Card 提问，不生成默认范围 |
| Context Diagram | 仅根据用户明确提供的实体关系绘制；不足时写 `未提供足够上下文` |
| Business Rules | 列出需要补充的问题，不写入正式规则 |
| Constraints | 可放入 Review Card 的 `AI 假设`，不写入正式约束 |
| Acceptance | 可放入 Review Card；如写入正文，只能作为 `# Acceptance` 下的 `Draft` 小节，不能新增顶级章节 |

R8

Review Card 替代默认的重型 decision summary，最多 1 页，最多 3 个待确认决策、5 个假设、5 个风险。

# Constraints

C1

Minimal Spec 中禁止出现：

```text
类设计
函数设计
伪代码
数据库表设计
接口定义
任务拆解
实现步骤
技术选型细节
```

C2

Minimal Spec 长度限制：小需求 ≤ 1 页，中需求 ≤ 3 页，大需求 ≤ 5 页；超过限制应拆分或转为显式详细文档。

C3

Minimal Spec 的建议正式目录为：

```text
docs/mvp-lite/specs/
```

但在 `DOC-WRITING-GUIDE` 未正式新增该目录前，`zdoc-write` 不得擅自创建新的 SSOT 目录；只能写入用户显式指定的 `--output-dir`。

如果用户未提供 `--output-dir`，`zdoc-write` 必须先询问输出目录，或只在对话中返回 Minimal Spec 草案，不写文件。

C4

Minimal Spec 文件命名建议为：

```text
SPEC-M{编号}-{Slug}.md
```

Review Card 命名建议为：

```text
.zdoc-write/SPEC-M{编号}-{Slug}-review-card.md
```

C5

Minimal Spec frontmatter 默认只保留必要治理字段：

```yaml
---
title: "{中文标题}"
doc_id: "SPEC-M{编号}-{Slug}"
status: draft
created: "{YYYY-MM-DD}"
updated: "{YYYY-MM-DD}"
doc_type: spec
module_id: "{Mxx}"   # 非模块级 Spec 可省略
related_docs: []
---
```

`layer`、`priority`、`relationships`、`context_policy` 仅在提升为正式 SSOT 或上下文装配需要时补齐。

C6

Minimal Spec 使用短英文 canonical headings 是 `DOC-WRITING-GUIDE` “章节标题中文为主”的例外；该例外用于提升 Agent 读取稳定性。

C7

`zdoc-write` 对 `DOC-WRITING-GUIDE` 的引用必须指向当前实际路径：

```text
docs/DOC-WRITING-GUIDE.md
```

# Acceptance

A1

用户输入普通需求、功能想法、业务规则或讨论结论，且未指定类型时，`zdoc-write` 输出 Minimal Spec。

A2

用户显式指定 `api`、`tech`、`testset`、`prd` 等类型时，`zdoc-write` 仍可生成对应详细 SSOT 文档。

A3

Minimal Spec 只包含 Goal、Scope、Context Diagram、Business Rules、Constraints、Acceptance、Risks，不包含实现设计、伪代码、接口定义或任务拆解。

A4

缺失 Goal 时，`zdoc-write` 必须停止并询问，不生成 Minimal Spec；缺失 Scope、Business Rules、Constraints、Acceptance 时，只能提问、放入 Review Card，或在允许位置标为草案，不把 AI 推断内容写成正式事实。

A5

Review Card 控制在 1 页内，并明确列出：需要确认的决策、AI 假设、主要风险、是否可进入 AI 实施。

A6

`zdoc-write` 的文档路径引用修正为 `docs/DOC-WRITING-GUIDE.md`。

A7

在 `DOC-WRITING-GUIDE` 批准 `specs/` 目录前，Minimal Spec 只能输出到用户显式指定目录；如果没有指定目录，必须询问用户或仅返回对话内草案。

# Risks

风险1

默认改为 Minimal Spec 后，单次生成的信息量会减少；部分场景需要二次生成 API、TECH 或 TESTSET。

风险2

下游 `zdoc-design-check`、`zdoc-i2i`、`zdoc-quality-loop` 需要识别 Minimal Spec 与详细 SSOT 的差异，否则可能误判“缺少完整工程文档”。

风险3

如果 `docs/mvp-lite/specs/` 未及时进入 `DOC-WRITING-GUIDE`，`spec` 类型会存在输出目录不稳定的问题。

风险4

如果实现时仍保留“必填章节不跳过”的旧规则，Minimal Spec 会被重新膨胀为完整 SSOT 文档。
