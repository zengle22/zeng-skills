---
name: zcode-patrol
description: "定期对代码库进行自动化巡检，发现常见代码问题（风格漂移、架构腐化、安全漏洞、性能陷阱、重复代码等），生成结构化报告并推动修复，阻止代码熵增。"
argument-hint: "[--paths <dir>...] [--scope full|delta|staged|targeted] [--format markdown|json] [--max-files 500] [--output-dir .zcode-patrol] [--min-severity P0|P1|P2|P3] [--baseline <path>]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Agent
---

# zcode-patrol

代码熵巡检技能。对代码库执行自动化静态分析，发现质量退化问题，生成结构化报告。

## Not Equal To

- Not a replacement for ESLint, Pylint, SonarQube（补充/聚合）
- Not a runtime profiler or test executor
- Not a source code modifier（read-only）
- Not a gate decision maker（evidence-only）

## Execution Model

本技能采用**协作式执行架构**：

| 组件 | 职责 |
|------|------|
| **外层 AI Agent** | 完整流程编排：参数解析、文件发现、模式匹配、聚合、报告生成 |
| **agents/*.md** | Agent 角色定义（渐进式披露，按需加载） |
| **evidence/*.json** | 输出产物的 JSON Schema 契约 |
| **validate.py** | 输出产物的契约验证（可选） |

> **注意**：本技能是纯 SKILL.md 实现，所有流程逻辑由外层 AI Agent 执行。
> `validate.py` 仅用于验证输出产物是否符合 JSON Schema 契约。

## Parameters

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--paths` | array | `["."]` | 扫描的目录或文件路径 |
| `--scope` | enum | `full` | 扫描范围：`full` \| `delta` \| `staged` \| `targeted` |
| `--format` | enum | `markdown` | 输出格式：`markdown` \| `json` |
| `--max-files` | int | 500 | 最大扫描文件数 |
| `--output-dir` | string | `.zcode-patrol` | 输出目录 |
| `--min-severity` | enum | `P3` | 最低严重级别：`P0` \| `P1` \| `P2` \| `P3` |
| `--baseline` | string | null | 基线报告路径（用于对比） |

## Output Schema

所有输出产物必须符合以下 JSON Schema：

| 产物 | Schema | 说明 |
|------|--------|------|
| `report.json` | `patrol-report.schema.json` | 巡检报告 |
| `patrol-state.json` | `patrol-state.schema.json` | 执行状态 |
| `issues[]` | `issue.schema.json` | 问题列表 |

## Issue Schema（每条问题）

```json
{
  "id": "{patrol_id}-{rule_id}-{seq:04d}",
  "rule_id": "如 D01-001",
  "dimension": "D01 | D02 | D03 | D04 | D05 | D06 | D07 | D08",
  "severity": "P0 | P1 | P2 | P3",
  "file": "相对文件路径",
  "line_start": 10,
  "message": "问题描述",
  "found_by": "L1-pattern-matching | L3-statistical-aggregation",
  "confidence": 0.85
}
```

## Patrol Dimensions

| ID | Name | Severity |
|----|------|----------|
| D01 | Style Consistency | P2-P3 |
| D02 | Architecture Compliance | P0-P1 |
| D03 | Security Patterns | P0-P1 |
| D04 | Performance Anti-patterns | P1-P2 |
| D05 | Duplication & Dead Code | P2-P3 |
| D06 | Documentation Sync | P2-P3 |
| D07 | Dependency Health | P1-P2 |
| D08 | Test Coverage Drift | P1-P2 |

## Execution Protocol

1. **Initialize**
   - 解析参数，生成 `patrol_id`
   - 创建输出目录结构

2. **Discovery**
   - 按 `--scope` 展开文件列表
   - 应用排除规则（.gitignore, node_modules 等）
   - 写入 `manifest.json`

3. **Scan (L1 + L3)**
   - **L1 Pattern Matching**: 应用规则集的正则/AST 规则
   - **L3 Statistical Aggregation**: 运行外部工具（jscpd, vulture, pip-audit）
   - 写入 `raw/L1-results.json`, `raw/L3-results.json`

4. **Aggregation & Enrichment**
   - 去重合并跨层发现
   - 补充 git 元数据（git blame）
   - 计算质量分数
   - 基线对比（如提供）

5. **Reporting**
   - 生成 `report.json` + `report.md`
   - 生成 `hotspots.json`, `baseline-diff.json`
   - 写入最终 `patrol-state.json`

## Artifact Directory Structure

```
{output_dir}/{patrol_id}/
├── patrol-state.json
├── manifest.json
├── report.json
├── report.md
├── hotspots.json
├── baseline-diff.json (if baseline)
├── suggested-fixes.json (if fix_mode)
└── raw/
    ├── L1-results.json
    └── L3-results.json
```

## Validation

使用 `validate.py` 验证输出产物是否符合 Schema 契约：

```bash
# 验证整个巡检结果
python validate.py .zcode-patrol/20260527-120000-abc123def456

# 安装依赖
pip install jsonschema
```

## Non-Negotiable Rules

- 不修改源文件（read-only）
- 不执行测试或运行时分析
- 不做 gate 决策（仅产出证据）
- 不捏造统计数据（计数必须匹配原始证据）
- 工具不可用时优雅跳过，不崩溃

## Usage

在 Claude Code 中调用：

```
/zcode-patrol --paths src/ --scope full
/zcode-patrol --paths src/ --scope delta --baseline .zcode-patrol/20260527-120000-xxx/report.json
```
