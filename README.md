# Zeng Skills

[![Skills](https://img.shields.io/badge/skills-8-blue)](./)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

个人全局自定义 AI Agent Skill 集合，主要用于 Claude Code / Codex 及其他兼容 Agent Skill 协议的运行时。

本仓库以**单一 Skill 单目录**的形式组织，每个 Skill 自包含完整的 `SKILL.md` 与所需附属资源，可直接挂载到 Agent 的 skills 路径下使用。

---

## Skill 目录

> 详细使用说明请参阅 [docs/SKILL-USAGE-GUIDE.md](./docs/SKILL-USAGE-GUIDE.md)

### 设计与实施流水线

| Skill | 描述 | 适用场景 |
|-------|------|----------|
| [`zeng-design-check`](./zeng-design-check) | Pre-SSOT 文档校验（6 大维度 + 跨维度一致性，55 项检查） | 设计文档写完后、进入 SSOT 前，校验输入质量 |
| [`zeng-i2i`](./zeng-i2i) | 设计文档到实施任务转化引擎（15+ 种设计文档输入） | 设计文档校验通过后，拆分为可执行的实施任务 |
| [`zgsd-bootstrap-milestone`](./zgsd-bootstrap-milestone) | 从预设计文档包引导生成 GSD Milestone | 设计文档包完成，直接转换为 GSD 里程碑与阶段计划 |
| [`zgsd-plan-phase`](./zgsd-plan-phase) | 桥接 I2I 任务包到 GSD PLAN 格式 | I2I 产出的任务包需转换为 GSD 可执行的 PLAN |

### 文档质量

| Skill | 描述 | 适用场景 |
|-------|------|----------|
| [`zeng-doc-quality-loop`](./zeng-doc-quality-loop) | 多文档质量收敛流水线（BMAD 多角色评审团） | 对多份文档执行并行评审、冲突讨论、修复与验证的完整质量闭环 |

### 代码质量

| Skill | 描述 | 适用场景 |
|-------|------|----------|
| [`zeng-safe-code`](./zeng-safe-code) | 临时安全编码助手（6 条硬约束 + 自检清单） | 修改项目代码时，作为编码阶段的硬约束与自检流程 |
| [`zeng-code-patrol`](./zeng-code-patrol) | 代码库自动化巡检（8 大维度） | 定期扫描代码库，发现风格漂移、架构腐化、安全漏洞等问题 |
| [`zeng-code-review-deep`](./zeng-code-review-deep) | 多智能体深度代码审查（Commit/PR/模块并行专项审查） | 关键 PR 的深度审查，生成结构化修复任务与报告 |

---

## 快速开始

### 1. 克隆仓库

```bash
git clone git@github.com:zengle22/zeng-skills.git
```

### 2. 挂载 Skill

#### Claude Code

将 Skill 目录链接或复制到 Claude Code 的全局 skills 路径：

```bash
# 创建 skills 目录（如不存在）
mkdir -p ~/.claude/skills

# 方式 A：符号链接（推荐，自动同步更新）
ln -s /path/to/zeng-skills/* ~/.claude/skills/

# 方式 B：直接复制
cp -r /path/to/zeng-skills/* ~/.claude/skills/
```

或在项目级 `.claude/settings.json` 中指定：

```json
{
  "skills": {
    "paths": ["/path/to/zeng-skills"]
  }
}
```

#### Codex (OpenAI)

将 Skill 目录挂载到 Codex 的 skills 搜索路径：

```bash
# 查看当前 skills 路径
codex skills path

# 将本仓库添加到 skills 路径
codex skills add /path/to/zeng-skills
```

或在配置文件中指定：

```yaml
# ~/.codex/config.yaml
skills:
  paths:
    - /path/to/zeng-skills
```

### 3. 调用 Skill

在对话中通过斜杠命令或工具调用：

```
/zeng-safe-code
```

或

```
Skill(skill="zeng-doc-quality-loop", arguments="doc1.md doc2.md")
```

---

## Skill 规范

本仓库遵循以下结构约定：

```
<skill-name>/
├── SKILL.md          # 核心定义文件（必须）
├── references/       # 附属参考文档（可选）
├── scripts/          # 辅助脚本（可选）
└── ...               # 其他资源
```

每个 `SKILL.md` 头部均包含标准 YAML Frontmatter：

```yaml
---
name: <skill-name>
description: <一句话描述>
author: <作者>
date: <日期>
version: <版本>
---
```

---

## 贡献

1. 新增 Skill 请创建独立目录，并确保 `SKILL.md` 自包含完整使用说明。
2. 修改现有 Skill 时，同步更新对应目录下的 `SKILL.md` 元数据中的 `version` 与 `date`。
3. 提交前运行本地检查，确保目录命名与 `SKILL.md` 中的 `name` 字段一致。

---

## License

MIT © zengle22
