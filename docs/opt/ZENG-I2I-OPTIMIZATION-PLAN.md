---
title: "zeng-i2i Skill 优化方案 — 基于 M12 Impl Review Handoff"
status: draft
created: "2026-05-29"
layer: "L3 实现层"
priority: "P0"
related_docs:
  - "../zeng-i2i/SKILL.md"
  - "../adr/ADR-004-设计文档到实施任务拆分技能-I2I-Impl-Skill-设计规范.md"
relationships:
  depends_on:
    - "ZENG-I2I-HANDOFF.md (M12 评审发现)"
  implements: []
  constrains: []
  references: []
  supersedes: []
  superseded_by: []
context_policy:
  load_priority: required
  task_scopes: ["I2I skill 优化", "源文档校验增强", "生成逻辑修复"]
  max_tokens_hint: 5000
---

# zeng-i2i Skill 优化方案

> 基于 M12 Onboarding & Identity 实现文档评审 Handoff，针对 zeng-i2i 在源文档校验和 impl 生成中暴露的系统性问题，提出分层优化方案。

---

## 一、问题根因分析

Handoff 发现的 10 个问题可归为 3 类根因：

| 根因类别 | 涉及问题 | 核心缺陷 |
|---------|---------|---------|
| **Phase 0 校验维度不足** | S-1, S-2, S-3, S-4, S-5 | 当前交叉校验仅覆盖 ARCH↔TESTSET，未覆盖 PRD↔TECH/ARCH 的 ENUM/数值/字段对齐 |
| **Phase 3→4 数据桥接断裂** | I-1, I-2 | task-list.json → SUMMARY.md 的统计值未动态计算；ENUM 值从 TECH 直接继承而非以 PRD 为准 |
| **严重性分级粗糙** | I-3, I-4, I-5 | consistency report 对所有差异统一 WARN，未区分阻断级 vs 告警级；Data Model 概览未区分新建/复用表 |

---

## 二、优化方案

### 优化 1：Phase 0 增加 PRD↔TECH/ARCH 交叉校验维度

**对应问题**：S-1, S-3, S-4, S-5

**现状**：Phase 0.1 仅校验 ARCH ↔ TESTSET 的数量/语义/路径/版本一致性，不覆盖 PRD 与 TECH/ARCH 之间的定义对齐。

**改动点**：

#### 1.1 在 Phase 0.1 交叉一致性扫描表中新增 4 个维度

| 新增维度 | 检查方法 | 阻断级别 | 对应 Handoff |
|---------|---------|---------|-------------|
| **ENUM 值集合对齐** | 提取 PRD 中所有 ENUM 定义（含正文中描述的枚举值），与 TECH/ARCH 中的 ENUM 定义逐字段比对 | **FAIL**（阻断） | S-1, S-3 |
| **数值常量对齐** | 扫描所有源文档（含 ASCII 流程图）中的数值型描述（长度、金额、时间、档位数），以 PRD FR 定义为准 | **FAIL**（阻断） | S-2 |
| **字段存在性对齐** | 提取 PRD 中引用的所有字段名，检查是否在 TECH 数据模型中定义（或明确标记为已移除） | **WARN** | S-4 |
| **编码格式对齐** | 检查 TECH 中同一字段的标题描述与实际映射表/API 是否一致 | **WARN** | S-5 |

#### 1.2 执行顺序调整

```
原有: ARCH ↔ TESTSET 扫描 → 约束溯源 → 术语预扫描 → 路径规范化
新增: ARCH ↔ TESTSET 扫描
     → PRD ↔ TECH/ARCH ENUM/数值对齐（新增）
     → 约束溯源 → 术语预扫描 → 路径规范化
```

#### 1.3 source-consistency-report.json 新增字段

```json
{
  "prd_tech_alignment": {
    "enum_checks": [
      {
        "field": "gender",
        "prd_source": "PRD-M12 FR-M12-001 L378",
        "prd_values": ["male", "female"],
        "tech_source": "TECH-M12 §2.3.1",
        "tech_values": ["male", "female", "other"],
        "arch_source": "ARCH-M12 L136",
        "arch_values": ["male", "female", "other", "prefer_not_to_say"],
        "status": "FAIL",
        "resolution": "以 PRD 为准，TECH/ARCH 移除 extra values"
      }
    ],
    "numeric_checks": [
      {
        "concept": "邀请码长度",
        "prd_value": "8位",
        "prd_source": "PRD-M12 FR-M12-001 L378",
        "discrepancies": [
          { "doc": "BUSINESS-M12 L114", "value": "6位", "location": "ASCII 流程图" }
        ],
        "status": "FAIL"
      }
    ],
    "field_existence_checks": [
      {
        "field": "pain_impact_level",
        "prd_referenced": true,
        "prd_location": "PRD-M12 Open Questions #5 L786",
        "tech_defined": false,
        "status": "WARN",
        "resolution": "stale discussion in PRD, field removed in v3.0"
      }
    ]
  }
}
```

---

### 优化 2：ENUM 生成以 PRD 为准 + 自动校验

**对应问题**：I-2, S-1

**现状**：Phase 4 生成 Task 文档时，从 TECH/ARCH 直接复制 DDL 和 ENUM 定义，未检查与 PRD 的差异。

**改动点**：

#### 2.1 新增 Phase 4 枚举校验步骤

在 Phase 4 文档生成流程中（§4.3 之后，§4.4 之前）新增步骤：

```
Phase 4 步骤 3.5（新增）: ENUM 生成校验
─────────────────────────────────────────
1. 读取 source-consistency-report.json 中的 enum_checks
2. 对每个 FAIL 级别的 ENUM 差异：
   a. 以 PRD 定义的值集合为准生成 DDL/校验逻辑
   b. 在 Task 文档的"完整上下文 > 技术约束"中标注：
      "⚠️ 注意：TECH/ARCH 文档中包含额外值 [X]，但 PRD 未定义。
       本 Task 以 PRD 为准，仅使用 [PRD 定义的值]。
       如需扩展，请先更新 PRD。"
3. 在 delivery-report.json 中记录 ENUM 校验结果
```

#### 2.2 Task 模板新增 ENUM 溯源字段

在 `templates/task.md` 的"完整上下文 > 技术约束"部分增加 ENUM 溯源说明模板：

```markdown
### 技术约束（来自 Architecture / Tech Design）

{与本 Task 相关的技术约束}

#### 枚举值定义（以 PRD 为准）

| 字段 | PRD 定义值 | TECH/ARCH 值 | 本 Task 使用 |
|------|-----------|-------------|-------------|
| {field} | {prd_values} | {tech_values} | {prd_values} |
```

---

### 优化 3：SUMMARY.md 统计动态计算

**对应问题**：I-1

**现状**：SUMMARY.md 的总工时等统计值可能与 task-list.json 不一致（早期版本残留或硬编码）。

**改动点**：

#### 3.1 新增 Phase 4 校验步骤

在 Phase 4 产物完整性检查（§4.7）中新增：

| # | 检查项 | 规则 |
|---|--------|------|
| 15 | **SUMMARY 统计一致性** | `SUMMARY.预估总工时 == SUM(task-list.tasks[*].estimated_hours)` |
| 16 | **SUMMARY Task 数一致性** | `SUMMARY.Task总数 == COUNT(task-list.tasks)` |
| 17 | **INDEX 工时一致性** | `SUM(INDEX.task_hours) == SUMMARY.预估总工时` |

#### 3.2 生成逻辑约束

在 Phase 4 生成 SUMMARY.md 时，明确标注：

> SUMMARY.md 中的统计数字**必须**从 task-list.json 动态计算，**禁止**硬编码或从早期版本复制。

---

### 优化 4：consistency report 严重性分级

**对应问题**：I-3

**现状**：source-consistency-report.json 对所有差异统一输出 WARN，未区分阻断级 vs 告警级。

**改动点**：

#### 4.1 定义 FAIL 级差异（阻断，不进入 Phase 1）

| 差异类型 | 说明 | Handoff 示例 |
|---------|------|-------------|
| ENUM 值集合不一致 | 影响 DDL + 校验逻辑 + 前端组件 | gender ENUM, risk_level |
| API 请求/响应字段名不一致 | 影响接口契约 | — |
| Frozen Contract 字段类型不一致 | 影响序列化/反序列化 | — |
| 数值常量不一致 | 影响业务规则执行 | 邀请码长度 6 vs 8 |

#### 4.2 定义 WARN 级差异（告警，带标注继续）

| 差异类型 | 说明 |
|---------|------|
| 路径前缀约定差异 | lib/ vs src/（路径规范化已处理） |
| 文本描述措辞差异 | 同义词但含义相同 |
| 编码格式标题 vs 实际不一致 | TECH 标题描述是设计层说明，实际 API 使用简单枚举 |

#### 4.3 判定逻辑修改

```
IF 差异类型 IN [ENUM_VALUES, API_FIELD_NAME, FROZEN_CONTRACT_TYPE, NUMERIC_CONSTANT]
  → FAIL（阻断，要求源文档澄清后重跑）
ELSE IF 差异类型 IN [PATH_PREFIX, TEXT_WORDING, ENCODING_FORMAT_AMBIGUITY]
  → WARN（记录到报告，带标注继续）
```

---

### 优化 5：IMPL 主文档 Data Model 分区

**对应问题**：I-4

**现状**：IMPL 主文档的 Data Model 概览引用所有表（含 Out of Scope 的），未区分新建/复用。

**改动点**：

#### 5.1 feature-context.md 模板修改

在 `templates/feature-context.md` 的 Data Model 章节中增加分区：

```markdown
## 数据模型

### 本 Feature 新建的表

| 表名 | 说明 | 创建 Task |
|------|------|----------|
| {table_name} | {description} | task-{nnn} |

### 复用/预留的表（不在本 Feature 实施范围）

| 表名 | 说明 | 状态 |
|------|------|------|
| ~~{table_name}~~ | {description} | 已存在 / Phase 2 预留 |
```

#### 5.2 验收检查点

在 §4.7 产物完整性检查中新增：

| # | 检查项 | 规则 |
|---|--------|------|
| 18 | **Data Model 分区** | feature-context.md 中 Out of Scope 的表不出现在"新建的表"列表中 |

---

### 优化 6：已有表依赖显式声明

**对应问题**：I-5

**现状**：Task 引用 "existing table" 时未验证该表是否在当前 codebase 的 migration 文件中存在。

**改动点**：

#### 6.1 新增 Phase 3 依赖校验步骤

在 Phase 3 依赖完整性校验（§3.8）中新增规则：

| 校验规则 | 检查方法 |
|----------|----------|
| **已有表依赖验证** | 当 Task 的 AC 或实施步骤引用 "existing table" 或 "已有表" 时，Grep 检查当前 codebase 的 migration 文件中是否存在该表的 CREATE TABLE 语句 |

#### 6.2 校验结果处理

```
IF Task 引用 "existing table" AND migration 文件中不存在该表
  → FAIL
  → 建议：(a) 将该表加入当前 Feature 的 migration，或 (b) 明确标注依赖的 migration 版本号
```

#### 6.3 输出格式

在 `dependency-suggestions.json` 中新增字段：

```json
{
  "existing_table_checks": [
    {
      "task_id": "task-005",
      "table": "runner_risk_profiles",
      "referenced_as": "existing table",
      "found_in_migrations": false,
      "status": "FAIL",
      "suggestion": "该表在当前 codebase 的 migration 文件中不存在。建议：(a) 在 TASK-001 中增加 CREATE TABLE runner_risk_profiles，或 (b) 标注依赖的前置 migration 版本号"
    }
  ]
}
```

---

### 优化 7：遗留字段/讨论检测

**对应问题**：S-4

**现状**：Phase 0 不检测 PRD 中引用但 TECH 数据模型中不存在的字段名。

**改动点**：

已在优化 1 的 §1.1 中覆盖（字段存在性对齐维度）。补充执行细节：

#### 7.1 检测范围

| 检测源 | 检测目标 | 方法 |
|--------|---------|------|
| PRD 正文 + Open Questions + 附录 | TECH 数据模型中的字段定义 | Grep 字段名，交叉比对 |

#### 7.2 处理逻辑

```
IF 字段在 PRD 正文中引用 AND 在 TECH 数据模型中不存在 AND 在 PRD Open Questions 中有讨论
  → WARN: "遗留讨论字段 '{field}'，PRD 有引用但 TECH 未定义，请确认是否已移除"
IF 字段在 PRD 正文中引用 AND 在 TECH 数据模型中不存在 AND 无 Open Questions 讨论
  → FAIL: "跨文档遗漏字段 '{field}'，PRD 引用但 TECH 未定义"
```

---

## 三、改动文件清单

| 文件 | 改动类型 | 改动内容 |
|------|---------|---------|
| `zeng-i2i/SKILL.md` | **编辑** | Phase 0 新增 PRD↔TECH/ARCH 校验维度（§0.1）；Phase 3 新增已有表依赖验证（§3.8）；Phase 3→4 新增 ENUM 校验步骤（§4.3 之后）；Phase 4 新增 SUMMARY 动态计算校验（§4.7 #15-17）；Phase 5 delivery-report.json 增加 ENUM 校验字段 |
| `zeng-i2i/gate/rubric.md` | **编辑** | G5 一致性检查增加 ENUM/数值/字段存在性子维度，明确 FAIL/WARN 分级标准 |
| `zeng-i2i/templates/summary.md` | **编辑** | 新增"源文档 PRD↔TECH 对齐结果"章节；统计数字标注"从 task-list.json 动态计算" |
| `zeng-i2i/templates/task.md` | **编辑** | "技术约束"章节新增"枚举值定义（以 PRD 为准）"子表；"验收/检查点"新增 ENUM 溯源确认项 |
| `zeng-i2i/templates/feature-context.md` | **编辑** | Data Model 章节分区：新建表 vs 复用/预留表 |
| `adr/ADR-004-*.md` | **编辑** | 更新 Phase 0/3/4 规范，对齐上述改动 |

---

## 四、实施优先级

| 优先级 | 优化项 | 原因 | 预期收益 |
|--------|-------|------|---------|
| **P0** | 优化 1（Phase 0 PRD↔TECH 校验） | 根因级修复，阻断枚举/数值不一致流入 impl | 消除 S-1, S-2, S-3, S-4, S-5 |
| **P0** | 优化 2（ENUM 以 PRD 为准） | 防止 impl 继承 TECH 的额外枚举值 | 消除 I-2 |
| **P0** | 优化 4（严重性分级） | 让 FAIL 真正阻断，避免关键差异被 WARN 放过 | 消除 I-3 |
| **P1** | 优化 3（SUMMARY 动态计算） | 消除统计值不一致 | 消除 I-1 |
| **P1** | 优化 5（Data Model 分区） | 消除新建/复用表混淆 | 消除 I-4 |
| **P2** | 优化 6（已有表依赖验证） | 防止 migration 依赖缺失 | 消除 I-5 |
| **P2** | 优化 7（遗留字段检测） | 清理 PRD 中的 stale 引用 | 消除 S-4 |

---

## 五、验证方案

优化实施后，用 M12 作为回归测试用例：

| 验证项 | 方法 | 预期结果 |
|--------|------|---------|
| ENUM 交叉校验 | 运行 I2I，检查 source-consistency-report.json | gender ENUM 差异标记为 FAIL |
| 数值常量校验 | 运行 I2I，检查 numeric_checks | 邀请码长度差异标记为 FAIL |
| SUMMARY 动态计算 | 运行 I2I，检查 SUMMARY.md | 总工时 == SUM(task-list) |
| 严重性分级 | 检查 source-consistency-report.json | ENUM 差异为 FAIL，路径差异为 WARN |
| Data Model 分区 | 检查 feature-context.md | runner_devices 在"复用/预留"区 |
| 已有表依赖 | 检查 dependency-suggestions.json | runner_risk_profiles 标记为 FAIL |

---

## 六、与源文档维护流程的联动

以下问题需要源文档维护者同步修复（非 skill 改动）：

| # | 建议 | 负责方 | 状态 |
|---|------|--------|------|
| 1 | TECH/ARCH 的 ENUM 定义引用 PRD 作为 source of truth，不自行扩展 | 文档维护者 | M12 已修复 |
| 2 | PRD Open Questions 中已决策/已移除的条目标注状态并清理 | 产品负责人 | M12 已修复 |
| 3 | BUSINESS 文档 ASCII 流程图中的数值与 PRD FR 对齐 | 文档维护者 | M12 已修复 |

> skill 优化的目标是：即使源文档存在不一致，I2I 也能**检测并阻断**，而非静默继承错误。源文档维护是理想状态，skill 校验是安全网。
