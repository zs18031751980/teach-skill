# 示例来源维护

本文件供仓库维护时使用，不属于运行时参考，不在教学回答中附加维护报告。实际讲解的核实规则只维护在 `SKILL.md` 的“核实关键事实”中。

## 如何更新

收到用户环境、复现错误、官方行为变更或准备修改相关示例时，定位下面对应条目。稳定的数学关系复算条件和推导；实现或产品相关的行为查匹配版本的官方资料，涉及实际执行结果时再在对应环境运行。不要以链接仍能打开作为结论已得到验证的依据。

只修改受影响的例子、限定及来源，随后生成平台入口。记录核对日期、资料版本或适用语境、核对方式和剩余限制；若实际运行，补命令、运行环境与结果。没有运行就记录“文档核对”，不用“验证通过”掩盖证据差别。跨版本结论需要分别有依据，不因检索到新版本而批量改写稳定知识。

新增试讲问题应与参考中的代表例子不同，保留原始请求和完整回答；对追问在首答完成后再发送，不提前泄露。判断回答是否接上具体卡点、例子是否解释关键关系、条件有无保留、范围是否合适，以及是否泄漏内部检查。不要用匹配固定标题或句式代替阅读回答。试讲记录放 `tests/trials/`，不复制进运行时。

## 来源映射

以下外部条目于 **2026-09-13** 重新打开并核对所列行为，均为文档核对，未运行相应产品。动态页面的页头版本只是本次查阅标识，不代表用户安装版本，也不声称跨版本测试。

- **数学与算法的稳定示例**：`references/math.md`、`references/algorithm.md`。以明确域、量词、边界条件及手算过程为依据；变化来自题意或假设变化，不能用产品文档替代证明。新的真实问题证据见 `trials/transfer/`。
- **字典查询复杂度**：`references/examples.md`。[Python Wiki TimeComplexity](https://wiki.python.org/moin/TimeComplexity) 的 CPython 字典表及碰撞条件。页面已标明归档，没有固定实现版本；作为已有复杂度讨论的参考，不视为今后每个 CPython 版本的保证。涉及具体实现的新行为时还需核对目标版本源码或文档；键的哈希、比较代价及平均/最坏情况必须保留。
- **容器与镜像层**：`references/examples.md`。[Docker storage drivers](https://docs.docker.com/engine/storage/drivers/) 区分经典存储驱动和 Engine 29.0 起全新安装默认的 containerd image store；当前例子只用层概念，不能直接照搬该页命令到所有安装。[Multi-platform builds](https://docs.docker.com/build/building/multi-platform/) 支持 Linux 容器与宿主内核、Desktop 虚拟机的语境区别。
- **消息投递语义**：`references/examples.md`。[SQS standard queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html) 的至少一次投递及尽力有序，仅用于标准队列，不外推为 FIFO 或所有队列产品语义。托管服务页未锁定软件版本。
- **训练与测试隔离**：`references/data-analysis.md`。[scikit-learn Common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html)，本次页头 1.9.1；核对预处理仅在训练数据拟合，以及交叉验证使用 Pipeline 防止泄漏。未据此承诺所有预处理方法或用户版本行为完全相同。
- **多对多连接**：`references/data-analysis.md`。[pandas merging guide](https://pandas.pydata.org/docs/user_guide/merging.html)，本次页头 3.0.5；核对同键多对多产生笛卡尔组合，以及连接基数验证。示例针对普通完整键；空键匹配或不同 join 类型需另查，不能外推。
- **浏览器 Fetch**：`references/web-development.md`。[MDN Using Fetch](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)；核对 HTTP 错误不单独导致拒绝、Response 状态及正文异步读取。适用于浏览器 Fetch 的所述语义，不自动推广到 Axios、服务器封装或所有旧浏览器兼容性。
- **原生表单字段**：同上。[MDN FormData](https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest_API/Using_FormData_Objects)；核对 `name` 和 `disabled` 的行为，针对 `FormData(form)`。不等同于框架自己序列化状态。
- **盒模型**：同上。[MDN box-sizing](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/box-sizing)；核对 content-box 与 border-box 范围，保留示例中普通块及无其他尺寸约束的前提。
- **执行时序**：同上。[MDN JavaScript execution model](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Execution_model)；核对浏览器任务、微任务及运行至完成。不能用该例直接断定 Node.js 的所有调度次序。
- **React 更新队列**：同上。[Queueing a Series of State Updates](https://react.dev/learn/queueing-a-series-of-state-updates)，本次页头 v19.3；核对同一事件内快照值更新与纯 updater 串联，不外推其他框架、不同事件或包含副作用的 updater。
- **数据库隔离**：`references/software-development.md`。[PostgreSQL 17 transaction isolation](https://www.postgresql.org/docs/17/transaction-iso.html)；核对 Read Committed 下普通 SELECT 的语句快照，以及 Repeatable Read 的区别。这里固定可追溯文档版本，讲用户数据库时仍匹配其产品、版本和隔离级别。

教学指南中的外链位于结论附近；本文件记录维护语境，不另存一套教学规则。只有某条的证据发生变化才更新该条核对记录。
