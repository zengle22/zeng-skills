---
name: zeng-i2i
description: "设计文档到实施任务转化引擎。输入 15+ 种设计文档（PRD/Arch/API/UX/Tech/Test/Data/DDD/...），校验质量 → 整合内容 → 按最小可验收颗粒度拆分 Task → 产出独立 impl 文档 + 依赖 DAG + 汇总报告。纯 LLM + 结构化输出架构。"
argument-hint: "[--dir DIR] [--feature ID] [--prd PATH] [--arch PATH] [--api PATH] [--ux PATH] [--tech PATH] [--test PATH] [--data PATH] [--ddd PATH] [--output-dir DIR] [--validate-only]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---

# zeng-i2i

Design-to-Impl Skill — 将设计文档转化为可执行的实施任务。纯 LLM + 结构化输出架构，复用 Design Check Gate Rubric 做输入校验。

## Primary Abstraction

Skill (governed capability template)

## Secondary Abstraction

Pipeline — LLM 4-phase validation + integration + decomposition + generation

## Authority

Canonical bundle: `zeng-i2i/`

## Not Equal To

- Not a document editor（只读取设计文档，不修改任何输入文件）
- Not a code generator（产出实施计划文档，不产出代码）
- Not a gate decision maker（evidence-only，汇总报告供人工确认）
- Not a replacement for `zeng-design-check`（Design Check 校验质量，I2I 做实施转化）

## Canonical Authority

- ADR: ADR-004 v1.3（设计文档到实施任务拆分技能 — I2I Design-to-Impl Skill）

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
│                                                                     │
│  Phase 4: 文档生成                                                  │
│  ──────────────────────────────────────────                         │
│  task-*.md + INDEX.md + SUMMARY.md + IMPL-INDEX.md                  │
│                                                                     │
│  输入: 设计文档路径                                                   │
│  输出: impl-{feature}-{PRD-ID}/ 目录                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
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
| T07 | UX Prototype | 可选 | 设计系统、组件规范 |
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
| `--output-dir` | 输出目录（默认 `.impl`） |
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
> 3. 为每个 Task 定义依赖关系（§3.4），包括依赖类型（FS / FF / data-dependency）
> 4. 写入 `task-list.json`（§3.6 格式）
> 5. 运行 `validate-dag.py` 校验 DAG（§3.5）
> 6. 处理校验结果：CYCLE_DETECTED → SUMMARY.md 警告；WARNING → 记录但不阻塞

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
python zeng-i2i/validate-dag.py {output_dir}/impl-{feature}-{id}/task-list.json
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
      "exception": null
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
      "exception": null
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

---

## Phase 4: 文档生成

> **执行步骤**：
> 1. 创建输出目录结构（§4.1）
> 2. 读取 `templates/` 下对应模板，按模板格式逐个生成文件
> 3. 为每个 Task 生成 `task-{nnn}-{slug}.md`（模板见 `templates/task.md`）
> 4. 生成 `INDEX.md`（模板见 `templates/index.md`）
> 5. 多 Feature 时生成 `IMPL-INDEX.md`（模板见 `templates/impl-index.md`）
> 6. 生成 `SUMMARY.md`（模板见 `templates/summary.md`）
> 7. 执行产物完整性检查（§4.5）

### 4.1 目录结构

```
{output_dir}/
├── IMPL-INDEX.md                         # 全局索引（多 Feature 时）
├── impl-{feature}-{PRD-ID}/
│   ├── SUMMARY.md                        # 汇总报告
│   ├── INDEX.md                          # Feature 索引
│   ├── feature-context.md                # Feature 聚合上下文
│   ├── task-001-{slug}.md                # Task 实施文档
│   ├── task-002-{slug}.md
│   └── ...
└── ...
```

### 4.2 命名规则

| 元素 | 规则 | 示例 |
|------|------|------|
| **目录名** | `impl-{kebab-case-feature-name}-{PRD Feature ID}` | `impl-user-registration-M01` |
| **Task 文件名** | `task-{3位序号}-{kebab-case-slug}.md` | `task-001-data-model.md` |
| **Feature ID** | 从 PRD 的 Feature/Milestone 编号继承 | `M01`, `M02` |
| **slug** | Task 核心内容的 kebab-case 摘要（≤ 5 词） | `data-model`, `api-endpoint-post-register` |

### 4.3 版本戳

所有生成的文件必须包含以下元数据头部：

```markdown
<!-- Generated by zeng-i2i v1.3 | {YYYY-MM-DDTHH:MM:SS} | source-hash: {md5 of input doc paths} -->
```

### 4.4 文件模板

#### SUMMARY.md

读取 `templates/summary.md` 模板，按模板格式填充。包含：
- 输入文档校验结果（含 CONDITIONAL 的 WARN 项）
- Feature → Task 映射
- Out of Scope 汇总
- 关键决策记录
- 风险与注意事项

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

#### feature-context.md

读取 `templates/feature-context.md` 模板。包含：
- 功能概述、用户故事、验收标准
- 业务规则、技术约束、API 契约
- 交互流程、领域模型、数据流
- 测试要点、Out of Scope

#### task-{n}-{slug}.md

读取 `templates/task.md` 模板，按模板格式填充。每个 Task 的 impl 文档必须包含：
- Task 元数据（Feature、优先级、工时、依赖、产出物）
- 验收标准
- 完整上下文（业务规则、技术约束、API 契约、交互要求、领域模型、数据流、测试要点）
- 排除项
- 实施指引（仅基于设计文档已明确信息）

### 4.5 文档状态冻结

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

### 4.6 产物完整性检查

生成完成后，自动执行以下检查：

| # | 检查项 | 规则 |
|---|--------|------|
| 1 | Task 文件数量 = INDEX.md 中的 Task 数量 | 一致性 |
| 2 | 每个 Task 的依赖项在 INDEX.md 中存在 | 引用完整性 |
| 3 | DAG 校验脚本输出 PASS | 确定性验证 |
| 4 | 每个 Task 有验收标准 | 完整性 |
| 5 | 每个 Task 有完整上下文 | 自包含性 |
| 6 | Out of Scope 项未被任何 Task 涵盖 | 范围防护 |
| 7 | 每个文件包含版本戳头部 | §4.3 规范 |
| 8 | 多 Feature 时存在 IMPL-INDEX.md | 全局索引完整性 |
| 9 | 超过 8h 的 Task 有例外理由记录 | 工时例外规则 |

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
7. **不修改源文档**：只读取设计文档（状态冻结除外，见 §4.5）
8. **可追溯**：每个 Task 信息可追溯到源设计文档的具体章节
9. **命名规范**：严格遵循 §4.2 命名规则
10. **全局索引必出**：多 Feature 时必须生成 IMPL-INDEX.md
11. **版本戳必加**：所有生成文件必须包含 §4.3 版本戳
12. **工时例外记录**：超过 8h 的 Task 必须记录例外理由
13. **文档状态准入**：仅接受 `approved` / `frozen` 状态的输入文档，`draft` / `reviewing` 状态 BLOCK 并提示需先通过评审
14. **执行后冻结**：成功生成全部 Task 文档后，将所有输入文档状态置为 `frozen`

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
zeng-i2i --dir docs/mvp-lite/

# 指定 Feature
zeng-i2i --dir docs/mvp-lite/ --feature M01

# 最小输入
zeng-i2i --prd docs/prds/PRD-M01.md --arch docs/arch/ARCH-M01.md

# 指定输出目录
zeng-i2i --dir docs/mvp-lite/ --output-dir .impl

# 仅校验
zeng-i2i --dir docs/mvp-lite/ --validate-only
```
