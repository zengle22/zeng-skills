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

## 1. 目标与非目标

### 1.1 目标

- 对 Pre-SSOT 设计文档执行 6 大维度（商业/产品/UX/架构/测试/工程）+ 跨维度一致性检查。
- 基于 ITERATION-DOCUMENT-CHECKLIST 和 ADR-002 的 55 项规则，产出 BLOCK / WARN / PASS 诊断报告。
- 对涉及用户交互的 PRD，强制校验用户旅程是否覆盖主路径、分支路径、异常路径，并能映射到 FR / AC。
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

### 2.1.1 输入模式与文档识别

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
| PRD（含用户故事、AC、业务规则、用户旅程） | 路径含 `prd/` 或内容含 `US-`/`AC`/`用户故事`/`用户旅程` | D1 商业设计 + D2 产品设计 |
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
| **D2** | 产品设计 | `PD-*` | 7 | `domains/product-design/rubric.md`（PD-7 包含交互型 PRD 用户旅程强制检查） | 仅详细文档 |
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

已实现的域：
- **D1 商业设计**: `domains/business-design/rubric.md` (BD-1–BD-6)
- **D2 产品设计**: `domains/product-design/rubric.md` (PD-1–PD-7；PD-7 校验交互型 PRD 用户旅程)
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

- Do not modify source documents under any circumstance.
- Do not fabricate findings — every BLOCK/WARN must cite specific evidence from the document.
- Gate Check (Layer 0) must complete before domain checks begin.
- Any BLOCK in Gate Check stops execution — do not proceed to domain checks.
- Domain checks are independent — one domain's BLOCK does not block other domains.
- **不误判轻量 Spec**: Minimal Spec 只执行 MS 域，不套用详细文档标准。
- **Minimal Spec 优先识别**: 先判断是否为 spec，再识别为详细文档。
- All artifacts written to disk immediately; no in-memory-only state.
- Verdict is always human-confirmed; the skill only recommends.
- Check IDs must be stable within a run (no renumbering).
- MAC standards from ITERATION-DOCUMENT-CHECKLIST / ADR-006 are authoritative.
- 涉及用户交互的 PRD 若缺少用户旅程，或用户旅程未覆盖主路径/分支路径/异常路径，必须判为 BLOCK；纯后端/无人工交互 PRD 仅在文档明确说明不适用原因时可标记 N/A。
- New domain rubrics must follow the rubric protocol (rubric.md with PASS/FAIL conditions).

## Severity Levels

| 级别 | 含义 | 后果 |
|------|------|------|
| **BLOCK** | 必输要素缺失或严重不合格 | 阻塞进入 SSOT，必须补充后重新提交 |
| **WARN** | 要素存在但质量不足（如 Out of Scope 不够具体） | 建议补充，不阻塞但标记风险 |
| **PASS** | 要素完整且达到 MAC 标准 | 通过 |
| **N/A** | 不适用（如功能迭代复用用户画像；单个 MS 时的 G3/XC） | 标注不适用原因 |
| **SKIPPED** | 缺少相关域产物或单个 Minimal Spec | 不计入统计 |

## Pitfalls / 常见坑与规避

| # | 常见坑 | 影响 | 规避方法 |
|---|--------|------|----------|
| 1 | 把 Design Check 当文档编辑器，要求它直接修改源文档 | 破坏已评审基线、引入未授权变更 | 明确只产出诊断报告；修改文档使用 `zdoc-write` 或手动编辑 |
| 2 | 传入 `draft` / `reviewing` 状态文档并期望通过 | 检查结果无效，下游仍可能大幅变更 | 确保文档至少为 `approved` 状态再运行 Design Check |
| 3 | 只跑单文档却期望触发跨维度一致性（XC）检查 | XC 被 SKIP，遗漏跨文档冲突 | 传入 2+ 个不同域文件或使用 `--dir` 目录扫描 |
| 4 | 忽略 WARN 项直接进入 SSOT | 低质量文档进入下游，导致 I2I 任务缺陷 | 将 WARN 项视为必须修复或显式接受的风险 |
| 5 | 自定义 rubric 未遵循 `rubric.md` 协议 | Check ID 不稳定、报告无法被工具消费 | 新增域 rubric 必须含 PASS/FAIL 条件和稳定 ID 格式 |
| 6 | 交互型 PRD 缺少用户旅程但仍被判通过 | 下游 UX、测试和实施无法对齐真实用户流程 | PD-7 必须先判断交互信号；触发时缺少用户旅程或缺少主/分支/异常路径均判 BLOCK |

## Usage Examples

```bash
# 校验单个 Minimal Spec（仅 G1–G5 spec 兼容 + MS-1–MS-8，跳过 D1–D6/XC）
zdoc-design-check --input docs/drafts/specs/SPEC-M001-xxx.md

# 校验单个详细 PRD（D1+D2）
zdoc-design-check --input docs/prd/xxx-prd.md

# 预期输出：
# {output_dir}/DC-20260616-001/design-check.json
# {output_dir}/DC-20260616-001/design-check-report.md

# 仅校验 Business Design (D1)
zdoc-design-check --input docs/prd/xxx-prd.md --domain business

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
