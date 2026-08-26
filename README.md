# teach-skill — 知识详细讲解

三平台兼容 Skill，用于系统性讲解任意知识主题。

## 平台接入方式

| 平台 | 接入文件 | 作用 |
|------|---------|------|
| **Opencode** | `.opencode/skills/zs-teach-skill/SKILL.md` | Opencode 原生 skill，通过 `skill zs-teach-skill` 或在对话中匹配触发 |
| **Cursor** | `.cursor/rules/zs-teach-skill.mdc` | Cursor Rules，自动应用到所有文件（alwaysApply: true），讲解知识时自动生效 |
| **Codex** | `.github/copilot-instructions.md` | GitHub Copilot Codex 指令，讲解知识时自动遵循 |

## 7 条核心要求

1. 讲解无错误及逻辑问题
2. 详细全面，清楚易懂
3. 难懂处举例说明
4. 工具/组件做比喻
5. 包含实现原理、工作流程、如何应用
6. 每个要求到达，不遗漏任何一句
7. 高质量落实，不减轻任务量

## 使用方法

在任意支持平台中提出讲解请求即可，句式如：
- "请讲解 XXX"
- "解释一下 XXX"
- "介绍一下 XXX"
- "帮我理解 XXX"
- "什么是 XXX"

AI 将自动执行完整教学流程：声明 → 结构化讲解（含例子/比喻/原理/流程/应用） → 内部核验（不向用户输出检查表格） → 确认理解。
