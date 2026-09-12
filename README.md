# teach-skill

按问题范围讲解知识：具体疑点直接讲透，系统学习再组织完整原理、流程和应用。支持逐行代码解释、算法题及文件概括；检查在内部完成，学习输出不附带核验报告。

## 维护结构

- `SKILL.md`：唯一维护的共同规则与模式路由。
- `references/`：知识讲解、文件概括、代码解释、算法讲解及示例边界，按需读取；数学、数据分析、Web 与软件开发指南补充领域讲解重点，算法复用已有指南。
- `scripts/sync_entries.py`：从上述源文件生成平台入口，不单独维护入口里的规则。
- `tests/`：同步脚本测试与实际试讲材料；不随教学模式加载。
- `teach-skill.md`：历史入口指向主文件，不再保存另一套规则。

## 平台入口

| 入口 | 生成方式与使用范围 |
|------|--------------------|
| `.opencode/skills/zs-teach-skill/` | 生成主文件及参考副本，整个目录可作为独立 skill 包使用 |
| `.cursor/rules/zs-teach-skill.mdc` | 生成共同规则，引用仓库根目录参考；保留原有 `alwaysApply: true` 设置，具体参考仅在讲解任务命中时读取 |
| `.github/copilot-instructions.md` | 生成仓库指令并引用根目录参考；这是 Copilot 指令入口，不将它视作 Codex 原生 skill 安装目录 |

供 Codex 等支持标准 skill 目录的环境使用时，将根目录 `SKILL.md` 与 `references/` 一起作为 `zs-teach-skill` 包安装；仓库内重构不会自动更新其他位置已经安装的副本。

不要手改三个生成入口；Cursor 和 Copilot 入口需要连同根目录 `references/` 使用，不能只复制单个文件。

## 同步与验证

修改根目录主文件或参考后执行：

```sh
python3 scripts/sync_entries.py
python3 scripts/sync_entries.py --check
python3 -m unittest discover -s tests -v
```

`--check` 只读，入口缺失、被手改、参考过期或存在旧参考副本时返回非零。同步只改生成入口和 OpenCode 的生成参考目录；该参考目录中的过期 Markdown 会随源文件移除，其他目录不受影响。重复同步不重写未变化文件。

自然表达原则改编自 X-math-paper-deai，已融入主文件，无需运行论文技能。示例资料与具体边界见 `references/examples.md`。实际试讲结果位于 `tests/trials/`，仅作为维护证据，不是学习正文中的检查报告。
