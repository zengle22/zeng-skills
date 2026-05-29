# Zeng Skills 详细使用说明

> 本文档提供本仓库所有 8 个 Skill 的详细使用指南，包括功能说明、参数、使用示例和注意事项。

---

## 目录

| # | Skill | 分类 | 一句话说明 |
|---|-------|------|-----------|
| 1 | [zcode-safe-dev](#1-zcode-safe-dev) | 编码安全 | 临时安全编码助手 — 修改项目代码时的硬约束与自检清单 |
| 2 | [zdoc-quality-loop](#2-zdoc-quality-loop) | 文档质量 | 多文档质量收敛流水线 — BMAD 多角色评审团 |
| 3 | [zcode-patrol](#3-zcode-patrol) | 代码质量 | 代码库自动化巡检 — 风格/安全/性能/重复/死代码 |
| 4 | [zcode-review-deep](#4-zcode-review-deep) | 代码审查 | 多智能体深度代码审查 — Commit/PR/模块并行专项审查 |
| 5 | [zdoc-design-check](#5-zdoc-design-check) | 设计校验 | Pre-SSOT 文档校验 — 6 大维度 + 跨维度一致性，55 项检查 |
| 6 | [zdoc-i2i](#6-zdoc-i2i) | 设计到实施 | 设计文档到实施任务转化引擎 — 15+ 种设计文档输入 |
| 7 | [zgsd-bootstrap-milestone](#7-zgsd-bootstrap-milestone) | GSD 集成 | 从预设计文档包引导生成 GSD Milestone |
| 8 | [zgsd-plan-phase](#8-zgsd-plan-phase) | GSD 集成 | 桥接 I2I 任务包到 GSD PLAN 格式 |

---

## 技能关系链

```
设计文档质量验证 → 设计到实施转化 → GSD 里程碑引导 / GSD Phase 规划
─────────────────────────────────────────────────────────────────────────

  zdoc-design-check          zdoc-i2i               zgsd-bootstrap-milestone
       │                         │                    zgsd-plan-phase
       ▼                         ▼                         │
  Pre-SSOT 文档校验    →    实施任务拆分          →    GSD 可执行计划
                                                         │
  zdoc-quality-loop                          GSD 执行 (gsd-execute-phase)
       │
       ▼
  文档质量收敛（BMAD 多角色评审）

  ────────────── 编码阶段 ──────────────

  zcode-safe-dev  →  zcode-patrol  →  zcode-review-deep
  (编码安全约束)     (自动化巡检)           (深度代码审查)
```

---

## 1. zcode-safe-dev

### 功能概述

临时安全编码助手，在 L3/L2 治理未完全到位前，用 6 条绝对禁止 + 7 步工作流避免最典型的编码陷阱。适用于修改项目自身代码的场景。

### 核心约束（6 条绝对禁止）

| # | 禁止行为 | 说明 |
|---|---------|------|
| 1 | 创建平行目录结构 | 禁止在仓库中创建与现有主目录平行的新根目录 |
| 2 | 不做集成/只写孤立模块 | 禁止只写新模块而不接入现有流程 |
| 3 | 不写测试/不跑测试 | 禁止改动已有逻辑时不写测试 |
| 4 | 修改覆盖率阈值制造绿灯 | 禁止降低覆盖率阈值或删除失败用例 |
| 5 | 不搜索就重复造轮子 | 禁止不搜索代码库就新增相似实现 |
| 6 | 不做自我 code review | 禁止不经检查就宣布任务完成 |

### 使用方式

```
/zcode-safe-dev
```

或通过 Skill 工具调用：

```
Skill(skill="zcode-safe-dev")
```

### 输入参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_description` | string | 本次编码任务描述 |
| `repo_root` | string | 仓库根目录 |
| `target_module` | string | 建议的主要修改目录 |
| `risk_level` | enum | `low` / `medium` / `high` |

### 工作流程（7 步）

1. **复述任务 + 确认范围** — 复述任务描述，明确改动类型
2. **检查目录结构** — 避免平行目录，写入承诺
3. **搜索同类实现** — 搜索关键字避免重复造轮子
4. **MVP 改动方案** — 列出计划修改/新增的文件及职责
5. **编写/修改代码** — 遵守 6 条禁令
6. **测试策略与执行** — 设计最小必要测试策略
7. **自我 code review** — 包含安全检查清单

### 自检清单（safety_checklist）

- `created_parallel_directory`: false
- `changed_coverage_threshold`: false
- `changed_pass_criteria`: false
- `skipped_similar_impl_search`: false
- `skipped_self_review`: false

---

## 2. zdoc-quality-loop

### 功能概述

有界、可追溯的文档质量收敛流水线。采用 BMAD 多角色评审团（选角 → 并行评审 → 合并 → 冲突讨论 → 共识/升级人类），配合全程落盘和独立审计报告，确保文档质量可追溯。

### 三大核心设计

1. **BMAD 多角色评审团** — 2-4 个专业角色并行评审 + 1 个 Moderator 合并
2. **全程落盘** — 每个 Agent 动作立即写文件，支持中断恢复
3. **独立审计和报告** — 审计 Agent 无共享上下文，仅通过磁盘了解全过程

### 角色池

| 角色 ID | subagent_type | 负责 Rubric | 视角专长 |
|---------|--------------|-----------|---------|
| `product-manager` | `product-manager` | R01, R07, R10 | 需求完整性、用户价值 |
| `architect` | `architect` | R02, R03, R06 | 技术可行性、数据模型 |
| `developer` | `code-reviewer` | R02, R04, R05, R09 | 实现细节、边界、伪闭环 |
| `ux-designer` | `ux-designer` | R06, R04 | UI 状态流、交互一致性 |
| `analyst` | `analyst` | R01, R08, R10 | 需求歧义、SSOT 对齐 |
| `security` | `security-reviewer` | R05, R04, R09 | 安全边界、失败路径 |

### Rubric 维度（R01-R10）

| # | 维度 | 检查内容 |
|---|------|---------|
| R01 | 需求完整性 | 用户故事/功能点是否已陈述 |
| R02 | 主流程可执行性 | 开发人员能否仅凭文档实现 Happy Path |
| R03 | 数据模型一致性 | 实体名称、字段、关系前后一致 |
| R04 | 边界与异常情况 | 空值、零值、超限、并发冲突 |
| R05 | 异常处理路径 | 失败模式和恢复路径 |
| R06 | UI/API/状态流一致性 | UI 状态 ↔ API 响应 ↔ 状态机对齐 |
| R07 | 测试可验证性 | AC 是否可转换为自动化测试用例 |
| R08 | SSOT 对齐 | 是否与项目 SSOT 冲突 |
| R09 | Mock/伪闭环风险 | TBD、存根、"后续补充"等 |
| R10 | 范围漂移 | 是否超出声明的目标范围 |

### 使用方式

```
/zdoc-quality-loop spec.md prd.md [--ssot <path>] [--rubric <path>] [--max-rounds 5] [--parallel] [--output-dir .quality-loop]
```

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| 位置参数 | array | — | 要评审的文档路径（至少 1 个） |
| `--ssot` | string | — | 项目 SSOT 文档路径（用于 R08 检查） |
| `--rubric` | string | — | 自定义 Rubric 路径 |
| `--max-rounds` | int | 5 | 最大评审轮数 |
| `--p1-threshold` | int | 3 | P1 问题超过此数触发修复 |
| `--p2` | enum | `low-risk` | P2 处理策略：`always` / `never` / `low-risk` |
| `--parallel` | flag | — | 并行评审各角色 |
| `--no-verify` | flag | — | 跳过 Verifier 验证 |
| `--output-dir` | string | `.quality-loop` | 输出目录 |

### 流水线阶段

| 阶段 | 说明 |
|------|------|
| Phase 0 | 初始化，锁定 Rubric |
| Phase 1 | 评审循环：选角 → 并行评审 → 合并 → 冲突讨论 → 共识 → 修复 → 验证 |
| Phase 2 | 独立审计（零共享上下文的 Agent） |
| Phase 3 | 独立报告生成 |
| Phase 4 | 批次汇总 |
| Phase 5 | 人工确认门 |

### 输出结构

所有产物写入 `{output_dir}/{batch_id}/`，包括 `role-panel.json`、各轮评审 JSON、`fix-log.json`、`final.md`、`audit-report.json`、`quality-report.md` 等。

---

## 3. zcode-patrol

### 功能概述

代码熵巡检技能，对代码库执行自动化静态分析，发现质量退化问题，生成结构化报告。补充/聚合 ESLint、Pylint 等工具的结果，不做 gate 决策。

### 巡检维度（D01-D08）

| ID | 维度 | 严重级别 |
|----|------|---------|
| D01 | Style Consistency（风格一致性） | P2-P3 |
| D02 | Architecture Compliance（架构合规） | P0-P1 |
| D03 | Security Patterns（安全模式） | P0-P1 |
| D04 | Performance Anti-patterns（性能反模式） | P1-P2 |
| D05 | Duplication & Dead Code（重复与死代码） | P2-P3 |
| D06 | Documentation Sync（文档同步） | P2-P3 |
| D07 | Dependency Health（依赖健康） | P1-P2 |
| D08 | Test Coverage Drift（测试覆盖率漂移） | P1-P2 |

### 使用方式

```
/zcode-patrol --paths src/ --scope full
```

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--paths` | array | `["."]` | 扫描的目录或文件路径 |
| `--scope` | enum | `full` | `full`（全量）/ `delta`（增量）/ `staged`（暂存区）/ `targeted`（定向） |
| `--format` | enum | `markdown` | 输出格式：`markdown` / `json` |
| `--max-files` | int | 500 | 最大扫描文件数 |
| `--output-dir` | string | `.zcode-patrol` | 输出目录 |
| `--min-severity` | enum | `P3` | 最低严重级别：`P0` / `P1` / `P2` / `P3` |
| `--baseline` | string | — | 基线报告路径（用于对比） |

### 执行协议

1. **Initialize** — 解析参数，生成 `patrol_id`
2. **Discovery** — 按 scope 展开文件列表，应用排除规则
3. **Scan (L1 + L3)** — L1 正则/AST 模式匹配 + L3 外部工具统计聚合
4. **Aggregation & Enrichment** — 去重合并，补充 git 元数据，基线对比
5. **Reporting** — 生成 `report.json` + `report.md`

### 使用示例

```
# 全量扫描
/zcode-patrol --paths src/ --scope full

# 增量扫描（与基线对比）
/zcode-patrol --paths src/ --scope delta --baseline .zcode-patrol/20260527-120000-xxx/report.json

# 仅扫描暂存区文件
/zcode-patrol --paths src/ --scope staged

# 只关注高严重级别
/zcode-patrol --paths src/ --min-severity P1
```

### 验证

```bash
# 验证输出产物
python validate.py .zcode-patrol/{patrol_id}
# 依赖: pip install jsonschema
```

---

## 4. zcode-review-deep

### 功能概述

多智能体深度代码审查技能。对单次 Commit/PR/模块执行 4+ 维度并行专项审查，合并去重后生成结构化修复任务与最终报告。适用于关键 PR 的深度审查，与 `bmad-code-review`（快速扫描）互补。

### 严重级别

| 级别 | 含义 | 说明 |
|------|------|------|
| P0 | Blocker | 必须立即修复 |
| P1 | High | 应在合并前修复 |
| P2 | Medium | 建议修复 |
| P3 | Low | 可选修复 |

### 使用方式

```
/zcode-review-deep --mode commit --ref HEAD~1
```

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--mode` | enum | — | `commit`（单次提交）/ `pr`（PR）/ `module`（模块）/ `frz`（FRZ 关联） |
| `--ref` | string | — | commit ref（如 `HEAD~1`） |
| `--base` | string | — | PR base branch |
| `--head` | string | — | PR head branch |
| `--path` | string | — | 模块路径（`--mode module` 时使用） |
| `--frz-ref` | string | — | FRZ 文档引用（`--mode frz` 时使用） |
| `--output-dir` | string | `.cr-deep` | 输出目录 |

### 执行协议（7 步）

1. **Initialize** — 解析参数，生成 `batch_id`，捕获输入快照
2. **Role Selection** — 根据变更内容选择 2-4 个专业 Agent + 1 个 Moderator
3. **Parallel Review** — 并行 Spawn 各 Agent 执行审查
4. **Merge & Conflict Detection** — Moderator 合并去重，检测严重级别冲突
5. **Consensus Build** — 相邻级别冲突自动取高级别
6. **Fix Task Generation** — 为 P0/P1 问题生成修复任务
7. **Report Synthesis** — 生成最终报告

### 使用示例

```
# 审查最近一次提交
/zcode-review-deep --mode commit --ref HEAD~1

# 审查 PR 的所有变更
/zcode-review-deep --mode pr --base main --head feature/x

# 审查指定模块
/zcode-review-deep --mode module --path src/services/order/
```

### 验证

```bash
python validate.py .cr-deep/{batch_id}
# 依赖: pip install jsonschema
```

---

## 5. zdoc-design-check

### 功能概述

Pre-SSOT 文档校验技能，覆盖 6 大维度（商业/产品/UX/架构/测试/工程）+ 跨维度一致性，共 55 项检查。纯 LLM + 结构化输出架构，产出 BLOCK/WARN/PASS 诊断报告。遵循 ADR-002 v2.1。

### 检查维度

| 域 ID | 域名称 | Check ID 前缀 | 检查项数 |
|-------|--------|---------------|---------|
| **G** | 通用质量门 | `G-*` | 5 |
| **D1** | 商业设计 | `BD-*` | 6 |
| **D2** | 产品设计 | `PD-*` | 7 |
| **D3** | UX 设计 | `UX-*` | 7 |
| **D4** | 架构设计 | `AD-*` | 9 |
| **D5** | 测试设计 | `TD-*` | 8 |
| **D6** | 工程实施 | `EI-*` | 5 |
| **XC** | 跨维度一致性 | `XC-*` | 8 |
| **合计** | | | **55** |

### 通用质量门（G1-G5）

| Gate | 检查项 | BLOCK 条件 |
|------|--------|-----------|
| G1 | 文档存在性 | 文件不存在、含占位符或 H2 < 3 |
| G2 | 决策可追溯性 | 关键决策无任何依据说明 |
| G3 | 异常覆盖度 | 仅写"错误处理"无细节 |
| G4 | 可测试性 | 全部 AC 无结构化表述 |
| G5 | 一致性 | 名称不同导致歧义 |

### 使用方式

```
/zdoc-design-check --dir docs/ --domain all
```

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--input` | string | — | 单个文档路径 |
| `--dir` | string | — | 文档目录（自动发现） |
| `--domain` | enum | `all` | `business` / `product` / `ux` / `arch` / `test` / `eng` / `all` |
| `--layer` | enum | `full` | `gate-only`（仅质量门）/ `full`（全量） |
| `--output-dir` | string | `.design-check` | 输出目录 |

### 输入模式

| 模式 | 输入 | 可执行检查 | XC 跨维度 |
|------|------|-----------|----------|
| 单文档 | 1 个文件 | G1-G5 + 对应域检查 | SKIPPED |
| 多文档 | 2+ 个不同域文件 | 全量检查 | 触发 |
| 目录扫描 | `--dir docs/` | 自动发现，等同多文档 | 触发 |

### 使用示例

```bash
# 全量校验
/zdoc-design-check --dir docs/ --project my-project --domain all

# 仅校验商业设计
/zdoc-design-check --input docs/prd/xxx-prd.md --domain business

# 仅校验架构设计
/zdoc-design-check --dir docs/ --domain architecture

# 仅做通用质量门检查（快速筛查）
/zdoc-design-check --dir docs/ --layer gate-only

# 自定义输出目录
/zdoc-design-check --dir docs/ --output-dir .design-check
```

### 严重级别

| Level | 含义 | 说明 |
|-------|------|------|
| BLOCK | 必输要素缺失或严重不足 | 必须在 SSOT 开始前解决 |
| WARN | 存在但质量低于 MAC | 建议改进，不阻塞但标记 |
| PASS | 完整且满足 MAC | 通过 |
| N/A | 不适用 | 标注复用来源 |

### 输出

- `design-check.json` — 结构化检查结果（全量）
- `design-check-report.md` — 人可读 Markdown 报告

---

## 6. zdoc-i2i

### 功能概述

设计文档到实施任务转化引擎。输入 15+ 种设计文档，经过 6 阶段流水线：源文档交叉一致性校验 → 输入校验 → 内容整合 → 任务拆分 → 文档生成 → 交付前审核。遵循 ADR-004 v1.6。

### 核心特性

- **只读** — 不修改源设计文档
- **只整合不补充** — 不发明输入文档中不存在的功能/方案
- **最小可验收颗粒度** — 每个 Task 满足 5 个条件
- **DAG 确定性校验** — 周期检测通过 `validate-dag.py`，非 LLM
- **文档状态准入** — 仅接受 `approved` / `frozen` 状态

### 支持的文档类型（15+）

| 优先级 | 类型 | 必输/可选 |
|--------|------|----------|
| T01 | PRD | **必输** |
| T02 | Architecture | **必输** |
| T03 | API Design | 可选 |
| T04 | Business Design | 可选 |
| T05 | Tech Design | 可选 |
| T06 | UX Spec | 可选 |
| T07 | UX Prototype | 可选 |
| T08 | Test Design | 可选 |
| T09 | Data Flow | 可选 |
| T10 | DDD | 可选 |
| T11 | Skill Design | 可选 |
| T12 | Adapter Design | 可选 |
| T13 | Job Design | 可选 |
| T14 | Strategy | 可选 |
| T15 | Review | 可选 |

### 6 阶段流水线

| 阶段 | 说明 |
|------|------|
| Phase 0 | 源文档交叉一致性校验（ARCH-TESTSET 数量/语义/路径/版本） |
| Phase 1 | 输入校验（Gate Rubric，文档状态检查） |
| Phase 2 | 内容整合（按 Feature 聚合跨文档信息） |
| Phase 3 | 任务拆分（最小可验收颗粒度 + DAG 校验） |
| Phase 4 | 文档生成（task-*.md + INDEX.md + SUMMARY.md） |
| Phase 5 | 交付前审核 + 交付报告 |

### 使用方式

```
/zdoc-i2i --dir docs/mvp-lite/
```

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--dir` | string | — | 设计文档目录（推荐） |
| `--feature` | string | — | 仅处理指定 Feature ID（如 `M01`） |
| `--prd` | string | — | 指定 PRD 文件路径 |
| `--arch` | string | — | 指定 Architecture 文件路径 |
| `--api` | string | — | 指定 API Design 文件路径 |
| `--ux` | string | — | 指定 UX Spec 文件路径 |
| `--tech` | string | — | 指定 Tech Design 文件路径 |
| `--test` | string | — | 指定 Test Design 文件路径 |
| `--data` | string | — | 指定 Data Flow 文件路径 |
| `--ddd` | string | — | 指定 DDD 文件路径 |
| `--src` | string | — | 源代码根路径（用于路径规范化） |
| `--output-dir` | string | `docs/mvp-lite/impl` | 输出目录 |
| `--validate-only` | flag | — | 仅校验，不生成 Task |

### 使用示例

```bash
# 从目录自动扫描并转化
/zdoc-i2i --dir docs/mvp-lite/

# 指定各文档路径
/zdoc-i2i --prd docs/PRD.md --arch docs/ARCH.md --api docs/API.md

# 仅校验输入
/zdoc-i2i --dir docs/mvp-lite/ --validate-only

# 指定源代码根路径（路径规范化）
/zdoc-i2i --dir docs/mvp-lite/ --src apps/my-app/src
```

### 输出结构

```
docs/mvp-lite/impl/
└── impl-{feature}-{PRD-ID}/
    ├── feature-context.md          # Feature 上下文
    ├── task-list.json              # 任务列表（机器可读）
    ├── dag-validation.json         # DAG 校验结果
    ├── dependency-suggestions.json # 依赖建议
    ├── INDEX.md                    # 任务索引
    ├── SUMMARY.md                  # 交付汇总
    ├── IMPL-INDEX.md               # 实施索引
    ├── task-001-*.md               # 各任务文档
    └── ...
```

---

## 7. zgsd-bootstrap-milestone

### 功能概述

将预设计完成的文档包（PRD、UX 规格、技术设计等）转换为完整的 GSD 里程碑及规划产物。桥接"设计完成"到"可执行"，自动生成 GSD 原生格式的里程碑、需求、路线图和阶段上下文。

**与 `gsd-ingest-docs` 的区别**：`ingest-docs` 是增量合并文档内容到现有规划中；本技能将文档包视为**自包含的里程碑蓝图**，生成完整的独立里程碑。

### 四阶段执行流

| 阶段 | 说明 |
|------|------|
| Phase 1 | 准入门控（Blocking）— 验证 6 大维度，不通过则拒绝创建 |
| Phase 2 | 解析与映射 — 检测包结构模式，提取结构化数据 |
| Phase 3 | 生成 GSD 产物 — MILESTONE-CONTEXT.md, REQUIREMENTS.md, ROADMAP.md, Phase CONTEXT.md |
| Phase 4 | 与 GSD 集成 — 直接写入 `.planning/`，不调用 `/gsd-new-milestone` |

### 使用方式

```
/zgsd-bootstrap-milestone /path/to/docs --name "Milestone Name" --version 1.0
```

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| 位置参数 | string | — | 文档包目录路径（必填） |
| `--name` | string | 自动推断 | 里程碑名称 |
| `--version` | string | 下一版本 | 里程碑版本号 |
| `--mode` | enum | 自动检测 | `new`（覆盖）/ `merge`（追加，默认） |
| `--reset-phase-numbers` | flag | — | 阶段编号从 1 开始 |
| `--force` | flag | — | 跳过准入门控（危险） |

### 使用示例

```bash
# 基本用法
/zgsd-bootstrap-milestone docs/mvp-lite/ --name "MVP v1.0" --version 1.0

# 覆盖模式（替换已有里程碑产物）
/zgsd-bootstrap-milestone docs/mvp-lite/ --name "MVP v1.0" --mode new

# 跳过准入检查（危险操作）
/zgsd-bootstrap-milestone docs/mvp-lite/ --force
```

### 准入门控（6 大维度）

| 检查项 | 说明 |
|--------|------|
| Q1 文档存在性 | 覆盖 6 大维度的文档是否存在 |
| Q2 决策可追溯性 | 关键决策是否有来源/假设 |
| Q3 异常覆盖度 | 业务和系统异常是否定义 |
| Q4 可测试性 | AC 是否可用 Given-When-Then |
| Q5 一致性 | 术语、数值、逻辑跨文档一致 |
| Q6 实施范围 | 文件级别范围声明是否存在 |

### 注意事项

- BLOCKED = 不创建里程碑，返回差距报告
- Phase 4 后**不要调用** `/gsd-new-milestone`，否则会破坏已映射的 REQ-ID

---

## 8. zgsd-plan-phase

### 功能概述

将 I2I 输出的实施任务包桥接到 GSD PLAN 格式，实现确定性阶段规划。转换 `task-list.json` + `task-*.md` + `dag-validation.json` 为 GSD 可执行的 `*-PLAN.md` 文件。

### 自包含结构

本技能目录完全自包含，可直接复制到任何项目使用：

```
zgsd-plan-phase/
├── SKILL.md                    # 技能定义
├── import-task-pack.mjs        # 主桥接脚本
├── validate-bridge.mjs         # 桥接验证脚本
└── schemas/
    ├── task-pack.schema.json   # 任务包 Schema
    └── task-bridge.schema.json # 桥接产物 Schema
```

### 前置条件

运行前确认以下文件存在：

- `.planning/ROADMAP.md`
- `AGENTS.md`
- `AI_CONSTITUTION.md`
- `rules/agent-coding-guardrails.md`
- Impl 目录包含 `task-list.json` 和 `dag-validation.json`（status 必须为 PASS）

### 使用方式

```
/zgsd-plan-phase 0 /path/to/impl-task-pack
```

### 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| 位置参数 1 | int | Phase 编号（如 `0`） |
| 位置参数 2 | string | Impl task pack 目录路径 |
| `--dry-run` | flag | 仅预检，不写入 |
| `--force` | flag | 跳过 review gate |
| `--append` | flag | 追加到已有 PLAN |
| `--skip-review` | flag | 跳过审查门控 |
| `--app-dir` | string | 应用目录路径 |

### 使用示例

```bash
# 基本用法（自动检测 app 目录）
/zgsd-plan-phase 0 /path/to/impl-task-pack

# 仅预览不写入
/zgsd-plan-phase 0 /path/to/impl-task-pack --dry-run

# 指定应用目录（推荐显式指定）
/zgsd-plan-phase 0 /path/to/impl-task-pack --app-dir apps/my-app
```

### 路径规范化（Path Normalization）

**问题**：impl task markdown 和 acceptance criteria 中可能引用裸路径，如 `src/lib/ai/provider.factory.ts` 或 `tests/unit/env.test.ts`。如果直接写入 PLAN，agent 会在项目根目录错误创建文件。

**解决方案**：桥接脚本自动检测并规范化裸路径，将 `src/` → `apps/ai-coach-skill/src/`，`tests/` → `apps/ai-coach-skill/tests/` 等。规范化结果同时写入 PLAN 的 `files_modified`、XML `<files>` 和 `<done>` 元素，并记录到 `00-TASK-BRIDGE.json` 的 `path_normalization` 字段。

**自动检测的裸路径前缀**：`src/`、`tests/`、`test/`、`lib/`、`app/`、`pages/`、`middleware`、`drizzle.config`、`next.config`、`tsconfig`、`.eslintrc`、`.env`

> 建议始终通过 `--app-dir` 显式指定应用目录，避免自动检测不准。

### 执行步骤

1. **解析用户命令** — 提取 phase 编号、impl 目录、可选标志
2. **运行桥接脚本** — `node import-task-pack.mjs --phase <n> --impl <dir>`
3. **展示结果** — 门控状态、任务映射摘要、波次与依赖、生成文件列表
4. **报告下一步** — PASS → `$gsd-execute-phase <phase>`；REJECT → 展示失败原因

### 生成产物

文件写入 `.planning/phases/{padded-phase}-{phase-slug}/`：

| 文件 | 说明 |
|------|------|
| `00-CONTEXT.md` | 锁定的实施决策 |
| `00-TASK-BRIDGE.json` | 机器可读的桥接清单 |
| `00-01-PLAN.md` ... `00-NN-PLAN.md` | GSD 可执行计划 |
| `00-QUALITY-MAP.json` | 需求到测试的映射 |
| `00-VALIDATION.md` | 验证策略骨架 |

### 验证

```bash
node validate-bridge.mjs --phase <n>
```

---

## 常见工作流

### 工作流 A：设计文档 → 实施任务 → GSD 执行

```
1. zdoc-design-check    →  校验设计文档质量（55 项检查）
2. zdoc-quality-loop →  多角色质量收敛（修复文档问题）
3. zdoc-i2i              →  设计文档转化为实施任务
4. zgsd-plan-phase       →  任务包桥接到 GSD PLAN
5. gsd-execute-phase     →  GSD 执行阶段计划
```

### 工作流 B：设计文档 → GSD 里程碑

```
1. zdoc-design-check           →  校验设计文档质量
2. zgsd-bootstrap-milestone    →  文档包转换为 GSD 里程碑
3. gsd-plan-phase              →  阶段规划
4. gsd-execute-phase           →  执行
```

### 工作流 C：代码质量保障

```
1. zcode-safe-dev          →  编码阶段安全约束
2. zcode-patrol        →  代码库自动化巡检
3. zcode-review-deep   →  关键 PR 深度审查
```

---

## 附录

### 输出验证

部分技能提供验证脚本：

```bash
# zcode-patrol 验证
python zcode-patrol/validate.py .zcode-patrol/{patrol_id}

# zcode-review-deep 验证
python zcode-review-deep/validate.py .cr-deep/{batch_id}

# zdoc-i2i DAG 校验
python zdoc-i2i/validate-dag.py {task-list.json}

# zgsd-plan-phase 桥接验证
node zgsd-plan-phase/validate-bridge.mjs --phase <n>
```

### 目录结构约定

```
<skill-name>/
├── SKILL.md              # 核心定义文件（必须）
├── agents/               # Agent 角色定义（可选）
├── evidence/             # JSON Schema 契约（可选）
├── gate/                 # 通用质量门 Rubric（可选）
├── domains/              # 域 Rubric（可选）
├── cross-dimension/      # 跨维度 Rubric（可选）
├── references/           # 附属参考文档（可选）
├── scripts/              # 辅助脚本（可选）
├── schemas/              # JSON Schema（可选）
└── templates/            # 输出模板（可选）
```
