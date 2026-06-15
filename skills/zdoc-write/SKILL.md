---
name: zdoc-write
description: "最小 Spec 优先的标准文档撰写引擎。未显式指定类型时默认生成人类 3 分钟可审核的 Minimal Spec；显式指定时仍支持 PRD/Arch/API/UX/Tech/Testset/Data/DDD/Skill/Adapter/Job/Business/Strategy/Review/UX-Prototype/Impl/Req 等详细 SSOT 文档。"
argument-hint: "[spec|type] [--input PATH] [--module ID] [--output-dir DIR] [--project PATH]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - AskUserQuestion
---

# zdoc-write

最小 Spec 优先的标准文档撰写引擎 — 未显式指定类型时默认生成人类 3 分钟可审核、AI 可稳定执行的 Minimal Spec；显式指定类型时生成对应详细 SSOT 文档。

## Primary Abstraction

Skill (governed capability template)

## Secondary Abstraction

Pipeline — LLM 4-phase: analyze → generate → summarize → finalize

## Authority

Canonical bundle: `zdoc-write/`

## Not Equal To

- Not a document editor（从零撰写，不修改已有文档）
- Not a design check tool（不校验已有文档质量，用 `zdoc-design-check`）
- Not a task decomposer（不拆分实施任务，用 `zdoc-i2i`）
- Not a quality loop（不做多轮评审收敛，用 `zdoc-quality-loop`）

## Canonical Authority

- DOC-WRITING-GUIDE v1.0 (`docs/DOC-WRITING-GUIDE.md`)
- ITERATION-DOCUMENT-CHECKLIST v2.1 (`docs/ITERATION-DOCUMENT-CHECKLIST.md`)

## 关联文档

| 文档 | 关系 | 说明 |
|------|------|------|
| [DOC-WRITING-GUIDE](../../docs/DOC-WRITING-GUIDE.md) | 上游 | 文档类型、命名、必输章节规范 |
| [ITERATION-DOCUMENT-CHECKLIST](../../docs/ITERATION-DOCUMENT-CHECKLIST.md) | 上游 | 完整性要求、MAC 标准 |
| zdoc-design-check | 下游 | 写完后可调用做质量校验 |
| zdoc-i2i | 下游 | 校验通过后可调用做实施转化 |

---

## 支持的文档类型

| 类型代码 | 文档类型 | 目录 | 命名规范 |
|---------|---------|------|---------|
| `spec` | 最小 Spec | 用户显式 `--output-dir`；正式目录待 DOC-WRITING-GUIDE 批准 | `SPEC-M{编号}-{Slug}.md` |
| `prd` | 产品需求文档 | `prds/` | `PRD-M{编号}-{Module-Slug}.md` |
| `arch` | 架构设计 | `arch/` | `ARCH-LITE-{序号}-{Slug}.md` 或 `ARCH-M{编号}-{Slug}.md` |
| `api` | API 契约 | `api/` | `API-M{编号}-{Slug}.md` 或 `API-{序号}-{slug}.md` |
| `ux` | UX 设计规范 | `ux/` | `UX-M{编号}-{Module-Slug}.md` |
| `tech` | 技术实现设计 | `tech/` | `TECH-M{编号}-{Module-Slug}.md` |
| `testset` | 测试策略与用例集 | `testset/` | `TESTSET-M{编号}-{Module-Slug}.md` |
| `data` | 数据流设计 | `data/` | `DataFlow-{Flow-Slug}.md` |
| `ddd` | 领域模型设计 | `ddd/` | `DDD-S{起始}-S{结束}-{Slug}.md` |
| `skill` | AI Skill 设计 | `skills/` | `SKILL-{序号}-{slug}.md` |
| `adapter` | 外部 Adapter 设计 | `adapters/` | `ADAPTER-M{编号}-{provider}.md` |
| `job` | 后台任务设计 | `jobs/` | `JOB-M{编号}-{slug}.md` |
| `business` | 模块商业设计 | `business/` | `BUSINESS-M{编号}-{Module-Slug}.md` |
| `stg` | 战略与商业宪法 | `stg/` | 自定义命名 |
| `review` | 审查与对齐报告 | `reviews/` | `Review-{scope}.md` |
| `ux-proto` | UX 原型 | `ux-prototypes/` | `proto-m{编号}-{slug}.html` |
| `impl` | 实施设计 | `tech/` | `IMPL-M{编号}-{Slug}.md` |
| `req` | 需求来源文档 | `reqs/` | `REQ-{source}-{YYYYMMDD}-{Slug}.md` 或 `REQ-M{编号}-{Slug}.md` |

---

## 架构

```text
┌──────────────────────────────────────────────────────────────────┐
│              zdoc-write — 标准文档撰写引擎                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 1: 输入分析与类型识别                                      │
│  ──────────────────────────────                                  │
│  1. 解析用户输入（文本/文件/混合）                                │
│  2. 识别文档类型：显式类型优先，否则默认 spec                      │
│  3. 加载对应类型的章节规范                                         │
│  4. 分析已有内容 vs 缺失内容                                      │
│  5. 确定模块编号和命名                                            │
│                                                                  │
│  Phase 1.5: 旧接口/功能变更检测                                   │
│  ──────────────────────────────                                  │
│  1. 搜索同模块/同功能的现有文档                                    │
│  2. 提取旧接口定义（端点、Schema、字段）                           │
│  3. 与新输入做差异对比                                            │
│  4. 生成变更清单（新增/修改/删除）                                │
│  5. API 类型：强制执行；其他类型：检测到变更时执行                  │
│                                                                  │
│  Phase 2: 文档生成                                               │
│  ──────────────────────────────                                  │
│  1. 生成 YAML frontmatter                                        │
│  2. spec 使用 Minimal Spec 模板；显式类型使用详细模板              │
│  3. 填充用户提供内容                                              │
│  4. spec 不自动补关键业务事实；详细类型按原规则处理                │
│  5. spec 输出 Review Card；详细类型输出决策摘要                    │
│  6. 建立交叉引用                                                  │
│                                                                  │
│  Phase 3: 核心决策点与分歧点摘要                                  │
│  ──────────────────────────────                                  │
│  1. 识别文档中的核心决策（影响全局的设计选择）                      │
│  2. 识别分歧点（存在多种合理方案的章节）                           │
│  3. 识别开放问题和假设                                            │
│  4. 输出结构化摘要供用户确认                                      │
│                                                                  │
│  Phase 4: 最终化                                                 │
│  ──────────────────────────────                                  │
│  1. 根据用户确认更新文档                                          │
│  2. 执行完整性自检                                                │
│  3. 输出最终文档                                                  │
│                                                                  │
│  输入: 用户描述 + 可选的现有文档/上下文                            │
│  输出: Minimal Spec + Review Card，或显式详细文档 + 决策摘要       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: 输入分析与类型识别

> **执行步骤**：
> 1. 解析 `{{args}}`，确定输入模式
> 2. 读取输入内容
> 3. 识别文档类型：类型代码前缀 > 明确详细文档意图 > 默认 `spec`
> 4. 加载对应类型的结构规范
> 5. 分析已有内容 vs 缺失内容
> 6. `spec` 仅记录旧行为影响风险；详细类型按规则检测变更关键词

### 1.1 输入模式

| 模式 | 触发条件 | 行为 |
|------|---------|------|
| **类型指定** | `{{args}}` 以类型代码开头（如 `spec`、`prd`、`arch`） | 直接使用指定类型 |
| **内容驱动** | 用户描述要写什么，但未明确指定详细类型 | 默认使用 `spec` |
| **文件驱动** | `--input` 指向现有文件，且未指定类型 | 默认生成 `spec`；仅当输入文件已有明确 `doc_type` / 类型元数据时沿用该类型 |
| **混合** | 类型 + 输入文件 | 用文件内容填充指定类型的文档 |

### 1.2 文档类型识别规则

类型识别优先级固定为：

```text
1. 类型代码前缀（如 `spec`、`api`、`tech`、`prd`）
2. 用户明确要求某类详细文档
3. 其他情况默认 `spec`
```

明确 opt-in 信号：

| 用户表达 | 推断类型 |
|---------|---------|
| `api`、`API 契约`、`接口文档`、`端点定义` | `api` |
| `tech`、`技术设计`、`实现设计` | `tech` |
| `testset`、`测试用例集`、`测试策略文档` | `testset` |
| `prd`、`完整 PRD`、`产品需求文档` | `prd` |
| `arch`、`架构设计` | `arch` |
| `ux`、`UX 规范`、`交互规范` | `ux` |
| `req`、`需求来源`、`访谈纪要`、`用户反馈整理` | `req` |
| `business`、`商业设计` | `business` |
| `data`、`数据流设计`、`数据契约` | `data` |
| `ddd`、`领域模型`、`领域设计` | `ddd` |
| `skill`、`AI Skill 设计` | `skill` |
| `adapter`、`适配器设计` | `adapter` |
| `job`、`后台任务设计`、`定时任务设计` | `job` |
| `stg`、`战略`、`商业宪法` | `stg` |
| `review`、`审查报告`、`对齐报告` | `review` |
| `ux-proto`、`UX 原型`、`HTML 原型` | `ux-proto` |
| `impl`、`实施设计` | `impl` |

非 opt-in 信号：普通需求中提到“可能需要 API / 数据库 / 测试 / 技术方案”，仍默认 `spec`。

### 1.3 必输章节加载

根据识别的文档类型，加载对应的必输章节规范。详见 `references/doc-type-requirements.md`，其中按类型列出了：

- `spec` 的 Minimal Spec 固定结构和禁止项
- 详细类型必须包含的章节（来自 DOC-WRITING-GUIDE）
- 详细类型可选包含的章节
- 不包含的边界（防止越界）
- ITERATION-DOCUMENT-CHECKLIST 中对应的完整性要求

### 1.4 内容差距分析

对比用户提供内容与必输章节要求：

```markdown
## 内容差距分析

| 章节 | 状态 | 说明 |
|------|------|------|
| 文档定位 | ✅ 已有 | {用户提供} |
| 用户故事 | ⚠️ 部分 | 有 3 条，缺少 AC |
| 业务规则 | ❌ 缺失 | 需要补充 |
| 验收标准 | ⚠️ 部分 | 有 AC 但缺少 Given-When-Then 格式 |
```

---

## Phase 1.5: 旧接口/功能变更检测

> **目的**：当撰写涉及旧功能变更的文档时，自动搜索同模块/同功能的现有文档，提取旧定义并与新输入做差异对比，生成变更标注。
>
> **强制级别**：API 文档为 **强制执行**（写 API 文档时必须运行此阶段）；其他类型文档为 **检测到变更时执行**（用户描述中提及"修改""变更""升级""迁移"等关键词时触发）。

### 1.5.1 搜索策略

根据当前文档类型和模块编号，搜索现有文档：

| 文档类型 | 搜索目录 | 搜索模式 | 说明 |
|---------|---------|---------|------|
| `api` | `**/api/` | `API-M{编号}-*.md`, `API-*.md` | **强制**：必须搜索 |
| `prd` | `**/prds/` | `PRD-M{编号}-*.md` | 检测到变更时搜索 |
| `tech` | `**/tech/` | `TECH-M{编号}-*.md`, `IMPL-M{编号}-*.md` | 检测到变更时搜索 |
| `arch` | `**/arch/` | `ARCH-M{编号}-*.md`, `ARCH-LITE-*.md` | 检测到变更时搜索 |
| `ux` | `**/ux/` | `UX-M{编号}-*.md` | 检测到变更时搜索 |
| `ddd` | `**/ddd/` | `DDD-S{编号}-*.md` | 检测到变更时搜索 |
| `data` | `**/data/` | `DataFlow-*.md` | 检测到变更时搜索 |
| `testset` | `**/testset/` | `TESTSET-M{编号}-*.md` | 检测到变更时搜索 |
| `skill` | `**/skills/` | `SKILL-*.md` | 检测到变更时搜索 |
| `adapter` | `**/adapters/` | `ADAPTER-M{编号}-*.md` | 检测到变更时搜索 |
| `job` | `**/jobs/` | `JOB-M{编号}-*.md` | 检测到变更时搜索 |
| `business` | `**/business/` | `BUSINESS-M{编号}-*.md` | 检测到变更时搜索 |

**搜索工具**：使用 Glob 扫描文件，使用 Grep 提取关键定义（端点、Schema、字段名等）。

### 1.5.2 变更检测维度

#### API 文档（强制）

对找到的每个旧 API 文档，提取并对比以下维度：

| 维度 | 提取方法 | 对比方式 |
|------|---------|---------|
| **端点列表** | Grep `## ` 章节标题 + 方法+路径模式（如 `POST /api/v1/...`） | 新旧端点集合对比 |
| **请求 Schema** | 提取字段名、类型、必填性 | 逐字段对比 |
| **响应 Schema** | 提取字段名、类型、嵌套结构 | 逐字段对比 |
| **错误码** | 提取错误码列表和描述 | 新旧错误码集合对比 |
| **鉴权方式** | 提取认证/授权描述 | 策略变更检测 |
| **速率限制** | 提取限流规则 | 参数变更检测 |
| **幂等性** | 提取幂等策略 | 策略变更检测 |

#### 其他文档类型（检测到变更时）

| 文档类型 | 检测维度 |
|---------|---------|
| `prd` | 用户故事增删、AC 变更、业务规则修改、范围变化 |
| `tech` | 数据模型字段变更、状态机转换变更、算法修改 |
| `arch` | 分层边界调整、依赖策略变更、技术选型替换 |
| `ux` | 交互流程变更、状态表达修改、设计令牌变更 |
| `ddd` | 领域边界调整、实体/值对象变更、Service 接口修改 |
| `data` | 数据实体字段变更、流转路径修改、Schema 变化 |
| `testset` | 测试用例增删、覆盖范围变更 |
| `skill` | 输入/输出 Schema 变更、内部流程修改 |
| `adapter` | 外部协议映射变更、字段转换修改 |
| `job` | 触发方式变更、执行流程修改 |

### 1.5.3 变更分类

对检测到的差异进行分类：

| 变更类型 | 标记 | 说明 | 风险等级 |
|---------|------|------|---------|
| **新增端点/字段** | `+ADD` | 旧文档中不存在，新文档中新增 | 低 — 向后兼容 |
| **修改端点/字段** | `~MOD` | 旧文档中存在但定义变更 | **高** — 可能破坏兼容性 |
| **删除端点/字段** | `-DEL` | 旧文档中存在但新文档中移除 | **高** — 破坏性变更 |
| **重命名** | `~REN` | 字段/端点名称变更 | 中 — 需要迁移 |
| **类型变更** | `~TYPE` | 字段类型或格式变更 | 高 — 可能导致解析失败 |
| **行为变更** | `~BEH` | 相同接口但行为语义变更 | 高 — 需要客户端适配 |

### 1.5.4 API 变更报告格式

API 文档检测到变更时，必须生成变更报告：

```markdown
## API 变更检测报告

### 旧文档来源
- **文件**: [{旧文档文件名}]({相对路径})
- **最后更新**: {日期}
- **模块**: {module_id}

### 变更清单

| # | 变更类型 | 端点/字段 | 旧定义 | 新定义 | 影响 |
|---|---------|----------|--------|--------|------|
| 1 | `~MOD` | `POST /api/v1/users` | 响应含 `user_id: string` | 响应含 `user_id: int64` | 客户端需适配类型变更 |
| 2 | `+ADD` | `GET /api/v1/users/:id/profile` | — | 新增端点 | 向后兼容 |
| 3 | `-DEL` | `DELETE /api/v1/users/:id` | 存在 | 移除 | 破坏性变更，需确认 |
| 4 | `~REN` | `POST /api/v1/plans` 字段 `plan_name` | `plan_name` | `title` | 需要迁移 |

### 破坏性变更确认

以下变更可能影响现有客户端，需要用户确认：

1. **{变更描述}** — {影响范围} — 请确认是否执行此变更
2. ...

### 迁移注意事项

- {迁移步骤 1}
- {迁移步骤 2}

### 旧文档中存在但新文档未提及的端点

| 端点 | 旧文档章节 | 状态 |
|------|-----------|------|
| `GET /api/v1/old-endpoint` | §3.2 | 未在新文档中提及，可能被遗漏 |
```

### 1.5.5 非 API 文档变更标注格式

其他文档类型检测到变更时，在文档对应章节内嵌入变更标注：

```markdown
### 字段变更

| 字段 | 旧定义 | 新定义 | 变更类型 |
|------|--------|--------|---------|
| `risk_level` | enum: low/medium/high | enum: low/medium/high/critical | `~MOD` — 新增 critical 值 |

<!-- [变更标注] 本字段在 TECH-M12 v1.0 中定义为 3 级枚举，本次变更为 4 级。
     旧文档: TECH-M12-Onboarding-Identity.md §3.2
     影响: 所有读取 risk_level 的下游服务需要适配新枚举值 -->
```

### 1.5.6 未找到旧文档的处理

| 场景 | 处理方式 |
|------|---------|
| 搜索同模块文档，未找到任何旧文档 | 标注为"首次撰写，无历史版本"，跳过变更检测 |
| 搜索到旧文档但内容为空或占位符 | 标注为"旧文档内容不完整，跳过变更检测" |
| 搜索到旧文档但模块编号不完全匹配 | 列出疑似相关文档，由用户确认是否对比 |

### 1.5.7 输出物

Phase 1.5 的产出：

1. **`change-report.json`**：结构化变更检测结果（供后续阶段消费）
2. **变更标注**：注入到 Phase 2 生成的文档中

```json
{
  "doc_type": "api",
  "module_id": "M12",
  "old_doc_ref": {
    "path": "docs/mvp-lite/api/API-M12-Onboarding-Identity.md",
    "last_updated": "2026-05-20",
    "status": "frozen"
  },
  "changes_detected": true,
  "total_changes": 4,
  "breaking_changes": 1,
  "change_list": [
    {
      "id": "CHG-001",
      "type": "MOD",
      "target": "POST /api/v1/users",
      "dimension": "response_schema",
      "old_value": "user_id: string",
      "new_value": "user_id: int64",
      "breaking": true,
      "old_doc_ref": "API-M12-Onboarding-Identity.md §3.1"
    }
  ],
  "unmentioned_endpoints": [
    {
      "endpoint": "GET /api/v1/old-endpoint",
      "old_doc_section": "§3.2",
      "status": "potentially_missed"
    }
  ]
}
```

---

## Phase 2: 文档生成

> **执行步骤**：
> 1. 生成 YAML frontmatter
> 2. `spec` 使用 `templates/minimal-spec.md`；详细类型使用对应章节规范
> 3. 填充用户已有内容
> 4. `spec` 不注入完整变更报告，仅记录旧行为影响风险；详细类型按 Phase 1.5 注入变更标注
> 5. `spec` 不自动补关键业务事实；详细类型缺失内容标记 [需确认]
> 6. 建立与其他文档的交叉引用

### 2.1 Frontmatter 规范

`spec` 使用最小 frontmatter：

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

详细类型使用标准 SSOT frontmatter：

```yaml
---
title: "{中文标题}"
status: draft
created: "{YYYY-MM-DD}"
updated: "{YYYY-MM-DD}"
module_id: ""        # 模块级文档必须填写
layer: ""            # L0-L3 层级
priority: ""         # P0/P1/P2
related_docs: []
relationships:
  depends_on: []
  implements: []
  constrains: []
  references: []
  supersedes: []
  superseded_by: []
---
```

### 2.2 章节生成规则

按类型模板生成：

**Minimal Spec 固定章节**（`spec`）：
- Goal
- Scope
- Context Diagram
- Business Rules
- Constraints
- Acceptance
- Risks（可选）

**详细类型通用章节**：
- 文档定位：一句话说明本文负责回答什么问题
- 关联文档：列出上下游文档
- 范围边界：In Scope / Out of Scope
- 验收或检查点：判断本文描述成立的条件

**类型特定章节**：参见 `references/doc-type-requirements.md`

**req 类型章节生成规则**：

req 文档按以下结构生成章节：

| 章节 | 内容 | 说明 |
|------|------|------|
| §1 需求来源 | 来源类型、提供方、获取方式、原始出处、获取日期 | 保留需求原始出处信息 |
| §2 原始需求描述 | 直接记录原始语言、上下文背景、相关方 | 不翻译为产品术语 |
| §3 痛点或机会分析 | 痛点描述、机会描述、现有替代方案 | 分析价值空间 |
| §4 初步价值判断 | 用户价值、商业价值、技术可行性、合规/风险 | 四维度快速评估 |
| §5 转化为 PRD 的关键问题 | 需要在 PRD 阶段回答的问题清单 | 作为 PRD 撰写输入 |
| §6 关联文档 | 上下游文档引用 | 主要是未来的 PRD |
| §7 范围边界 | In Scope / Out of Scope | 初步范围判断 |
| §8 验收或检查点 | 需求来源确认、完整性、转化决策 | 可勾选的检查项 |
| §9 变更日志 | 日期/变更/变更人 | 版本追踪 |

**testset 类型章节生成规则**：

testset 文档必须按以下 9 节标准结构生成章节（对齐 TD-8）：

| 章节 | 内容 | 说明 |
|------|------|------|
| §1 测试范围 | In Scope / Out of Scope | 保持不变 |
| §2 测试策略 | 测试分层策略 + 执行顺序 + 并行/串行 + 失败重试 + 阻断条件 | 从原 §10 测试分层策略前置，扩充为完整策略章节 |
| §3 测试用例 | 按类型分 3.1-3.8 子章节 | 合并原 §2-§9 为子章节 |
| §4 测试数据 | fixture 清单、数据隔离、清理策略 | 保持不变 |
| §5 环境需求 | DB、缓存、测试框架、Mock、CI/CD、数据隔离 | 新增 |
| §6 执行计划 | 执行顺序、依赖关系、并行策略、失败重试、阻断条件 | 新增 |
| §7 准入/准出标准 | 准入条件、准出条件、阻断条件 | 新增 |
| §8 风险与应对 | 风险/影响/缓解措施三列表 | 新增 |
| §9 质量指标 | 指标/目标/说明三列表 | 新增 |
| 附录 A | 测试执行检查清单 | 从原 §12 移至附录 |
| 附录 B | Traceability Matrix | 从原 §13 移至附录 |
| 附录 C | 变更日志 | 保持 |

### 2.3 内容填充策略

| 内容来源 | `spec` 处理方式 | 详细类型处理方式 |
|---------|----------------|------------------|
| 用户明确提供 | 直接使用，保持原意 | 直接使用，保持原意 |
| 用户暗示但未展开 | 可整理表达，但不得写成关键事实 | 适度补充，标记 [需确认] |
| Goal 缺失 | 停止并询问 | 标记 [需确认] 后补充 |
| Scope 缺失 | 在 Review Card 提问，不生成默认范围 | 标记 [需确认] 后补充 |
| Business Rules 缺失 | 列出需要补充的问题，不写入正式规则 | 标记 [需确认] 后补充 |
| Constraints 缺失 | 放入 Review Card 的 AI 假设，不写入正式约束 | 标记 [需确认] 后补充 |
| Acceptance 缺失 | 放入 Review Card；如写正文，只能作为 `# Acceptance` 下的 `Draft` 小节 | 标记 [需确认] 后补充 |
| Context Diagram 缺失 | 仅根据用户明确实体关系绘制；不足时写“未提供足够上下文” | 可按详细类型补充图示 |
| 可选章节 | 仅在用户提供相关内容时包含 | 仅在用户提供相关内容时包含 |
| Out of Scope | 必须具体；缺失时提问 | 必须至少列出 3 项，防止 scope creep |

### 2.4 补充标记规范

AI 补充的内容使用以下标记，确保用户知道哪些是 AI 生成的：

```markdown
<!-- [需确认] AI 根据上下文补充，可能不准确 -->
{补充内容}

<!-- [AI 建议] 基于文档类型规范自动生成 -->
{建议内容}
```

### 2.5 交叉引用

使用 Markdown 相对路径建立文档间引用：

```markdown
[PRD-M12-Onboarding-Identity](../prds/PRD-M12-Onboarding-Identity.md)
```

frontmatter 中的 `related_docs` 使用纯文件名。

### 2.6 命名规则

遵循 DOC-WRITING-GUIDE §0.6：

- 文件名：英文 kebab-case，含类型前缀和模块编号
- frontmatter `title`：中文
- 章节标题：中文为主，技术术语保留英文
- 序号：三位补零格式（`001`、`002`）

### 2.7 变更标注注入

当 Phase 1.5 检测到旧文档变更时，按以下规则注入变更标注：

#### API 文档

在文档中新增 **"变更说明"** 章节（位于"文档定位"之后、具体端点定义之前）：

```markdown
## 变更说明

> 本文档基于 [{旧文档文件名}]({相对路径}) 进行变更，以下为变更清单。

### 变更概要

| 变更类型 | 数量 |
|---------|------|
| 新增端点 | {N} |
| 修改端点 | {N} |
| 删除端点 | {N} |
| 字段变更 | {N} |

### 破坏性变更

> ⚠️ 以下变更可能影响现有客户端，需确认迁移方案。

1. **{端点} {变更描述}** — {影响}
2. ...

### 详细变更清单

| # | 类型 | 端点/字段 | 旧定义 | 新定义 |
|---|------|----------|--------|--------|
| 1 | `~MOD` | {target} | {old} | {new} |
| 2 | `+ADD` | {target} | — | {new} |

### 旧文档中未提及的端点

| 端点 | 来源 | 处理建议 |
|------|------|---------|
| {endpoint} | {old_doc} §{section} | {保留/移除/迁移} |
```

在 frontmatter 中关联旧文档：

```yaml
related_docs:
  - "{旧文档文件名}"
relationships:
  supersedes:
    - "{旧文档文件名}"
```

#### 其他文档类型

在变更涉及的章节内，紧跟变更内容后插入标注块：

```markdown
<!-- [变更标注] 相对于 {旧文档文件名} §{section} 的变更
     变更类型: {~MOD/+ADD/-DEL}
     旧定义: {旧内容摘要}
     影响: {影响范围}
-->
```

---

## Phase 3: Review Card / 决策摘要

> **目的**：在生成文档后，识别需要用户确认的关键点，避免 AI 自行决策导致语义漂移。
>
> **spec 输出**：使用 `templates/review-card.md`，控制在 1 页内，最多 3 个待确认决策、5 个假设、5 个风险。
>
> **详细类型输出**：使用 `templates/decision-summary.md`，保留核心决策点、分歧点、变更检测和完整性自检。
>
> **核心原则**（来自 ITERATION-DOCUMENT-CHECKLIST）：凡是需要人类反复讨论、拍板、确认的内容，都必须明确标记，让用户决策。

### 3.1 识别维度

#### 核心决策点

影响全局的设计选择，一旦确定难以修改：

| 决策类型 | 示例 | 为什么需要确认 |
|---------|------|--------------|
| **范围边界** | Out of Scope 列表 | 直接影响 scope creep 防控 |
| **优先级** | P0/P1/P2 划分 | 影响资源分配 |
| **技术选型** | 框架、数据库、AI Provider | 影响整体架构 |
| **同步/异步** | API 调用策略 | 影响用户体验和系统设计 |
| **存储方案** | 关系型 vs 文档型、JSONB vs 规范化 | 影响数据模型 |

#### 分歧点

存在多种合理方案的章节：

| 分歧类型 | 示例 | 为什么是分歧点 |
|---------|------|--------------|
| **阈值取值** | 超时时间、重试次数、速率限制 | 缺乏数据支撑时有多种合理选择 |
| **异常处理** | 降级策略、错误码设计 | 不同团队有不同偏好 |
| **命名** | 字段名、枚举值、API 路径 | 有多种命名惯例 |
| **覆盖范围** | 测试分层策略、性能指标 | 取决于团队标准和资源 |

#### 开放问题

文档中无法确定、需要后续决策的内容。

### 3.2 摘要输出格式

#### spec Review Card

```markdown
# Review Card — {文档标题}

## 1. 这份 Spec 要解决什么？

{1-3 句话}

## 2. 需要确认的决策

- [ ] D1: {决策}
- [ ] D2: {决策}
- [ ] D3: {决策}

## 3. AI 假设

- H1: {假设}
- H2: {假设}

## 4. 主要风险

- RISK1: {风险}

## 5. 是否进入 AI 实施？

- [ ] 可以进入实施
- [ ] 需要补充后再实施：{原因}
```

#### 详细类型决策摘要

```markdown
## 文档摘要 — {文档标题}

### 文档概况
- **类型**: {doc_type}
- **模块**: {module_id}
- **章节完整性**: {已填充}/{总计} 个必填章节
- **补充内容**: {N} 处 [需确认]

### 核心决策点（需要您确认）

#### 1. {决策标题}
- **位置**: §{章节号}
- **当前方案**: {AI 生成的默认方案}
- **备选方案**: {其他合理方案}
- **影响范围**: {哪些章节/模块受影响}
- **建议**: {AI 的推荐及理由}
- **请确认**: {具体问题}

#### 2. ...

### 分歧点（可能需要讨论）

#### 1. {分歧标题}
- **位置**: §{章节号}
- **方案 A**: {描述}
- **方案 B**: {描述}
- **权衡**: {各方案的 trade-off}
- **请确认**: 选择哪个方案？

### 开放问题
1. {问题 1} — 建议 {处理方式}
2. {问题 2} — 建议 {处理方式}

### 下一步
请确认上述决策点和分歧点后，我将更新文档并生成最终版本。
```

---

## Phase 4: 最终化

> **执行步骤**：
> 1. 根据用户确认更新文档
> 2. 执行完整性自检
> 3. 输出最终文档

### 4.1 用户确认处理

- 用户确认的决策：更新文档，移除 [需确认] 标记
- 用户修改的方案：按用户选择更新
- 用户跳过的点：保留 [需确认] 标记，在 Open Questions 中记录

### 4.2 完整性自检

输出文档前执行以下检查：

| # | 检查项 | 规则 |
|---|--------|------|
| 1 | Frontmatter 完整 | title、status、created 必填；`spec` 还需 doc_id、doc_type |
| 2 | spec 章节完整 | Goal、Scope、Context Diagram、Business Rules、Constraints、Acceptance、Risks（可选） |
| 3 | 详细类型通用章节完整 | 文档定位、关联文档、范围边界、验收标准 |
| 4 | 类型必填章节完整 | 详细类型按类型要求检查 |
| 5 | 无占位符残留 | `TODO`、`TBD`、`{placeholder}` 已清理或标注 |
| 6 | 交叉引用有效 | 链接的目标文件存在或为已知文档 |
| 7 | 命名规范 | 文件名、slug 符合规范 |
| 8 | spec 无禁止项 | 不含类设计、函数设计、伪代码、数据库表设计、接口定义、任务拆解、实现步骤、技术选型细节 |
| 9 | spec 关键事实未被 AI 静默补齐 | Goal 缺失必须停止；候选约束和 Draft Acceptance 不写成正式事实 |
| 10 | API 变更标注完整 | API 文档必须包含"变更说明"章节或"首次撰写"标注 |
| 11 | 破坏性变更已确认 | 检测到破坏性变更时，决策摘要中必须包含确认项 |

### 4.3 输出

最终输出两个文件：

**spec**：
1. **文档本体**：`{output_dir}/SPEC-M{编号}-{Slug}.md`
2. **Review Card**：`{output_dir}/.zdoc-write/SPEC-M{编号}-{Slug}-review-card.md`

在 `docs/mvp-lite/specs/` 未被 DOC-WRITING-GUIDE 批准前，如果用户没有提供 `--output-dir`，先询问输出目录，或只在对话中返回 Minimal Spec 草案，不写文件。

**详细类型**：
1. **文档本体**：`{output_dir}/{type_prefix}-{module_id}-{slug}.md`
2. **决策摘要**：`{output_dir}/.zdoc-write/{doc_id}-decisions.md`

---

## Workflow Boundary

- **Input**: 用户描述 + 可选的现有文档/上下文
- **Output**: Minimal Spec + Review Card，或显式详细 SSOT 文档 + 决策摘要
- **Out of scope**:
  - 不修改已有文档（除非用户明确要求更新）
  - 不校验文档质量（用 `zdoc-design-check`）
  - 不拆分实施任务（用 `zdoc-i2i`）
  - 不做多轮评审（用 `zdoc-quality-loop`）

## Non-Negotiable Rules

1. **默认 spec**：用户未显式指定类型时，默认生成 Minimal Spec，不按技术关键词推断为 PRD/API/TECH/TESTSET
2. **详细类型 opt-in**：只有类型代码前缀或明确详细文档意图，才生成对应详细 SSOT 文档
3. **spec 固定章节**：Goal、Scope、Context Diagram、Business Rules、Constraints、Acceptance、Risks（可选）
4. **spec 禁止实现内容**：不得包含类设计、函数设计、伪代码、数据库表设计、接口定义、任务拆解、实现步骤、技术选型细节
5. **spec 不猜关键事实**：AI 不得把自行推断的 Goal、Scope、Business Rules、Constraints、Acceptance 写成正式事实
6. **Goal 缺失必须停止**：spec 缺失 Goal 时必须询问，不生成默认目标
7. **Review Card 限长**：spec 的 Review Card 最多 1 页、3 个决策、5 个假设、5 个风险
8. **详细类型必填章节不跳过**：显式详细类型必须按 DOC-WRITING-GUIDE / doc-type-requirements 生成必填章节
9. **补充内容必须标记**：详细类型中 AI 补充的内容必须标记 [需确认]，不得冒充用户输入
10. **Out of Scope 必须具体**：详细类型至少列出 3 项具体排除内容；spec 缺失范围时提问
11. **不越界**：不同类型文档的内容不混写（如 PRD 不写 API 端点细节；spec 不写实现设计）
12. **命名规范**：严格遵循 DOC-WRITING-GUIDE §0.6；spec 使用 `SPEC-M{编号}-{Slug}.md`
13. **状态初始为 draft**：新文档 status 初始为 draft，不擅自设为 approved/frozen
14. **API 变更检测强制**：撰写 API 文档时，必须执行 Phase 1.5 搜索同模块旧 API 文档并生成变更标注。未搜索到旧文档时标注"首次撰写"，搜索到旧文档时必须生成完整变更清单和破坏性变更确认
15. **spec 变更检测轻量化**：spec 只记录旧行为影响风险，不输出完整变更检测报告
16. **其他详细类型变更检测**：撰写非 API 详细文档时，如果用户描述中包含变更/修改/升级/迁移等关键词，必须执行 Phase 1.5 搜索相关旧文档。未触发变更关键词时可跳过
17. **spec 输出目录受限**：在 `docs/mvp-lite/specs/` 未被 DOC-WRITING-GUIDE 批准前，未提供 `--output-dir` 时先询问或只返回对话内草案，不写文件

---

## Usage

```bash
# 默认：生成 Minimal Spec（需显式输出目录；否则只返回草案或询问目录）
zdoc-write "支持根据最近 7 天训练情况自动调整训练计划" --module M12 --output-dir docs/drafts/specs/

# 显式指定 spec
zdoc-write spec --module M12 --output-dir docs/drafts/specs/

# 显式指定详细 PRD
zdoc-write prd --module M12 --output-dir docs/mvp-lite/prds/

# 明确要求 API 契约
zdoc-write api --module M12 --output-dir docs/mvp-lite/api/ --project .

# 明确要求技术设计
zdoc-write tech --module M12 --project . --output-dir docs/mvp-lite/tech/

# 从现有文件补充详细 PRD
zdoc-write prd --input docs/drafts/prd-notes.md --output-dir docs/mvp-lite/prds/
```

---

## Compatibility Note

本技能遵循 DOC-WRITING-GUIDE v1.0、ITERATION-DOCUMENT-CHECKLIST v2.1 和 ADR-006。默认输出 Minimal Spec；详细 SSOT 文档需显式 opt-in。`spec` 的正式目录 `docs/mvp-lite/specs/` 需先由 DOC-WRITING-GUIDE 批准，批准前只能写入用户显式指定目录或返回对话内草案。
