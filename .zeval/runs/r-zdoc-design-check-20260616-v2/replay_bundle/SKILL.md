---
name: zdoc-design-check
description: "Pre-SSOT 文档校验技能。6 大维度（商业/产品/UX/架构/测试/工程）+ 跨维度一致性，共 55 项检查。纯 LLM + 结构化输出架构，产出 BLOCK/WARN/PASS 诊断报告。"
argument-hint: "[--input PATH] [--dir DIR] [--domain business|product|ux|arch|test|eng|all] [--layer gate-only|full] [--output-dir .design-check]"
allowed-tools:
  - ReadFile
  - WriteFile
  - Shell
  - Grep
  - Glob
---

# zdoc-design-check

Skill for Pre-SSOT document validation across 6 dimensions (Business Design, Product Design, UX Design, Architecture Design, Test Design, Engineering Implementation) + cross-dimension consistency. Pure LLM + structured output architecture — LLM handles all checks (deterministic + semantic), domain rubrics embedded in prompt.

## 1. 目标与非目标

### 1.1 目标

- 对 Pre-SSOT 设计文档执行 6 大维度（商业/产品/UX/架构/测试/工程）+ 跨维度一致性检查。
- 基于 ITERATION-DOCUMENT-CHECKLIST 和 ADR-002 的 55 项规则，产出 BLOCK / WARN / PASS 诊断报告。
- 帮助团队在正式进入 SSOT 撰写前发现文档缺陷，降低下游返工成本。
- 作为纯 LLM + 结构化输出技能运行，无需外部 linter 或人工逐项检查。

### 1.2 非目标

- **Not a replacement for `zdoc-quality-loop`**（互补；Quality Loop 负责文档结构/可读性/多轮收敛，Design Check 负责商业设计输入充分性）
- **Not a document editor**（只产出诊断报告，绝不修改源文档）
- **Not a gate decision maker**（只提供证据，最终 verdict 由人工确认）
- **Not a SSOT formalization tool**（在 SSOT 之前运行，不参与 SSOT 规范化）
- **Not a code review tool**（代码审查请使用 `zcode-review-deep` / `zcode-patrol`）

## 2. 输入/输出

### 2.1 输入

| 输入项 | 形态 | 必填 | 说明 |
|--------|------|------|------|
| `--input` / `--dir` | 文件路径或目录 | 是 | 待校验的设计文档（单个/多个/目录扫描） |
| `--domain` | `business\|product\|ux\|arch\|test\|eng\|all` | 否，默认 `all` | 指定校验域 |
| `--layer` | `gate-only\|full` | 否，默认 `full` | 仅通用质量门或全量检查 |
| `--output-dir` | 目录路径 | 否，默认 `.design-check` | 产物输出根目录 |
| `--project` | 项目标识 | 否 | 用于跨文档一致性追踪 |

### 2.2 输出

| 输出项 | 路径约定 | 说明 |
|--------|----------|------|
| `design-check.json` | `{output_dir}/{check_id}/design-check.json` | 结构化检查结果（全量） |
| `design-check-report.md` | `{output_dir}/{check_id}/design-check-report.md` | 人可读 Markdown 报告 |
| `design-check-verdict.json` | `{output_dir}/{check_id}/design-check-verdict.json` | 人工确认后的 verdict |

### 2.3 退出状态

| 状态 | 含义 |
|------|------|
| `PASS` | 所有检查通过 |
| `CONDITIONAL` | 有 WARN 但无 BLOCK，可带标注继续 |
| `BLOCK` | 任一文档/域触发 FAIL，需修复后重跑 |

## 3. 执行步骤

```
1. 参数解析      读取 --input/--dir/--domain/--layer/--output-dir 等参数
2. 文档发现      扫描路径，按文件名/目录/内容特征识别文档类型与域映射
3. Gate 校验     按 gate/rubric.md 执行 G1–G5；任一 BLOCK 则停止
4. 域检查        对每个识别到的域执行对应 rubric.md（BD/PD/UX/AD/TD/EI）
5. 跨维度一致性   多文档模式下执行 cross-dimension/rubric.md（XC）
6. 结构化输出     生成 design-check.json + design-check-report.md
7. 人工确认       展示摘要，用户确认或补充后写入 design-check-verdict.json
```

## Primary Abstraction

Skill (governed capability template)

## Secondary Abstraction

Pipeline — LLM multi-layer validation with structured report output

## Authority

Canonical bundle: `zdoc-design-check/`

## Canonical Authority

- ADR: ADR-002 v2.1 (Pre-SSOT 文档校验技能 — 纯 LLM + 结构化输出架构)
- Reference: `ITERATION-DOCUMENT-CHECKLIST v2.1` (§2.1–§2.6 六大维度 + §二 Pre-SSOT 质量门 + PRD 可测性预审)

## 关联文档

| 文档 | 关系 | 说明 |
|------|------|------|
| [ADR-002](../adr/ADR-002-商业设计文档校验技能-Design-Check-Skill-基线.md) | 上游 | 设计基线，定义 55 项校验规则 |
| [ADR-004](../adr/ADR-004-设计文档到实施任务拆分技能-I2I-Impl-Skill-设计规范.md) | 下游 | 校验通过后的设计文档进入任务拆分 |
| [ITERATION-DOCUMENT-CHECKLIST](../docs/ITERATION-DOCUMENT-CHECKLIST.md) | 上游 | 定义 MAC 标准和必输要素 |

## Runtime Boundary Baseline

This capability is a governed `Skill` for `Business Design Document → Structured Validation Report` transformation.

- **Read-only validation** — does NOT modify source documents.
- **Evidence-only output** — does NOT make gate decisions; human confirms.
- **MAC-driven** — uses Minimum Acceptable Criteria from ITERATION-DOCUMENT-CHECKLIST as thresholds.
- **Pure LLM execution** — all checks (deterministic + semantic) handled by LLM, domain rubrics embedded in prompt.
- **Check IDs** follow `{layer}-{seq}` format (e.g., `G1`, `BD-4`, `P2`, `XC-1`).

## 架构

```
┌───────────────────────────────────────────────────────────────────┐
│                    纯 LLM + 结构化输出 架构                        │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  LLM Agent（单一执行者）                                           │
│  ────────────────────                                             │
│  1. 读取输入文档                                                   │
│  2. 自动识别文档类型 → 映射到域                                     │
│  3. 按 Rubric 逐项校验（G1–G5 → BD/PD/UX/AD/TD/EI → XC）         │
│  4. 输出结构化 JSON（每项: check_id + status + evidence）           │
│  5. 输出人可读 Markdown 报告                                        │
│                                                                   │
│  Rubric 文件（按需加载）                                            │
│  ────────────────────                                             │
│  gate/rubric.md                     → G1–G5 通用质量门（始终加载）  │
│  domains/business-design/rubric.md  → D1 商业设计 (BD-1–BD-6)     │
│  domains/product-design/rubric.md   → D2 产品设计 (PD-1–PD-7)     │
│  domains/ux-design/rubric.md        → D3 UX 设计 (UX-1–UX-7)     │
│  domains/architecture/rubric.md     → D4 架构设计 (AD-1–AD-9)     │
│  domains/test-design/rubric.md      → D5 测试设计 (TD-1–TD-8)     │
│  domains/engineering/rubric.md      → D6 工程实施 (EI-1–EI-5)     │
│  cross-dimension/rubric.md          → XC 跨维度 (XC-1–XC-8)      │
│                                                                   │
│  输入: 文档路径（单个/多个/目录）                                     │
│  输出: design-check.json + design-check-report.md                  │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### 2.1.1 输入模式与文档识别

| 模式 | 输入 | 可执行的检查 | XC 跨维度 |
|------|------|------------|----------|
| **单文档** | 1 个文件 | 通用质量门 G1–G5 + 该文档对应的域检查 | ❌ SKIPPED |
| **多文档** | 2+ 个不同域文件 | 全量检查 | ✅ 触发 |
| **目录扫描** | `--dir docs/` | 自动发现，等同多文档 | ✅ 触发 |

文档→域自动识别规则：

| 文档特征 | 识别规则 | 映射到域 |
|---------|---------|---------|
| PRD（含用户故事、AC、业务规则） | 路径含 `prd/` 或内容含 `US-`/`AC`/`用户故事` | D1 商业设计 + D2 产品设计 |
| UX 规格说明书 | 路径含 `ux/` 或内容含 `设计原则`/`交互流程`/`设计令牌` | D3 UX 设计 |
| Tech Design（含 API、数据流、时序图） | 路径含 `tech/` 或内容含 `API`/`时序图`/`同步.*异步` | D4 架构设计 |
| TESTSET 文档 | 路径含 `testset/` 或内容含 `测试范围`/`Happy Path`/`边界条件` | D5 测试设计 |
| 实施范围声明 | 内容含 `实施范围`/`涉及模块`/`关键决策` | D6 工程实施 |
| 产品愿景/简报 | 路径含 `PROJECT.md` 或内容含 `产品定位`/`目标用户`/`核心价值` | D1 商业设计 |

XC 检查缺少任一相关域产物时标记 `SKIPPED`，不计入 BLOCK/WARN。

## 领域总览

| 域 ID | 域名称 | Check ID 前缀 | 检查项数 | Rubric 文件 |
|-------|--------|---------------|---------|-------------|
| **G** | 通用质量门 | `G-*` | 5 | `gate/rubric.md` |
| **D1** | 商业设计 | `BD-*` | 6 | `domains/business-design/rubric.md` |
| **D2** | 产品设计 | `PD-*` | 7 | `domains/product-design/rubric.md` |
| **D3** | UX 设计 | `UX-*` | 7 | `domains/ux-design/rubric.md` |
| **D4** | 架构设计 | `AD-*` | 9 | `domains/architecture/rubric.md` |
| **D5** | 测试设计 | `TD-*` | 8 | `domains/test-design/rubric.md` |
| **D6** | 工程实施 | `EI-*` | 5 | `domains/engineering/rubric.md` |
| **XC** | 跨维度一致性 | `XC-*` | 8 | `cross-dimension/rubric.md` |
| **合计** | | | **55** | |

## Execution Protocol

### 执行流程

#### 阶段 1: 文档读取与上下文构建

1. 读取输入参数（`--input` / `--dir` / `--domain` / `--layer`）
2. 读取输入文档内容
3. 确定文档→域映射（按上表规则自动识别）
4. 加载 Gate Rubric: 读取 `gate/rubric.md`
5. 加载已识别域的 Rubric: 读取 `domains/{domain}/rubric.md`
6. 如果是多文档模式，加载 `cross-dimension/rubric.md`

#### 阶段 2: 通用质量门 (G1–G5)

按 `gate/rubric.md` 逐项校验。**任一 BLOCK 则停止，不进入域检查**。

对每项检查输出：
```json
{
  "check_id": "G1",
  "status": "PASS | WARN | BLOCK",
  "evidence": "具体发现",
  "suggestion": "改进建议（WARN/BLOCK 时必填）"
}
```

#### 阶段 3: 领域检查

对每个已识别的域，按该域的 `rubric.md` 逐项校验。

已实现的域：
- **D1 商业设计**: `domains/business-design/rubric.md` (BD-1–BD-6)
- **D2 产品设计**: `domains/product-design/rubric.md` (PD-1–PD-7)
- **D3 UX 设计**: `domains/ux-design/rubric.md` (UX-1–UX-7)
- **D4 架构设计**: `domains/architecture/rubric.md` (AD-1–AD-9)
- **D5 测试设计**: `domains/test-design/rubric.md` (TD-1–TD-8)
- **D6 工程实施**: `domains/engineering/rubric.md` (EI-1–EI-5)

对每项检查输出：
```json
{
  "check_id": "BD-1",
  "status": "PASS | WARN | BLOCK | N/A",
  "evidence": "具体发现",
  "suggestion": "改进建议（WARN/BLOCK 时必填）",
  "na_source": "N/A 时标注复用来源"
}
```

域检查独立执行 — 一个域的 BLOCK 不阻塞其他域。

#### 阶段 4: 跨维度一致性 (XC) — 仅多文档模式

按 `cross-dimension/rubric.md` 逐项校验。从各域结果中提取指标/故事/AC/Feature/Scope 列表，做语义对齐判断。

XC 检查项缺少任一相关域产物时标记 `SKIPPED`（原因：`missing_domain:{domain_id}`），不计入 BLOCK/WARN。

#### 阶段 5: 结构化输出

输出两个文件：

**design-check.json**:
```json
{
  "check_id": "DC-{YYYYMMDD}-{seq}",
  "timestamp": "ISO 8601",
  "iteration_type": "商业迭代 | 功能迭代",
  "document_refs": [{"path": "...", "type": "..."}],
  "verdict": "PASS | BLOCK | CONDITIONAL",
  "stats": {"total_checks": 0, "pass": 0, "warn": 0, "block": 0, "na": 0, "skipped": 0},
  "gate_results": [{"check_id": "G1", "status": "...", "evidence": "..."}],
  "domain_results": {
    "D1": [{"check_id": "BD-1", "status": "...", "evidence": "..."}]
  },
  "xc_results": [{"check_id": "XC-1", "status": "...", "evidence": "..."}],
  "blocking_items": [{"check_id": "...", "level": "BLOCK", "message": "...", "suggestion": "..."}],
  "warn_items": [{"check_id": "...", "level": "WARN", "message": "...", "suggestion": "..."}]
}
```

**design-check-report.md**: 人可读的 Markdown 报告，按域分组展示结果。

#### 阶段 6: 人工确认 [Human]

展示报告摘要，用户确认或补充。

## Workflow Boundary

- **Input**: Document path(s) — PRD, UX Spec, Tech Design, or project directory
- **Output**: Validation artifact bundle under `{output_dir}/design-check/{check_id}/`
  - `design-check.json` — [LLM] 结构化检查结果（全量）
  - `design-check-report.md` — [LLM] human-readable final report
  - `design-check-verdict.json` — [Human] verdict after confirmation
- **Out of scope**:
  - Document editing or correction
  - SSOT formalization

## Non-Negotiable Rules

- Do not modify source documents under any circumstance.
- Do not fabricate findings — every BLOCK/WARN must cite specific evidence from the document.
- Gate Check (Layer 0) must complete before domain checks begin.
- Any BLOCK in Gate Check stops execution — do not proceed to domain checks.
- Domain checks are independent — one domain's BLOCK does not block other domains.
- All artifacts written to disk immediately; no in-memory-only state.
- Verdict is always human-confirmed; the skill only recommends.
- Check IDs must be stable within a run (no renumbering).
- MAC standards from ITERATION-DOCUMENT-CHECKLIST v2.1 are authoritative.
- New domain rubrics must follow the rubric protocol (rubric.md with PASS/FAIL conditions).

## Severity Levels

| Level | Meaning | Action |
|-------|---------|--------|
| **BLOCK** | Required element missing or critically insufficient | Must be resolved before SSOT can start |
| **WARN** | Element exists but quality is below MAC | Recommended to improve; does not block but flagged |
| **PASS** | Element complete and meets MAC | Cleared |
| **N/A** | Not applicable for this iteration type | Labeled with reuse source |

## Pitfalls / 常见坑与规避

| # | 常见坑 | 影响 | 规避方法 |
|---|--------|------|----------|
| 1 | 把 Design Check 当文档编辑器，要求它直接修改源文档 | 破坏已评审基线、引入未授权变更 | 明确只产出诊断报告；修改文档使用 `zdoc-write` 或手动编辑 |
| 2 | 传入 `draft` / `reviewing` 状态文档并期望通过 | 检查结果无效，下游仍可能大幅变更 | 确保文档至少为 `approved` 状态再运行 Design Check |
| 3 | 只跑单文档却期望触发跨维度一致性（XC）检查 | XC 被 SKIP，遗漏跨文档冲突 | 传入 2+ 个不同域文件或使用 `--dir` 目录扫描 |
| 4 | 忽略 WARN 项直接进入 SSOT | 低质量文档进入下游，导致 I2I 任务缺陷 | 将 WARN 项视为必须修复或显式接受的风险 |
| 5 | 自定义 rubric 未遵循 `rubric.md` 协议 | Check ID 不稳定、报告无法被工具消费 | 新增域 rubric 必须含 PASS/FAIL 条件和稳定 ID 格式 |

## Usage Examples

```bash
# Validate all dimensions (full check)
zdoc-design-check --dir docs/ --project my-project --domain all

# 预期输出：
# {output_dir}/DC-20260616-001/design-check.json
# {output_dir}/DC-20260616-001/design-check-report.md

# Validate only Business Design (D1)
zdoc-design-check --input docs/prd/xxx-prd.md --domain business

# Validate only Architecture Design (D4)
zdoc-design-check --dir docs/ --domain architecture

# Gate check only (quick screen, all domains)
zdoc-design-check --dir docs/ --layer gate-only

# Custom output directory
zdoc-design-check --dir docs/ --output-dir .design-check
```

## Compatibility Note

This is a Skill for Pre-SSOT document validation following ADR-002 v2.1 (pure LLM + structured output architecture). All 6 domain rubrics (D1–D6) + cross-dimension (XC) + gate check (G) are implemented. All validation rules and rubrics are bundled in this directory — no external resources required.
