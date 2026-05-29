---
title: "I2I Skill 改进建议：基于 ARCH-LITE-007 实施文档评审的回溯分析"
doc_id: "I2I-IMPROVE-001"
status: draft
created: "2026-05-28"
layer: "L2"
source_event: "ARCH-LITE-007 impl 文档四轮评审"
---

# I2I Skill 改进建议

> 基于 `impl-formal-app-foundation-ARCH-LITE-007` 四轮评审中发现的 15 个问题的回溯分析，提出 I2I Pipeline（zeng-i2i v1.2）在输入准入、拆解过程、交付审核三个环节的改进建议。

---

## 1. 问题溯源汇总

四轮评审共发现 15 个问题，按根因分类：

| 根因来源 | 数量 | 占比 | CRITICAL | HIGH | 说明 |
|----------|------|------|----------|------|------|
| 源文档内部不一致 | 5 | 33% | 3 | 2 | ARCH-LITE-007 或 TESTSET 自身的约束冲突、语义模糊 |
| I2I 拆解信息丢失 | 8 | 53% | 0 | 5 | 任务分解时丢失上下文、约束、依赖 |
| I2I 拆解语义偏移 | 2 | 13% | 0 | 2 | 任务描述偏离源文档原意 |

**关键发现**：所有 3 个 CRITICAL 问题均来自源文档，说明 I2I Pipeline 当前缺乏对输入源的质量校验。53% 的 HIGH 问题来自拆解过程中的信息丢失，说明任务上下文传递机制需要加强。

### 1.1 CRITICAL 问题清单（源文档）

| ID | 问题 | 源文档 | 影响 |
|----|------|--------|------|
| C1 | ESLint 约束数量：ARCH-LITE-007 §11 写 4 条，TESTSET 细化为 7 条，未同步 | ARCH-LITE-007 + TESTSET | 架构文档与测试设计矛盾，task-012 无所适从 |
| C2 | Auth 失败语义：§5.4 表格将 401 和 503 写在同一行，未区分 JWT 失效 vs 服务不可用 | ARCH-LITE-007 | task-008 无法确定 Auth 失败的 HTTP 状态码映射 |
| C3 | 分层例外矛盾：task-010 的排除项说"Health Service 直接调用基础设施无需通过 Repository"，与 §4 分层边界表的 L0 约束矛盾 | ARCH-LITE-007 + task-010 | 架构约束的例外未被源文档显式批准 |

### 1.2 HIGH 问题清单（拆解信息丢失）

| ID | 问题模式 | 涉及 task | 丢失内容 |
|----|----------|-----------|----------|
| D1 | 依赖缺失 | task-014, task-016 | task-014 缺少 task-001 依赖；task-016 缺少 task-005, task-009 依赖 |
| D2 | 约束丢失 | task-003 | AC3 未体现 Mock 优先级链；AC4 未区分 AI SDK 3.x/4.x API |
| D3 | 上下文截断 | task-008 | 未携带 §5.4 的 Auth 失败语义（401 vs 503 区分） |
| D4 | 测试范围模糊 | task-015 | 未明确排除延迟指标（PERF-04/05），与 task-016 职责重叠 |
| D5 | 配置示例不完整 | task-012 | ESLint 配置仅展示 3/7 条约束 |
| D6 | API 名称歧义 | task-003 | AC4 引用 `toDataStreamResponse()` 未区分 3.x vs 4.x |
| D7 | 排除项语义错误 | task-010 | "无需通过 Repository"未标注为分层例外 |
| D8 | 语义偏移 | task-003 AC5 | "移除旧 ai-config.ts"未强调验证后删除的安全顺序 |

---

## 2. 输入准入门槛改进建议

> **目标**：在 I2I 拆解启动前，扫描源文档的内部一致性问题，拦截 C 类（源文档不一致）问题。

### 2.1 源文档交叉一致性扫描

**当前状态**：I2I Pipeline 直接读取 ARCH + TESTSET 进行拆解，不校验两份文档之间的一致性。

**建议增加**：在拆解前执行一轮「源文档交叉扫描」，检查以下维度：

| 扫描维度 | 检查方法 | 阻断级别 |
|----------|----------|----------|
| 数量一致性 | 扫描 ARCH §11 门槛表中的数字（约束条数、接入点数等）与 TESTSET 中对应的细化数字是否匹配 | BLOCK（不一致则拒绝拆解） |
| 语义明确性 | 检查表格中同一行是否包含多个语义不同的值（如 401 和 503 写在同一行） | BLOCK（模糊则要求源文档澄清） |
| 例外显式化 | 检查"排除项"或"例外"是否在 ARCH 中有显式批准声明 | WARN（不排除但标记） |
| 路径一致性 | 检查 ARCH 和 TESTSET 中的文件路径是否一致（如 `src/handlers/` vs `src/lib/handlers/`） | BLOCK |
| 版本一致性 | 检查两份文档对同一依赖的版本号表述是否一致 | BLOCK |

**实现形式**：可作为 I2I Pipeline 的 Phase 0 step，输出 `source-consistency-report.json`，包含 `pass/fail` 和具体冲突项。

### 2.2 约束溯源图构建

**当前状态**：I2I Pipeline 将 ARCH §11 门槛直接映射为 task acceptance criteria，但不追踪门槛与 §4/§5/§8 具体约束的对应关系。

**建议增加**：在拆解前构建「约束溯源图」，记录：

```
§11 门槛 N → 对应 §X.Y 具体约束 → TESTSET 测试点编号
```

**作用**：
- 当 TESTSET 细化约束时（如 4 条 → 7 条），溯源图能自动检测 ARCH §11 是否需要同步更新
- 拆解出的 task acceptance criteria 可以自动携带溯源链，避免 D2（约束丢失）

### 2.3 术语/命名预扫描

**当前状态**：I2I Pipeline 不检查源文档中 API 名称、库名称的一致性。

**建议增加**：扫描以下模式：

| 模式 | 检查方法 | 示例 |
|------|----------|------|
| 版本相关 API 名 | 检查 API 名称是否标注了适用版本 | `toDataStreamResponse()` 应标注为 3.x 兼容 |
| 废弃 API 引用 | 检查是否引用了已废弃的 API（需维护一个废弃 API 清单） | `StreamingTextResponse` 在 4.x 中废弃 |
| 命名空间一致性 | 检查同一模块在不同位置的路径是否一致 | `src/handlers/` vs `src/lib/handlers/` |

---

## 3. 拆解过程质量改进建议

> **目标**：减少 D 类（信息丢失）和 E 类（语义偏移）问题，确保 task 上下文完整。

### 3.1 Task 上下文注入模板

**当前状态**：每个 task 的"完整上下文"部分由 I2I Pipeline 从源文档摘录，但摘录粒度不统一，容易丢失关联约束。

**建议**：为每个 task 定义强制注入的上下文字段：

```yaml
task_context:
  # 必填：该 task 涉及的所有 §11 门槛编号
  acceptance_gates: [§11 门槛 N, ...]
  
  # 必填：该 task 涉及的所有 §4/§5/§6/§7/§8 具体约束编号
  source_constraints: [§X.Y, ...]
  
  # 必填：该 task 的排除项与例外声明
  exclusions:
    - description: "..."
      exception_approved_by: "§11 门槛 N 或 §X.Y 显式批准"
  
  # 选填：与该 task 存在语义重叠的其他 task
  semantic_overlaps: [task-NNN, ...]
  
  # 选填：该 task 依赖的外部 API 版本信息
  api_versions:
    - library: "ai"
      version: "^4.1.54"
      deprecated_apis: ["StreamingTextResponse"]
      compatible_apis: ["toDataStreamResponse()", "pipeDataStreamToResponse()"]
```

### 3.2 依赖完整性校验

**当前状态**：DAG 校验检查循环和孤立节点，但不检查依赖是否完整（即 task 实际需要但未声明的依赖）。

**建议增加**：在 DAG 校验之后、交付之前，执行「依赖完整性校验」：

| 校验规则 | 检查方法 |
|----------|----------|
| 目录结构依赖 | 任何创建文件的 task 必须依赖 task-001（目录结构） |
| 配置依赖 | 任何使用 env 变量的 task 必须依赖 task-002（环境配置） |
| 基础设施依赖 | 任何使用 Drizzle 的 task 必须依赖 task-005；使用 Redis 的必须依赖 task-009 |
| 类型依赖 | 任何定义 API 类型的 task 必须依赖 task-004（错误/API 类型） |

**实现形式**：基于 task acceptance criteria 中的关键词匹配，自动生成依赖建议，输出 `dependency-suggestions.json`，由人工确认后合并。

### 3.3 Acceptance Criteria 到测试点映射校验

**当前状态**：每个 task 的 AC 与 TESTSET 测试点的对应关系由 I2I Pipeline 附带，但不校验完整性。

**建议增加**：在拆解后检查：

```
TESTSET 中的每个测试点（HP-01~07, BC-01~12, ARC-01~04, ...）
  → 是否至少被一个 task 的 AC 覆盖？
  → 是否有 task 的 AC 覆盖了 TESTSET 之外的内容？
```

**作用**：
- 检测 D4（测试范围模糊）：如果 PERF-04/05 未被任何 task 显式排除或覆盖，标记为 GAP
- 检测测试点遗漏：如果 TESTSET 中有测试点未被任何 task 的 AC 引用，标记为 ORPHAN

---

## 4. 交付前审核改进建议

> **目标**：在 I2I Pipeline 输出 task 文档后、交付给开发者前，执行一轮自动化质量门禁。

### 4.1 交付前自动审核清单

**当前状态**：I2I Pipeline 交付 task 文档后，由人工评审发现问题（本次四轮评审）。

**建议增加**：在交付前自动执行以下检查：

| 检查项 | 检查方法 | 阻断级别 |
|--------|----------|----------|
| AC-测试点覆盖率 | 每个 task 的 AC 至少引用一个 TESTSET 测试点 | BLOCK |
| 排除项一致性 | task 排除项中的"无需 XX"必须标注例外来源（§X.Y 或 §11 门槛 N） | BLOCK |
| API 版本标注 | task 中引用的 API 名称必须标注适用版本范围 | WARN |
| 依赖 DAG 完整性 | 通过 3.2 的依赖完整性校验 | BLOCK |
| 上下文字段完整性 | 通过 3.1 的强制字段检查 | BLOCK |
| 配置示例完整性 | ESLint/lint 配置示例覆盖所有声明的约束条数 | WARN |

### 4.2 语义偏移检测

**当前状态**：I2I Pipeline 的 task 描述由 LLM 生成，可能存在语义偏移（如将"验证后删除"简化为"删除"）。

**建议增加**：对每个 task 的关键 AC 执行语义对比：

```
源文档原文 ↔ task AC 表述
  → 计算语义相似度
  → 若 < 阈值，标记为 SEMANTIC_DRIFT
  → 输出差异说明
```

**示例**：

| 源文档 | task AC | 检测结果 |
|--------|---------|----------|
| "在新 Provider factory 验证 Mock 模式通过后执行移除" | "移除旧 ai-config.ts" | SEMANTIC_DRIFT: 丢失了"验证后"的安全顺序约束 |

### 4.3 交付报告

**建议**：I2I Pipeline 在交付时附带一份 `delivery-report.json`：

```json
{
  "feature_id": "ARCH-LITE-XXX",
  "generated_at": "...",
  "source_consistency": {
    "status": "PASS | FAIL",
    "issues": []
  },
  "dependency_validation": {
    "status": "PASS | WARN",
    "suggestions": []
  },
  "ac_coverage": {
    "total_test_points": 40,
    "covered_by_tasks": 38,
    "orphan_test_points": ["PERF-04", "PERF-05"],
    "coverage_rate": "95%"
  },
  "semantic_drift": {
    "total_acs": 64,
    "flagged": 2,
    "details": []
  },
  "pre_delivery_checks": {
    "passed": 8,
    "failed": 0,
    "warnings": 1
  }
}
```

---

## 5. 实施优先级

| 优先级 | 改进项 | 预估工作量 | 收益 |
|--------|--------|-----------|------|
| **P0** | 2.1 源文档交叉一致性扫描 | 2-3h | 拦截所有 C 类问题（当前 3 个 CRITICAL） |
| **P0** | 4.1 交付前自动审核清单 | 3-4h | 拦截 D1/D5/D7 等可自动化检测的问题 |
| **P1** | 3.1 Task 上下文注入模板 | 2h | 结构化上下文，减少信息丢失 |
| **P1** | 3.2 依赖完整性校验 | 2h | 自动发现缺失依赖（D1 类问题） |
| **P1** | 4.3 交付报告 | 1-2h | 可观测性，便于追踪改进效果 |
| **P2** | 2.2 约束溯源图构建 | 3-4h | 长期维护性，防止约束漂移 |
| **P2** | 3.3 AC-测试点映射校验 | 2h | 测试覆盖完整性 |
| **P2** | 4.2 语义偏移检测 | 4-5h | 减少 E 类问题，但实现复杂度高 |
| **P3** | 2.3 术语/命名预扫描 | 1-2h | 锦上添花，依赖废弃 API 清单维护 |

---

## 6. 预期效果

如果实施 P0 + P1 改进项，预期能拦截本次发现的 15 个问题中的：

| 问题类型 | 拦截数 | 拦截率 |
|----------|--------|--------|
| C 类（源文档不一致） | 3/3 | 100% — 2.1 交叉扫描直接检测 |
| D 类（信息丢失） | 6/8 | 75% — 3.1 上下文模板 + 3.2 依赖校验 + 4.1 审核清单 |
| E 类（语义偏移） | 1/2 | 50% — 4.1 排除项一致性检查可部分覆盖 |

综合拦截率：**10/15（67%）**，剩余 5 个需 P2/P3 改进项或人工评审覆盖。

---

## 附录 A：本次评审发现的完整问题列表

### CRITICAL（3 个，均来自源文档）

1. **C1** — ESLint 约束数量不一致：ARCH §11 写 4 条，TESTSET 细化为 7 条
2. **C2** — Auth 失败语义模糊：§5.4 将 401 和 503 写在同一表格行
3. **C3** — 分层例外矛盾：Health Service 直接调用基础设施与 §4 L0 约束冲突

### HIGH（7 个）

4. **D1a** — task-014 缺少 task-001 依赖
5. **D1b** — task-016 缺少 task-005, task-009 依赖
6. **D2** — task-003 AC 未体现 Mock 优先级链和 AI SDK 版本约束
7. **D3** — task-008 未携带 Auth 失败语义（401 vs 503）
8. **D4** — task-015 未明确排除延迟指标，与 task-016 职责重叠
9. **D5** — task-012 ESLint 配置仅展示 3/7 条约束
10. **D7** — task-010 排除项未标注为分层例外

### MEDIUM（3 个）

11. **D6** — task-003 AC4 引用 `toDataStreamResponse()` 未区分版本
12. **E1** — task-003 AC5 语义偏移：丢失"验证后删除"安全顺序
13. **D8** — feature-context.md AC9 数量与 §11 不一致

### LOW/INFO（2 个）

14. **N1** — task-012 ESLint 配置不完整（已在 HIGH 中覆盖）
15. **N2** — task-003 AC4 API 名称版本歧义（已在 MEDIUM 中覆盖）

---

> **下一步**：将本建议中的 P0/P1 改进项转化为 I2I Pipeline v1.3 的具体 feature spec，纳入下一轮迭代。
