---
title: "MVP Lite 文档撰写说明"
status: frozen
created: "2026-05-28"
updated: "2026-05-28"
scope: "docs/mvp-lite"
related_docs:
  - "../ai-infra/DOC-GOVERNANCE-IMPLEMENTATION-PLAN.md"
  - "../ai-infra/DOC-LIFECYCLE-STATE-MACHINE.md"
  - "../ai-infra/DOC-RELATIONSHIP-MODEL.md"
  - "../ai-infra/AI-CONTEXT-ASSEMBLY.md"
  - "../ai-infra/context-assembly-rules.yaml"
---

# MVP Lite 文档撰写说明

> 本指南面向所有需要在 `docs/mvp-lite/` 下新增或维护文档的角色，包括产品、研发、UX、测试和架构评审者。
>
> 本文定义 `docs/mvp-lite/` 下各类 SSOT 文档的写作边界、命名规范、必填内容、可选内容与文档关系。
> `docs/mvp-lite/` 是 SSOT（Single Source of Truth），即项目唯一的结构化文档真源，供 agent 实施使用。

---

## 0. 通用规则

### 0.1 文档定位

本文中的 **SSOT**（Single Source of Truth，单一真源）指 `docs/mvp-lite/` 中的结构化文档，供 agent 实施使用。
`docs/mvp-lite/` 是 SSOT，用于回答：

- 为什么这样设计？
- 某个模块在产品、接口、技术、数据流、测试、UX 上的补充上下文是什么？
- 当前 SSOT 未覆盖的历史决策、方案推演、架构边界、审查记录是什么？

### 0.1.1 治理规范关系

本文只负责 `docs/mvp-lite/` 的写作边界、目录职责和内容结构。跨目录的文档治理能力由以下规范定义：

| 能力 | 权威规范 | 本文关系 |
|------|----------|----------|
| 三能力维护入口 | [`DOC-GOVERNANCE-THREE-CAPABILITIES-GUIDE`](../ai-infra/DOC-GOVERNANCE-THREE-CAPABILITIES-GUIDE.md) | 后续维护文档治理三核心能力的总入口 |
| 文档状态机 | [`DOC-LIFECYCLE-STATE-MACHINE`](../ai-infra/DOC-LIFECYCLE-STATE-MACHINE.md) | 本文中的状态说明仅保留为 mvp-lite 写作简表 |
| 文档关系模型 | [`DOC-RELATIONSHIP-MODEL`](../ai-infra/DOC-RELATIONSHIP-MODEL.md) | 本文中的文档关系图仅表示目录级关系 |
| AI 上下文装配 | [`AI-CONTEXT-ASSEMBLY`](../ai-infra/AI-CONTEXT-ASSEMBLY.md) 与 [`context-assembly-rules.yaml`](../ai-infra/context-assembly-rules.yaml) | AI agent 应按任务动态装配上下文，而不是全量读取 |

当本文与上述治理规范冲突时，按以下优先级处理：

```text
AI_CONSTITUTION.md
  → docs/mvp-lite/
    → docs/ai-infra/DOC-GOVERNANCE-THREE-CAPABILITIES-GUIDE.md
      → docs/ai-infra/ 文档治理规范
      → docs/mvp-lite/DOC-WRITING-GUIDE.md
        → docs/mvp-lite/ 具体补充文档
```

### 0.2 通用头部

新文档建议使用 YAML frontmatter：

```yaml
---
title: "文档标题"
status: draft | reviewing | approved | frozen | deprecated | archived
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
module_id: ""        # 可选：M12 | S01 等，模块级文档必须填写
layer: ""            # 可选：L0 战略层 | L1 业务层 | L2 设计层 | L3 实现层
priority: ""         # 可选：P0 必须有 | P1 应该有 | P2 可以延后
related_docs: []     # 可选：关联文档文件名列表，如 ["PRD-M12-Onboarding-Identity.md"]
relationships:       # 可选：正式治理文档或新建模块文档建议填写
  depends_on: []
  implements: []
  constrains: []
  references: []
  supersedes: []
  superseded_by: []
context_policy:      # 可选：需要被 AI agent 自动装配时填写
  load_priority: required | recommended | optional
  task_scopes: []
  max_tokens_hint: 3000
---
```

字段说明：
- `layer` 标识文档在架构分层中的位置：L0 战略层（stg/）、L1 业务层（business/、prds/）、L2 设计层（ux/、api/）、L3 实现层（tech/、arch/、ddd/、data/、skills/、adapters/、jobs/）。
- `priority` 标识文档的交付优先级。
- `relationships` 的语义以 [`DOC-RELATIONSHIP-MODEL`](../ai-infra/DOC-RELATIONSHIP-MODEL.md) 为准。
- `context_policy` 的语义以 [`AI-CONTEXT-ASSEMBLY`](../ai-infra/AI-CONTEXT-ASSEMBLY.md) 为准。
- 已有历史文档可不强制补齐，但新增正式补充文档应包含 `title`、`status`、`created`。模块级文档应包含 `module_id`。需要被 AI agent 自动装配的文档应补齐 `relationships` 与 `context_policy`。

**状态流转规则**：
- 完整状态机以 [`DOC-LIFECYCLE-STATE-MACHINE`](../ai-infra/DOC-LIFECYCLE-STATE-MACHINE.md) 为准。
- `draft → reviewing → approved → frozen` 是标准正向路径。
- `frozen` 文档的修订：仅允许 typo 级修正（错别字、格式、链接），直接在 frozen 状态修改并更新 `updated` 字段。实质性变更（新增章节、修改需求、调整边界）必须走 `deprecated` + 新建文档流程。
- `frozen → deprecated`：新文档取代旧文档时，原文档标记 `deprecated` 并附替代文档链接。
- `deprecated` 和 `archived` 不可作为 AI 实施任务的 primary source。

### 0.3 通用章节

除 `stg/`、`reviews/`、`ux-prototypes/` 中的特殊文档外，模块级文档建议包含：

- 文档定位：一句话说明本文负责回答什么问题。
- 关联文档：列出上游 PRD、API、TECH、ARCH、TESTSET、UX 或 SSOT。
- 范围边界：明确 In Scope / Out of Scope。
- 术语或概念：解释本文引入的关键概念。
- 验收或检查点：说明如何判断本文描述的设计成立。
- Open Questions / Assumptions：记录未决问题和假设。

> 以下各目录的"必须包含"已隐含上述通用章节的要求。各目录在此基础上增加了领域特定的必填项。
> 撰写文档时，应同时满足本节的通用章节和对应目录的必填项。

### 0.4 通用边界

所有文档都不应包含：

- secrets、真实密钥、真实用户隐私数据、生产连接串。
- 与文档既定结论冲突但未标注来源和状态的结论。
- 无关联的实现细节、临时代码片段、个人备忘。
- 未说明适用版本的旧方案。

> 正例：在 TECH 中引用一段伪代码说明算法流程——与文档主题直接相关。
> 反例：在 PRD 中贴一段 console.log 调试输出——无关联的临时内容。

### 0.5 术语定义

本文及 `docs/mvp-lite/` 下文档中出现的技术术语：

| 术语 | 定义 |
|------|------|
| **SSOT** | Single Source of Truth，单一真源。本项目中指 `docs/mvp-lite/` 中的结构化文档。 |
| **CardAction** | 前端卡片上的用户操作按钮及其绑定的后端调用（详见 ARCH-LITE-004）。 |
| **Normalizer** | 将外部 Provider 原始数据转换为项目 canonical 数据结构的中间层。 |
| **canonical store** | 项目内部统一的数据存储格式，所有外部数据经 Normalizer 转换后写入此处。 |
| **AC** | Acceptance Criteria，验收标准。PRD 中定义的功能验收条件。 |
| **Skill** | 本项目中指需要 LLM 判断、组合、解释、推演、生成的 AI 编排能力。注意区分：作为文档类型时指 `skills/` 目录下的设计文档；作为能力类型时指运行时的 AI 编排流程。 |
| **Guardrail** | 安全护栏引擎，对 AI 输出进行规则校验和安全拦截（详见 DDD-S04）。 |
| **LlmPort** | LLM 调用端口抽象层，隔离具体 LLM Provider 实现（详见 ARCH-LITE-004）。 |
| **Module-Slug** | 模块的英文标识名，使用 train-case 格式，如 `Onboarding-Identity`。 |

### 0.6 命名共识

- 模块文档使用 `Mxx`：如 `M12`。
- 子模块拆分使用 `Mxx{字母}`：如 `M10a`。规则：字母仅限 `[a-z]`，单字母；用于一个模块的 PRD 过大需要拆分时。
- 领域系统文档使用 `Sxx`：如 `S01`、`S06`。
- 文件名前缀标识文档类型：`PRD-`、`API-`、`TECH-`、`ARCH-`、`DDD-`、`SKILL-`、`TESTSET-`、`UX-` 等。
- HTML 原型文件名使用小写前缀 `proto-`，与 web 文件名惯例保持一致。
- 英文 slug 使用 train-case（首字母大写的 kebab-case）：`Onboarding-Identity`、`Plan-Generation`。`ux-prototypes/` 的 HTML 文件例外，使用全小写 kebab-case（`proto-m12-onboarding.html`）。
- 中文标题可用于战略类和审查类文档，但模块级工程文档优先使用稳定英文 slug，避免路径不稳定。
- 序号统一使用三位补零格式：`001`、`002`、`004`。

**中英文使用规则**：
- 文件名：统一使用英文 kebab-case。
- frontmatter `title`：统一使用中文。
- 章节标题：中文为主，代码标识符、文件路径、技术术语保留英文。
- 正文内容：中文为主，API 端点名、字段名、枚举值保留英文。

**文档间引用格式**：
- 引用其他文档时使用 Markdown 相对路径：`[PRD-M12-Onboarding-Identity](../prds/PRD-M12-Onboarding-Identity.md)`。
- 引用同文档内其他章节时使用锚点：`[Section 4](#4-prds产品需求文档)`。
- frontmatter 中的 `关联文档` 字段可使用纯文件名，与正文 Markdown 链接互为补充。

---

## 1. 目录类型总览

| 子目录 | 文档类型 | 主要读者 | 主要职责 |
|--------|----------|----------|----------|
| `stg/` | 战略与商业宪法 | 创始人、产品、策略评审者 | 定义长期商业判断、用户边界、产品原则、运营和数据指标 |
| `business/` | 模块商业设计 | 产品、运营、研发 | 将战略宪法落到具体模块的商业目标、漏斗、角色和范围 |
| `prds/` | 产品需求文档 | 产品、研发、测试、UX | 定义模块目标、用户故事、功能需求、验收标准和上下游契约 |
| `ux/` | UX 设计规范 | UX、前端、产品 | 定义模块交互流程、状态表达、设计令牌和组件行为 |
| `ux-prototypes/` | 静态视觉原型与设计系统 | UX、前端、评审者 | 用 HTML 原型和设计系统展示可视化方案 |
| `api/` | API 契约 | 前后端、测试 | 定义端点、请求响应、错误码、鉴权、幂等和速率限制 |
| `tech/` | 技术实现设计 | 研发、测试、架构评审者 | 定义数据模型、状态机、业务规则、实现细节和技术约束 |
| `arch/` | 架构设计与边界决策 | 架构、研发、技术评审者 | 定义系统分层、依赖策略、运行时架构、能力边界和非目标 |
| `ddd/` | 领域模型与领域服务设计 | 领域研发、架构、测试 | 定义 S01-S06 领域职责、实体、服务契约、领域规则和跨域依赖 |
| `data/` | 数据流设计 | 后端、数据、测试、审计 | 以数据实体为第一视角描述产生、流转、转换、存储和消费 |
| `skills/` | AI Skill 设计 | AI 工程、后端、产品 | 定义需要判断、组合、解释、推演、生成的 AI 编排能力 |
| `adapters/` | 外部 Provider Adapter 设计 | 后端、集成工程 | 定义外部协议适配、输入输出映射和边界 |
| `jobs/` | 后台任务设计 | 后端、运维、测试 | 定义异步任务、触发方式、幂等、审计和错误处理 |
| `testset/` | 测试策略与用例集 | 测试、研发、产品验收 | 将 PRD/API/TECH 转化为可执行测试覆盖 |
| `reviews/` | 审查与对齐报告 | 产品、架构、研发 | 记录跨文档一致性审查、变更验证、风险和待办 |

---

## 2. `stg/`：战略与商业宪法

### 文档类型

战略、基石、产品、运营、数据等长期经营判断文档，以及未修复问题说明。

### 命名规范

- 宪法类：`跑步大师商业落地宪法——{篇章名}篇 v{major.minor}.md`
- 问题跟踪类：`未修复问题说明.md`

### 必须包含

- 版本或变更日志。
- 依赖声明：说明依赖其他篇章或上游判断。
- 核心原则、明确不做什么、阶段性目标。
- 风险、缺口、待决策项。

### 可选包含

- 市场判断、竞品判断、融资或国际化策略。
- 指标字典、用户分层、运营动作。
- 回顾与更新记录。

### 文档边界

负责高层判断和经营约束，不负责具体模块 API、数据库表结构、组件交互细节。

### 不包含

- 端点定义、代码级接口、DDL、测试用例细节。
- 模块内局部流程的完整 PRD。

### 文档关系

`stg/` 是 `business/` 和 `prds/` 的战略上游。模块文档引用战略结论时，应标注来源篇章和章节。

---

## 3. `business/`：模块商业设计

### 文档类型

单个模块的商业设计文档，如 `BUSINESS-M12-Onboarding-Identity.md`。

### 命名规范

```text
BUSINESS-M{模块号}-{Module-Slug}.md
```

示例：`BUSINESS-M12-Onboarding-Identity.md`

### 必须包含

- 问题域：该模块解决的商业问题。
- 业务目标：指标、目标值、验收标准。
- 目标用户和角色。
- 触发场景和关键用户旅程。
- In Scope / Out of Scope。
- 与战略宪法的映射。
- 替代方案分析：用户当前用什么替代方案？为什么我们的方案更好？（Jobs-to-be-Done 框架）
- MVP 假设与验证计划：核心业务假设是什么？如果指标未达标，下一步行动是什么？
- 成本预估：开发成本、运营成本、LLM 调用成本、用户获取成本等。

### 可选包含

- 商业漏斗、运营后台工具需求（运营侧使用的管理后台的功能需求）、付费或留存假设。
- 风险和反功能。
- P1 / Post-MVP 延展。

### 文档边界

负责解释模块为什么值得做、服务谁、解决什么业务目标。

### 不包含

- 详细 API 字段、数据库 schema、技术实现算法。
- 视觉样式和组件 token 细节。

### 文档关系

上游引用 `stg/`；下游支撑 `prds/`。当 `business/` 与 PRD 不一致时，应在 `reviews/` 中形成对齐结论后再更新。

---

## 4. `prds/`：产品需求文档

### 文档类型

模块级 PRD、跨 S 领域数据层 PRD。

### 命名规范

```text
PRD-M{模块号}-{Module-Slug}.md
PRD-M{模块号}{子模块字母}-{Module-Slug}.md
PRD-S{起始编号}-S{结束编号}-{Domain-Slug}.md
```

示例：

- `PRD-M12-Onboarding-Identity.md`
- `PRD-M10a-Plan-View.md`
- `DDD-S01-S06-Domain-Data-Layer.md`

### 必须包含

- 模块定位和一句话定义。
- 非目标（Non-Goals）：明确列出本模块**不**解决的问题，防止 scope creep。
- 复用基线或历史背景。
- 变更清单：新增、修改、删除。
- 概念说明。
- 用户故事，包含 Priority 和 Acceptance Criteria。
  - 优先级定义：P0 = MVP 必须有，P1 = 应该有，P2 = 可以延后。
- 用户旅程：主路径、分支路径、异常路径。
- 功能需求（FR）和非功能需求（NFR）。
- 成功指标与度量方案：上线后如何验证业务假设，指标来源和目标值。
- 数据模型摘要或关键字段来源。
- API 摘要或接口需求。
- 与上下游模块的边界契约。
- 验收标准汇总。
- Open Questions / Assumptions。

### 可选包含

- ASCII UX 原型。
- Phase 2 升级路径。
- 状态转换图。
- 与旧版本的迁移说明。

### 文档边界

PRD 定义「做什么」和「为什么」，可以约束关键业务规则，但不展开完整技术实现。

### 不包含

- 完整 DDL、Repository 代码、Route Handler 代码。
- 端点级请求响应样例全集；这些进入 `api/`。
- 组件级视觉 token；这些进入 `ux/` 或 `ux-prototypes/`。

### 文档关系

PRD 是 `api/`、`tech/`、`ux/`、`testset/` 的产品上游。模块级 PRD 应显式链接相关 API、TECH、UX、TESTSET 文档。

---

## 5. `ux/`：UX 设计规范

### 文档类型

模块级交互与视觉设计规范。

### 命名规范

```text
UX-M{模块号}-{Module-Slug}.md
```

示例：`UX-M12-Onboarding-Identity.md`

### 必须包含

- 设计原则：系统级继承和模块特有原则。
- 交互流程：步骤、用户动作、系统响应、视觉变化。
- 状态表达：加载、成功、失败、空状态、阻断态。
- 组件结构或页面结构。
- 设计令牌使用：颜色、间距、字体、状态色。
- 响应式或移动端约束。
- 与原型、PRD、设计系统的关联。

### 可选包含

- 动效规范。
- 可访问性要求。
- 文案规则。
- QA 检查清单。

### 文档边界

负责「用户如何看见并操作」，不负责 API 语义、数据持久化或领域算法。

### 不包含

- 后端接口完整契约。
- 数据库表结构。
- 商业目标详细论证。

### 文档关系

上游来自 PRD；下游指导 `ux-prototypes/` 和前端实现。若 UX 调整改变用户旅程或验收，应回写 PRD 或形成 review 结论。

---

## 6. `ux-prototypes/`：静态视觉原型与设计系统

### 文档类型

单文件 HTML 原型、设计系统说明、原型索引。

> 由于 `ux-prototypes/` 包含三种不同形态的文件（HTML 原型、索引、设计系统），"必须包含"按文件类型分组说明，与其他目录的平铺列表格式有所不同。

### 命名规范

```text
proto-m{模块号}-{feature-slug}.html
_design-system.md
_index.md
```

示例：

- `proto-m12-onboarding.html`
- `proto-m16-founder-console.html`
- `_design-system.md`

### 必须包含

HTML 原型必须：

- 可直接在浏览器打开。
- 标明或通过索引映射对应 PRD。
- 覆盖关键状态，而不是只展示 happy path。
- 使用统一设计系统中的颜色、字体、组件语义。

`_index.md` 必须：

- 列出原型文件。
- 标明对应 PRD。
- 说明使用方式和最佳预览尺寸。
- 维护 PRD 覆盖检查。

`_design-system.md` 必须：

- 定义色彩、字体、布局、组件、状态色和动画规范。
- 定义 CardType 或核心组件映射。

### 可选包含

- 原型覆盖矩阵。
- 文件大小或状态说明。
- 设计变更记录。

### 文档边界

负责可视化方案验证和交互感知，不作为正式 API 或业务规则真源。

### 不包含

- 生产代码承诺。
- 后端字段契约。
- 未经 PRD 支撑的新业务能力。

### 文档关系

上游来自 PRD 和 UX 规范；下游给前端实现提供参考。原型发现的新需求必须回到 PRD 或 review 文档确认。

---

## 7. `api/`：API 契约

### 文档类型

模块级 API 文档、单接口 API 文档。

### 命名规范

```text
API-M{模块号}-{Module-Slug}.md
API-{序号}-{endpoint-or-capability-slug}.md
```

示例：

- `API-M12-Onboarding-Identity.md`
- `API-005-get-current-plan.md`

### 必须包含

- 文档定位和关联 PRD / TECH / ARCH。
- API 清单：方法、端点、描述、请求 schema、响应 schema、错误码、优先级。
- 鉴权方式。
- 通用错误响应。
- 每个端点的请求头、请求体、字段说明。
- 成功响应和主要错误响应示例。
- 幂等、速率限制、权限、设备指纹或会话约束。
- 与前端 CardAction（详见术语定义 0.5）、Skill 或 Service 的调用边界。

### 可选包含

- JWT payload 规范。
- 缓存策略。
- 响应头约定。
- 迁移兼容说明。

### 文档边界

API 文档定义传输层契约和前后端集成语义。

### 不包含

- 完整业务推导过程。
- UI 视觉规则。
- 内部 Repository 实现。
- Skill 的内部推理步骤。

### 文档关系

上游来自 PRD；实现细节与 TECH 对齐；测试由 TESTSET 覆盖。

---

## 8. `tech/`：技术实现设计

### 文档类型

模块级技术实现文档、局部实现计划或实现说明。

### 命名规范

```text
TECH-M{模块号}-{Module-Slug}.md
IMPL-M{模块号}-{Module-Slug}.md
```

示例：

- `TECH-M12-Onboarding-Identity.md`
- `IMPL-M12-Onboarding-Identity.md`

### 必须包含

- 文档定位和关联 PRD / API。
- 数据模型 / Schema。
- 状态机或核心状态枚举。
- 关键业务规则和算法。
- 输入校验和边界值。
- 幂等、事务、并发、错误处理。
- 数据写入与读取路径。
- 与 Service、Repository、Adapter、Skill 的边界。
- 非功能要求：性能、可靠性、安全、可观测性。

### 可选包含

- TypeScript interface。
- SQL / DDL 草案。
- 决策表。
- 伪代码。
- 迁移策略和回滚策略。

### 文档边界

TECH 定义「如何实现」的技术设计，但不替代正式代码、迁移文件或 SSOT API。

### 不包含

- 产品价值论证。
- 视觉设计细节。
- 测试用例全集。
- 与本模块无关的基础设施重构。

### 文档关系

TECH 下接实现；上接 PRD / API / ARCH；TESTSET 应引用 TECH 中的边界值、状态机和决策表。

---

## 9. `arch/`：架构设计与边界决策

### 文档类型

整体架构、运行时架构、能力分层边界、外部集成架构、模块架构。

### 命名规范

```text
ARCH-LITE-{序号}-{Architecture-Slug}.md
ARCH-M{模块号}-{Module-Slug}.md
```

示例：

- `ARCH-LITE-004-Skill-API-Tool-CLI-能力分层边界.md`
- `ARCH-M12-Onboarding-Identity.md`

### 必须包含

- 背景与结论。
- 目标和非目标。
- 分层边界。
- 目录结构或运行时结构。
- 依赖策略。
- 数据访问策略。
- 安全、降级、成本、可观测性或事务策略（按主题选择）。
- 与 PRD / TECH / API 的关系。
- 验收门槛或架构守则。

### 可选包含

- 时序图。
- 决策记录。
- 冲突处理。
- 环境变量策略。
- Feature Flag、迁移顺序、回滚策略。

### 文档边界

架构文档负责系统级约束和跨模块边界，不能沦为单模块 PRD 或接口手册。

**arch/ 与 tech/ 的边界判据**：
- `arch/` 回答"系统整体怎么切、跨模块约束是什么"。
- `tech/` 回答"单个模块内部怎么实现"。
- 当一份文档既涉及系统级分层又涉及模块级实现时，拆分为两份：系统约束入 `arch/`，模块实现入 `tech/`，双向链接。

### 不包含

- 单个端点的完整请求响应样例全集。
- 组件级视觉设计。
- 具体测试用例列表。

### 文档关系

ARCH 是 PRD / API / TECH / SKILL 的边界上游。涉及 Skill、API、Tool、CLI 分层时，必须引用能力分层架构文档。

---

## 10. `ddd/`：领域模型与领域服务设计

### 文档类型

S01-S06 总览、单个领域系统详细设计、领域决策冻结和评审修复记录。

> `ddd/` 支持二级子目录，如 `ddd/s01-s06-detailed/` 存放单个领域的详细设计文档，根目录存放总览和决策文档。

### 命名规范

```text
DDD-S{起始编号}-S{结束编号}-{Domain-Slug}.md
DDD-S{编号}-{Domain-System-Slug}.md
DECISIONS-FROZEN.md
REVIEW-FIXES-AND-DISCUSSIONS.md
```

示例：

- `DDD-S01-S06-Domain-Data-Layer.md`
- `s01-s06-detailed/DDD-S04-Safety-Guardrail-Engine.md`

### 必须包含

- 领域定位与职责。
- 不可违反约束。
- 功能边界和跨域边界。
- 核心实体、值对象、数据结构。
- Service 函数接口。
- 输入输出契约。
- 领域流程和状态转换。
- 上下游依赖。
- 验收标准。

### 可选包含

- 训练学原理。
- LLM 是否允许介入及原因。
- 领域规则表。
- 附录、评审发现、冻结决策。

### 文档边界

DDD 定义领域层核心规则和服务契约，尤其是 S01-S06 的职责边界。

### 不包含

- 页面流程和 UI 文案。
- API transport 细节。
- 外部 Provider 协议细节。

### 文档关系

DDD 支撑 TECH、SKILL 和 DataFlow。Skill 不应绕过 DDD Service 直接读写数据库或重写领域规则。

---

## 11. `data/`：数据流设计

### 文档类型

特定业务流程的数据流完整设计，如计划生成、跑前决策、跑后决策。

### 命名规范

```text
DataFlow-{Flow-Slug}.md
```

示例：

- `DataFlow-Plan-Generation.md`
- `DataFlow-PostRun-Decision.md`

### 必须包含

- 文档视角：以数据实体为第一视角。
- 设计目标。
- 上游文档。
- 已知 Schema 不对齐或冲突说明。
- 宏观数据流图。
- 数据实体清单：产生阶段、持久化位置、消费方、生命周期。
- 每个实体的 Schema、来源、值域、必填性。
- 数据缺失策略：Default / Fallback / Reject。
- 存储、审计、幂等和时区规则。
- 跨模块字段映射。

### 可选包含

- 阶段化执行流程。
- 状态枚举映射。
- 数据质量检查。
- 审计表设计。

### 文档边界

DataFlow 负责数据如何在模块间流动，不负责产品动机或 UI 呈现。

### 不包含

- 用户故事全集。
- 视觉原型。
- 单个端点的完整 API 文档。

### 文档关系

上游引用 PRD、SKILL、DDD、TECH；下游支撑 API、TECH、TESTSET 和审计设计。发现不一致时，应在文档开头明确采用哪一版。

---

## 12. `skills/`：AI Skill 设计

### 文档类型

独立 Skill 设计文档、Skill 索引、Skill 模板、Skill 审核报告。

### 命名规范

```text
SKILL-{三位序号}-{skill-slug}.md
SKILL-INDEX-{三位序号}-{Index-Slug}.md
SKILL-TEMPLATE.md
SKILL-AUDIT-{scope}-审核报告.md
```

示例：

- `SKILL-004-plan-generation.md`
- `SKILL-INDEX-000-MVP-Skill完整清单.md`

### 必须包含

- ARCH 前置检查：确认该能力确实应该是 Skill，而不是 API / Tool。
- Skill 概述：一句话定义、业务定位、核心属性。
- 输入 Schema、输入来源、输入校验。
- 输出 Schema、前端卡片映射、副作用。
- 调用方式：触发途径、接口暴露方式、调用时序。
- 内部流程与步骤。
- 涉及的 Domain Service、LlmPort、Repository / Adapter 调用。
- 示例：典型调用、边界案例。
- 上下游关系。
- 安全与治理：幂等、安全门禁、降级。
- 错误码和变更日志。

### 可选包含

- 状态机。
- 时序图。
- LLM prompt 策略。
- 配额、成本、灰区判断说明。

### 文档边界

Skill 只描述需要判断、组合、解释、推演、生成的 AI 编排流程。

### 不包含

- 纯只读查询。
- 确定性表单写入。
- 无 LLM 判断、无多源决策、无自然语言解释的流程。
- 前端页面直接展示数据的查询路径。

### 文档关系

Skill 上接 PRD / ARCH / DDD，下接 API chat 编排、Service 和测试。Skill 不直接暴露为 REST Endpoint；前端直接调用的确定性能力应写入 `api/`。

---

## 13. `adapters/`：外部 Provider Adapter 设计

### 文档类型

外部设备、平台或协议的 Provider Adapter 设计。

### 命名规范

```text
ADAPTER-M{模块号}-{provider-or-capability}-provider.md
```

示例：`ADAPTER-M11-coros-provider.md`

### 必须包含

- 定位：Adapter 在调用链中的位置。
- 边界：做什么 / 不做什么。
- TypeScript 接口。
- 外部 MCP / SDK / API 调用映射。
- 输出到 Normalizer（详见术语定义 0.5）或上游服务的契约。
- 错误映射。
- 安全和凭证处理边界。

### 可选包含

- Provider 可用性判断。
- rawPayload 保留策略。
- 字段映射表。
- 扩展到其他 Provider 的接口一致性要求。

### 文档边界

Adapter 只负责外部协议适配和原始数据映射。

### 不包含

- 业务决策。
- 用户解释。
- 直接前端服务。
- Skill 调用逻辑。

### 文档关系

Adapter 被 Job、Service 或 Repository 边界后的集成层调用；输出通常进入 Normalizer（详见术语定义 0.5），再进入 canonical store。

---

## 14. `jobs/`：后台任务设计

### 文档类型

异步任务、定时任务、事件驱动任务设计。

### 命名规范

```text
JOB-M{模块号}-{job-slug}.md
```

示例：`JOB-M11-coros-sync.md`

### 必须包含

- 定位：Job 在系统链路中的位置。
- 非 Skill 边界。
- 触发方式：API、Cron、EventBus、用户动作。
- 输入输出接口。
- 执行流程。
- 幂等策略。
- 错误处理。
- 审计日志和可观测性。

### 可选包含

- 重试策略。
- 并发控制。
- 任务拆分和队列策略。
- 降级或部分成功策略。

### 文档边界

Job 负责后台确定性流程，不做 LLM 判断，不直接返回自然语言解释。

### 不包含

- 前端交互细节。
- 产品用户故事全集。
- Provider 协议细节；这些进入 `adapters/`。

### 文档关系

Job 通常调用 Adapter、Normalizer、Repository，并可能触发领域状态重算。它的输入输出应被 API 或事件契约引用。

---

## 15. `testset/`：测试策略与用例集

### 文档类型

模块级测试策略、测试用例设计。

### 命名规范

```text
TESTSET-M{模块号}-{Module-Slug}.md
```

示例：`TESTSET-M12-Onboarding-Identity.md`

### 必须包含

- 测试范围：In Scope / Out of Scope。
- Happy Path 端到端测试。
- 边界条件测试。
- 异常路径测试。
- 安全、鉴权、幂等、速率限制测试。
- 数据一致性和事务测试。
- 与 PRD AC、API、TECH 章节的引用关系。
- 清理策略：涉及写操作的用例必须指定具体清理资源（`DB: 表名; Redis: key pattern; 清理时机`）。

**测试用例结构化格式**：
- 每条用例必须有唯一 ID（如 `HP-01`、`BC-01`、`EX-01`）。
- 每条用例必须引用具体 PRD AC 编号（如 `AC-M12-01`）。
- 每条用例必须标注测试层级（单元 / 集成 / E2E / 性能 / 安全）。

**Traceability Matrix**：文档末尾必须包含一张 PRD AC → TESTSET 用例的映射矩阵，清楚显示每条 AC 被哪些用例覆盖。未覆盖的 AC 必须标注理由（如"前端范围"、"OAT"）。

**测试数据管理**：
- Fixture 清单必须独立维护，包含预期结果的版本号。
- Fixture 文件存放在代码仓库的 `fixtures/` 目录下，按模块组织（如 `fixtures/m12/`）。跨模块共享的公共 Fixture 存放在 `fixtures/shared/`。
- 涉及写操作的用例，清理失败时的策略：优先重试一次；若仍失败，标记环境为脏数据并阻断后续依赖该数据的用例。

### 可选包含

- 性能测试。
- 前端交互测试。
- 可观测性测试。
- 回归测试矩阵。

### 文档边界

TESTSET 定义应该验证什么和如何构造测试场景，不替代测试代码。

### 不包含

- 产品方案论证。
- 完整实现代码。
- 与模块无关的全局测试策略。

### 文档关系

TESTSET 下游对接自动化测试；上游必须引用 PRD、API、TECH。每个关键 AC 至少应能在 TESTSET 中找到对应覆盖。

---

## 16. `reviews/`：审查与对齐报告

### 文档类型

跨文档一致性审查、变更验证报告、框架对齐审查、Round 评审记录。

### 命名规范

```text
Review-{scope-or-topic}.md
Cross-Review-{scope}-Round{n}.md
{Subject}-Alignment-Review.md
```

示例：

- `Review-M10-M12-Identity-vs-Intent-v3.0.md`
- `Cross-Review-Plan-Generation-v6-Docs-Round2.md`

### 必须包含

- 评审日期。
- 评审范围。
- 变更主题或审查目标。
- 核心结论。
- 文件变更清单或覆盖检查。
- 不一致、风险、缺口。
- 修复建议或后续行动。
- 架构纪律确认。

### 可选包含

- 字段覆盖矩阵。
- 决策前后对比。
- 多轮审查记录。
- 验证证据。

### 文档边界

Review 记录「是否一致、是否可接受、还缺什么」，不应成为新的需求真源。

### 不包含

- 未经 PRD / ARCH 接受的新需求。
- 完整 API 或 TECH 重写。

### 文档关系

Review 可推动 PRD、API、TECH、DataFlow、UX 更新。结论被采纳后，应回写对应文档；Review 自身保留审查历史。

---

## 17. 文档关系图

```text
图例：→ = 上游约束/输出方向，← = 读取/引用方向，├→ = 分支输出

stg/
  → business/
    → prds/
      ├→ ux/ → ux-prototypes/
      ├→ api/
      ├→ tech/
      ├→ testset/ ← api/ + ddd/ + tech/ + data/
      └→ skills/

arch/
  → prds/
  → api/
  → tech/
  → ddd/
  → data/
  → skills/
  → jobs/ → adapters/
  → adapters/

ddd/
  → tech/
  → skills/
  → data/
  → testset/

data/
  → api/
  → tech/
  → testset/

ux-prototypes/
  → prds/（原型发现的新需求回到 PRD 确认）

reviews/
  ← 读取 stg / business / prds / ux / api / tech / arch / ddd / data / skills / testset
  → 回写上述各目录（更新对应文档）
```

---

## 18. 新增文档选择规则

新增文档前，先按问题选择目录：

| 你要回答的问题 | 应放目录 |
|----------------|----------|
| 这个产品长期做什么、不做什么？ | `stg/` |
| 这个模块解决什么商业问题？ | `business/` |
| 用户要什么、验收是什么？ | `prds/` |
| 用户界面怎么操作和感知？ | `ux/` |
| 可视化方案长什么样？ | `ux-prototypes/` |
| 前后端怎么通信？ | `api/` |
| 代码实现规则、数据模型和算法是什么？ | `tech/` |
| 系统分层和跨模块边界是什么？ | `arch/` |
| 领域服务和业务规则归属哪里？ | `ddd/` |
| 数据字段如何跨模块流动？ | `data/` |
| AI 编排如何判断、组合、解释、生成？ | `skills/` |
| 外部平台如何接入？ | `adapters/` |
| 后台任务如何运行？ | `jobs/` |
| 怎么验证？ | `testset/` |
| 多份文档是否一致？ | `reviews/` |
| 这个决策当时为什么这样定的？ | `reviews/` 或 `ddd/DECISIONS-FROZEN.md` |
| 两个模块之间的数据契约冲突了怎么办？ | `reviews/` |
| 这个 Skill 要不要降级成 API？ | `arch/` + `skills/` |
| 以上都对不上？ | 先在 `reviews/` 中讨论，确认后再创建或归入现有目录 |

**交叉场景处理**：当一份文档同时涉及多个问题域时，放入其**主要职责**对应的目录，并在"关联文档"章节链接其他相关目录的文档。

> 示例：一份同时涉及 API 契约和数据流的文档——如果核心问题是字段流转和数据生命周期，放 `data/`；如果核心问题是端点契约和请求响应格式，放 `api/`。

**新建目录规则**：当一个新领域既不属于现有 15 个目录中的任何一个，且不属于交叉场景时，应先在 `reviews/` 中讨论是否新增目录，而非自行创建。

---

## 19. 更新顺序建议

当一个模块发生需求或设计变更时，建议按以下顺序更新：

1. 若是正式真源变更，更新对应 `docs/mvp-lite/` 文档。
2. 若涉及战略或商业目标，更新 `stg/` 或 `business/`。
3. 更新 `prds/`，明确用户故事、FR、AC 和边界。
4. 更新 `arch/` 或 `ddd/`，处理分层和领域职责变化。
5. 更新 `api/`、`tech/`、`data/`、`skills/`。
6. 更新 `ux/` 和 `ux-prototypes/`。
7. 更新 `testset/`，确保 AC 和边界条件有测试覆盖。
8. 对涉及两个以上文档的跨模块变化，或影响 AC / API schema / 领域规则的变更，在 `reviews/` 中记录一致性审查和结论。小改动（如修正错别字）无需触发此步骤。

---

## 20. 最小质量检查

提交或冻结 `docs/mvp-lite/` 文档前，至少检查：

**结构检查**：
- 文件名是否符合目录前缀和模块编号规范。
- 是否说明本文定位、范围和关联文档。
- 是否明确 In Scope / Out of Scope。
- 是否标注状态：`draft`、`review`、`frozen` 或 `deprecated`。
- 是否与文档既定结论冲突；若冲突，是否标注来源和状态。
- 是否存在未解释的英文缩写、字段来源或状态枚举。
- 是否把 API、TECH、UX、TESTSET 的内容混写到不合适的文档中。
- 是否保留 Open Questions / Assumptions 或明确无未决问题。

**语义检查**：
- TESTSET 是否覆盖了 PRD 中的每条 AC（traceability matrix 存在且完整）。
- 每条 TESTSET 用例是否能追溯到至少一条 PRD AC 或 TECH 边界条件。无源用例需标注依据（如"TECH 边界值"、"安全基线"）。
- TESTSET 中断言的响应字段、构造的请求字段，是否均在对应 API 文档的 Schema 中有定义。TESTSET 覆盖的字段是否与 TECH 数据模型字段对齐（三个集合的差集应为空或有明确标注）。
- 同一模块下 PRD / API / TECH / TESTSET 的 `module_id` 是否一致。
- TECH 中定义的状态机，TESTSET 是否覆盖了所有关键转换路径。
- API 文档中定义的错误码（如 400/403/404/429），TESTSET 是否有对应覆盖用例。
