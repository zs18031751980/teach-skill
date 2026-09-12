# teach-skill

按问题范围讲解知识：具体疑点直接讲透，系统学习再组织完整原理、流程和应用。支持逐行代码解释、算法题及文件概括；检查在内部完成，学习输出不附带核验报告。

## 维护结构

- `SKILL.md`：唯一维护的共同规则与模式路由。
- `references/`：知识讲解、文件概括、代码解释、算法讲解及示例边界，按需读取；数学、数据分析、Web 与软件开发指南补充领域讲解重点，算法复用已有指南。五个领域共 46 个子主题各自提供卡点、具体演示、边界及换问法后的调整，示例按用户材料适配，不作为固定答案模板。
- `scripts/sync_entries.py`：从上述源文件生成平台入口，不单独维护入口里的规则。
- `scripts/sync_runtime.py`：从同一源文件同步已安装的 Codex / OpenCode 包，默认预览，显式写入时备份并核对内容。
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

## 同步已安装的运行时

```sh
python3 scripts/sync_runtime.py --target both
python3 scripts/sync_runtime.py --target both --apply
python3 scripts/sync_runtime.py --target both --check
```

第一条只预览文件差异，不创建目录或备份；第二条先备份所有将被覆盖或移除的原文件，再写入并逐文件比较；第三条只读，内容或管理记录不同返回 1，源文件、路径或其他错误返回 2。`--target` 可选 `codex`、`opencode` 或 `both`；`--apply` 和 `--check` 不能同时使用。运行要求 Python 3.9+，只依赖标准库。

Codex 目标为 `${CODEX_HOME:-$HOME/.codex}/skills/zs-teach-skill`，OpenCode 目标为 `${XDG_CONFIG_HOME:-$HOME/.config}/opencode/skills/zs-teach-skill`。默认值对应此前使用的安装位置；自定义环境变量会改变目标，以预览中显示的绝对路径为准。脚本从根 `SKILL.md` 与 `references/` 构建包，OpenCode 的入口格式复用生成器，因此不会安装过期的仓库内副本。

运行时的 `.teach-skill-sync.json` 记录本脚本管理的文件及摘要。首次同步只接管当前源包中的同名文件；以后源中删除的参考，只有仍与上次同步内容相同才移除。已被手改的过期参考会报错，需先处理；无管理记录的其他文件、`agents/openai.yaml` 和本地笔记保留。首次接管前遗留但当前源中不存在的文件不会自动清理。源与目标不能重叠，不通过符号链接读写。

备份位于系统临时目录的 `teach-runtime-backup-*`，实际位置在写入前打印；原文件按 `codex/`、`opencode/` 保存，`restore.json` 记录目标和新建文件。需要恢复时按记录把备份复制回原位置，并仅移除该记录列出的本次新建文件。重要备份应移到长期保存位置，临时目录可能被系统清理。每个文件采用原子替换，但多个文件或两平台不是一个事务；中途写入失败会返回非零并保留备份，不声称整包自动回滚。重复同步不重写一致文件、不新增备份。文件同步不代表客户端已经热加载新规则。

## 讲解与来源维护

背景适配和连续追问的规则见 `references/learner-adaptation.md`；实际试讲应使用未在指南中出现的问题，并按反馈继续下一轮。来源与版本维护依据集中在 [tests/source-maintenance.md](tests/source-maintenance.md)，试讲原文和评阅放在 `tests/trials/`，都不复制进运行时包。
