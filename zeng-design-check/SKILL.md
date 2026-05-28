---
name: zeng-design-check
description: "Pre-SSOT 文档校验技能。6 大维度（商业/产品/UX/架构/测试/工程）+ 跨维度一致性，共 55 项检查。纯 LLM + 结构化输出架构，产出 BLOCK/WARN/PASS 诊断报告。"
argument-hint: "[--input PATH] [--dir DIR] [--domain business|product|ux|arch|test|eng|all] [--layer gate-only|full] [--output-dir .design-check]"
allowed-tools:
  - ReadFile
  - WriteFile
  - Shell
  - Grep
  - Glob
---

# zeng-design-check

Skill for Pre-SSOT document validation across 6 dimensions (Business Design, Product Design, UX Design, Architecture Design, Test Design, Engineering Implementation) + cross-dimension consistency. Pure LLM + structured output architecture — LLM handles all checks (deterministic + semantic), domain rubrics embedded in prompt.

## Primary Abstraction

Skill (governed capability template)

## Secondary Abstraction

Pipeline — LLM multi-layer validation with structured report output

## Authority

Canonical bundle: `zeng-design-check/`

## Not Equal To

- Not a replacement for `zeng-doc-quality-loop` (complements it; Doc Quality Loop for document structure/readability, Design Check for business design input sufficiency)
- Not a document editor (produces diagnostic reports only, never modifies source documents)
- Not a gate decision maker (evidence-only, human confirms verdict)
- Not a SSOT formalization tool (runs BEFORE SSOT, not during)

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

## 输入模型

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

## Usage Examples

```bash
# Validate all dimensions (full check)
zeng-design-check --dir docs/ --project my-project --domain all

# Validate only Business Design (D1)
zeng-design-check --input docs/prd/xxx-prd.md --domain business

# Validate only Architecture Design (D4)
zeng-design-check --dir docs/ --domain architecture

# Gate check only (quick screen, all domains)
zeng-design-check --dir docs/ --layer gate-only

# Custom output directory
zeng-design-check --dir docs/ --output-dir .design-check
```

## Compatibility Note

This is a Skill for Pre-SSOT document validation following ADR-002 v2.1 (pure LLM + structured output architecture). All 6 domain rubrics (D1–D6) + cross-dimension (XC) + gate check (G) are implemented. All validation rules and rubrics are bundled in this directory — no external resources required.
