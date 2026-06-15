---
name: zdoc-design-check
description: "Pre-SSOT 文档校验技能。支持 Minimal Spec 轻量准入和 6 大维度详细检查 + 跨维度一致性，共 63 项检查。纯 LLM + 结构化输出架构，产出 BLOCK/WARN/PASS 诊断报告。"
argument-hint: "[--input PATH] [--dir DIR] [--domain business|product|ux|architecture|test|engineering|minimal-spec|all] [--layer gate-only|full] [--output-dir .design-check]"
allowed-tools:
  - ReadFile
  - WriteFile
  - Shell
  - Grep
  - Glob
---

# zdoc-design-check

Skill for Pre-SSOT document validation. 自 ADR-006 起，支持两类输入：
1. **Minimal Spec 准入检查**：`doc_type: spec` / `SPEC-M...` 文件，仅执行 MS 域检查，避免误判
2. **详细 SSOT 文档检查**：6 大维度（Business/Product/UX/Architecture/Test/Engineering）+ Cross-dimension consistency

纯 LLM + 结构化输出架构。

## Primary Abstraction

Skill (governed capability template)

## Secondary Abstraction

Pipeline — LLM multi-layer validation with structured report output

## Authority

Canonical bundle: `zdoc-design-check/`

## Not Equal To

- Not a replacement for `zdoc-quality-loop` (complements it; Doc Quality Loop for document structure/readability, Design Check for business design input sufficiency)
- Not a document editor (produces diagnostic reports only, never modifies source documents)
- Not a gate decision maker (evidence-only, human confirms verdict)
- Not a SSOT formalization tool (runs BEFORE SSOT, not during)

## Canonical Authority

- ADR-002: Pre-SSOT 文档校验技能基线 (v2.2)
- ADR-006: zdoc-write 最小 Spec 模式
- Reference: `ITERATION-DOCUMENT-CHECKLIST v2.1` (§2.1–§2.6 六大维度 + §二 Pre-SSOT 质量门 + PRD 可测性预审)

## 关联文档

| 文档 | 关系 | 说明 |
|------|------|------|
| [ADR-002](../../adr/ADR-002-商业设计文档校验技能-Design-Check-Skill-基线.md) | 上游 | 设计基线，定义 63 项校验规则 |
| [ADR-006](../../adr/ADR-006-zdoc-write最小Spec模式-Minimal-Spec-Mode-设计决策.md) | 上游 | Minimal Spec 默认模式规范 |
| [ADR-004](../../adr/ADR-004-设计文档到实施任务拆分技能-I2I-Impl-Skill-设计规范.md) | 下游 | 校验通过后的设计文档进入任务拆分 |
| [ITERATION-DOCUMENT-CHECKLIST](../../docs/ITERATION-DOCUMENT-CHECKLIST.md) | 上游 | 定义 MAC 标准和必输要素 |

## Runtime Boundary Baseline

This capability is a governed `Skill` for `Document → Structured Validation Report` transformation.

- **Read-only validation** — does NOT modify source documents
- **Evidence-only output** — does NOT make gate decisions; human confirms
- **MAC-driven** — uses ITERATION-DOCUMENT-CHECKLIST / ADR-006 defined thresholds
- **Pure LLM execution** — all checks (deterministic + semantic) handled by LLM, domain rubrics embedded in prompt
- **Check IDs** follow `{layer}-{seq}` format (e.g., `G1`, `BD-1`, `MS-1`, `XC-1`)

## 架构

```
┌───────────────────────────────────────────────────────────────────┐
│                  纯 LLM + 结构化输出架构                           │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  LLM Agent（单一执行者）                                           │
│  ──────────────────────────                                       │
│  1. 读取输入文档路径（单个/多个/目录扫描）                           │
│  2. 文档族识别：先判断是否为 Minimal Spec（最高优先级）              │
│  3. 按 Rubric 逐项校验（G1–G5 → MS/BD/UX/AD/TD/EI → XC）          │
│  4. 输出结构化 JSON（每项: check_id + status + evidence）          │
│  5. 输出人可读 Markdown 报告                                      │
│                                                                   │
│  Rubric 文件（按需加载）                                           │
│  ──────────────────────────                                       │
│  gate/rubric.md → G1–G5 通用质量门（始终加载）                      │
│  domains/minimal-spec/rubric.md → MS 域（仅 Minimal Spec）        │
│  domains/business-design/rubric.md → D1 商业设计（仅详细文档）     │
│  domains/product-design/rubric.md → D2 产品设计（仅详细文档）      │
│  domains/ux-design/rubric.md → D3 UX 设计（仅详细文档）            │
│  domains/architecture/rubric.md → D4 架构设计（仅详细文档）         │
│  domains/test-design/rubric.md → D5 测试设计（仅详细文档）         │
│  domains/engineering/rubric.md → D6 工程实施（仅详细文档）         │
│  cross-dimension/rubric.md → XC 跨维度（仅多文档且非单 MS）        │
│                                                                   │
│  输入: 文档路径（单个/多个/目录）                                  │
│  输出: design-check.json + design-check-report.md + verdict       │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## 输入模型

| 模式 | 输入 | 可执行的检查 | XC 跨维度 |
|------|------|------------|----------|
| **Minimal Spec 单文档** | 1 个 `doc_type: spec` 或 `SPEC-M...` 文件 | G1–G5（spec 兼容）+ MS-1–MS-8 | ❌ 全部 SKIPPED（minimal_spec_single_mode） |
| **详细单文档** | 1 个详细文件（PRD/UX/Tech/TESTSET 等） | G1–G5 + 该文档对应域 | ❌ SKIPPED |
| **多文档** | 2+ 个不同域文件 | G1–G5 + MS（若有）+ 各详细域 + XC（可触发） | ✅ 触发 |
| **目录扫描** | `--dir docs/` | 自动发现，等同多文档模式 | ✅ 触发 |

### 文档→域自动识别规则

**Minimal Spec（最高优先级）**：
| 文档特征 | 识别规则 | 映射到域 |
|---------|---------|---------|
| Minimal Spec | `frontmatter.doc_type == spec` **或** 文件名以 `SPEC-M` 开头 **或** 同时包含 `# Goal`、`# Scope`、`# Business Rules` | MS Minimal Spec 域 |

**详细 SSOT 文档**（非 spec）：
| 文档特征 | 识别规则 | 映射到域 |
|---------|---------|---------|
| PRD（含用户故事、AC、业务规则） | 路径含 `prd/` 或内容含 `US-`/`AC`/`用户故事` | D1 商业设计 + D2 产品设计 |
| UX 规格说明书 | 路径含 `ux/` 或内容含 `设计原则`/`交互流程`/`设计令牌` | D3 UX 设计 |
| Tech Design（含 API、数据流、时序图） | 路径含 `tech/` 或内容含 `API`/`时序图`/`同步.*异步` | D4 架构设计 |
| TESTSET 文档 | 路径含 `testset/` 或内容含 `测试范围`/`Happy Path`/`边界条件` | D5 测试设计 |
| 实施范围声明 | 内容含 `实施范围`/`涉及模块`/`关键决策` | D6 工程实施 |
| 产品愿景/简报 | 路径含 `PROJECT.md` 或内容含 `产品定位`/`目标用户`/`核心价值` | D1 商业设计 |

XC 检查项缺少任一相关域产物时标记 `SKIPPED`，不计入 BLOCK/WARN；单个 Minimal Spec 时全部 XC 项标记 `SKIPPED`。

## 领域总览

| 域 ID | 域名称 | Check ID 前缀 | 检查项数 | Rubric 文件 | 适用输入 |
|-------|--------|---------------|---------|-------------|---------|
| **G** | 通用质量门 | `G-*` | 5 | `gate/rubric.md` | 全部 |
| **MS** | Minimal Spec 准入 | `MS-*` | 8 | `domains/minimal-spec/rubric.md` | 仅 Minimal Spec |
| **D1** | 商业设计 | `BD-*` | 6 | `domains/business-design/rubric.md` | 仅详细文档 |
| **D2** | 产品设计 | `PD-*` | 7 | `domains/product-design/rubric.md` | 仅详细文档 |
| **D3** | UX 设计 | `UX-*` | 7 | `domains/ux-design/rubric.md` | 仅详细文档 |
| **D4** | 架构设计 | `AD-*` | 9 | `domains/architecture/rubric.md` | 仅详细文档 |
| **D5** | 测试设计 | `TD-*` | 8 | `domains/test-design/rubric.md` | 仅详细文档 |
| **D6** | 工程实施 | `EI-*` | 5 | `domains/engineering/rubric.md` | 仅详细文档 |
| **XC** | 跨维度一致性 | `XC-*` | 8 | `cross-dimension/rubric.md` | 仅多文档且非单 MS |
| **合计** | | | **63** | | |

## Execution Protocol

### 执行流程

#### 阶段 1：文档读取与上下文构建

1. 读取输入参数（`--input` / `--dir` / `--domain` / `--layer`）
2. 读取输入文档内容
3. **文档族识别**（优先判断是否为 Minimal Spec）
4. 确定文档→域映射
5. 加载 Gate Rubric: `gate/rubric.md`
6. 加载已识别域的 Rubric:
   - MS 则加载 `domains/minimal-spec/rubric.md`
   - 详细文档则加载对应 `domains/{domain}/rubric.md`
7. 多文档模式加载 `cross-dimension/rubric.md`

#### 阶段 2：通用质量门 (G1–G5)

按 `gate/rubric.md` 逐项校验。**任一 BLOCK 则停止，不进入域检查**。

- 对 Minimal Spec，G1/G3/G4 走兼容分支
- 对详细文档，走原分支

#### 阶段 3：领域检查

- 若为 Minimal Spec：按 `domains/minimal-spec/rubric.md` 执行 MS-1–MS-8，**跳过 D1–D6**
- 若为详细文档：对每个已识别域按 Rubric 逐项检查

域检查独立执行 — 一个域的 BLOCK 不阻塞其他域。

#### 阶段 4：跨维度一致性 (XC) — 仅多文档模式且非单个 Minimal Spec

按 `cross-dimension/rubric.md` 逐项校验。

- 单个 Minimal Spec：全部 XC 项 SKIPPED，原因 `minimal_spec_single_mode`
- 其他多文档：从各域结果提取指标/故事/AC/Feature/Scope 做语义对齐

#### 阶段 5：结构化输出

输出两个文件：
- `design-check.json`：完整结构化结果
- `design-check-report.md`：人可读 Markdown 报告

#### 阶段 6：人工确认 [Human]

展示报告摘要，用户确认或补充，输出 `design-check-verdict.json`。

## Workflow Boundary

- **Input**: Document path(s) — Minimal Spec, PRD, UX Spec, Tech Design, etc.
- **Output**: Validation artifact bundle under `{output_dir}/design-check/{check_id}/`
  - `design-check.json` — [LLM] 结构化检查结果
  - `design-check-report.md` — [LLM] 人可读报告
  - `design-check-verdict.json` — [Human] 人工确认结果
- **Out of scope**:
  - Document editing or correction
  - SSOT formalization

## Non-Negotiable Rules

- Do not modify source documents under any circumstance
- Do not fabricate findings — every BLOCK/WARN must cite specific evidence from the document
- Gate Check (Layer 0) must complete before domain checks begin
- Any BLOCK in Gate Check stops execution — do not proceed to domain checks
- Domain checks are independent — one domain's BLOCK does not block other domains
- **不误判轻量 Spec**: Minimal Spec 只执行 MS 域，不套用详细文档标准
- **Minimal Spec 优先识别**: 先判断是否为 spec，再识别为详细文档
- All artifacts written to disk immediately; no in-memory-only state
- Verdict is always human-confirmed; the skill only recommends
- Check IDs must be stable within a run (no renumbering)
- MAC standards from ITERATION-DOCUMENT-CHECKLIST / ADR-006 are authoritative
- New domain rubrics must follow rubric protocol (rubric.md with PASS/FAIL conditions)

## Severity Levels

| 级别 | 含义 | 后果 |
|------|------|------|
| **BLOCK** | 必输要素缺失或严重不合格 | 阻塞进入 SSOT，必须补充后重新提交 |
| **WARN** | 要素存在但质量不足（如 Out of Scope 不够具体） | 建议补充，不阻塞但标记风险 |
| **PASS** | 要素完整且达到 MAC 标准 | 通过 |
| **N/A** | 不适用（如功能迭代复用用户画像；单个 MS 时的 G3/XC） | 标注不适用原因 |
| **SKIPPED** | 缺少相关域产物或单个 Minimal Spec | 不计入统计 |

## Usage Examples

```bash
# 校验单个 Minimal Spec（仅 G1–G5 spec 兼容 + MS-1–MS-8，跳过 D1–D6/XC）
zdoc-design-check --input docs/drafts/specs/SPEC-M001-xxx.md

# 校验单个详细 PRD（D1+D2）
zdoc-design-check --input docs/prd/xxx-prd.md

# 多文档校验（触发 XC）
zdoc-design-check --input docs/prd/xxx-prd.md --input docs/ux/xxx-ux-spec.md --input docs/tech/xxx-tech.md

# 目录扫描（自动发现 Minimal Spec 和详细文档）
zdoc-design-check --dir docs/ --project my-project

# 仅校验特定域（如 minimal-spec）
zdoc-design-check --dir docs/ --domain minimal-spec

# 仅运行质量门（快速筛查）
zdoc-design-check --dir docs/ --layer gate-only

# 自定义输出目录
zdoc-design-check --dir docs/ --output-dir .design-check
```

## Compatibility Note

This is a Skill for Pre-SSOT document validation following ADR-002 v2.2 and ADR-006. 支持 Minimal Spec 默认模式和详细 SSOT 文档检查。
