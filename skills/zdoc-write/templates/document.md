---
title: "{中文标题}"
status: draft
created: "{YYYY-MM-DD}"
updated: "{YYYY-MM-DD}"
module_id: "{M{编号}}"
layer: "{L0 战略层|L1 业务层|L2 设计层|L3 实现层}"
priority: "{P0|P1|P2}"
related_docs: []
relationships:
  depends_on: []
  implements: []
  constrains: []
  references: []
  supersedes: []
  superseded_by: []
context_policy:
  load_priority: recommended
  task_scopes: []
  max_tokens_hint: 3000
---

# {文档标题}

## 文档定位

<!-- 一句话说明本文负责回答什么问题 -->
{本文负责回答……}

## 关联文档

| 文档 | 关系 | 说明 |
|------|------|------|
| [{文档名}]({相对路径}) | {上游/下游/参考} | {说明} |

## 范围边界

### In Scope

- {本次负责的内容 1}
- {本次负责的内容 2}

### Out of Scope

- {明确不做的内容 1}
- {明确不做的内容 2}
- {明确不做的内容 3}

---

<!-- ========== 以下为类型特定章节，按文档类型填充 ========== -->

## {类型特定章节 1}

<!-- 根据文档类型插入对应章节 -->

## {类型特定章节 2}

<!-- 根据文档类型插入对应章节 -->

---

## 术语或概念

| 术语 | 定义 |
|------|------|
| {术语 1} | {定义} |

## 验收或检查点

- [ ] {检查项 1}
- [ ] {检查项 2}

## Open Questions / Assumptions

- {问题或假设 1}
- {问题或假设 2}
