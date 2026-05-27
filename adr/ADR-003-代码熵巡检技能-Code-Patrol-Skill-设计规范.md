# ADR-003：代码熵巡检技能（Code Patrol Skill）设计规范

> **SSOT ID**: ADR-003
> **Title**: 代码熵巡检技能设计规范 — 多维度静态分析、结构化报告、基线对比
> **Status**: Draft
> **Version**: v1.1
> **Effective Date**: TBD
> **Scope**: 代码巡检治理 / 静态分析 / 质量度量
> **Owner**: 架构 / 研发流程
> **Governance Kind**: NEW
> **Audience**: AI 实施代理、Code Patrol Skill、开发者、Tech Lead
> **Depends On**: ADR-020 (Skill 基线), ADR-057 (文件管理规范)
>
> 状态：Draft
> 日期：2026-05-27

---

## 1. 背景

### 1.1 One-Sentence Summary

> **现有代码质量保障依赖 PR Review 和 CI Lint，缺乏对代码库整体健康度的周期性巡检能力，无法系统性发现风格漂移、架构腐化、安全漏洞、性能陷阱、重复代码等问题，导致"代码熵增"持续累积。**

### 1.2 现有能力与缺口

| 工具 | 能力 | 缺口 |
|------|------|------|
| ESLint / Pylint | 单文件 Lint | 无跨文件架构检查，无基线对比 |
| SonarQube | 全面分析 | 需要独立部署，与 AI Agent 流程脱节 |
| PR Review | 变更审查 | 仅覆盖增量代码，不覆盖存量问题 |
| bmad-code-review | 快速扫描 | 维度单一，无结构化报告 |

需要一套**与 AI Agent 流程集成**的周期性代码巡检能力。

### 1.3 核心设计

```text
文件发现 → L1 模式匹配 + L3 统计聚合 → 去重合并 → 结构化报告 → 基线对比
```

---

## 2. 问题定义

### 2.1 代码熵增的五类表现

| 类型 | 表现 | 影响 |
|------|------|------|
| **风格漂移** | 命名不一致、格式混乱、注释缺失 | 可读性下降，维护成本增加 |
| **架构腐化** | 分层违规、循环依赖、上帝类 | 可维护性下降，变更风险增加 |
| **安全漏洞** | 硬编码凭证、SQL 拼接、XSS | 安全风险 |
| **性能陷阱** | N+1 查询、内存泄漏、重复计算 | 性能退化 |
| **代码重复** | 复制粘贴、平行实现 | DRY 违反，bug 修复遗漏 |

### 2.2 巡检需求

1. **周期性执行**：支持定期巡检（daily/weekly）
2. **增量对比**：支持与历史基线对比，发现退化
3. **多维度覆盖**：8 个质量维度
4. **结构化产物**：JSON Schema 约束，支持自动化处理
5. **AI Agent 集成**：与 Claude Code / Kimi CLI 流程无缝衔接

---

## 3. 架构设计

### 3.1 执行模型

采用**协作式执行架构**，纯 SKILL.md 实现 + JSON Schema 契约验证：

| 组件 | 职责 |
|------|------|
| **外层 AI Agent** | 完整流程编排：参数解析、文件发现、模式匹配、聚合、报告生成 |
| **agents/*.md** | Agent 角色定义（渐进式披露，按需加载） |
| **evidence/*.json** | 输出产物的 JSON Schema 契约 |
| **validate.py** | 输出产物的契约验证（可选） |

### 3.2 文件结构

```
zeng-code-patrol/
├── SKILL.md                        # 主文档
├── validate.py                     # 输出契约验证脚本
├── agents/
│   ├── executor.md                 # 执行器定义
│   └── supervisor.md               # 监督器定义
└── evidence/
    ├── issue.schema.json           # Issue Schema
    ├── patrol-report.schema.json   # 报告 Schema
    └── patrol-state.schema.json    # 状态 Schema
```

### 3.3 渐进式披露

| 文件 | 何时需要 |
|------|---------|
| `SKILL.md` | 总是需要 |
| `agents/*.md` | 需要理解 Agent 角色时 |
| `evidence/*.json` | 需要校验输出或扩展 Schema 时 |

---

## 4. 巡检维度

### 4.1 维度矩阵

| ID | Name | 检查内容 | Severity | Engine |
|----|------|---------|----------|--------|
| **D01** | Style Consistency | 命名规范、格式、注释质量 | P2-P3 | L1 + L3 |
| **D02** | Architecture Compliance | 分层违规、循环依赖、模块边界 | P0-P1 | L1 |
| **D03** | Security Patterns | 硬编码凭证、SQL 拼接、XSS | P0-P1 | L1 |
| **D04** | Performance Anti-patterns | N+1 查询、内存泄漏、重复计算 | P1-P2 | L1 |
| **D05** | Duplication & Dead Code | 代码重复、未使用代码 | P2-P3 | L3 |
| **D06** | Documentation Sync | 文档与代码不一致 | P2-P3 | L1 |
| **D07** | Dependency Health | 过时依赖、安全漏洞 | P1-P2 | L3 |
| **D08** | Test Coverage Drift | 测试覆盖下降、测试质量 | P1-P2 | L1 |

### 4.2 引擎说明

| 引擎 | 说明 | 工具示例 |
|------|------|---------|
| **L1** | 模式匹配（正则/AST） | 自定义规则、grep、ast-grep |
| **L3** | 统计聚合（外部工具） | jscpd、vulture、pip-audit、npm audit |

---

## 5. 执行流程

### 5.1 流水线

```
阶段 0: Initialize
    │
    ├── 解析参数，生成 patrol_id
    ├── 创建输出目录结构
    └── 输出: patrol-state.json (status: initializing)
    │
    ▼
阶段 1: Discovery
    │
    ├── 按 --scope 展开文件列表
    ├── 应用排除规则（.gitignore, node_modules 等）
    ├── 强制 max_files 和 max_file_size 限制
    └── 输出: manifest.json
    │
    ▼
阶段 2: Scan (L1 + L3)
    │
    ├── L1 Pattern Matching
    │      ├── 对每个文件应用规则集
    │      └── 输出: raw/L1-results.json
    │
    └── L3 Statistical Aggregation
           ├── 运行外部工具（如可用）
           ├── 记录跳过的维度及原因
           └── 输出: raw/L3-results.json
    │
    ▼
阶段 3: Aggregation & Enrichment
    │
    ├── 去重合并跨层发现
    ├── 分组相关问题
    ├── 补充 git 元数据（git blame）
    ├── 计算质量分数
    └── 基线对比（如提供 --baseline）
    │
    ▼
阶段 4: Reporting
    │
    ├── 生成 report.json（符合 Schema）
    ├── 生成 report.md（人类可读）
    ├── 生成 hotspots.json, baseline-diff.json
    └── 输出: patrol-state.json (status: completed)
    │
    ▼
阶段 5: Validation（可选）
    │
    └── 运行 validate.py 校验输出产物
```

### 5.2 状态机

```
initializing → scanning → aggregating → reporting → completed
                      ↓
                    failed
```

---

## 6. 输出产物

### 6.1 目录结构

```
{output_dir}/{patrol_id}/
├── patrol-state.json               # 执行状态
├── manifest.json                   # 扫描文件清单
├── report.json                     # 巡检报告（JSON）
├── report.md                       # 巡检报告（Markdown）
├── hotspots.json                   # 热点目录分析
├── baseline-diff.json              # 基线对比（如有）
└── raw/
    ├── L1-results.json             # L1 原始结果
    └── L3-results.json             # L3 原始结果
```

### 6.2 Issue Schema

```json
{
  "id": "{patrol_id}-{rule_id}-{seq:04d}",
  "rule_id": "如 D01-001",
  "dimension": "D01 | D02 | ... | D08",
  "severity": "P0 | P1 | P2 | P3",
  "file": "相对文件路径",
  "line_start": 10,
  "line_end": 15,
  "message": "问题描述",
  "evidence": "匹配的代码片段",
  "impact": "影响描述",
  "fix_suggestion": "修复建议",
  "found_by": "L1-pattern-matching | L3-statistical-aggregation",
  "confidence": 0.85,
  "author_git": "git blame 结果",
  "commit_hash": "最后修改的 commit"
}
```

### 6.3 Report Schema

```json
{
  "patrol_id": "20260527-120000-abc123def456",
  "summary": {
    "total_files_scanned": 150,
    "total_issues": 42,
    "by_severity": { "P0": 2, "P1": 5, "P2": 15, "P3": 20 },
    "by_dimension": { "D01": 10, "D02": 8, ... },
    "quality_score": 78
  },
  "issues": [...],
  "hotspots": [
    { "directory": "src/services", "issue_count": 15, "issue_density": 2.3 }
  ],
  "baseline_comparison": {
    "new_issues": 5,
    "resolved_issues": 3,
    "persistent_issues": 39
  }
}
```

---

## 7. 参数定义

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--paths` | array | `["."]` | 扫描的目录或文件路径 |
| `--scope` | enum | `full` | 扫描范围：`full` \| `delta` \| `staged` \| `targeted` |
| `--format` | enum | `markdown` | 输出格式：`markdown` \| `json` |
| `--max-files` | int | 500 | 最大扫描文件数 |
| `--max-file-size` | int | 1048576 | 单文件大小限制（字节） |
| `--output-dir` | string | `.zeng-code-patrol` | 输出目录 |
| `--min-severity` | enum | `P3` | 最低严重级别 |
| `--baseline` | string | null | 基线报告路径 |
| `--ruleset` | string | null | 自定义规则集路径 |
| `--non-interactive` | bool | false | 禁用交互提示 |
| `--fail-on-p0p1` | bool | false | 发现 P0/P1 时返回非零退出码 |

---

## 8. 契约验证

使用 `validate.py` 验证输出产物是否符合 JSON Schema：

```bash
# 验证整个巡检结果
python validate.py .zeng-code-patrol/20260527-120000-abc123def456

# 安装依赖
pip install jsonschema
```

验证内容：
- `report.json` → `patrol-report.schema.json`
- `patrol-state.json` → `patrol-state.schema.json`
- `issues[]` → `issue.schema.json`

---

## 9. Usage

在 Claude Code 中调用：

```bash
# 全量扫描
/zeng-code-patrol --paths src/ --scope full

# 增量扫描 + 基线对比
/zeng-code-patrol --paths src/ --scope delta --baseline .zeng-code-patrol/20260527-120000-xxx/report.json

# CI 模式（发现 P0/P1 失败）
/zeng-code-patrol --paths src/ --min-severity P1 --format json --non-interactive --fail-on-p0p1
```

---

## 10. Non-Negotiable Rules

- 不修改源文件（read-only）
- 不执行测试或运行时分析
- 不做 gate 决策（仅产出证据）
- 不捏造统计数据（计数必须匹配原始证据）
- 工具不可用时优雅跳过，不崩溃
- Issue ID 格式：`{patrol_id}-{rule_id}-{seq:04d}`
- Quality score 范围：0-100

---

## 11. Exit Codes

| Code | Meaning |
|------|---------|
| 0 | 成功（默认，即使发现 P0/P1） |
| 1 | 成功但发现 P0/P1（仅当 `--fail-on-p0p1`） |
| 2 | 系统错误（参数无效、git 不可用） |
| 3 | 部分成功（某些维度因超时/工具缺失跳过） |

---

## 12. 与现有技能的关系

```
bmad-code-review（快速扫描）          zeng-code-patrol（周期巡检）
        │                                      │
        ├── 日常 PR 审查 ──────────────────────→ 用 bmad-code-review
        ├── 代码库健康度检查 ──────────────────→ 用 zeng-code-patrol
        └── 发现架构腐化趋势 ─────────────────→ 触发 zeng-code-patrol 深度扫描
```

---

*文档版本：v1.1*
*创建日期：2026-05-27*
