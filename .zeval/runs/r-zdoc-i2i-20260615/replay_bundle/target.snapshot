---
name: zdoc-i2i
description: "设计文档到实施任务转化引擎。输入 15+ 种设计文档（PRD/Arch/API/UX/Tech/Test/Data/DDD/...），源文档交叉一致性校验 → 内容整合 → 按最小可验收颗粒度拆分 Task → 交付前自动审核 → 产出独立 impl 文档 + 依赖 DAG + 交付报告。纯 LLM + 结构化输出架构。"
argument-hint: "[--dir DIR] [--feature ID] [--prd PATH] [--arch PATH] [--api PATH] [--ux PATH] [--tech PATH] [--test PATH] [--data PATH] [--ddd PATH] [--output-dir DIR] [--validate-only]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---

# zdoc-i2i

Design-to-Impl Skill — 将设计文档转化为可执行的实施任务。纯 LLM + 结构化输出架构，复用 Design Check Gate Rubric 做输入校验。

## Primary Abstraction

Skill (governed capability template)

## Secondary Abstraction

Pipeline — LLM 4-phase validation + integration + decomposition + generation

## Authority

Canonical bundle: `zdoc-i2i/`

## Not Equal To

- Not a document editor（只读取设计文档，不修改任何输入文件）
- Not a code generator（产出实施计划文档，不产出代码）
- Not a gate decision maker（evidence-only，汇总报告供人工确认）
- Not a replacement for `zdoc-design-check`（Design Check 校验质量，I2I 做实施转化）

## Canonical Authority

- ADR: ADR-004 v1.7（设计文档到实施任务拆分技能 — I2I Design-to-Impl Skill）
- Reference: `DOC-WRITING-GUIDE v1.0` (输出文档结构规范 — frontmatter / 标准章节 / 命名 / 交叉引用)

## Runtime Boundary Baseline

This capability is a governed `Skill` for `Design Documents → Implementation Tasks` transformation.

- **Read-only** — does NOT modify source design documents.
- **只整合不补充** — does NOT invent features, tech solutions, or business rules not in input docs.
- **最小可验收颗粒度** — each Task must satisfy 5 conditions (§3.4 of ADR-004).
- **上下文自包含** — each Task impl doc is independently executable.
- **DAG 确定性校验** — cycle detection via `validate-dag.py`, not LLM.
- **文档状态准入** — only accepts `approved` or `frozen` status documents; `draft` / `reviewing` → BLOCK.
- **执行后冻结** — successful execution sets all input documents to `frozen` status.

---

## 架构

```text
┌─────────────────────────────────────────────────────────────────────┐
│              I2I — 设计文档 → 实施任务 转化引擎                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Phase 0: 源文档交叉一致性校验                                       │
│  ──────────────────────────────────────────                         │
│  1. ARCH ↔ TESTSET 交叉扫描（数量/语义/路径/版本）                    │
│  2. 约束溯源图构建                                                   │
│  3. 术语/命名预扫描                                                  │
│  4. BLOCK → 要求源文档澄清后重跑                                     │
│                                                                     │
│  Phase 1: 输入校验（内嵌 Gate Rubric）                               │
│  ──────────────────────────────────────────                         │
│  1. 识别输入文档类型（15+ 种）                                       │
│  2. 校验必输要素 → BLOCK / CONDITIONAL / PASS                       │
│  3. BLOCK → 返回缺失清单，停止                                       │
│                                                                     │
│  Phase 2: 内容整合                                                  │
│  ──────────────────────────────────────────                         │
│  按 Feature 聚合跨文档信息 → feature-context.md                      │
│                                                                     │
│  Phase 3: 任务拆分                                                  │
│  ──────────────────────────────────────────                         │
│  最小可验收颗粒度拆分 → task-list.json → validate-dag.py             │
│  → 依赖完整性校验 → dependency-suggestions.json                      │
│                                                                     │
│  Phase 4: 文档生成                                                  │
│  ──────────────────────────────────────────                         │
│  task-*.md + INDEX.md + SUMMARY.md + IMPL-INDEX.md                  │
│                                                                     │
│  Phase 5: 交付前审核 + 交付报告                                      │
│  ──────────────────────────────────────────                         │
│  自动审核清单 → delivery-report.json                                 │
│                                                                     │
│  输入: 设计文档路径                                                   │
│  输出: impl-{feature}-{PRD-ID}/ 目录 + delivery-report.json         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase 0: 源文档交叉一致性校验

> **执行步骤**：
> 1. 识别所有已识别的输入文档对（ARCH ↔ TESTSET、ARCH ↔ PRD、API ↔ TECH 等）
> 2. 执行交叉一致性扫描（§0.1），记录冲突项
> 3. 构建约束溯源图（§0.2），记录 §11 门槛与 §4/§5/§8 具体约束的对应关系
> 4. 执行术语/命名预扫描（§0.3），检查 API 名称版本标注
> 5. 执行原型文件检测与索引（§0.6），建立 UX Spec ↔ Prototype 映射
> 6. 输出 `source-consistency-report.json`
> 7. 任一 BLOCK 级冲突 → 要求源文档澄清后重跑，不进入 Phase 1
> 8. 仅 WARN → 记录到报告，带标注进入 Phase 1

### 0.1 交叉一致性扫描

扫描以下维度：

| 扫描维度 | 检查方法 | 阻断级别 |
|----------|----------|----------|
| **数量一致性** | 扫描 ARCH §11 门槛表中的数字（约束条数、接入点数等）与 TESTSET 中对应的细化数字是否匹配 | BLOCK |
| **语义明确性** | 检查表格中同一行是否包含多个语义不同的值（如 401 和 503 写在同一行） | BLOCK |
| **例外显式化** | 检查"排除项"或"例外"是否在 ARCH 中有显式批准声明 | WARN |
| **路径一致性** | 检查 ARCH 和 TESTSET 中的文件路径是否一致（如 `src/handlers/` vs `src/lib/handlers/`） | BLOCK |
| **版本一致性** | 检查两份文档对同一依赖的版本号表述是否一致 | BLOCK |
| **PRD↔TECH/ARCH ENUM 值集合对齐** | 提取 PRD 中所有 ENUM 定义（含正文中描述的枚举值），与 TECH/ARCH 中的 ENUM 定义逐字段比对。PRD 为权威源 | **FAIL** |
| **PRD↔TECH/ARCH 数值常量对齐** | 扫描所有源文档（含 ASCII 流程图）中的数值型描述（长度、金额、时间、档位数），以 PRD FR 定义为准 | **FAIL** |
| **PRD↔TECH 字段存在性对齐** | 提取 PRD 中引用的所有字段名，检查是否在 TECH 数据模型中定义（或明确标记为已移除） | WARN |
| **TECH 编码格式对齐** | 检查 TECH 中同一字段的标题描述与实际映射表/API 是否一致（如复合格式描述 vs 简单枚举） | WARN |

### 0.2 约束溯源图构建

记录 §11 门槛与具体约束的映射关系：

```
§11 门槛 N → 对应 §X.Y 具体约束 → TESTSET 测试点编号
```

**作用**：
- 当 TESTSET 细化约束时（如 4 条 → 7 条），溯源图能自动检测 ARCH §11 是否需要同步更新
- 拆解出的 task acceptance criteria 可以自动携带溯源链，避免约束丢失

### 0.3 术语/命名预扫描

| 模式 | 检查方法 | 示例 |
|------|----------|------|
| 版本相关 API 名 | 检查 API 名称是否标注了适用版本 | `toDataStreamResponse()` 应标注为 3.x 兼容 |
| 废弃 API 引用 | 检查是否引用了已废弃的 API | `StreamingTextResponse` 在 4.x 中废弃 |
| 命名空间一致性 | 检查同一模块在不同位置的路径是否一致 | `src/handlers/` vs `src/lib/handlers/` |

### 0.4 源代码路径规范化

> **问题**：设计文档中可能使用简写路径（如 `src/handlers/`），但实际项目源代码位于更深层级（如 `apps/ai-coach-skill/src/handlers/`）。如果 Task 文档中沿用简写路径，Agent 执行时可能在项目根目录错误创建 `src/` 目录。

**执行步骤**：

1. 如果指定了 `--src` 参数，将其作为**源代码根路径基准**
2. 从设计文档（Architecture / Tech Design）中提取所有引用的源代码文件路径
3. 对每个路径执行规范化：
   - 如果路径以 `src/` 开头且 `--src` 指定了更深层级（如 `apps/ai-coach-skill/src`），将路径前缀替换为完整路径
   - 例如：`src/handlers/register.ts` → `apps/ai-coach-skill/src/handlers/register.ts`
4. 将规范化后的路径记录到 `source-consistency-report.json` 的 `path_normalization` 字段
5. 后续 Phase 4 生成 Task 文档时，所有文件路径必须使用**项目根目录相对路径**（非简写）

**路径规范化规则**：

| 场景 | 输入路径 | `--src` 值 | 规范化结果 |
|------|---------|-----------|-----------|
| 标准前缀替换 | `src/handlers/` | `apps/ai-coach-skill/src` | `apps/ai-coach-skill/src/handlers/` |
| 无 `--src` | `src/handlers/` | — | `src/handlers/`（保持原样，视为项目根相对） |
| 已是完整路径 | `apps/ai-coach-skill/src/` | `apps/ai-coach-skill/src` | `apps/ai-coach-skill/src/`（不变） |
| 部分匹配 | `lib/utils.ts` | `apps/ai-coach-skill/src` | `lib/utils.ts`（不匹配 src 前缀，保持原样） |

**用途**：此规范化结果写入 `source-consistency-report.json`，Phase 4 读取并应用到所有 Task 文档的"关键文件"和"产出物"路径中。

### 0.6 原型文件检测与索引

> **问题**：设计文档（如 UX Spec）可能引用 HTML/原型文件作为视觉和交互的参考源，但任务拆分时往往只间接引用 UX Spec，丢失了原型的直接引用链，导致实施者不知道有原型可参考。

**执行步骤**：

1. 扫描 `ux-prototypes/` 目录下的所有非 Markdown 文件（HTML、Vue、React 等可运行原型）
2. 对每个原型文件，提取其覆盖的交互阶段/Phase/模块信息（通过文件名、目录结构或文件内注释）
3. 将原型文件路径与 UX Spec 文档的 `references` 字段交叉比对，建立 UX Spec ↔ Prototype 映射关系
4. 记录到 `source-consistency-report.json` 的 `prototype_index` 字段
5. 后续 Phase 3 拆分 UI 相关 Task 时，自动注入对应原型的直接引用

**原型识别规则**：

| 模式 | 检查方法 | 示例 |
|------|----------|------|
| 文件扩展名 | `ux-prototypes/` 下的 `.html`、`.vue`、`.jsx`、`.tsx` 文件 | `proto-m12-onboarding.html` |
| UX Spec 引用 | UX Spec frontmatter 的 `references` 字段指向的原型路径 | `references: docs/mvp-lite/ux-prototypes/proto-m12-onboarding.html` |
| 目录约定 | 原型文件放在 `ux-prototypes/` 目录下 | `ux-prototypes/proto-*.html` |

**原型阶段映射**：

对 HTML 等可运行原型，提取其内部注释或 DOM 结构中标注的 Phase/阶段划分（如 `<!-- PHASE B: 表单填写 -->`），建立「原型阶段 → 对应 UX Spec 章节 → 对应 Task」的三层映射。

### 0.5 输出 source-consistency-report.json

```json
{
  "feature_id": "ARCH-LITE-XXX",
  "generated_at": "...",
  "status": "PASS | FAIL | WARN",
  "consistency_checks": [
    {
      "dimension": "quantity_consistency",
      "status": "PASS | FAIL",
      "details": "..."
    }
  ],
  "prd_tech_alignment": {
    "enum_checks": [
      {
        "field": "gender",
        "prd_source": "PRD-M12 FR-M12-001 L378",
        "prd_values": ["male", "female"],
        "tech_source": "TECH-M12 §2.3.1",
        "tech_values": ["male", "female", "other"],
        "arch_source": "ARCH-M12 L136",
        "arch_values": ["male", "female", "other", "prefer_not_to_say"],
        "status": "FAIL",
        "resolution": "以 PRD 为准，TECH/ARCH 移除 extra values"
      }
    ],
    "numeric_checks": [
      {
        "concept": "邀请码长度",
        "prd_value": "8位",
        "prd_source": "PRD-M12 FR-M12-001 L378",
        "discrepancies": [
          { "doc": "BUSINESS-M12 L114", "value": "6位", "location": "ASCII 流程图" }
        ],
        "status": "FAIL"
      }
    ],
    "field_existence_checks": [
      {
        "field": "pain_impact_level",
        "prd_referenced": true,
        "prd_location": "PRD-M12 Open Questions #5 L786",
        "tech_defined": false,
        "status": "WARN",
        "resolution": "stale discussion in PRD, field removed in v3.0"
      }
    ],
    "encoding_format_checks": [
      {
        "field": "injury_selections",
        "tech_header": "{body_part}_{injury_type}_{severity}",
        "tech_mapping_table": ["none", "knee", "ankle_foot", "hip_back", "illness_recovery", "doctor_advice", "other"],
        "api_values": ["none", "knee", "ankle_foot", "hip_back", "illness_recovery", "doctor_advice", "other"],
        "status": "WARN",
        "resolution": "TECH header is design-level description, API enum values are canonical"
      }
    ]
  },
  "constraint_traceability": [
    {
      "gate_id": "§11 N",
      "source_section": "§X.Y",
      "test_points": ["HP-01", "BC-01"]
    }
  ],
  "naming_issues": [],
  "path_normalization": {
    "src_base": "apps/ai-coach-skill/src",
    "normalized_paths": [
      {
        "original": "src/handlers/register.ts",
        "normalized": "apps/ai-coach-skill/src/handlers/register.ts"
      }
    ]
  },
  "prototype_index": [
    {
      "file": "ux-prototypes/proto-m12-onboarding.html",
      "type": "html",
      "phases": [
        {
          "phase_id": "PHASE-A",
          "description": "邀请码验证",
          "ux_spec_section": "UX-M12 §3.1"
        },
        {
          "phase_id": "PHASE-B",
          "description": "5题身份建档表单",
          "ux_spec_section": "UX-M12 s9.3"
        }
      ],
      "referenced_by": ["UX-M12-Onboarding-Identity.md"]
    }
  ]
}
```

---

## Phase 1: 输入校验

> **执行步骤**：
> 1. 解析 `{{args}}`，确定输入模式（目录扫描 / 显式指定 / 混合）
> 2. 使用 Glob 扫描输入目录，按§1.4 优先级识别文档类型
> 3. **检查文档状态**（§1.7），仅接受 `approved` / `frozen`，`draft` / `reviewing` → BLOCK
> 4. 对每个已识别文档执行 Gate 校验（§1.5），记录 PASS / WARN / FAIL
> 5. 必输文档（T01 PRD、T02 Arch）缺失 → BLOCK，输出缺失清单并停止
> 6. 汇总判定三态（§1.6），CONDITIONAL 时记录 WARN 项
> 7. 如有 `--validate-only`，输出校验结果后停止

### 1.1 输入模式

根据参数组合确定输入模式：

| 模式 | 触发条件 | 行为 |
|------|---------|------|
| **目录扫描** | `--dir` | 扫描目录下所有文档，自动识别类型（推荐） |
| **显式指定** | `--prd` / `--arch` / `--api` 等 | 仅处理指定路径的文档 |
| **混合** | `--dir` + `--prd` 等 | 目录扫描 + 指定路径覆盖 |

### 1.2 文档类型优先级

文档分为**必输**和**可选**两类：

| 优先级 | 文档类型 | 必输/可选 | 说明 |
|--------|---------|----------|------|
| T01 | PRD | **必输** | 用户故事、AC、业务规则 |
| T02 | Architecture | **必输** | 技术选型、分层、模块边界 |
| T03 | API Design | 可选 | 端点定义、Schema、错误码 |
| T04 | Business Design | 可选 | 用户画像、业务价值 |
| T05 | Tech Design | 可选 | 时序图、集成点、降级策略 |
| T06 | UX Spec | 可选 | 交互流程、状态表达、文案 |
| T07 | UX Prototype | 可选 | 设计系统、组件规范、交互原型（含 HTML 原型） |
| T08 | Test Design | 可选 | 测试用例、边界条件 |
| T09 | Data Flow | 可选 | 数据流转、状态机 |
| T10 | DDD | 可选 | 领域模型、聚合根 |
| T11 | Skill Design | 可选 | Skill 定义、Prompt |
| T12 | Adapter Design | 可选 | 外部系统适配 |
| T13 | Job Design | 可选 | 异步任务、定时任务 |
| T14 | Strategy | 可选 | 战略规划、产品定位 |
| T15 | Review | 可选 | 审查结论、对齐意见 |

> **必输文档缺失 → BLOCK**；可选文档缺失 → 跳过，不影响判定。

### 1.3 解析参数

从 `{{args}}` 解析以下参数：

| 参数 | 说明 |
|------|------|
| `--dir` | 设计文档目录（自动扫描） |
| `--feature` | 仅处理指定 Feature ID（如 `M01`） |
| `--prd` | 指定 PRD 文件路径 |
| `--arch` | 指定 Architecture 文件路径 |
| `--api` | 指定 API Design 文件路径 |
| `--ux` | 指定 UX Spec 文件路径 |
| `--tech` | 指定 Tech Design 文件路径 |
| `--test` | 指定 Test Design 文件路径 |
| `--data` | 指定 Data Flow 文件路径 |
| `--ddd` | 指定 DDD 文件路径 |
| `--src` | 项目源代码根路径（如 `apps/ai-coach-skill/src`），确保所有文件路径使用项目根相对路径 |
| `--output-dir` | 输出目录（默认 `docs/mvp-lite/impl`） |
| `--validate-only` | 仅校验，不生成 Task |

### 1.4 文档发现与类型识别

使用 Glob 工具扫描输入目录，按以下优先级识别文档类型：

```
识别优先级: 文件名前缀 > 目录路径 > 内容特征

1. 文件名前缀匹配（最高优先级）
   PRD-*     → T01  ARCH-*    → T02  API-*     → T03
   BUSINESS-*→ T04  TECH-*     → T05  UX-*      → T06
   TESTSET-* → T08  DataFlow-* → T09  DDD-*     → T10
   SKILL-*   → T11  ADAPTER-*  → T12  JOB-*     → T13

2. 目录路径匹配（次优先级）
   prds/      → T01  arch/      → T02  api/       → T03
   business/  → T04  tech/      → T05  ux/        → T06
   ux-prototypes/ → T07  testset/ → T08  data/    → T09
   ddd/       → T10  skills/    → T11  adapters/  → T12
   jobs/      → T13  stg/       → T14  reviews/   → T15

3. 内容特征匹配（兜底）
   含用户故事/AC          → T01  含架构分层/技术选型 → T02
   含 API 端点/Schema     → T03  含交互流程/设计原则 → T06
   含设计系统/组件规范     → T07  含测试范围/Happy Path  → T08
   含领域模型/聚合根      → T10  含数据流转/状态机  → T09
```

### 1.5 Gate 校验（内嵌 Gate Rubric）

读取 `gate/rubric.md`，对每个已识别的文档执行以下校验：

| Gate ID | 检查项 | PASS 条件 | WARN 条件 | FAIL 条件 |
|---------|--------|----------|----------|----------|
| **G1** | 文档存在性 | 文件存在 + 大小 > 100 字节 + 不含占位符 + H2 ≥ 3 | — | 文件不存在或含占位符或 H2 < 3 |
| **G2** | 决策可追溯性 | 关键决策有"依据"/"基于"/"参考"或标注"暂定" | 有依据但未标注是否暂定 | 无任何依据说明 |
| **G3** | 异常覆盖度 | 错误码 + 系统行为 + 用户感知 三层均有 | 错误码存在但无用户端描述 | 仅写"错误处理"无细节 |
| **G4** | 可测试性 | 至少 1 条 AC 含 Given/When/Then 或可观察指标 | AC 有指标但无可观察阈值 | 全部 AC 无结构 |
| **G5** | 一致性 | 同一概念在不同文档中名称和数值一致 | 同义词表述但含义相同 | 名称不同导致歧义 |

### 1.6 三态判定

对每个文档的 Gate 结果做汇总判定：

| 判定 | 条件 | 行为 |
|------|------|------|
| **BLOCK** | 任一文档有 Gate FAIL | 输出缺失清单到 stdout，停止执行。不补充任何新内容 |
| **CONDITIONAL** | 有 WARN 但无 BLOCK | 记录 WARN 项，带标注继续 Phase 2 |
| **PASS** | 所有文档 Gate PASS | 直接进入 Phase 2 |

如果判定为 BLOCK，输出格式：

```markdown
## 输入校验失败 — BLOCK

以下文档缺失必输要素，无法进入实施转化：

| 文档 | 类型 | 缺失项 |
|------|------|--------|
| {filename} | {type} | {missing_items} |

请补充上述文档后重新执行。
```

如果判定为 CONDITIONAL，记录 WARN 项并在后续 SUMMARY.md 中呈现。

如果 `--validate-only`，到此停止，输出校验结果。

### 1.7 文档状态检查

在 Gate 校验之前，先检查每个输入文档的状态：

| 状态 | 说明 | I2I 行为 |
|------|------|---------|
| **approved** | 文档已通过评审 | 接受，标记待 frozen |
| **frozen** | 文档已锁定 | 接受，保持不变 |
| **draft** | 尚在编写中 | **BLOCK** — 提示文档需先通过评审 |
| **reviewing** | 正在评审中 | **BLOCK** — 提示文档需先通过评审 |

**状态识别规则**（按优先级）：

1. 文档 frontmatter 中的 `status` 字段：`status: approved`
2. 文档头部的状态标记：`**Status**: approved` 或 `**状态**: 已批准`
3. 文件名中的状态后缀：`PRD-M01.approved.md`
4. 以上均无 → 默认视为 `draft`，BLOCK

如果文档状态检查失败，输出格式：

```markdown
## 输入校验失败 — BLOCK（文档状态）

以下文档状态不符合要求，无法进入实施转化：

| 文档 | 当前状态 | 需要状态 |
|------|---------|---------|
| {filename} | {current_status} | approved 或 frozen |

请将文档通过评审后重新执行。
```

---

## Phase 2: 内容整合

> **执行步骤**：
> 1. 从 PRD 中识别 Feature（按用户故事前缀 / Milestone 编号 / 文件名）
> 2. 对每个 Feature，从各类型文档中提取相关信息（§2.1 映射表）
> 3. 从 PRD 中提取 Out of Scope 列表（§2.2）
> 4. 为每个 Feature 生成 `feature-context.md`（模板见 `templates/feature-context.md`）

### 2.1 按 Feature 聚合

从已识别的文档中，按 Feature（功能特性）聚合跨文档信息。Feature 的识别规则：

1. PRD 中的用户故事编号前缀（如 `US-M01-*` → Feature M01）
2. PRD 中的 Milestone 编号
3. 文件名中的 Feature ID（如 `PRD-M01-*.md` → M01）

对每个 Feature，从各类型文档中提取相关信息：

| 文档类型 | 提取什么 | 用于 Task 的哪个部分 |
|---------|---------|-------------------|
| T01 PRD | 用户故事、AC、业务规则、优先级、Out of Scope | Task 描述、验收标准、优先级、排除项 |
| T02 Architecture | 技术选型、分层、模块边界 | 技术约束、架构分层要求 |
| T03 API Design | 端点定义、Schema、错误码 | 接口契约、数据结构、异常处理 |
| T04 Business Design | 用户画像、业务价值、成功指标 | 需求背景、验收指标 |
| T05 Tech Design | 时序图、同步/异步、集成点、降级策略 | 实现细节、集成要求、异常处理 |
| T06 UX Spec | 交互流程、状态表达、文案、平台差异 | UI 实现要求、交互细节 |
| T07 UX Prototype | 设计系统、组件规范 | UI 组件要求、样式约束 |
| T08 Test Design | 测试用例、边界条件、Mock 需求 | 验收标准、测试验证点 |
| T09 Data Flow | 数据流转、状态机、数据依赖 | 数据模型约束、状态转换规则 |
| T10 DDD | 领域模型、聚合根、值对象 | 领域边界、数据模型设计 |
| T11 Skill Design | Skill 定义、Prompt、工具链 | AI 能力约束 |
| T12 Adapter Design | 外部系统适配、数据转换 | 集成层实现、数据映射 |
| T13 Job Design | 异步任务、定时任务、队列 | 后台任务实现、调度策略 |
| T14 Strategy | 战略规划、产品定位 | 需求优先级、产品方向约束 |
| T15 Review | 审查结论、对齐意见 | 跨文档一致性参考 |

### 2.2 Out of Scope 标注

从 PRD 中提取 Out of Scope 列表（BD-4），明确标注哪些内容**不纳入**后续 Task 拆分。

### 2.3 输出 feature-context.md

为每个 Feature 生成 `feature-context.md`，格式见 `templates/feature-context.md`。

---

## Phase 3: 任务拆分

> **执行步骤**：
> 1. 对每个 Feature 的 feature-context.md，按§3.2 策略确定拆分方式
> 2. 按§3.1 五个条件逐个拆分 Task，确保每个 Task 满足最小可验收颗粒度
> 3. 为每个 Task 注入结构化上下文（§3.7），确保信息完整传递
> 4. 为每个 Task 定义依赖关系（§3.4），包括依赖类型（FS / FF / data-dependency）
> 5. 写入 `task-list.json`（§3.6 格式）
> 6. 运行 `validate-dag.py` 校验 DAG（§3.5）
> 7. 处理校验结果：CYCLE_DETECTED → SUMMARY.md 警告；WARNING → 记录但不阻塞
> 8. 执行依赖完整性校验（§3.8），输出 `dependency-suggestions.json`
> 9. 执行 AC-测试点映射校验（§3.9），确保 TESTSET 覆盖完整
> 10. 执行原型感知上下文注入（§3.10），为 UI 相关 Task 注入原型引用和对齐验收项

### 3.1 最小可验收颗粒度

每个 Task 必须满足以下**全部**条件：

| # | 条件 | 说明 |
|---|------|------|
| 1 | **可独立验收** | 完成后有明确的验收标准，无需等待其他 Task |
| 2 | **有明确产出物** | 产出可观察的代码/配置/文档变更 |
| 3 | **工作量可控** | 预估 ≤ 8h。例外：强耦合无法拆分时允许超 8h，必须记录理由 |
| 4 | **上下文完整** | 实施者只看本 Task 的 impl 文档即可开始工作 |
| 5 | **不跨层** | 不同时涉及前端 + 后端 + 数据库（除非是集成 Task） |

### 3.2 拆分策略

| 设计粒度 | 拆分策略 |
|---------|---------|
| 一个用户故事（US） | 按 AC 拆分，每条 AC → 1 个 Task |
| 一个 API 端点 | 按层拆分：Model → Service → Controller → Test |
| 一个页面 | 按交互拆分：骨架 → 核心交互 → 边界状态 → 样式 |
| 一个业务规则 | 按验证 + 实现 + 测试拆分 |
| 一个数据流 | 按流转阶段拆分：入口 → 转换 → 存储 → 出口 |
| 一个领域模型 | 按聚合拆分：聚合根 → 值对象 → 仓储 → 领域服务 |

### 3.3 不应拆分的情况

| 情况 | 原因 |
|------|------|
| 单个 AC 已经很简单（< 2h） | 拆分后管理成本 > 价值 |
| 两个操作强耦合（拆开后无法独立验收） | 保持为一个 Task |

### 3.4 依赖关系定义

为每个 Task 定义依赖关系：

| 类型 | 说明 |
|------|------|
| **finish-to-start (FS)** | 前置 Task 完成后才能开始 |
| **finish-to-finish (FF)** | 前置 Task 完成后当前 Task 才能完成 |
| **data-dependency** | 前置 Task 的产出物是当前 Task 的输入 |

### 3.5 DAG 确定性校验

LLM 产出依赖关系后，写入 `task-list.json`，然后运行 `validate-dag.py`：

```bash
python zdoc-i2i/validate-dag.py {output_dir}/impl-{feature}-{id}/task-list.json
```

脚本输出 `dag-validation.json`：
- `PASS` — 无环，拓扑排序成功
- `CYCLE_DETECTED` — 含循环依赖，输出环路路径
- `WARNING` — 含孤立节点（无依赖也无被依赖的 Task）

如果 `CYCLE_DETECTED`：在 SUMMARY.md 中输出警告，不自动修改依赖关系。
如果 `WARNING`：记录但不阻塞。

### 3.6 输出 task-list.json

Phase 3 产出 `task-list.json`，作为 Phase 4 文档生成的数据源（Phase 3→4 桥接文件）。Phase 4 读取此文件生成所有 Task impl 文档、INDEX.md 和 SUMMARY.md。

```json
{
  "feature_id": "M01",
  "feature_name": "用户注册",
  "generated_at": "2026-05-28T10:00:00",
  "tasks": [
    {
      "id": "task-001",
      "slug": "data-model",
      "name": "数据模型定义",
      "priority": "P0",
      "estimated_hours": 4,
      "dependencies": [],
      "dependency_type": {},
      "acceptance_criteria": ["AC-001: Given ..., When ..., Then ..."],
      "source_docs": ["PRD-M01 §3.1", "ARCH-M01 §4.2"],
      "exception": null,
      "acceptance_gates": ["§11 门槛 1"],
      "source_constraints": ["§4.2", "§5.1"],
      "exclusions": [],
      "api_versions": [],
      "semantic_overlaps": []
    },
    {
      "id": "task-002",
      "slug": "api-endpoint-post-register",
      "name": "注册接口实现",
      "priority": "P0",
      "estimated_hours": 6,
      "dependencies": ["task-001"],
      "dependency_type": {
        "task-001": "FS"
      },
      "acceptance_criteria": ["AC-002: Given 已有数据模型, When 调用 POST /register, Then 返回 201"],
      "source_docs": ["API-M01 §2.1", "PRD-M01 §3.2"],
      "exception": null,
      "acceptance_gates": ["§11 门槛 2"],
      "source_constraints": ["§4.2"],
      "exclusions": [],
      "api_versions": [
        {
          "library": "ai",
          "version": "^4.1.54",
          "deprecated_apis": ["StreamingTextResponse"],
          "compatible_apis": ["toDataStreamResponse()"]
        }
      ],
      "semantic_overlaps": []
    }
  ]
}
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `feature_id` | string | 是 | Feature 编号 |
| `feature_name` | string | 是 | Feature 名称 |
| `generated_at` | string | 是 | ISO 8601 时间戳 |
| `tasks` | array | 是 | Task 列表 |
| `tasks[].id` | string | 是 | `task-{3位序号}` |
| `tasks[].slug` | string | 是 | kebab-case 摘要（≤ 5 词） |
| `tasks[].name` | string | 是 | Task 名称 |
| `tasks[].priority` | string | 是 | P0 / P1 / P2 |
| `tasks[].estimated_hours` | number | 是 | 预估工时（h） |
| `tasks[].dependencies` | string[] | 是 | 依赖的 Task ID 列表 |
| `tasks[].dependency_type` | object | 是 | 依赖类型映射 `{task_id: "FS"\|"FF"\|"data-dependency"}` |
| `tasks[].acceptance_criteria` | string[] | 是 | 验收标准 |
| `tasks[].source_docs` | string[] | 是 | 来源文档引用（`文件名 §章节`） |
| `tasks[].exception` | string\|null | 是 | 超 8h 时的例外理由，否则 null |
| `tasks[].acceptance_gates` | string[] | 是 | 该 task 涉及的所有 §11 门槛编号 |
| `tasks[].source_constraints` | string[] | 是 | 该 task 涉及的所有 §X.Y 具体约束编号 |
| `tasks[].exclusions` | object[] | 是 | 排除项与例外声明（空数组 = 无排除） |
| `tasks[].exclusions[].description` | string | 是 | 排除内容描述 |
| `tasks[].exclusions[].exception_approved_by` | string | 是 | 例外来源（§11 门槛 N 或 §X.Y 显式批准） |
| `tasks[].api_versions` | object[] | 是 | 外部 API 版本信息（空数组 = 无） |
| `tasks[].api_versions[].library` | string | 是 | 库名 |
| `tasks[].api_versions[].version` | string | 是 | 版本号 |
| `tasks[].api_versions[].deprecated_apis` | string[] | 是 | 已废弃 API 列表 |
| `tasks[].api_versions[].compatible_apis` | string[] | 是 | 兼容 API 列表 |
| `tasks[].semantic_overlaps` | string[] | 否 | 与该 task 存在语义重叠的其他 task ID |
| `tasks[].prototype_refs` | object[] | 否 | UI 相关 task 关联的原型引用（空数组 = 无原型）。含 `file`（原型路径）、`phase_id`（原型阶段）、`phase_description`（阶段描述）、`alignment_ac`（原型对齐验收项） |

---

### 3.7 Task 上下文注入模板

为每个 Task 定义强制注入的上下文字段，确保信息完整传递：

```yaml
task_context:
  # 必填：该 task 涉及的所有 §11 门槛编号
  acceptance_gates: ["§11 门槛 N", ...]

  # 必填：该 task 涉及的所有 §4/§5/§6/§7/§8 具体约束编号
  source_constraints: ["§X.Y", ...]

  # 必填：该 task 的排除项与例外声明
  exclusions:
    - description: "..."
      exception_approved_by: "§11 门槛 N 或 §X.Y 显式批准"

  # 选填：与该 task 存在语义重叠的其他 task
  semantic_overlaps: ["task-NNN", ...]

  # 选填：UI 相关 task 关联的原型引用（§3.10 原型感知上下文注入）
  prototype_refs:
    - file: "ux-prototypes/proto-m12-onboarding.html"
      phase_id: "PHASE-B"
      phase_description: "5题身份建档表单"
      alignment_ac: "实现必须对齐 proto-m12-onboarding.html PHASE-B 的布局、文案、状态和交互，并提供截图或 Playwright 核对证据"

  # 选填：该 task 依赖的外部 API 版本信息
  api_versions:
    - library: "ai"
      version: "^4.1.54"
      deprecated_apis: ["StreamingTextResponse"]
      compatible_apis: ["toDataStreamResponse()", "pipeDataStreamToResponse()"]
```

### 3.8 依赖完整性校验

DAG 校验通过后，执行依赖完整性检查：

| 校验规则 | 检查方法 |
|----------|----------|
| 目录结构依赖 | 任何创建文件的 task 必须依赖 task-001（目录结构） |
| 配置依赖 | 任何使用 env 变量的 task 必须依赖 task-002（环境配置） |
| 基础设施依赖 | 任何使用 Drizzle 的 task 必须依赖 task-005；使用 Redis 的必须依赖 task-009 |
| 类型依赖 | 任何定义 API 类型的 task 必须依赖 task-004（错误/API 类型） |
| **已有表依赖验证** | 当 Task 的 AC 或实施步骤引用 "existing table" 或 "已有表" 时，Grep 检查当前 codebase 的 migration 文件中是否存在该表的 CREATE TABLE 语句。如不存在 → FAIL，建议：(a) 加入当前 Feature 的 migration，或 (b) 标注依赖的 migration 版本号 |

**输出**：`dependency-suggestions.json`，由人工确认后合并到 task-list.json。

```json
{
  "suggestions": [
    {
      "task_id": "task-014",
      "suggested_dependency": "task-001",
      "reason": "task-014 创建文件，需依赖目录结构",
      "rule": "directory_structure_dependency"
    }
  ],
  "existing_table_checks": [
    {
      "task_id": "task-005",
      "table": "runner_risk_profiles",
      "referenced_as": "existing table",
      "found_in_migrations": false,
      "status": "FAIL",
      "suggestion": "该表在当前 codebase 的 migration 文件中不存在。建议：(a) 在 TASK-001 中增加 CREATE TABLE runner_risk_profiles，或 (b) 标注依赖的前置 migration 版本号"
    }
  ]
}
```

### 3.9 AC-测试点映射校验

拆解后检查 TESTSET 覆盖完整性：

```
TESTSET 中的每个测试点（HP-01~07, BC-01~12, ARC-01~04, ...）
  → 是否至少被一个 task 的 AC 覆盖？→ 未覆盖标记为 ORPHAN
  → 是否有 task 的 AC 覆盖了 TESTSET 之外的内容？→ 标记为 EXTRA
```

**作用**：
- 检测测试范围模糊：如果 PERF-04/05 未被任何 task 显式排除或覆盖，标记为 GAP
- 检测测试点遗漏：如果 TESTSET 中有测试点未被任何 task 的 AC 引用，标记为 ORPHAN

### 3.10 原型感知上下文注入

> **问题**：当前 Task 拆分中，UI 相关 Task 仅通过 UX Spec 间接引用原型，实施者无法直接找到对应的原型文件和具体阶段。实际项目中（如 Task-011 onboarding-form-ui），原型包含表单布局、错误文案、loading 状态、sticky 按钮等可对照实现的细节，但这些信息在 Task 文档中丢失。

**执行步骤**：

1. 从 Phase 0 的 `source-consistency-report.json` 读取 `prototype_index`
2. 对每个 Task，判断是否涉及 UI 实现（拆分策略为"页面"或涉及 T06 UX Spec / T07 UX Prototype）
3. 若涉及 UI 且存在对应原型：
   a. 根据 Task 的验收标准和 UX Spec 章节引用，匹配原型中的对应 Phase
   b. 将原型文件路径 + 阶段信息注入 Task 上下文
   c. 在 Task 的验收标准中自动追加一条**原型对齐验收项**：
      ```
      实现必须对齐 {prototype_file} 中 {phase_id} 的布局、文案、状态和交互，
      并提供截图或 Playwright 核对证据
      ```
   d. 在 Task 文档的"关联文档"表格中增加原型引用行
4. 若涉及 UI 但无原型 → 不追加原型对齐验收项，但记录 WARNING

**原型匹配规则**：

| 匹配维度 | 方法 |
|----------|------|
| UX Spec 章节 | Task 的 `source_docs` 包含 `UX-*` 引用 → 查找 UX Spec `references` 中的原型 |
| 原型阶段 | Task AC 中的交互描述 ↔ 原型 Phase 注释/标题（语义匹配） |
| 原型文件 | `prototype_index` 中 `phases[].ux_spec_section` 与 Task 引用的 UX Spec 章节匹配 |

**注入后的 task-list.json 扩展字段**：

```json
{
  "prototype_refs": [
    {
      "file": "ux-prototypes/proto-m12-onboarding.html",
      "phase_id": "PHASE-B",
      "phase_description": "5题身份建档表单",
      "alignment_ac": "实现必须对齐 proto-m12-onboarding.html PHASE-B 的布局、文案、状态和交互，并提供截图或 Playwright 核对证据"
    }
  ]
}
```

---

## Phase 4: 文档生成

> **执行步骤**：
> 1. 创建输出目录结构（§4.1）
> 2. 读取 `templates/` 下对应模板，按模板格式逐个生成文件
> 3. **应用路径规范化**：从 `source-consistency-report.json` 读取 `path_normalization` 结果，将所有 Task 文档中的文件路径替换为规范化后的完整路径
> 4. **ENUM 生成校验**（§4.8）：以 PRD 定义为准生成 ENUM，校验 TECH/ARCH 差异
> 5. 为每个 Task 生成 `task-{nnn}-{slug}.md`（模板见 `templates/task.md`）
> 6. 生成 `INDEX.md`（模板见 `templates/index.md`）
> 7. 多 Feature 时生成 `IMPL-INDEX.md`（模板见 `templates/impl-index.md`）
> 8. 生成 `SUMMARY.md`（模板见 `templates/summary.md`），统计数字**必须**从 task-list.json 动态计算
> 9. 执行产物完整性检查（§4.7）
> 10. 执行交付前自动审核（§5.1）
> 11. 生成交付报告 `delivery-report.json`（§5.3）

### 4.1 目录结构

```
{output_dir}/
├── IMPL-INDEX.md                         # 全局索引（多 Feature 时）
├── impl-{feature}-{PRD-ID}/
│   ├── SUMMARY.md                        # 汇总报告
│   ├── INDEX.md                          # Feature 索引
│   ├── IMPL-{PRD-ID}-{feature-slug}.md   # Feature 聚合上下文
│   ├── IMPL-TASK-001-{slug}.md           # Task 实施文档
│   ├── IMPL-TASK-002-{slug}.md
│   └── ...
└── ...
```

### 4.2 命名规则

遵循 DOC-WRITING-GUIDE §0.6 命名规范：

| 元素 | 规则 | 示例 |
|------|------|------|
| **目录名** | `impl-{kebab-case-feature-name}-{PRD Feature ID}` | `impl-user-registration-M01` |
| **Feature 上下文** | `IMPL-{PRD-ID}-{kebab-case-feature-slug}.md` | `IMPL-M01-user-registration.md` |
| **Task 文件名** | `IMPL-TASK-{3位序号}-{kebab-case-slug}.md` | `IMPL-TASK-001-data-model.md` |
| **Feature ID** | 从 PRD 的 Feature/Milestone 编号继承 | `M01`, `M02` |
| **slug** | Task 核心内容的 kebab-case 摘要（≤ 5 词） | `data-model`, `api-endpoint-post-register` |

### 4.3 输出文档结构规范（DOC-WRITING-GUIDE 对齐）

所有生成的产物文档必须遵循 `DOC-WRITING-GUIDE` 的结构规范（详见 ADR-004 §4.0）。

**Frontmatter 必填字段**：

```yaml
---
title: "{中文标题}"
status: draft
created: "{YYYY-MM-DD}"
updated: "{YYYY-MM-DD}"
layer: "L3 实现层"
priority: "{P0/P1/P2}"
related_docs: []
relationships:
  depends_on: []
  implements: []
  constrains: []
  references: []
  supersedes: []
  superseded_by: []
context_policy:
  load_priority: recommended
  task_scopes: []
  max_tokens_hint: 3000
---
```

**标准章节**：

| 章节 | 必填 | 说明 |
|------|------|------|
| 文档定位 | 是 | 一句话说明本文负责回答什么问题 |
| 关联文档 | 是 | 表格列出上游设计文档、下游产物 |
| 范围边界 | 是 | In Scope / Out of Scope |
| 验收或检查点 | 是 | 判断本文描述成立的条件 |

**交叉引用格式**：

```markdown
[PRD-M01-Onboarding](../prds/PRD-M01-Onboarding.md)
[Section 3.4 最小可验收颗粒度](#34-最小可验收颗粒度定义)
```

**中英文规则**：文件名英文 kebab-case，frontmatter title 中文，章节标题中文为主，技术术语保留英文。

### 4.4 版本戳

所有生成的文件必须包含以下元数据头部：

```markdown
<!-- Generated by zdoc-i2i v1.6 | {YYYY-MM-DDTHH:MM:SS} | source-hash: {md5 of input doc paths} -->
```

### 4.5 文件模板

#### SUMMARY.md

读取 `templates/summary.md` 模板，按模板格式填充。包含：
- 输入文档校验结果（含 CONDITIONAL 的 WARN 项）
- Feature → Task 映射
- Out of Scope 汇总
- 关键决策记录
- 风险与注意事项
- DAG 校验结果
- 依赖完整性校验结果
- AC-测试点覆盖率
- 源文档交叉一致性结果
- 文档状态变更日志
- 验收/检查点

#### INDEX.md

读取 `templates/index.md` 模板，按模板格式填充。包含：
- Task 清单（ID + 名称 + 状态 + 优先级 + 工时 + 依赖）
- 依赖关系图（Mermaid + 表格，表格为权威源）
- 执行顺序（拓扑排序分层）
- 关键路径

#### IMPL-INDEX.md（多 Feature 时）

读取 `templates/impl-index.md` 模板。包含：
- Feature 清单 + 统计
- 跨 Feature 依赖关系
- 全局 DAG + 全局执行顺序

#### IMPL-{PRD-ID}-{feature-slug}.md（Feature 聚合上下文）

读取 `templates/feature-context.md` 模板。包含：
- YAML frontmatter（title/status/layer/priority/related_docs/relationships/context_policy）
- 文档定位、关联文档、范围边界
- 功能概述、用户故事、验收标准
- 业务规则、技术约束、API 契约
- 交互流程、领域模型、数据流
- 测试要点、Out of Scope
- 验收/检查点

#### IMPL-TASK-{nnn}-{slug}.md（Task 实施文档）

读取 `templates/task.md` 模板，按模板格式填充。每个 Task 的 impl 文档必须包含：
- YAML frontmatter（title/status/layer/priority/module_id/related_docs/relationships/context_policy）
- 文档定位、关联文档、范围边界
- Task 元数据（Feature、优先级、工时、依赖、产出物、例外理由）
- 验收标准
- 溯源链（§11 门槛 → §X.Y 约束 → TESTSET 测试点）
- 完整上下文（业务规则、技术约束、API 契约、交互要求、领域模型、数据流、测试要点）
- 排除项（含例外来源标注）
- API 版本信息
- 实施指引（仅基于设计文档已明确信息）
- 验收/检查点

### 4.6 文档状态冻结

Phase 4 文档生成全部成功后，执行文档状态冻结：

1. **冻结条件**：Phase 4 所有产物完整性检查通过
2. **冻结操作**：对每个输入文档，将状态置为 `frozen`
   - 更新 frontmatter：`status: frozen`
   - 更新头部状态标记：`**Status**: frozen` 或 `**状态**: 已锁定`
   - 注意：文件名中的状态后缀不做更新，frontmatter 为权威源
3. **记录日志**：在 SUMMARY.md 中记录状态变更

```markdown
## 文档状态变更

| 文档 | 原状态 | 新状态 | 变更时间 |
|------|--------|--------|---------|
| PRD-M01.md | approved | frozen | {timestamp} |
| ARCH-M01.md | approved | frozen | {timestamp} |
```

4. **失败处理**：如果 Phase 4 生成失败，不冻结文档，保持原有状态，允许修复后重跑

### 4.7 产物完整性检查

生成完成后，自动执行以下检查：

| # | 检查项 | 规则 |
|---|--------|------|
| 1 | Task 文件数量 = INDEX.md 中的 Task 数量 | 一致性 |
| 2 | 每个 Task 的依赖项在 INDEX.md 中存在 | 引用完整性 |
| 3 | DAG 校验脚本输出 PASS | 确定性验证 |
| 4 | 每个 Task 有验收标准 | 完整性 |
| 5 | 每个 Task 有完整上下文 | 自包含性 |
| 6 | Out of Scope 项未被任何 Task 涵盖 | 范围防护 |
| 7 | 每个文件包含版本戳头部 | §4.4 规范 |
| 8 | 多 Feature 时存在 IMPL-INDEX.md | 全局索引完整性 |
| 9 | 超过 8h 的 Task 有例外理由记录 | 工时例外规则 |
| 10 | 每个文件包含 YAML frontmatter | §4.3 DOC-WRITING-GUIDE 对齐 |
| 11 | 每个文件包含标准章节（文档定位 + 关联文档 + 范围边界 + 验收/检查点） | §4.3 DOC-WRITING-GUIDE 对齐 |
| 12 | frontmatter `layer` 为 `L3 实现层` | §4.3 层级分类 |
| 13 | frontmatter `related_docs` 包含相关设计文档引用 | §4.3 交叉引用 |
| 14 | 文件名符合英文 kebab-case 规范 | §4.2 命名规范 |
| 15 | SUMMARY.md `预估总工时` == `SUM(task-list.tasks[*].estimated_hours)` | 动态计算一致性 |
| 16 | SUMMARY.md `Task总数` == `COUNT(task-list.tasks)` | 动态计算一致性 |
| 17 | INDEX.md 工时加总 == SUMMARY.md `预估总工时` | 跨文档一致性 |
| 18 | feature-context.md 中 Out of Scope 的表不出现在"新建的表"列表中 | Data Model 分区一致性 |
| 19 | SUMMARY.md 中无硬编码统计值（禁止从早期版本复制） | 防残留 |

### 4.8 ENUM 生成校验

Phase 4 生成 Task 文档时，对所有 ENUM 类型字段执行以 PRD 为准的校验：

**执行步骤**：

1. 读取 `source-consistency-report.json` 中的 `prd_tech_alignment.enum_checks`
2. 对每个 FAIL 级别的 ENUM 差异：
   a. 以 PRD 定义的值集合为准生成 DDL/校验逻辑
   b. 在 Task 文档的"完整上下文 > 技术约束"中标注：
      > ⚠️ 注意：TECH/ARCH 文档中包含额外值 `[X]`，但 PRD 未定义。本 Task 以 PRD 为准，仅使用 `[PRD 定义的值]`。如需扩展，请先更新 PRD。
3. 在 `delivery-report.json` 中记录 ENUM 校验结果

**ENUM 追溯标注格式**（在 Task 文档"技术约束"章节中）：

```markdown
#### 枚举值定义（以 PRD 为准）

| 字段 | PRD 定义值 | TECH/ARCH 值 | 本 Task 使用 |
|------|-----------|-------------|-------------|
| gender | male, female | male, female, other | male, female（以 PRD 为准） |
```

---

## Phase 5: 交付前审核 + 交付报告

> **执行步骤**：
> 1. 执行交付前自动审核清单（§5.1）
> 2. 执行语义偏移检测（§5.2）
> 3. 生成 `delivery-report.json`（§5.3）

### 5.1 交付前自动审核清单

| 检查项 | 检查方法 | 阻断级别 |
|--------|----------|----------|
| **AC-测试点覆盖率** | 每个 task 的 AC 至少引用一个 TESTSET 测试点 | BLOCK |
| **排除项一致性** | task 排除项中的"无需 XX"必须标注例外来源（§X.Y 或 §11 门槛 N） | BLOCK |
| **API 版本标注** | task 中引用的 API 名称必须标注适用版本范围 | WARN |
| **依赖 DAG 完整性** | 通过 §3.8 依赖完整性校验 | BLOCK |
| **上下文字段完整性** | 通过 §3.7 强制字段检查 | BLOCK |
| **配置示例完整性** | ESLint/lint 配置示例覆盖所有声明的约束条数 | WARN |

### 5.2 语义偏移检测

对每个 task 的关键 AC 执行语义对比：

```
源文档原文 ↔ task AC 表述
  → 检查是否存在语义偏移（如将"验证后删除"简化为"删除"）
  → 若检测到偏移，标记为 SEMANTIC_DRIFT
  → 输出差异说明
```

| 源文档 | task AC | 检测结果 |
|--------|---------|----------|
| "在新 Provider factory 验证 Mock 模式通过后执行移除" | "移除旧 ai-config.ts" | SEMANTIC_DRIFT: 丢失了"验证后"的安全顺序约束 |

### 5.3 交付报告

I2I Pipeline 在交付时附带 `delivery-report.json`：

```json
{
  "feature_id": "ARCH-LITE-XXX",
  "generated_at": "...",
  "i2i_version": "v1.6",
  "source_consistency": {
    "status": "PASS | FAIL",
    "issues": []
  },
  "dependency_validation": {
    "status": "PASS | WARN",
    "suggestions": []
  },
  "ac_coverage": {
    "total_test_points": 40,
    "covered_by_tasks": 38,
    "orphan_test_points": ["PERF-04", "PERF-05"],
    "coverage_rate": "95%"
  },
  "semantic_drift": {
    "total_acs": 64,
    "flagged": 2,
    "details": []
  },
  "pre_delivery_checks": {
    "passed": 8,
    "failed": 0,
    "warnings": 1
  }
}
```

---

## 重跑语义

| 场景 | 行为 |
|------|------|
| **同 Feature 重跑** | 覆盖该 Feature 目录下所有文件 |
| **全局索引更新** | 重新生成 IMPL-INDEX.md（覆盖） |
| **幂等保证** | 相同输入 + 相同版本 → 相同输出 |
| **已冻结文档重跑** | frozen 文档可被 I2I 接受并重新生成 Task。冻结操作对已冻结文档是幂等的（frozen → frozen）。如需修改设计文档，必须走 deprecated + 新建文档流程（见 DOC-WRITING-GUIDE） |

---

## Non-Negotiable Rules

1. **只整合不补充**：不发明设计文档中没有的功能、技术方案或业务规则
2. **缺失即停止**：BLOCK 时返回缺失清单并停止，不猜测或填补
3. **上下文自包含**：每个 Task impl 文档必须包含该 Task 需要的全部上下文
4. **依赖关系显式化**：不允许隐式依赖
5. **DAG 确定性校验**：环检测由 `validate-dag.py` 执行，不依赖 LLM
6. **Out of Scope 不纳入**：设计文档明确排除的内容不生成 Task
7. **不修改源文档**：只读取设计文档（状态冻结除外，见 §4.6）
8. **可追溯**：每个 Task 信息可追溯到源设计文档的具体章节
9. **命名规范**：严格遵循 §4.2 命名规则
10. **全局索引必出**：多 Feature 时必须生成 IMPL-INDEX.md
11. **版本戳必加**：所有生成文件必须包含 §4.4 版本戳
12. **工时例外记录**：超过 8h 的 Task 必须记录例外理由
13. **文档状态准入**：仅接受 `approved` / `frozen` 状态的输入文档，`draft` / `reviewing` 状态 BLOCK 并提示需先通过评审
14. **执行后冻结**：成功生成全部 Task 文档后，将所有输入文档状态置为 `frozen`
15. **DOC-WRITING-GUIDE 对齐**：所有生成的产物文档必须包含 YAML frontmatter（§4.3）和标准章节（文档定位、关联文档、范围边界、验收/检查点），遵循 DOC-WRITING-GUIDE 的结构规范
16. **源文档交叉一致性**：Phase 0 执行源文档交叉一致性校验，BLOCK 级冲突要求源文档澄清后重跑，不进入拆解
17. **依赖完整性**：Phase 3 执行依赖完整性校验，自动检测缺失依赖并输出建议
18. **交付前审核**：Phase 5 执行交付前自动审核清单，BLOCK 级问题不交付
19. **交付报告必出**：每次执行必须生成 `delivery-report.json`，记录校验覆盖率和质量指标
20. **文件路径完整性**：Task 文档中所有文件路径必须使用项目根目录相对的完整路径，禁止使用简写路径（如 `src/`）。如指定了 `--src` 参数，Phase 0 规范化所有路径后传递到 Phase 4
21. **原型引用显式化**：UI 相关 Task 的验收标准必须包含原型对齐验收项（当存在对应原型时），原型文件路径和阶段信息必须直接写入 Task 文档的"关联文档"表格和 task-list.json 的 `prototype_refs` 字段，禁止仅通过 UX Spec 间接引用

---

## 术语定义

| 术语 | 定义 |
|------|------|
| **I2I** | Design-to-Impl 的缩写 |
| **Feature** | 一个完整的功能特性，拥有独立的 impl 目录 |
| **Task** | 最小可验收的实施单元 |
| **最小可验收颗粒度** | 满足 5 个条件：可独立验收、有产出物、工作量可控、上下文完整、不跨层 |
| **DAG** | Task 依赖关系的有向无环图 |
| **关键路径** | 依赖链中累计工时最长的路径。计算方法：在拓扑排序基础上，对每个节点求最长路径（动态规划），取累计 `estimated_hours` 最大的路径 |
| **必输要素** | 设计文档中必须包含的要素。缺失时判定为 BLOCK |
| **CONDITIONAL** | 有 WARN 但无 BLOCK，允许带标注继续 |
| **Out of Scope** | 设计文档中明确声明本期不做的内容 |
| **文档状态** | 设计文档的生命周期状态：draft → reviewing → approved → frozen |
| **Frozen** | 文档已锁定，不可修改。I2I 成功执行后自动置为 frozen |

---

## Usage

```bash
# 全量目录扫描（推荐）
zdoc-i2i --dir docs/mvp-lite/

# 指定 Feature
zdoc-i2i --dir docs/mvp-lite/ --feature M01

# 最小输入
zdoc-i2i --prd docs/prds/PRD-M01.md --arch docs/arch/ARCH-M01.md

# 指定源代码根路径（确保文件路径使用项目根相对的完整路径）
zdoc-i2i --dir docs/mvp-lite/ --src apps/ai-coach-skill/src

# 指定输出目录
zdoc-i2i --dir docs/mvp-lite/ --output-dir docs/mvp-lite/impl

# 仅校验
zdoc-i2i --dir docs/mvp-lite/ --validate-only
```
