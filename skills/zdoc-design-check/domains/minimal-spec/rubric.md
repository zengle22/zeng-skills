# Minimal Spec 检查 Rubric (MS-1–MS-8)

此域检查 `zdoc-write` 默认输出的 Minimal Spec (`doc_type: spec` 或 `SPEC-M...` 命名)。

---

## MS-1 — 固定章节完整性

| PASS 条件 | FAIL 条件 |
|----------|----------|
| 包含 `# Goal`、`# Scope`、`# Business Rules`、`# Constraints`、`# Acceptance` 五个一级标题 | 缺少任一必含章节 |

## MS-2 — 禁止实现内容

| PASS 条件 | FAIL 条件 |
|----------|----------|
| 文档中**不含**类设计、函数设计、伪代码、数据库表设计、接口定义、任务拆解、实现步骤、技术选型细节 | 出现任一禁止项 |

## MS-3 — Goal 存在性

| PASS 条件 | FAIL 条件 |
|----------|----------|
| Goal 非空，3–10 行，清晰表达目标与边界 | Goal 为空或不足 2 行 |

## MS-4 — 不推断关键事实

| PASS 条件 | FAIL 条件 |
|----------|----------|
| Business Rules、Constraints、Acceptance 仅记录用户明确提供内容；AI 候选内容放入 `# Acceptance > Draft` 或 Review Card 并标注为假设/待确认 | AI 推断内容被写成正式事实，无标注 |

## MS-5 — Review Card 合规性

| PASS 条件 | FAIL 条件 |
|----------|----------|
| 存在 Review Card，不超过 1 页，最多 3 个决策、5 个假设、5 个风险 | 缺少 Review Card 或数量超限 |

## MS-6 — 长度合规性

| PASS 条件 | FAIL 条件 |
|----------|----------|
| 小需求 ≤ 1 页，中需求 ≤ 3 页，大需求 ≤ 5 页 | 超过限制且未建议拆分或转为详细文档 |

## MS-7 — 输出目录合规性

| PASS 条件 | FAIL 条件 |
|----------|----------|
| 在 `docs/mvp-lite/specs/` 正式批准前，spec 不自动写入其他固定目录；或用户显式指定输出目录 | 未经用户显式指定，自动写入未批准的固定目录 |

## MS-8 — 无模糊占位内容

| PASS 条件 | FAIL 条件 |
|----------|----------|
| 不含 `TODO`/`TBD`/`占位`/`待补充` 等占位符；缺失内容在 Review Card 提问，或标注 `Draft` | 出现占位符且未在 Review Card 中补充 |
