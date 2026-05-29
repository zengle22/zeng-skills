# ADR-058：多智能体深度代码审查技能（Deep Code Review Skill）基线

> **SSOT ID**: ADR-058
> **Title**: 建立多 Agent 并行、多维度覆盖、带修复能力的深度代码审查技能，支持单次 Commit/PR 与模块级审查，覆盖代码一致性、规范、逻辑、数据结构、并发、安全、UX、性能、契约、AI 代码风险、需求一致性及测试质量
> **Status**: Draft
> **Version**: v1.0
> **Effective Date**: TBD
> **Scope**: 代码审查治理 / AI 辅助代码质量 / Skill-First 开发流程 / 多 Agent 评审编排
> **Owner**: 架构 / 研发流程 / QA 治理
> **Governance Kind**: NEW
> **Audience**: AI 实施代理、Code Review Skill、开发者、Tech Lead
> **Depends On**: ADR-047 (双链测试架构), ADR-050 (SSOT 语义治理总纲), ADR-055 (Bug 流转闭环), ADR-056 (LL v2 架构), ADR-057 (SSOT 文件管理规范)
> **Supersedes**: 无
>
> 状态：Draft
> 日期：2026-05-21
> 相关 ADR：ADR-047, ADR-050, ADR-055, ADR-056, ADR-057

---

## 1. 背景

### 1.1 One-Sentence Summary

> **现有代码审查依赖单一 Agent 或人工进行浅层扫描，无法系统性地从一致性、规范、逻辑、安全、性能、契约、AI 生成风险、需求对齐、测试质量等十余个维度进行深度审查；且审查与修复脱节，发现的问题缺乏结构化修复路径，导致"发现问题但无人修复、修复后无人验证"的断裂。**

### 1.2 现有能力与缺口

当前项目存在两类代码审查能力：

1. **`bmad-code-review`**：对抗式三层评审（Blind Hunter / Edge Case Hunter / Acceptance Auditor），适合快速扫描，但维度单一、无修复能力、无结构化产物。
2. **人工 PR Review**：依赖开发者经验，覆盖度不可控，对 AI 生成代码的特殊风险（mock 数据残留、TODO 未实现、平行实现等）缺乏系统性检查清单。

`zdoc-quality-loop` 已证明**多角色并行评审 + 独立审计 + 独立报告**的方法论在文档场景有效（ADR-049/050 治理框架下），但尚未迁移到代码审查场景。

### 1.3 核心洞察

代码审查与文档审查存在本质差异，不能直接复用 `zdoc-quality-loop`：

| 差异维度 | 文档评审 | 代码评审 |
|---------|---------|---------|
| 输入 | Markdown 文本 | 代码变更集（diff / 多文件快照 / AST） |
| 审查粒度 | 章节、段落 | 函数、模块、文件、调用链、类型边界 |
| 跨文件依赖 | 弱（引用链接） | 强（导入、调用、继承、接口实现） |
| 修复方式 | Fixer 直接修改文档 | 产出修复任务清单 + 可选自动补丁 |
| AI 特殊风险 | 低（人类撰写为主） | 高（AI 生成代码有特定模式化缺陷） |
| 语言特异性 | 无 | 强（Python/TS/Go 各自有独特风险模式） |

因此，需要一套**专为代码审查设计**的多 Agent 深度评审技能。

### 1.4 相关 ADR 关系

| ADR | 关系 | 说明 |
|-----|------|------|
| ADR-047 | 依赖 | 双链测试架构提供测试覆盖与测试代码审查的基线 |
| ADR-050 | 依赖 | SSOT 语义治理定义审查产物的持久化规范 |
| ADR-055 | 衔接 | Bug 流转闭环为审查发现的 P0 问题提供下游修复追踪 |
| ADR-056 | 衔接 | LL v2 的 impl-verify 可在验收阶段复用本 Skill 的审查产物 |
| ADR-057 | 参考 | SSOT 文件管理规范定义审查产物的文件组织标准 |

---

## 2. 问题

### 2.1 单一视角无法覆盖多维风险

一次代码变更可能同时引入：
- **逻辑错误**（边界条件遗漏）
- **安全漏洞**（用户输入未校验）
- **性能退化**（N+1 查询）
- **契约漂移**（后端修改字段但前端调用未更新）
- **AI 生成残留**（TODO 未实现、mock 数据硬编码）

单一 Agent 无法同时在所有维度保持专家级敏感度。

### 2.2 AI 生成代码的特殊风险未被系统化识别

AI 编码助手（Copilot、Cursor、Kimi 等）生成的代码存在特定模式化缺陷：

- **实现未集成**：生成了独立函数但未被既有代码路径调用（orphaned code）
- **平行重复实现**：AI 未察觉已有工具函数，重新实现一套功能等价但签名不同的代码
- **Mock 数据渗透**：开发阶段的 mock 数据、假配置、硬编码凭证被意外提交
- **TODO/FIXME 残留**：AI 用 TODO 占位未实现逻辑，开发者未补全即提交
- **过度工程化**：为简单场景引入不必要的抽象层、设计模式或依赖
- **错误处理缺失**：AI 生成 Happy Path 代码，忽略异常分支和错误返回码
- **调试代码残留**：`console.log`、`print`、`debugger`、临时文件操作未清理
- **类型断言滥用**：用 `any` / `interface{}` / `unsafe` 绕过类型系统
- **资源泄露**：文件句柄、数据库连接、goroutine、event listener 未关闭
- **不一致的错误处理风格**：同一模块中混用异常、返回码、Result 类型

现有审查流程没有专门针对上述 AI 代码风险的系统化检查清单。

### 2.3 审查与修复脱节

当前流程：

```
code-review (发现问题)
    ↓
[报告输出到聊天窗口或注释]
    ↓
[开发者手动阅读、理解、修复]
    ↓
[无人验证修复是否准确]
```

问题：
1. 审查产物非结构化，难以追踪
2. 无修复任务清单，开发者容易遗漏
3. 修复后无二次验证，可能引入新问题

### 2.4 语言特异性风险被忽视

Python、TypeScript、Go 各自有独特的高频风险模式：

- **Python**：可变默认参数、GIL 误解、循环导入、`None` 返回值未处理、异步上下文管理器误用
- **TypeScript**：`as` 类型断言滥用、`any` 逃逸、Promise 未 await、枚举与常量对象混用、JSX key 缺失
- **Go**：Goroutine 泄露、Channel 阻塞、`nil` interface 与 `nil` pointer 差异、`defer` 在循环中的误用、Error 未 wrapping

通用审查 Agent 难以在三个语言栈上同时保持专家级敏感度。

### 2.5 测试代码本身缺乏审查

测试代码的质量直接影响测试可信度：
- 测试用例与需求 AC 不对齐（测了不需要测的，漏了必须测的）
- 测试覆盖度虚高但主流程未覆盖
- 测试代码本身有 bug（错误断言、flaky setup、状态泄露）
- 测试未独立（测试间顺序依赖）

现有流程中测试代码往往不被审查，或仅由通用规范 Agent 轻扫。

---

## 3. 决策

### 3.1 总体决策

引入 **`zcode-review-deep`** 技能（Deep Code Review Skill），核心设计：

```text
多 Agent 并行专项审查 → 去重合并 → 冲突仲裁 → 修复任务生成 → 合成报告
```

**执行模型**：采用**协作式执行架构**，纯 SKILL.md 实现 + JSON Schema 契约验证。

| 组件 | 职责 |
|------|------|
| **外层 AI Agent** | 完整流程编排：参数解析、角色选择、并行审查、合并、报告生成 |
| **agents/*.md** | Agent 角色定义（渐进式披露，按需加载） |
| **schemas/*.json** | 输出产物的 JSON Schema 契约 |
| **validate.py** | 输出产物的契约验证（可选） |

关键原则：
1. **专项专审**：每个维度由独立 Agent 负责，确保专家级深度
2. **必选+可选**：4 个必选维度常驻，9 个可选维度智能选角
3. **修复内建**：审查产物直接生成结构化修复任务，支持自动补丁
4. **语言专家**：Python / TypeScript / Go 各配备语言级审查 Agent
5. **冲突仲裁**：Agent 间分歧由 Moderator 自动仲裁，必要时升级人工
6. **落盘追溯**：每个 Agent 动作立即写文件，支持中断恢复与独立审计
7. **契约验证**：validate.py 强制校验输出产物符合 JSON Schema

### 3.2 审查维度矩阵

#### 3.2.1 必选维度（Core Dimensions）— 任何代码变更必须覆盖

| 维度 ID | 维度名称 | 审查重点 | 对应 Agent |
|---|---|---|---|
| **C01** | **代码一致性** (Consistency) | 命名规范、项目约定、架构分层一致性、API 风格统一、重复代码（DRY）、跨文件约定对齐 | `consistency-hunter` |
| **C02** | **代码规范** (Standards) | Lint/Format、类型注解、注释质量、文档字符串、Imports 组织、版权头、行长度、复杂度 | `standards-guardian` |
| **C03** | **功能逻辑** (Logic) | 业务逻辑正确性、边界条件、空值处理、异常路径、状态机转换、算法正确性 | `logic-verifier` |
| **C04** | **数据结构** (Data Structure) | 模型设计合理性、类型安全、序列化/反序列化、DB Schema 对齐、DTO/Entity 一致性、不可变约束 | `data-architect` |

#### 3.2.2 可选维度（Specialist Dimensions）— 智能选角，按需激活

| 维度 ID | 维度名称 | 审查重点 | 对应 Agent | 触发条件 |
|---|---|---|---|---|
| **C05** | **并发安全** (Concurrency) | 竞态条件、死锁、线程安全、锁粒度、异步/协程模式、原子性、goroutine 泄露、Channel 阻塞 | `concurrency-expert` | 变更涉及多线程、异步、锁、channel、goroutine、async/await |
| **C06** | **安全性** (Security) | 注入攻击、XSS/CSRF、权限绕过、敏感信息硬编码、密码学误用、CORS、文件上传、Secrets 泄露、路径遍历 | `security-sentinel` | 变更涉及用户输入、认证授权、网络请求、文件操作、配置管理 |
| **C07** | **UX 体验** (UX) | 前端交互一致性、a11y、响应式、错误提示友好度、加载状态、焦点管理、表单校验反馈 | `ux-inspector` | 变更涉及前端组件、UI 库、CSS、交互事件 |
| **C08** | **性能** (Performance) | 时间/空间复杂度、N+1 查询、内存泄漏、大对象拷贝、不必要重渲染、缓存策略、算法效率 | `performance-hunter` | 变更涉及循环、查询、大数据处理、渲染逻辑、网络请求 |
| **C09** | **可维护性** (Maintainability) | SOLID 原则、圈复杂度、函数长度、耦合度、重复代码、测试覆盖度、代码异味、注释与代码不同步 | `maintainability-analyst` | 变更涉及核心业务模块、公共库、工具函数（或人工指定） |
| **C10** | **可观测性** (Observability) | 日志级别、上下文完整性、错误追踪 ID、Metrics 埋点、Tracing、告警阈值、日志泄露敏感信息 | `observability-engineer` | 变更涉及服务入口、关键链路、错误处理、调度器 |
| **C11** | **契约一致性** (Contract Consistency) | 前后端接口调用与 API 文档对齐、DTO 与 Schema 一致、字段增减同步、类型映射正确、版本兼容性、Breaking Change 标注 | `contract-guardian` | 变更涉及 API 定义、DTO、Client/Server 通信、OpenAPI/Protobuf 契约 |
| **C12** | **AI 代码风险** (AI Code Risk) | 实现未集成、平行重复实现、Mock 数据渗透、TODO/FIXME 残留、过度工程化、调试代码残留、错误处理缺失、资源泄露、类型断言滥用、不一致错误风格 | `ai-code-inspector` | 当 commit message / PR 描述包含 AI 生成标记，或代码中存在 AI 典型模式时强制触发；否则作为抽样审查 |
| **C13** | **需求一致性** (Requirement Consistency) | 代码实现与 FRZ/FEAT/AC 对齐、范围漂移检测、未授权功能实现、AC 映射到代码路径、验收条件可追踪 | `requirement-aligner` | 当有 FRZ Package 或 FEAT 文档可对照时触发；核心模块强制触发 |
| **C14** | **测试质量** (Test Quality) | 测试用例与需求 AC 对齐、测试覆盖度（行/分支/主流程）、测试代码本身 bug、测试独立性、Flaky 风险、Mock 合理性、断言质量 | `test-auditor` | 变更涉及测试文件，或核心模块变更时（检查对应测试是否同步更新） |

#### 3.2.3 语言专家维度（Language Expert）— 与必选/可选叠加

| 维度 ID | 维度名称 | 审查重点 | 对应 Agent | 触发条件 |
|---|---|---|---|---|
| **L01** | **Python 专家** (Python Expert) | 可变默认参数、GIL 误解、循环导入、`None` 处理、异步上下文管理器、`dataclass`/`pydantic` 误用、装饰器顺序、元类滥用 | `python-expert` | 变更包含 `.py` 文件 |
| **L02** | **TypeScript 专家** (TS Expert) | `as` 断言滥用、`any` 逃逸、Promise 未 await、枚举与常量对象混用、JSX key 缺失、类型收窄不足、模块循环依赖、`strict` 模式违规 | `ts-expert` | 变更包含 `.ts/.tsx` 文件 |
| **L03** | **Go 专家** (Go Expert) | Goroutine 泄露、Channel 阻塞、nil interface vs nil pointer、`defer` 循环误用、Error wrapping、`context` 传递、Slice 越界、Map 并发写入 | `go-expert` | 变更包含 `.go` 文件 |

> **选角规则**：语言专家 Agent 与业务维度 Agent **并行运行**，但输出独立。语言专家产出归入 `language-review.json`，供 Moderator 合并时作为 severity 调整依据（同一问题被语言专家和业务维度同时发现时，severity 上调一级，最高 P0）。

### 3.3 Agent 角色总览

#### 3.3.1 审查 Agent（Reviewer Agents）

| Agent ID | 类型 | 主责维度 | 副责维度 | 模型要求 |
|---|---|---|---|---|
| `consistency-hunter` | 必选 | C01 | C02, C09 | 通用代码模型 |
| `standards-guardian` | 必选 | C02 | C01, C04 | 通用代码模型 |
| `logic-verifier` | 必选 | C03 | C04, C06 | 通用代码模型 |
| `data-architect` | 必选 | C04 | C03, C08 | 通用代码模型 |
| `concurrency-expert` | 可选 | C05 | C03, C08 | 通用代码模型 |
| `security-sentinel` | 可选 | C06 | C03, C11 | 安全专项模型优先 |
| `ux-inspector` | 可选 | C07 | C11, C09 | 通用代码模型 |
| `performance-hunter` | 可选 | C08 | C04, C05 | 通用代码模型 |
| `maintainability-analyst` | 可选 | C09 | C01, C02 | 通用代码模型 |
| `observability-engineer` | 可选 | C10 | C03, C09 | 通用代码模型 |
| `contract-guardian` | 可选 | C11 | C04, C07 | 通用代码模型 |
| `ai-code-inspector` | 可选 | C12 | C01, C03, C09 | 通用代码模型 |
| `requirement-aligner` | 可选 | C13 | C03, C11 | 通用代码模型 |
| `test-auditor` | 可选 | C14 | C03, C13 | 通用代码模型 |
| `python-expert` | 语言 | L01 | C03, C04, C05 | Python 专项 |
| `ts-expert` | 语言 | L02 | C03, C04, C07 | TS 专项 |
| `go-expert` | 语言 | L03 | C03, C04, C05 | Go 专项 |

#### 3.3.2 仲裁与汇总 Agent（Orchestrator Agents）

| Agent ID | 职责 | 模型要求 |
|---|---|---|
| `selector` | 阶段 0 智能选角：分析变更内容，决定激活哪些可选维度 + 语言专家 | 轻量模型 |
| `moderator` | 阶段 1B：合并各 Agent 输出，去重，检测冲突 | 强推理模型 |
| `conflict-arbiter` | 阶段 1C：对冲突进行讨论仲裁（最多 2 轮），决定是否升级人工 | 强推理模型 |
| `fix-planner` | 阶段 2：将共识问题转化为结构化修复任务，生成修复方案（可选自动补丁） | 代码生成模型 |
| `audit-agent` | 阶段 3：独立审计全过程一致性（无共享上下文，仅读磁盘） | 通用模型 |
| `synthesizer` | 阶段 4：独立合成最终报告（无共享上下文，仅读磁盘） | 通用模型 |

### 3.4 执行流程（流水线）

本技能采用**纯 SKILL.md 实现**，所有流程逻辑由外层 AI Agent（Claude Code / Kimi CLI）执行。

```
阶段 0: 初始化 & 智能选角
    │
    ├── 输入: diff / PR / 模块文件集 + FRZ Package(可选) + 既有代码上下文
    ├── 分析: 文件类型、语言、变更范围、触发关键词
    ├── 输出: role-panel.json (选定 Agent 列表 + Moderator 指定)
    │
    ▼
阶段 1: Review Pass（并行审查）
    │
    ├── Step A: 各专项 Agent 并行审查（全部同时 spawn，run_in_background=true）
    │      ├── 必选 Agent × 4
    │      ├── 可选 Agent × 1-5（由 selector_rules.yaml 决定）
    │      ├── 语言专家 Agent × 1-3（由文件后缀决定）
    │      └── 输出: {agent_id}-review.json
    │
    ├── Step B: Moderator 合并与冲突检测
    │      ├── 读取所有 review.json
    │      ├── 按 (file + line_range + dimension) 合并去重
    │      ├── 检测冲突（severity 分歧 ≥ 2 级，或"非问题" vs P0/P1）
    │      └── 输出: consolidated-review.json + review-conflicts.json
    │
    ├── Step C: 冲突讨论与仲裁（最多 2 轮）
    │      ├── 冲突 Agent 各自 spawn 回应
    │      ├── Conflict-Arbiter 综合判断
    │      ├── 规则: 相邻级别取高 | N-1 方一致则解决 | 2 轮未决则升级人工
    │      └── 输出: discussion/{id}-r{n}.json + review-human-decisions.json(如有)
    │
    └── Step D: 生成共识清单
           ├── 应用冲突仲裁结果更新 severity
           ├── 移除人工决策"忽略"的问题
           ├── 持续性问题保留原 ID，新增问题分配新 ID
           └── 输出: review-consensus.json
                  统计: P0={n} P1={n} P2={n} P3={n}
    │
    ▼
阶段 2: Fix Pass（修复规划）
    │
    ├── 读取 review-consensus.json
    ├── 按 severity 分组:
    │      P0/P1 → 必须修复（生成 fix-task）
    │      P2   → 按策略修复（low-risk: 仅修复明显无副作用）
    │      P3   → 记录不处理
    ├── 生成修复方案:
    │      ├── 每个 P0/P1 问题生成修复任务（fix-task 条目）
    │      └── 对复杂问题生成修复 PLAN
    └── 输出: fix-tasks.json
    │
    ▼
阶段 3: 报告合成
    │
    ├── 生成: 按文件汇总、按维度汇总、按 severity 汇总、修复任务清单
    └── 输出: final-report.md
    │
    ▼
阶段 4: 契约验证（可选）
    │
    ├── 运行 validate.py 验证所有产物符合 JSON Schema
    └── 输出: 验证结果（OK / FAIL + 详细错误）
```

### 3.5 修复能力设计（Fix Pass）

本 Skill 与文档质量循环的关键差异：**不直接修改代码**，而是产出**结构化修复任务 + 可选自动补丁**。

#### 3.5.1 修复任务 Schema（`fix-tasks.json`）

```json
{
  "task_id": "{batch_id}-fix-{seq:03d}",
  "issue_id": "{对应 consensus issue id}",
  "severity": "P0 | P1 | P2",
  "status": "PENDING | PATCH_GENERATED | MANUAL_REQUIRED | DEFERRED",
  "file": "src/services/order.ts",
  "line_range": [42, 58],
  "dimension": "C03-功能逻辑",
  "problem": "当 order.total 为 0 时，折扣计算函数会除以零",
  "fix_strategy": "MINIMAL_CHANGE | REFACTOR | ADD_TEST | UPDATE_CONTRACT | REMOVE_CODE",
  "auto_patch": {
    "available": true,
    "patch_ref": "auto-patches/{task_id}.diff",
    "confidence": "high | medium | low",
    "affected_tests": ["tests/unit/order.test.ts"],
    "risk_assessment": "无副作用 | 需回归验证 | 可能引入行为变更"
  },
  "manual_guidance": "若 auto_patch 不可用或 confidence < high，提供详细修复步骤",
  "verification_command": "pytest tests/unit/order/test_discount.py -v",
  "estimated_effort": "XS(<5min) | S(5-15min) | M(15-60min) | L(>60min)"
}
```

#### 3.5.2 修复策略分类

| 策略 | 说明 | 适用场景 |
|------|------|---------|
| `MINIMAL_CHANGE` | 最小范围修改（加 guard、改判断条件） | P0 边界条件、空值处理 |
| `REFACTOR` | 结构调整（提取函数、重命名、简化复杂度） | P1 可维护性问题 |
| `ADD_TEST` | 补充测试用例 | P1 覆盖缺失 |
| `UPDATE_CONTRACT` | 更新 API 文档、DTO、类型定义 | P1 契约漂移 |
| `REMOVE_CODE` | 删除死代码、重复实现、调试代码 | P2 代码清理 |

#### 3.5.3 自动补丁规则

- **仅对 `MINIMAL_CHANGE` 和 `REMOVE_CODE` 策略生成自动补丁**
- **Confidence = high** 且无副作用评估时，补丁写入 `auto-patch.diff`
- **Confidence < high** 或涉及跨文件修改时，标记 `MANUAL_REQUIRED`，提供详细修复指导
- 自动补丁必须附带 `affected_tests`，用于快速验证
- 自动补丁不直接应用，由开发者在 `zcode-review-deep --apply-patches` 时选择性应用

### 3.6 冲突仲裁机制

#### 3.6.1 冲突触发条件

| 条件 | 行为 |
|------|------|
| 同一问题，不同 Agent severity 相差 ≥ 2 级 | 必须讨论 |
| 同一问题，某 Agent 给 P0/P1，另一 Agent 明确标注"非问题" | 必须讨论 |
| 相邻级别分歧（P0 vs P1，P1 vs P2，P2 vs P3） | Moderator 直接取高级别，无需讨论 |
| 语言专家与业务维度对同一问题severity一致 | 上调一级（最高 P0） |

#### 3.6.2 自动仲裁 vs 人工升级

```
Conflict-Arbiter 判断:
  ├── 至少 N-1 方接受同一级别（含妥协）→ 自动解决，记录 agreed_severity
  ├── 多方让步但级别不一致 → 若第 1 轮 → 进入第 2 轮
  ├── 第 2 轮仍不一致 → 升级人工（AskUserQuestion）
  ├── 所有角色维持原立场 → 若第 2 轮 → 升级人工
  └── 相邻级别剩余分歧 → 自动解决，取高级别
```

**人工升级时机**：
- 冲突讨论 2 轮未达成一致
- 涉及 P0 判定且冲突方 ≥ 2 个
- 语言专家与业务维度对根本性问题（如是否存在 race condition）存在分歧

### 3.7 输入与触发粒度

#### 3.7.1 支持的输入模式

| 模式 | 输入 | 适用场景 | 产物 |
|------|------|---------|------|
| **Commit 模式** | `git diff HEAD~1` | 单次提交审查 | 轻量报告 |
| **PR 模式** | `git diff base...head` + PR 描述 | Pull Request 审查 | 完整报告 + fix-tasks |
| **Module 模式** | 指定目录/文件快照 | 模块级健康检查 | 完整报告 + fix-tasks |
| **FRZ 对照模式** | 代码 + FRZ Package（FEAT/TECH/API） | 需求一致性深度审查 | 完整报告 + 需求漂移清单 |

#### 3.7.2 触发命令设计

```bash
# 在 Claude Code 中通过 Skill 调用（推荐）
/zcode-review-deep --mode commit --ref HEAD~1
/zcode-review-deep --mode pr --base main --head feature/x
/zcode-review-deep --mode module --path src/services/order/

# 验证输出产物（可选）
cd zcode-review-deep
pip install jsonschema
python validate.py .cr-deep/CR-20260527-001
```

### 3.8 产物规范

所有产物写入 `{output_dir}/{batch_id}/`，符合 `schemas/*.json` 定义的 JSON Schema 契约：

```
{output_dir}/
└── {batch_id}/
    ├── batch-state.json                    # 批次状态（schema: batch-state.schema.json）
    ├── role-panel.json                     # 选角结果（schema: role-panel.schema.json）
    │
    ├── reviews/
    │   ├── consistency-hunter-review.json  # 各 Agent 审查结果（schema: problem.schema.json）
    │   ├── logic-verifier-review.json
    │   ├── security-expert-review.json     # (如激活)
    │   ├── python-expert-review.json       # (如激活)
    │   └── ...
    │
    ├── consolidated-review.json            # 合并后问题清单（schema: problem.schema.json）
    ├── review-conflicts.json               # 冲突记录（schema: conflict.schema.json）
    ├── review-consensus.json               # 共识问题清单（schema: problem.schema.json）
    │
    ├── fix-tasks.json                      # 修复任务清单（schema: fix-task.schema.json）
    │
    └── final-report.md                     # 最终审查报告
```

**契约验证**：使用 `validate.py` 验证所有产物符合 JSON Schema：

```bash
python validate.py .cr-deep/CR-20260527-001
# 输出: OK    role-panel.json
#        OK    batch-state.json
#        OK    reviews/consistency-hunter-review.json
#        ...
#        Checked: 8 files, Errors: 0
```

---

## 4. 术语定义

| 术语 | 定义 |
|------|------|
| **Deep Review** | 相对于快速扫描（bmad-code-review）的深度多维度评审，覆盖 10+ 质量维度 |
| **必选维度** | 任何代码变更都必须审查的 4 个基础维度（C01-C04） |
| **可选维度** | 根据变更内容智能激活的 9 个专项维度（C05-C14） |
| **语言专家** | 针对 Python/TS/Go 的专项审查 Agent（L01-L03），与业务维度叠加 |
| **AI 代码风险** | AI 生成代码特有的模式化缺陷类别（C12），区别于通用代码质量问题 |
| **Fix Task** | 结构化修复任务条目，含修复策略、自动补丁、验证命令、预估工作量 |
| **Auto Patch** | Fix-Planner 生成的代码 diff，confidence=high 时提供，不自动应用 |
| **FRZ 对照模式** | 将代码实现与 FRZ Package 中的 FEAT/TECH/API 进行对齐审查的模式 |
| **Shadow Fix** | 开发者绕过审查流程直接修复代码的行为（ADR-055 §2.10 已定义，本 Skill 复用检测机制） |

---

## 5. 审查维度详细定义（Rubric）

### 5.1 必选维度 Rubric

#### C01 — 代码一致性 (Consistency)

| # | 检查项 | P0 条件 | P1 条件 | P2 条件 |
|---|--------|---------|---------|---------|
| C01-1 | 命名规范一致性 | 严重违反（如类型名用小写、常量名用 camelCase 且导致误解） | 局部不一致（同一场景混用 snake_case 和 camelCase） | 轻微风格偏差 |
| C01-2 | 架构分层一致性 | 业务逻辑泄露到不该出现的层（如 SQL 直接写在 Handler） | 分层边界模糊，但可通过重构快速修复 | 注释或文档未说明分层职责 |
| C01-3 | 重复代码（DRY） | 完全相同的业务逻辑复制粘贴 ≥ 3 处 | 相同逻辑 ≥ 2 处，或近似逻辑可提取 | 仅出现 1 次但明显可参数化 |
| C01-4 | API 风格统一 | 同一模块中 RESTful 与 RPC 风格混用导致调用方困惑 | 参数命名风格不一致 | 响应包装格式轻微不一致 |
| C01-5 | 跨文件约定对齐 | 接口定义与实现签名不匹配（编译可通过但语义不一致） | 类型别名与原始类型混用导致困惑 | 导入路径组织不统一 |

#### C02 — 代码规范 (Standards)

| # | 检查项 | P0 条件 | P1 条件 | P2 条件 |
|---|--------|---------|---------|---------|
| C02-1 | 类型安全 | 关键路径缺少类型注解导致运行时错误 | 公共函数返回值未标注类型 | 内部辅助函数类型推断足够 |
| C02-2 | 注释质量 | 函数行为与注释完全矛盾 | 复杂算法无注释 | 注释有拼写错误或过期 |
| C02-3 | Imports 组织 | 循环导入导致运行时错误 | 未使用的导入残留 | 导入顺序未按项目约定分组 |
| C02-4 | 复杂度 | 圈复杂度 > 20 且缺少测试 | 圈复杂度 > 15 | 圈复杂度 > 10 但逻辑清晰 |
| C02-5 | 文档字符串 | 公共 API 完全缺少文档 | 文档未描述异常抛出 | 文档参数名与实际不符 |

#### C03 — 功能逻辑 (Logic)

| # | 检查项 | P0 条件 | P1 条件 | P2 条件 |
|---|--------|---------|---------|---------|
| C03-1 | 边界条件 | 除零、数组越界、空指针可触发崩溃 | 边界条件处理不完整（如仅处理正数） | 边界条件有处理但缺少测试 |
| C03-2 | 空值处理 | 用户输入未校验直接解引用 | 内部函数未防御性编程 | nil/None 处理与项目约定不一致 |
| C03-3 | 异常路径 | 关键异常路径完全未处理（如网络失败=崩溃） | 异常处理但错误信息无意义 | 异常日志级别不当 |
| C03-4 | 状态机转换 | 状态转换存在不可达或死循环状态 | 缺少状态转换验证 | 状态枚举未覆盖全部场景 |
| C03-5 | 算法正确性 | 排序/查找/聚合逻辑结果错误 | 算法效率明显低于最优解 | 算法正确但实现可读性差 |

#### C04 — 数据结构 (Data Structure)

| # | 检查项 | P0 条件 | P1 条件 | P2 条件 |
|---|--------|---------|---------|---------|
| C04-1 | 模型一致性 | DB Schema、DTO、Entity 三者字段类型严重不匹配 | 字段命名不一致（如 user_id vs userId） | 可选字段默认值不一致 |
| C04-2 | 序列化安全 | 敏感字段未排除在序列化外 | 枚举值在序列化中未校验 | 时间格式未统一 |
| C04-3 | 类型安全 | 泛型/接口使用错误导致编译期无法捕获的类型漏洞 | 使用 `any` / `interface{}` 绕过类型检查 | 类型转换冗余 |
| C04-4 | 不可变约束 | 关键配置对象/常量被意外修改 | 函数参数在内部被修改（副作用） | 建议使用 readonly/frozen 但未使用 |

### 5.2 可选维度 Rubric（节选关键项）

#### C11 — 契约一致性 (Contract Consistency)

| # | 检查项 | P0 条件 | P1 条件 | P2 条件 |
|---|--------|---------|---------|---------|
| C11-1 | API 文档对齐 | 代码实现与 OpenAPI/Protobuf 定义字段名/类型/必填性冲突 | 文档未标注新字段或废弃字段 | 示例值与实际不符 |
| C11-2 | DTO 同步 | 后端修改响应结构但前端 DTO 未更新（或反之） | 字段增减未标注版本兼容性 | 类型映射存在精度损失风险 |
| C11-3 | Breaking Change | 未标注兼容性破坏且未提供迁移路径 | 破坏性变更仅在内部文档提及 | 变更影响范围评估不完整 |

#### C12 — AI 代码风险 (AI Code Risk)

| # | 检查项 | P0 条件 | P1 条件 | P2 条件 |
|---|--------|---------|---------|---------|
| C12-1 | 实现未集成 | 新增函数/模块完全未被既有代码路径调用（orphaned） | 有调用但只在测试中使用 | 导出但未在预期位置使用 |
| C12-2 | 平行重复实现 | 与既有工具函数功能 80%+ 重叠但签名不同 | 部分重叠，可提取公共逻辑 | 语义近似但使用场景不同 |
| C12-3 | Mock 数据渗透 | Mock 配置/假数据/硬编码凭证出现在非测试代码 | Mock 逻辑与真实逻辑未隔离 | 测试配置泄露到生产配置 |
| C12-4 | TODO/FIXME 残留 | P0 功能路径上存在未实现的 TODO | 非关键路径 TODO 无截止日期 | 已实现的 TODO 未清理 |
| C12-5 | 过度工程化 | 为简单 CRUD 引入不必要的抽象工厂/插件架构 | 过早优化（如为 <100 条数据加缓存层） | 依赖数量明显超出功能复杂度 |
| C12-6 | 错误处理缺失 | AI 生成的函数签名返回 error 但所有调用点用 `_` 忽略 | 关键路径错误被静默吞掉 | 日志记录但无后续处理 |
| C12-7 | 调试代码残留 | `console.log`、`print`、`debugger`、临时文件写入在生产代码中 | 测试用 `time.sleep` 未清理 | 注释掉的代码块 > 20 行 |
| C12-8 | 资源泄露 | 文件/连接/goroutine/event listener 明确未关闭 | 依赖垃圾回收的资源未显式管理 | 资源关闭在错误路径上被跳过 |
| C12-9 | 类型断言滥用 | 用 `as` / `.(T)` / `unsafe` 绕过类型系统且无校验 | 类型断言失败无处理分支 | 本可用泛型/接口但用了断言 |

#### C13 — 需求一致性 (Requirement Consistency)

| # | 检查项 | P0 条件 | P1 条件 | P2 条件 |
|---|--------|---------|---------|---------|
| C13-1 | AC 映射覆盖 | 代码未实现 FEAT 中声明的关键 AC | 实现方式与 AC 描述有偏差 | 实现完整但缺少 AC 追溯注释 |
| C13-2 | 范围漂移 | 实现了 FRZ 明确声明为 Out of Scope 的功能 | 实现范围超出当前 FEAT 但合理 | 实现细节与 TECH 决策不一致 |
| C13-3 | 状态机对齐 | 代码状态转换与 FEAT.state_changes 定义冲突 | 未覆盖 FEAT 声明的所有状态 | 状态命名与文档不一致 |

#### C14 — 测试质量 (Test Quality)

| # | 检查项 | P0 条件 | P1 条件 | P2 条件 |
|---|--------|---------|---------|---------|
| C14-1 | AC 对齐 | 测试用例与需求 AC 明显不对齐（测了不存在的需求） | 关键 AC 无对应测试 | 测试描述与 AC 措辞不一致 |
| C14-2 | 主流程覆盖 | Happy Path 完全未被测试覆盖 | 分支路径覆盖 < 50% | 边界条件测试缺失 |
| C14-3 | 测试代码 bug | 断言逻辑错误（如 assertTrue(false)） | Setup 有副作用导致测试间依赖 | Mock 返回值与真实行为不符 |
| C14-4 | 测试独立性 | 测试间存在顺序依赖或共享可变状态 | 测试未清理全局状态 | 测试数据未隔离 |
| C14-5 | Flaky 风险 | 测试依赖外部服务/时间/随机数且无 stub | 异步测试无适当等待机制 | 测试在慢环境可能超时 |

---

## 6. Agent 详细规范

### 6.1 审查 Agent Prompt 结构

每个专项 Agent 接收统一结构的 Prompt：

```
你是代码评审团成员，角色：{role_name}。

【你的评审视角】
{role_perspectives[role_id]}

【你主要负责（须深入评审）】
{primary_dimensions 对应的 Rubric 条目}

【你也须覆盖（基本评审）】
其余 Rubric 维度（至少扫描，发现问题则记录）

【待审查代码变更】
---
{diff_content}
---

【完整文件上下文】（用于跨引用和类型检查）
{relevant_files_content}

【FRZ 对照文档】（FRZ 模式下提供）
{frz_package_content}

【固定 Rubric】
{LOCKED_RUBRIC}

【严重级别】
P0：阻塞合并（崩溃、数据丢失、安全漏洞、需求未实现）
P1：高风险（边界遗漏、契约漂移、主路径逻辑错误）
P2：中风险（规范偏离、可维护性问题、性能隐患）
P3：低风险（风格、注释、轻微重构建议）

【规则】
1. evidence 必须是代码精确原文（含文件名和行号）
2. 不捏造问题
3. 风格类问题不得标注 P0/P1
4. ID 格式：{batch_id}-{agent_id}-{severity}-{seq:03d}
5. 对 AI 生成代码风险（C12）须额外敏感
6. 只输出 JSON 数组

输出：JSON 数组，每条符合 Problem Schema
```

### 6.2 语言专家 Agent 特殊规则

语言专家 Agent 除审查 L01-L03 专项外，还需：
1. 扫描业务维度 Agent 可能遗漏的语言级陷阱
2. 对同一问题，若语言专家和业务维度同时发现，在 `found_by` 中标注两者
3. 输出独立文件 `language-review.json`，结构同 Problem Schema

---

## 7. 执行主体矩阵

本技能采用**纯 SKILL.md 实现**，所有流程逻辑由外层 AI Agent 执行。`validate.py` 仅用于可选的契约验证。

| 阶段 | 功能 / 动作 | 执行者 | 说明 |
|------|------------|--------|------|
| 阶段 0 | 参数解析与输入快照 | **外层 AI Agent** | 解析参数，生成代码快照 |
| 阶段 0 | 智能选角 | **外层 AI Agent** | 根据 `selector_rules.yaml` 分析变更内容，决定激活哪些可选 Agent |
| 阶段 1A | 并行审查 | **外层 AI Agent (各专项 Agent)** | 同时 spawn，独立审查，无共享上下文 |
| 阶段 1A | 审查产物写入 | **外层 AI Agent** | 各 Agent 返回后立即写入 `{agent_id}-review.json` |
| 阶段 1B | 合并与冲突检测 | **外层 AI Agent (Moderator)** | 读取所有 review.json，产出 consolidated + conflicts |
| 阶段 1C | 冲突讨论 | **外层 AI Agent (冲突各方 + Conflict-Arbiter)** | 每轮讨论 spawn 新 Agent 实例 |
| 阶段 1C | 人工升级 | **人类** | AskUserQuestion，2 轮未决时触发 |
| 阶段 1D | 共识清单生成 | **外层 AI Agent** | 基于仲裁结果结构化生成 consensus.json |
| 阶段 2 | 修复任务生成 | **外层 AI Agent** | 将 P0/P1 转化为 fix-tasks |
| 阶段 3 | 报告合成 | **外层 AI Agent** | 生成 final-report.md |
| 阶段 4 | 契约验证 | **validate.py** | 可选，验证产物符合 JSON Schema |

---

## 8. 与现有技能的衔接

### 8.1 与 `bmad-code-review` 的关系

```
快速扫描（bmad-code-review）          深度审查（zcode-review-deep）
        │                                      │
        ├── 日常小变更、文档修改、配置调整 ───────→ 用 bmad-code-review（轻量）
        ├── 核心模块、安全敏感、AI 生成代码 ───────→ 用 zcode-review-deep（深度）
        └── 发现高风险 ───────────────────────────→ 触发 zcode-review-deep
```

### 8.2 与 ADR-055 Bug 流转的关系

```
zcode-review-deep 发现 P0 问题
    ↓
生成 fix-tasks.json（status=PENDING）
    ↓
开发者修复后提交
    ↓
可选: 触发 ll-qa-test-run（ADR-047）验证修复
    ↓
若验证失败 → 按 ADR-055 进入 Bug 流转闭环
```

### 8.3 与 LL v2 `impl-verify` 的关系

`impl-verify`（ADR-056 §7.4）在验收阶段检查"功能是否做完"。`zcode-review-deep` 在开发阶段检查"代码质量是否达标"。两者互补：

- `zcode-review-deep` → 开发阶段的代码质量门
- `impl-verify` → 交付阶段的功能完成度验收

---

## 9. 非功能性需求（NFR）

### 9.1 性能

| 指标 | 目标 | 说明 |
|------|------|------|
| 单文件审查延迟 | < 30s | 轻量文件（<500 行）的端到端审查 |
| 多文件 PR 审查 | < 5min | 典型 PR（10 文件，+500/-200 行） |
| 模块级审查 | < 15min | 大型模块（50+ 文件） |
| Agent 并行度 | ≤ 8 个 | 同时 spawn 的 Agent 上限，避免资源耗尽 |

### 9.2 可审计性

- 每个 Agent 动作写入磁盘，不依赖内存状态
- `batch-state.json` 实时更新，支持中断恢复
- 审计 Agent 无共享上下文，确保客观性
- 全部产物纳入 git 跟踪（`.cr-deep/` 目录加入 `.gitignore` 例外或单独归档）

### 9.3 可扩展性

- 新增审查维度只需：定义 Rubric → 新增 Agent Prompt → 在 selector 规则中注册触发条件
- 新增语言专家只需：定义语言风险清单 → 新增 Agent Prompt → 按文件后缀触发
- 不修改流水线核心逻辑即可扩展

---

## 10. Consequences

### 10.1 正向影响

1. **多维风险覆盖**：从 3 个对抗视角扩展到 14 个质量维度 + 3 个语言专家，风险发现率预期提升 3-5 倍
2. **AI 代码风险可控**：专门针对 AI 生成代码的 9 类模式化缺陷建立系统检查，降低"AI 写一半、人类没检查"的漏洞
3. **审查即修复**：结构化修复任务 + 自动补丁缩短"发现问题→修复问题"的周期
4. **语言特异性**：Python/TS/Go 专家 Agent 捕获通用审查无法发现的语言级陷阱
5. **可追溯**：全程落盘，支持事后审计、质量趋势分析、开发者能力画像

### 10.2 代价

1. **执行成本**：多 Agent 并行调用 LLM，Token 消耗是单 Agent 的 3-8 倍
2. **延迟增加**：完整深度审查需要 2-5 分钟，不适合高频提交的实时反馈（需与 bmad-code-review 分流）
3. **产物管理**：每次审查产生 10-20 个文件，需要清理策略（建议保留最近 30 天）
4. **误报风险**：维度越多，各 Agent 间的重复报告和边缘误报越多，依赖 Moderator 的合并质量

### 10.3 度量指标

| 指标 | 目标 | 度量方式 |
|------|------|---------|
| P0 发现率 | > 90% | 审查发现的 P0 / 生产环境实际发生的 P0（事后复盘） |
| AI 代码风险检出率 | > 80% | C12 维度发现的问题 / 后续代码审计中确认的 AI 代码缺陷 |
| 自动补丁采纳率 | > 60% | 开发者应用的 auto-patch / 生成的 auto-patch 总数 |
| 误报率 | < 20% | 开发者标记为"非问题"的 P1-P3 / 总 P1-P3 问题 |
| 审查→修复周期 | < 4h | fix-tasks 生成到对应任务关闭的平均时间 |

---

## 11. Rejected Alternatives

### 11.1 单 Agent 多轮审查（Sequential Deep Review）

**拒绝**。单 Agent 在多轮中切换视角会导致上下文污染和"前面忘了"问题。并行专项 Agent 确保每个视角独立且完整。

### 11.2 直接修改代码（Auto-Fix 直接应用）

**拒绝**。自动修改代码风险过高，可能引入语义变更或破坏未测试路径。采用"生成补丁 + 人工确认"的中间方案，既提供修复效率又保留人工决策权。

### 11.3 所有维度常驻（不分必选/可选）

**拒绝**。14 个维度全部常驻会导致 Token 成本过高、审查延迟不可接受、无关维度产生噪音。智能选角在覆盖度和成本间取得平衡。

### 11.4 不区分语言专家（通用 Agent 审查所有语言）

**拒绝**。Python/TS/Go 的语言级陷阱（如 Go 的 nil interface、Python 的可变默认参数、TS 的 any 逃逸）需要深度语言知识，通用 Agent 的检出率 < 30%。

---

## 12. 实现演进

### 12.1 v1.0 → v1.1 简化（2026-05-27）

**背景**：v1.0 设计了完整的 Python 运行时（runtime/），但实际执行仍依赖外层 AI Agent。Python 运行时的复杂度与收益不成正比。

**改动**：
1. **删除** `runtime/` 目录（20+ Python 模块）
2. **删除** `run.py` CLI 入口
3. **删除** `evidence/`, `input/`, `output/`, `scripts/` 目录
4. **新增** `validate.py`（~100 行）用于输出契约验证
5. **保留** `agents/*.md`（17 个 Agent 定义，便于渐进式披露）
6. **保留** `schemas/*.json`（5 个 JSON Schema，用于契约验证）
7. **更新** `SKILL.md` 为纯 SKILL.md 实现

**文件数变化**：47 → 27

**架构变化**：

| 维度 | v1.0 | v1.1 |
|------|------|------|
| 执行模型 | Python + 外层 Agent 协作 | 纯外层 Agent |
| 输出校验 | 有 schema 但未使用 | validate.py 强制校验 |
| 维护成本 | 高（多文件协调） | 低（单 SKILL.md + 验证脚本） |

**决策理由**：
- Python 运行时仅负责"生成 prompt 文件"和"读取 review JSON"，这些用 SKILL.md 指令同样可以实现
- JSON Schema 校验是真正有价值的差异化能力，保留为独立脚本
- `agents/*.md` 分开写便于渐进式披露，按需加载

---

*文档版本：v1.1*
*创建日期：2026-05-21*
*更新日期：2026-05-27*
