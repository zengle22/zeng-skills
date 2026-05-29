---
title: "zgsd-plan-phase 桥接方案：Impl Task Pack 到 GSD PLAN"
doc_id: "ZGSD-PLAN-PHASE-BRIDGE-001"
status: draft
created: "2026-05-28"
updated: "2026-05-28"
layer: "L2"
source_context:
  - "docs/mvp-lite/impl/impl-formal-app-foundation-ARCH-LITE-007/"
  - ".planning/ROADMAP.md"
  - ".planning/REQUIREMENTS.md"
  - "$HOME/.codex/get-shit-done/workflows/plan-phase.md"
---

# zgsd-plan-phase 桥接方案

> 目标：封装一个 `zgsd-plan-phase` skill，将 `docs/mvp-lite/impl/*` 中已经拆解好的 implementation task pack 转换为 GSD 可执行的 `*-PLAN.md`，然后复用 `$gsd-execute-phase` 执行、总结和验证。

---

## 1. 背景

当前项目同时存在两套互补体系：

| 体系 | 主要职责 | 当前产物 |
|------|----------|----------|
| `docs/mvp-lite/impl` | 从 ARCH / PRD / TESTSET 拆解出可实施 task pack | `feature-context.md`、`task-list.json`、`task-XXX.md`、`dag-validation.json` |
| GSD | 按 phase 生成 executable plan，按 wave 执行和验证 | `.planning/ROADMAP.md`、`.planning/phases/*/*-PLAN.md`、`*-SUMMARY.md` |

`gsd-plan-phase` 的默认行为是重新读取 roadmap / context / research，然后由 `gsd-planner` 再拆一轮 PLAN。这对普通 GSD 项目合理，但对本项目已经完成拆分的 task pack 有两个风险：

1. **重复规划**：`impl` task 已经包含 DAG、验收标准、源文档和依赖关系，再让 planner 自由拆分会产生二次发散。
2. **语义丢失**：`impl` task 中的 acceptance criteria、source docs、dependency type 可能在重新规划时被压缩或遗漏。
3. **审计链断裂**：执行结果无法稳定追溯到具体 `task-XXX.md` 和 `task-list.json` source hash。

因此需要一个专用桥接层：保留 `impl` 作为任务真源，只把它翻译成 GSD execute-phase 能消费的 PLAN 协议。

---

## 2. 设计目标

### 2.1 正向目标

1. **确定性转换**：同一个 task pack 在相同配置下生成相同的 `.planning/phases/*-PLAN.md`。
2. **覆盖完整**：每个 impl task 必须且只能映射到一个 GSD plan 的一个或多个 XML task。
3. **保持 DAG**：impl task 的依赖关系必须体现在 GSD plan 的 `wave` 和 `depends_on` 中。
4. **保留验收标准**：impl task 的 acceptance criteria 必须完整进入 PLAN 的 `<acceptance_criteria>`。
5. **复用 GSD 执行器**：不重写 `$gsd-execute-phase`，只生成它能读取的标准 PLAN。
6. **可审计**：生成 bridge manifest，记录 source task、plan、hash、requirements coverage、DAG 校验结果。
7. **符合项目工作协议**：每个 PLAN 明确要求执行前读取 `AGENTS.md`、`AI_CONSTITUTION.md`、`rules/agent-coding-guardrails.md` 和相关源文档。

### 2.2 非目标

1. 不替代 `$gsd-execute-phase`。
2. 不替代 GSD 的 SUMMARY / verify / ship 流程。
3. 不把所有 impl task 合并为单个巨型 PLAN。
4. 不允许 planner 自由新增或删除 impl task 范围。
5. 不在 bridge 阶段直接修改业务代码。

---

## 3. 总体方案

新增一个技能：

```text
zgsd-plan-phase
```

推荐调用：

```bash
$zgsd-plan-phase 0 --impl docs/mvp-lite/impl/impl-formal-app-foundation-ARCH-LITE-007
```

执行结果：

```text
.planning/phases/00-formal-app-foundation/
  00-CONTEXT.md
  00-TASK-BRIDGE.json
  00-01-PLAN.md
  00-02-PLAN.md
  ...
```

后续执行：

```bash
$gsd-execute-phase 0
```

`zgsd-plan-phase` 是 `impl task pack -> GSD PLAN` 的 adapter。它替代 `$gsd-plan-phase` 的 planning agent 部分，但保留 GSD phase directory、PLAN contract、wave execution、SUMMARY 和 verification 语义。

---

## 4. 输入协议

### 4.1 必需输入

| 输入 | 说明 |
|------|------|
| `--phase <n>` | GSD roadmap phase 编号，如 `0` |
| `--impl <dir>` | impl task pack 目录 |

### 4.2 impl task pack 目录要求

目录内至少包含：

```text
feature-context.md
INDEX.md
SUMMARY.md
task-list.json
dag-validation.json
task-001-*.md
task-002-*.md
...
```

当前 Phase 0 示例：

```text
docs/mvp-lite/impl/impl-formal-app-foundation-ARCH-LITE-007/
```

### 4.3 GSD 项目要求

项目根目录必须包含：

```text
.planning/ROADMAP.md
.planning/REQUIREMENTS.md
.planning/STATE.md
AGENTS.md
AI_CONSTITUTION.md
rules/agent-coding-guardrails.md
```

如果缺少 `.planning`，提示先运行 GSD milestone 初始化流程，而不是由 bridge 自动创建项目级 planning。

---

## 5. 输出协议

### 5.1 Phase 目录

phase 目录命名沿用 GSD：

```text
.planning/phases/{padded-phase}-{phase-slug}/
```

Phase 0 示例：

```text
.planning/phases/00-formal-app-foundation/
```

phase slug 从 `.planning/ROADMAP.md` 的 phase title 派生；如果派生失败，使用 `task-list.json.feature_name` 的 slug。

### 5.2 CONTEXT.md

生成：

```text
00-CONTEXT.md
```

内容角色：

1. 声明 impl task pack 是本 phase 的 locked implementation decisions。
2. 聚合 `feature-context.md` 的技术边界。
3. 引用 `SUMMARY.md` 的风险和关键决策。
4. 引用 `INDEX.md` 的拓扑顺序和关键路径。
5. 明确 canonical refs：ARCH / TESTSET / task files / guardrails。

### 5.3 PLAN.md

生成多个：

```text
00-01-PLAN.md
00-02-PLAN.md
...
```

每个 PLAN 必须满足 GSD contract：

```yaml
---
phase: 00-formal-app-foundation
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified: []
autonomous: true
requirements: []
user_setup: []
must_haves:
  truths: []
  artifacts: []
  key_links: []
---
```

正文必须包含：

```text
<objective>
<execution_context>
<context>
<tasks>
<verification>
<success_criteria>
<output>
```

每个 XML task 必须包含：

```text
<name>
<files>
<read_first>
<action>
<verify>
<acceptance_criteria>
<done>
```

### 5.4 Bridge Manifest

生成：

```text
00-TASK-BRIDGE.json
```

建议结构：

```json
{
  "schema_version": "1.0",
  "phase": "0",
  "phase_dir": ".planning/phases/00-formal-app-foundation",
  "impl_dir": "docs/mvp-lite/impl/impl-formal-app-foundation-ARCH-LITE-007",
  "feature_id": "ARCH-LITE-007",
  "source_hash": "sha256:...",
  "generated_at": "2026-05-28T00:00:00+08:00",
  "dag": {
    "status": "PASS",
    "topological_order": []
  },
  "requirements_coverage": {
    "required": ["FOUND-1", "FOUND-2", "FOUND-3", "FOUND-4", "FOUND-5", "FOUND-6"],
    "covered": [],
    "missing": []
  },
  "plans": [
    {
      "plan_id": "00-01",
      "wave": 1,
      "source_tasks": ["task-001"],
      "requirements": ["FOUND-1"],
      "depends_on": [],
      "files_modified": []
    }
  ],
  "task_mapping": {
    "task-001": {
      "plan_id": "00-01",
      "task_file": "task-001-directory-structure.md",
      "status": "mapped"
    }
  },
  "validation": {
    "all_tasks_mapped_once": true,
    "plan_dependencies_respect_task_dag": true,
    "same_wave_file_overlap": false
  },
  "path_normalization": {
    "app_dir": "apps/ai-coach-skill",
    "normalized_paths": [
      {
        "original": "src/lib/ai/provider.factory.ts",
        "normalized": "apps/ai-coach-skill/src/lib/ai/provider.factory.ts"
      },
      {
        "original": "tests/unit/env.test.ts",
        "normalized": "apps/ai-coach-skill/tests/unit/env.test.ts"
      }
    ]
  }
}
```

---

## 6. 转换规则

### 6.1 Task 到 PLAN 的映射

| Impl 字段 | GSD 字段 |
|----------|----------|
| `id` | XML task name 前缀 |
| `name` | XML task name |
| `priority` | PLAN notes / manifest |
| `estimated_hours` | manifest，不作为 GSD 执行 gate |
| `dependencies` | PLAN `depends_on` 和 `wave` 计算 |
| `dependency_type` | 判断是否可同 wave 并行 |
| `acceptance_criteria` | `<acceptance_criteria>` |
| `source_docs` | `<read_first>` 和 CONTEXT canonical refs |
| `task-XXX.md` 正文 | `<action>` 的主要来源 |

### 6.2 Requirements 映射

从 `.planning/ROADMAP.md` 的 Phase Requirements 获取：

```text
FOUND-1, FOUND-2, FOUND-3, FOUND-4, FOUND-5, FOUND-6
```

再按 task 的 source docs 和验收项归类：

| Requirement | 覆盖来源 |
-------------|----------|
| FOUND-1 | 目录结构、分层边界、占位文件 |
| FOUND-2 | env 治理、secret 边界 |
| FOUND-3 | Drizzle / Supabase / Redis |
| FOUND-4 | AI Provider factory |
| FOUND-5 | Health check / Chat layered endpoint |
| FOUND-6 | test:arch / ESLint 架构门控 |

要求：

1. 每个 PLAN 的 `requirements` 不得为空。
2. 每个 roadmap requirement 至少被一个 PLAN 覆盖。
3. 如果某 task 无法映射 requirement，bridge 必须失败并要求补充 mapping。

### 6.3 PLAN 分组原则

优先级：

1. 保持 DAG 正确。
2. 保持同一 PLAN 内任务强相关。
3. 避免一个 PLAN 超过 3 个 impl tasks。
4. 避免同 wave 修改同一文件。
5. 优先把测试计划靠近其被测能力，但不把全量测试塞进所有 PLAN。

不推荐：

```text
Plan 01: task-001 ~ task-016 全部
```

推荐：

```text
Plan 01: skeleton
Plan 02: env + shared types
Plan 03: infra clients
Plan 04: endpoint vertical slice
Plan 05: tests / gates
```

### 6.4 Wave 计算

算法：

1. 读取 `task-list.json.tasks[*].dependencies`。
2. 构建 task DAG。
3. 按拓扑层级计算 task wave。
4. 按 plan grouping 聚合 task wave：PLAN wave = 组内最大 task wave。
5. 如果 PLAN A 包含的 task 依赖 PLAN B 的 task，则 PLAN A `depends_on` 包含 PLAN B。
6. 同 wave PLAN 如果 `files_modified` 有交集，则后者提升到下一 wave。

### 6.5 files_modified 推断

优先级：

1. 从 `task-XXX.md` 的”关键文件”表提取。
2. 从 acceptance criteria 中出现的路径提取。
3. 从 `feature-context.md` 的目录结构提取。
4. 如果无法精确推断，允许使用目录级路径，但必须在 PLAN 中标注为 conservative scope。

对于 Phase 0，`files_modified` 应以 `apps/ai-coach-skill/` 下路径为主，不应默认包含 legacy Go 路径。

### 6.5.1 路径规范化（Path Normalization）

> **问题**：`task-*.md` 和 acceptance criteria 中可能引用裸路径（bare paths），如 `src/lib/ai/provider.factory.ts` 或 `tests/unit/env.test.ts`。如果直接写入 PLAN，agent 会在项目根目录错误创建文件，而不是在实际的 app 目录下。

**识别规则**：当路径匹配以下前缀之一且不包含 `APP_DIR` 前缀时，自动规范化：

| 裸路径前缀 | 规范化结果（假设 APP_DIR=`apps/ai-coach-skill`） |
|-----------|----------------------------------------------|
| `src/` | `apps/ai-coach-skill/src/` |
| `tests/` | `apps/ai-coach-skill/tests/` |
| `test/` | `apps/ai-coach-skill/test/` |
| `lib/` | `apps/ai-coach-skill/lib/` |
| `app/` | `apps/ai-coach-skill/app/` |
| `pages/` | `apps/ai-coach-skill/pages/` |
| `middleware` | `apps/ai-coach-skill/middleware` |
| `drizzle.config` | `apps/ai-coach-skill/drizzle.config` |
| `next.config` | `apps/ai-coach-skill/next.config` |
| `tsconfig` | `apps/ai-coach-skill/tsconfig` |
| `.eslintrc` | `apps/ai-coach-skill/.eslintrc` |
| `.env` | `apps/ai-coach-skill/.env` |

**不修改的情况**：
- 路径已包含 `APP_DIR` 前缀（如 `apps/ai-coach-skill/src/...`）
- 路径以 `./` 或 `../` 开头（相对路径）
- 路径不在上述前缀列表中

**实现**：`normalizeFilePath()` 函数在 `inferFilesModified()` 中对每条提取到的路径执行规范化。规范化结果同时写入 PLAN 的 `files_modified`、XML `<files>` 和 `<done>` 元素。

**验证**：Validation Gate 中新增 Path Normalization Gate，对所有已生成的 `files_modified` 做二次检查，任何未被规范化的裸路径将导致 REJECT。

### 6.6 read_first 规则

每个 XML task 的 `<read_first>` 至少包含：

```text
AGENTS.md
AI_CONSTITUTION.md
rules/agent-coding-guardrails.md
对应 task-XXX.md
feature-context.md
```

按需追加：

| 场景 | 必读 |
|------|------|
| Next.js Route Handler | `apps/ai-coach-skill/node_modules/next/dist/docs/` 对应文档 |
| middleware / cookies | Next.js middleware / cookies 文档 |
| AI SDK streaming | `apps/ai-coach-skill/node_modules/ai/` 或本地 AI SDK docs |
| Supabase SSR | `apps/ai-coach-skill/package.json` + Supabase 相关本地包版本 |
| Drizzle | `drizzle.config.ts`、schema、client 相关文件 |

### 6.7 action 生成规则

`<action>` 必须从 `task-XXX.md` 抽取具体目标，不得只写“按文档实现”。

必须包含：

1. 目标文件或目录。
2. 关键导出名、类型名、函数名。
3. 明确禁止项，例如“不要改 Go legacy 主线”。
4. 执行顺序。
5. 对应验收项。

### 6.8 verification 规则

每个 PLAN 的 `<verification>` 使用最小必要命令。

Phase 0 全局默认验证顺序来自 `AGENTS.md`：

```bash
cd apps/ai-coach-skill
npm run lint
npm run typecheck
npm run check:docs:strict
npm run test:arch
npm run test
npm run build
```

单个 PLAN 可选择子集，但最后一个或汇总 PLAN 必须覆盖完整链路，除非命令尚未存在，并在 SUMMARY 中说明。

---

## 7. Phase 0 示例分组

输入：

```text
docs/mvp-lite/impl/impl-formal-app-foundation-ARCH-LITE-007
```

推荐生成：

| PLAN | Wave | Source Tasks | 目标 | Requirements |
|------|------|--------------|------|--------------|
| `00-01` | 1 | `task-001` | App skeleton 与目录占位 | FOUND-1 |
| `00-02` | 2 | `task-002`, `task-004` | Env/runtime 与 API/error 类型 | FOUND-2 |
| `00-03` | 2 | `task-012` | ESLint 架构约束 | FOUND-6 |
| `00-04` | 3 | `task-003`, `task-013` | AI Provider factory 与单元测试 | FOUND-4 |
| `00-05` | 3 | `task-005`, `task-006`, `task-009` | Drizzle / Supabase / Redis clients | FOUND-3 |
| `00-06` | 3 | `task-014` | 架构测试入口 | FOUND-6 |
| `00-07` | 4 | `task-007`, `task-008` | service_role audit 与 middleware | FOUND-3 |
| `00-08` | 4 | `task-010` | Health endpoint vertical slice | FOUND-5 |
| `00-09` | 5 | `task-011` | Chat endpoint layered migration | FOUND-4, FOUND-5 |
| `00-10` | 5 | `task-015` | Integration tests | FOUND-3 |
| `00-11` | 6 | `task-016` | Performance baseline | FOUND-3, FOUND-5 |

依赖示例：

| PLAN | depends_on |
|------|------------|
| `00-01` | `[]` |
| `00-02` | `["00-01"]` |
| `00-03` | `["00-01"]` |
| `00-04` | `["00-02"]` |
| `00-05` | `["00-02"]` |
| `00-06` | `["00-01", "00-03"]` |
| `00-07` | `["00-05"]` |
| `00-08` | `["00-02", "00-05"]` |
| `00-09` | `["00-04", "00-07"]` |
| `00-10` | `["00-05", "00-07"]` |
| `00-11` | `["00-05", "00-08"]` |

说明：

- `task-013` 依赖 `task-002/task-003/task-004`，因此放入 `00-04`，但 PLAN 依赖 `00-02`。
- `task-014` 依赖 `task-001/task-012`，因此独立为 `00-06`，依赖 `00-01/00-03`。
- `task-015` 与 `task-011` 都在 wave 5，但修改范围不同，可并行执行；如果 files overlap 检测发现冲突，则提升其中一个到 wave 6。
- `task-016` 依赖 health endpoint，因此必须在 `00-08` 后执行。

---

## 8. Skill 封装设计

### 8.1 Skill 名称

```text
zgsd-plan-phase
```

### 8.2 触发方式

```bash
$zgsd-plan-phase 0 --impl docs/mvp-lite/impl/impl-formal-app-foundation-ARCH-LITE-007
```

可选参数：

| 参数 | 说明 |
|------|------|
| `--dry-run` | 只输出 mapping 和 validation，不写 PLAN |
| `--force` | 覆盖已有 bridge 生成的 PLAN |
| `--append` | 保留已有 PLAN，只追加新 task 对应 PLAN |
| `--skip-review` | 跳过 bridge 输出自审，不推荐 |
| `--grouping <file>` | 使用人工指定的 grouping 文件 |

### 8.3 执行流程

```text
1. Load project guardrails
2. Validate .planning phase exists in ROADMAP
3. Load impl task pack
4. Validate task pack schema
5. Validate DAG
6. Derive phase directory
7. Build task -> requirement mapping
8. Build task -> plan grouping
9. Compute wave / depends_on / files_modified
10. Generate 00-CONTEXT.md
11. Generate 00-TASK-BRIDGE.json
12. Generate *-PLAN.md
13. Run static PLAN contract validation
14. Run independent bridge review
15. Report next command: $gsd-execute-phase 0
```

### 8.4 内部实现建议

仓库内提供脚本：

```text
scripts/gsd/import-task-pack.mjs
```

skill 只作为 orchestrator：

```text
zgsd-plan-phase/SKILL.md
  -> 调用 node scripts/gsd/import-task-pack.mjs
  -> 展示 validation / review 结果
```

这样可以避免把转换逻辑散落在 prompt 中，也便于测试。

### 8.5 脚本 vs LLM 自然语言分工

`zgsd-plan-phase` 采用**脚本确定性转换 + LLM 编排调度**的混合架构。以下是明确的职责划分：

#### 脚本实现的部分（Node.js，确定性逻辑）

以下逻辑由 `import-task-pack.mjs` 和 `validate-bridge.mjs` 实现，保证同一输入产生同一输出：

| 功能 | 脚本函数 | 说明 |
|------|----------|------|
| CLI 参数解析 | `parseArgs()` | 解析 `--phase`、`--impl`、`--dry-run` 等参数 |
| Pre-flight 校验 | `validatePreflight()` | 检查 `.planning/ROADMAP.md`、`AGENTS.md`、`AI_CONSTITUTION.md`、`rules/agent-coding-guardrails.md` 是否存在 |
| Task Pack 加载 | `loadTaskPack()` | 读取 `task-list.json`、`dag-validation.json`、`task-*.md`，计算 `source_hash` |
| Phase 目录派生 | `derivePhaseDir()` | 从 ROADMAP.md 正则提取 phase slug，生成 `.planning/phases/{padded}-{slug}/` |
| Requirement 映射 | `buildRequirementMapping()` | Phase 0 使用固定映射，其他 phase 使用启发式匹配 |
| Task 分组 | `buildPhase0Grouping()` / `buildGenericGrouping()` | Phase 0 使用设计文档 §7 的固定 11-plan 分组；其他 phase 按 DAG 波次自动分组 |
| Wave / depends_on 计算 | `computePlanMetadata()` | 拓扑排序计算 task wave，聚合为 plan wave，推导 plan 依赖 |
| files_modified 推断 | `inferFilesModified()` | 从 task markdown 表格和 acceptance criteria 提取文件路径 |
| 输出文件生成 | `generateContext()` / `generateTaskBridge()` / `generatePlans()` / `generateQualityMap()` / `generateValidation()` | 生成 `00-CONTEXT.md`、`00-TASK-BRIDGE.json`、`*-PLAN.md`、`00-QUALITY-MAP.json`、`00-VALIDATION.md` |
| 静态校验 | `runValidationGates()` / `runReviewGate()` | 检查 task 映射完整性、requirement 覆盖、plan 合法性 |
| Bridge 验证 | `validate-bridge.mjs` | 验证 `TASK-BRIDGE.json` schema 和 `PLAN.md` contract（frontmatter、XML 元素） |

**关键原则**：所有涉及 JSON 解析、正则匹配、DAG 计算、文件 I/O 的逻辑都在脚本中完成，不依赖 LLM 推理。

#### LLM 自然语言实现的部分（Claude via SKILL.md）

以下逻辑由 Claude 通过 SKILL.md 指令驱动，利用 LLM 的自然语言理解能力：

| 功能 | 触发方式 | 说明 |
|------|----------|------|
| 用户意图解析 | SKILL.md trigger patterns | 识别 "plan phase"、"bridge task pack" 等自然语言指令 |
| 参数提取 | SKILL.md Step 1 | 从用户消息中提取 phase 编号和 impl 目录路径 |
| 脚本编排 | SKILL.md Step 2 | 决定何时调用 `import-task-pack.mjs`、何时调用 `validate-bridge.mjs` |
| 结果解读 | SKILL.md Step 3 | 解读脚本输出，向用户展示 mapping 摘要、wave 概览、validation 结果 |
| 下一步建议 | SKILL.md Step 4 | 根据 review gate 结果决定是否建议 `$gsd-execute-phase` |
| 异常处理 | LLM 判断 | 当脚本报错时，分析错误原因并给用户修复建议（如 "ROADMAP.md 中缺少 Phase 1 定义"） |
| 扩展分组（可选） | LLM 辅助 | 对于非 Phase 0 的 task pack，LLM 可以在 `--dry-run` 后建议手动分组调整 |

#### 二者协作流程

```text
用户: "plan phase 0 from impl task pack"
  |
  v
[LLM] SKILL.md 解析用户意图，提取参数
  |   phase=0, impl=docs/mvp-lite/impl/impl-formal-app-foundation-ARCH-LITE-007
  |
  v
[LLM] 通过 Bash 工具调用脚本
  |   node .claude/skills/zgsd-plan-phase/import-task-pack.mjs --phase 0 --impl <dir>
  |
  v
[脚本] 确定性执行全流程
  |   preflight → load → derive → map → group → compute → generate → validate
  |   输出: .planning/phases/00-formal-app-foundation/* (CONTEXT, BRIDGE, PLANS, QUALITY-MAP, VALIDATION)
  |
  v
[LLM] 解读脚本输出，向用户展示摘要
  |   "16 tasks mapped, 6/6 requirements covered, 11 plans across 5 waves"
  |   "Validation: PASS, Review: PASS"
  |
  v
[LLM] 可选：调用 validate-bridge.mjs 做二次校验
  |   node .claude/skills/zgsd-plan-phase/validate-bridge.mjs --phase 0
  |
  v
[LLM] 给出下一步建议
  |   "Next: $gsd-execute-phase 0"
```

#### 边界约定

| 约定 | 说明 |
|------|------|
| 脚本不依赖 LLM | `import-task-pack.mjs` 和 `validate-bridge.mjs` 可独立运行，不调用任何 AI API |
| LLM 不修改转换逻辑 | SKILL.md 只编排脚本调用，不自行生成 PLAN 内容 |
| 脚本可测试 | 每个函数可通过 Node.js 单元测试验证，不依赖 Claude 运行环境 |
| LLM 可替换 | 如果换成其他 agent 框架，只需重写 SKILL.md 的编排指令，脚本无需修改 |
| 自包含部署 | 整个 skill 目录（SKILL.md + 脚本 + schemas）可 copy 到任何项目使用 |

---

## 9. 校验 Gates

### 9.1 Pre-flight Gate

阻断条件：

1. `.planning/ROADMAP.md` 不存在。
2. phase 不存在。
3. impl 目录不存在。
4. `task-list.json` 解析失败。
5. `dag-validation.json.status != PASS`。
6. `rules/agent-coding-guardrails.md` 不存在。

### 9.2 Mapping Gate

阻断条件：

1. 存在未映射 task。
2. 某 task 被映射到多个 PLAN。
3. 某 PLAN 的 `requirements` 为空。
4. roadmap phase requirements 未被覆盖。
5. PLAN dependencies 不满足 task DAG。

### 9.3 Contract Gate

阻断条件：

1. PLAN frontmatter 缺少 GSD required fields。
2. XML task 缺少 `read_first`、`action`、`verify` 或 `acceptance_criteria`。
3. `files_modified` 为空且 PLAN 会修改代码。
4. `autonomous: true` 但 PLAN 中包含 checkpoint task。
5. 文档超过 1000 行。

### 9.4 Execution Safety Gate

阻断条件：

1. PLAN 指向 legacy Go 主线，且用户未明确要求 legacy Go。
2. PLAN 未要求读取 `AGENTS.md` / `AI_CONSTITUTION.md` / `rules/agent-coding-guardrails.md`。
3. Next.js API / middleware / streaming 相关 PLAN 未包含本地 Next docs 读取要求。
4. PLAN 要求删除或重置用户文件。

### 9.4.1 Path Normalization Gate（新增）

阻断条件：

1. `files_modified` 中存在裸路径（如 `src/xxx`、`tests/xxx`）未被规范化为 `APP_DIR/src/xxx`、`APP_DIR/tests/xxx`。
2. XML `<files>` 或 `<done>` 元素中存在未规范化的裸路径。
3. 路径规范化检测到的原始路径与规范化后路径不一致时，必须在 bridge manifest 的 `path_normalization` 字段记录映射关系。

### 9.5 Review Gate

生成后执行一轮独立审查，输出：

```text
PASS | REJECT | ESCALATE_TO_HUMAN
```

只有 `PASS` 时才建议运行：

```bash
$gsd-execute-phase 0
```

---

## 10. 与 GSD 原生 plan-phase 的关系

| 能力 | `$gsd-plan-phase` | `$zgsd-plan-phase` |
|------|-------------------|--------------------|
| 从 roadmap 自由规划 | 是 | 否 |
| 从 impl task pack 确定性导入 | 否 | 是 |
| 生成 GSD PLAN.md | 是 | 是 |
| research / pattern mapper | 是 | 可选 |
| plan checker revision loop | 是 | 可选静态审查 + 可接入 checker |
| execute-phase 兼容 | 是 | 是 |
| 保留 task pack 审计链 | 弱 | 强 |

建议规则：

1. 有 `docs/mvp-lite/impl/*` task pack 时，优先使用 `$zgsd-plan-phase`。
2. 没有 task pack，只有 roadmap phase 时，使用 `$gsd-plan-phase`。
3. `$zgsd-plan-phase` 生成的 PLAN 不应再被 `$gsd-plan-phase` 从零覆盖，除非用户明确选择 replan。

---

## 10.5 Quality Chain Bridge

`zgsd-plan-phase` 不能只对接 GSD 的 planning / execution 层，还必须让测试类 task 成为 GSD verify / validate 可消费的质量证据。否则 `task-013`、`task-014`、`task-015`、`task-016` 会被执行，但后续 `$gsd-verify-work`、`verify-phase`、`$gsd-validate-phase` 只能从 SUMMARY 里反推覆盖关系，容易漏掉 requirement 到测试证据的映射。

### 10.5.1 对接目标

桥接后应支持完整质量链路：

```text
$zgsd-plan-phase 0 --impl ...
  -> *-PLAN.md + 00-QUALITY-MAP.json + 00-VALIDATION.md
  -> $gsd-execute-phase 0
  -> verify-phase / $gsd-verify-work 0
  -> $gsd-validate-phase 0
  -> $gsd-execute-phase 0 --gaps-only
```

对接边界：

| GSD 环节 | 消费产物 | bridge 必须提供 |
|----------|----------|-----------------|
| `$gsd-execute-phase` | `*-PLAN.md` | 标准 PLAN contract |
| `verify-phase` | PLAN `must_haves` / `requirements` / `files_modified`、SUMMARY | 可验证的 must_haves 和 requirement evidence |
| `$gsd-verify-work` | `*-SUMMARY.md` | SUMMARY 输出约束，确保可抽取 UAT 项 |
| `$gsd-validate-phase` | PLAN、SUMMARY、`*-VALIDATION.md`、测试文件 | validation skeleton 和 requirement-test mapping |

### 10.5.2 新增质量产物

除第 5 节产物外，推荐额外生成：

```text
00-QUALITY-MAP.json
00-VALIDATION.md
```

`00-QUALITY-MAP.json` 是机器可读质量映射，给 bridge validator、后续脚本和审查流程使用。`00-VALIDATION.md` 是 GSD Nyquist validation 的初始骨架，给 `$gsd-validate-phase` 使用，避免完全从 SUMMARY 反推。

### 10.5.3 QUALITY-MAP.json 最小结构

`00-QUALITY-MAP.json` 至少记录 requirement、测试类 task、预期测试文件和命令：

```json
{
  "schema_version": "1.0",
  "phase": "0",
  "impl_dir": "docs/mvp-lite/impl/impl-formal-app-foundation-ARCH-LITE-007",
  "requirements": {
    "FOUND-1": {
      "truths": ["formal app layer directories exist"],
      "proving_tasks": ["task-001", "task-014"],
      "expected_test_files": ["apps/ai-coach-skill/tests/arch/**/*.test.*"],
      "commands": ["npm run test:arch"],
      "evidence_level": ["structure", "arch-test"]
    }
  },
  "test_tasks": {
    "task-013": {
      "kind": "unit",
      "requirements": ["FOUND-2", "FOUND-4"],
      "expected_files": ["apps/ai-coach-skill/tests/unit/**/*.test.*"],
      "commands": ["npm run test"],
      "blocks_phase_if_failing": true
    }
  }
}
```

字段要求：

1. 每个 roadmap requirement 必须至少有一个 `proving_tasks`。
2. 每个测试类 task 必须声明 `kind`、`requirements`、`expected_files`、`commands`。
3. `blocks_phase_if_failing` 为 `true` 的测试失败时，phase verification 必须视为 blocker。
4. `evidence_level` 必须从固定枚举中选择：`structure`、`unit`、`integration`、`arch-test`、`perf`、`runtime`、`uat`。

### 10.5.4 VALIDATION.md 骨架

`zgsd-plan-phase` 应预生成 `.planning/phases/00-formal-app-foundation/00-VALIDATION.md`。最小内容：

```markdown
---
phase: 00-formal-app-foundation
status: planned
source: zgsd-plan-phase
quality_map: 00-QUALITY-MAP.json
nyquist_compliant: pending
---

# Phase 0 Validation Strategy

## Requirement Coverage

| Requirement | Evidence Level | Proving Tasks | Expected Test Files | Commands | Status |
|-------------|----------------|---------------|---------------------|----------|--------|
| FOUND-1 | structure, arch-test | task-001, task-014 | tests/arch/**/*.test.* | npm run test:arch | planned |

## Validation Gaps

None at planning time. `$gsd-validate-phase` must update this section after execution.
```

执行完成后，`$gsd-validate-phase` 可以从 State A 进入，即“已有 VALIDATION.md，审计并填补缺口”，而不是 State B 的“从 SUMMARY 反推”。

### 10.5.5 PLAN must_haves 生成规则

每个 PLAN 的 `must_haves` 必须从三类来源生成：

1. `.planning/ROADMAP.md` 中 Phase success criteria。
2. impl task 的 acceptance criteria。
3. `00-QUALITY-MAP.json` 中对应 requirement 的 truths / expected evidence。

示例：

```yaml
must_haves:
  truths:
    - "npm run test:arch detects forbidden layer imports"
    - "GET /api/health uses Transport -> Handler -> Service -> Repository"
  artifacts:
    - "apps/ai-coach-skill/src/lib/handlers/health.handler.ts"
    - "apps/ai-coach-skill/tests/arch/"
  key_links:
    - "Health route imports handler, not repository or db client directly"
    - "test:arch script is wired in apps/ai-coach-skill/package.json"
```

规则：

1. `truths` 必须是可观察行为，不写“结构合理”这类主观描述。
2. `artifacts` 必须是文件或目录路径。
3. `key_links` 必须描述跨层连接关系，供 verify-phase 做 wiring audit。

### 10.5.6 SUMMARY 输出约束

为了让 `$gsd-verify-work` 能稳定生成 UAT，bridge 生成的每个 PLAN 的 `<output>` 必须要求 SUMMARY 包含：

```text
## Deliverables
## Files Changed
## Tests Added or Changed
## Commands Run
## Requirement Evidence
## Deviations
## Self-Check
```

`Requirement Evidence` 必须包含 `Requirement`、`Evidence`、`Test/Command`、`Result`。`Tests Added or Changed` 必须包含 `Test File`、`Requirement`、`Assertion Strength`、`Notes`。这样 `verify-phase` 和 `$gsd-validate-phase` 可以识别 requirement-linked tests，并审计 disabled tests、circular tests、assertion strength。

### 10.5.7 测试类 task 的处理规则

测试类 task 不应被降级为普通 checklist。bridge 必须识别以下类型：

| Task | Kind | GSD 质量角色 |
|------|------|--------------|
| `task-013-unit-tests` | unit | 证明 env / provider / error types 的单元行为 |
| `task-014-arch-tests` | architecture | 证明分层边界和 forbidden imports |
| `task-015-integration-tests` | integration | 证明 DB / audit / Redis 基础设施可运行 |
| `task-016-perf-baseline` | performance | 证明 health / build / Redis / DB 基线 |

处理要求：

1. 测试类 task 仍然生成 PLAN task，由 `$gsd-execute-phase` 实施。
2. 同时写入 `00-QUALITY-MAP.json` 和 `00-VALIDATION.md`。
4. PLAN 的 `<verification>` 必须包含对应命令。
5. SUMMARY 必须回填测试文件、命令、结果、覆盖 requirement。

### 10.5.8 Gap 回流

如果 verify / validate 发现质量缺口，保持 GSD 原生路径：

```text
VERIFICATION.md / UAT.md gaps
  -> $gsd-plan-phase --gaps 或 verify-work 内置 gap_closure
  -> gap PLAN
  -> $gsd-execute-phase --gaps-only
```

但对 `zgsd-plan-phase` 生成的 phase，gap planner 必须额外读取：

```text
00-TASK-BRIDGE.json
00-QUALITY-MAP.json
00-VALIDATION.md
```

这样修复计划能知道缺口来自哪个 impl task、哪个 requirement、哪个测试证据，而不是只看到失败现象。

### 10.5.9 新增 Gates

在第 9 节 gates 之外，增加质量链 gate：

| Gate | 阻断条件 |
|------|----------|
| Quality Map Gate | roadmap requirement 未出现在 `00-QUALITY-MAP.json` |
| Test Task Gate | 测试类 task 没有 `kind` / `commands` / `expected_files` |
| Validation Skeleton Gate | 未生成 `00-VALIDATION.md`，且 phase 含测试类 task |
| SUMMARY Contract Gate | PLAN `<output>` 未要求 `Requirement Evidence` 和 `Tests Added or Changed` |
| Evidence Blocking Gate | `blocks_phase_if_failing: true` 的测试命令未进入 PLAN verification |

### 10.5.10 结论

`zgsd-plan-phase` 应升级为：

```text
Impl Task Pack
  -> GSD PLAN Bridge
  -> GSD Quality Bridge
```

也就是同时生成 `*-PLAN.md`、`00-TASK-BRIDGE.json`、`00-QUALITY-MAP.json`、`00-VALIDATION.md`，完整接上 `plan -> execute -> verify -> validate -> gaps-only repair`。

---

## 11. 实施计划

### Step 1：定义 bridge schema

产物：

```text
scripts/gsd/schemas/task-pack.schema.json
scripts/gsd/schemas/task-bridge.schema.json
```

验收：

- 能校验当前 `task-list.json`。
- 能校验 `00-TASK-BRIDGE.json`。

### Step 2：实现 import-task-pack 脚本

产物：

```text
scripts/gsd/import-task-pack.mjs
```

验收：

- `--dry-run` 输出 Phase 0 mapping。
- DAG 校验失败时退出非 0。
- requirements coverage 缺失时退出非 0。

### Step 3：生成 Phase 0 PLAN

产物：

```text
.planning/phases/00-formal-app-foundation/00-CONTEXT.md
.planning/phases/00-formal-app-foundation/00-TASK-BRIDGE.json
.planning/phases/00-formal-app-foundation/00-01-PLAN.md
...
```

验收：

- 16 个 impl task 全部映射。
- FOUND-1 到 FOUND-6 全部覆盖。
- PLAN frontmatter 和 XML task contract 通过校验。

### Step 4：封装 zgsd-plan-phase skill

产物：

```text
.agents/skills/zgsd-plan-phase/SKILL.md
```

验收：

- 技能读取参数后调用脚本。
- 输出下一步 `$gsd-execute-phase 0`。
- 若 review gate 失败，不建议执行。

### Step 5：接入自动化校验

产物：

```text
npm run gsd:bridge:check
```

验收：

- CI 或本地命令可验证 bridge manifest 和 PLAN contract。
- 不依赖不可用的 `gsd-sdk query`。

---

## 12. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| files_modified 推断不准 | execute-phase 并行时可能冲突 | conservative scope + same-wave overlap gate |
| requirement mapping 人工规则不全 | plan-checker coverage gap | mapping 缺失直接 fail |
| PLAN action 过于抽象 | executor 浅执行 | action 从 task markdown 展开，强制 concrete values |
| GSD contract 版本变化 | execute-phase 解析失败 | PLAN contract validator 固化当前 required fields |
| 过度绕开 GSD planner | 失去 planner 的补漏能力 | bridge review + 可选 checker，不允许默默跳过缺口 |
| skill 与脚本逻辑分叉 | 行为不可预测 | skill 只做入口，核心逻辑放脚本 |

---

## 13. 开放问题

1. `zgsd-plan-phase` 是否要默认覆盖已有 `.planning/phases/{phase}`？
   - 建议：默认拒绝覆盖，要求 `--force`。
2. `files_modified` 是否必须精确到文件？
   - 建议：能精确则精确；不能精确时可用目录，但同 wave overlap gate 要保守。
3. 是否接入原生 `gsd-plan-checker`？
   - 建议：第一版先做静态 contract review；第二版接 checker。
4. 是否自动修改 `.planning/STATE.md`？
   - 建议：生成 PLAN 后可标记 Ready to execute，但第一版只报告，不自动改 STATE。

---

## 14. 方案审核

### 14.1 审核结论

```text
PASS
```

本方案通过方案级审核：用 `zgsd-plan-phase` 替代 `$gsd-plan-phase` 的自由规划，专门承接已拆好的 `impl` task pack，并保留 GSD execute-phase 作为唯一执行入口。第 14.3 节行动项是进入实现前必须满足的实施约束，不影响本设计方案成立。

### 14.2 审核项

| 审核项 | 结论 | 说明 |
|--------|------|------|
| 是否符合 GSD PLAN contract | PASS | 明确 frontmatter、XML task、must_haves、wave、depends_on |
| 是否保留 impl task 审计链 | PASS | 设计了 `00-TASK-BRIDGE.json` |
| 是否避免重复规划 | PASS | 明确 task pack 为 SSOT，不让 planner 自由删改 |
| 是否可直接接 `$gsd-execute-phase` | PASS | 输出标准 `.planning/phases/*-PLAN.md` |
| 是否满足项目 guardrails | PASS | PLAN 必读 guardrails，bridge 后有 review gate |
| 是否存在未决实现细节 | ACTION | files_modified 推断和 requirement mapping 需要脚本中固化规则 |

### 14.3 必须补齐的行动项

1. 实现前先定义 `task-bridge.schema.json`，避免 manifest 变成散文记录。
2. Phase 0 第一版 grouping 可采用本文第 7 节固定映射，不要一开始做复杂自动聚类。
3. `files_modified` 第一版宁可保守，避免 same-wave 写冲突。
4. 第一版不要自动调用 `$gsd-execute-phase`，只输出下一步命令，由人或上层流程触发。
5. 任何 review gate 非 PASS 时，不得建议执行 phase。

### 14.4 残余风险

1. GSD 当前本地 `gsd-sdk` CLI 与 workflow 文档中的 `gsd-sdk query` 能力不一致，bridge 实现不应依赖 `gsd-sdk query`。
2. PLAN action 的质量取决于 `task-XXX.md` 的具体程度；若 task markdown 本身含糊，bridge 应 fail 或要求人工补充。
3. 原生 `gsd-plan-checker` 是否能在当前 Codex 环境完整运行，需要后续单独验证。

---

## 15. 推荐决策

批准建设 `zgsd-plan-phase`，但按两阶段推进：

1. **Phase A：确定性导入**
   - 实现脚本和静态 validator。
   - 生成 Phase 0 PLAN。
   - 人工审核 PLAN 后执行。

2. **Phase B：GSD 深度集成**
   - 封装 skill。
   - 接入可选 plan-checker。
   - 接入 `npm run gsd:bridge:check`。
   - 探索自动更新 `.planning/STATE.md`。

第一阶段完成后，当前 `impl-formal-app-foundation-ARCH-LITE-007` 即可进入：

```bash
$gsd-execute-phase 0
```
