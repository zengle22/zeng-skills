# Zeng Skills

[![Skills](https://img.shields.io/badge/skills-3-blue)](./)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

个人全局自定义 AI Agent Skill 集合，主要用于 [Kimi Code CLI](https://github.com/MoonshotAI/kimi-cli) 及其他兼容 Agent Skill 协议的运行时。

本仓库以**单一 Skill 单目录**的形式组织，每个 Skill 自包含完整的 `SKILL.md` 与所需附属资源，可直接挂载到 Agent 的 skills 路径下使用。

---

## Skill 目录

| Skill | 描述 | 适用场景 |
|-------|------|----------|
| [`zeng-safe-code`](./zeng-safe-code) | 临时安全编码助手 —— 修改 LEE 项目代码时的安全约束与自检清单 | 在 L3/L2 治理未完全到位前，作为编码阶段的硬约束与自检流程 |
| [`zeng-doc-quality-loop`](./zeng-doc-quality-loop) | 多文档质量收敛流水线 | 对多份文档执行 BMAD 多角色并行评审、冲突讨论、修复与验证的完整质量闭环 |
| [`zgsd-bootstrap-milestone`](./zgsd-bootstrap-milestone) | 从预设计文档包引导生成 GSD Milestone | 当设计文档包（PRD、UX、技术设计等）已完成，直接转换为可执行的 GSD 里程碑与阶段计划 |

---

## 快速开始

### 1. 克隆仓库

```bash
git clone git@github.com:zengle22/zeng-skills.git
```

### 2. 挂载 Skill

以 **Kimi CLI** 为例，将本仓库目录加入 skills 搜索路径：

```bash
# 查看当前 skills 路径
kimi skills path

# 将本仓库添加到 skills 路径（示例）
kimi skills add /path/to/zeng-skills
```

或在配置文件中指定：

```yaml
# ~/.config/kimi/config.yaml
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
