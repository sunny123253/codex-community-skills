# 来源、改造与许可

本体系由用户授权在本机整合。入口和模块重新组织、改写为问题驱动的学术工作流；保留的成熟脚本、专门协议和资料片段按需加载，没有将外部技能逐个安装或把多个入口简单拼接。版本：1.0.0，整合日期：2026-11-16。

2026-11-16 更新至 1.1.0：补充模块协作、Zotero 写回授权、本地资源接口、修改后的验证范围及成品/诊断语言规则。核心脚本接口未改变，继承资源的权利与许可不变；详细修改记录位于本目录同级 `modifications/CHANGES.md`。

## Supervisor 五项方法

作者：Yuyu Luo（科研方法）及 Supervisor-Skills 贡献者。仓库：[HKUSTDial/supervisor-skills](https://github.com/hkustdial/supervisor-skills)，固定提交 `4bd3fef393e5ffc891c74309a5ef6c5ad3ad12c8`。

| 来源 | 吸收内容 | 有意改造 |
|---|---|---|
| idea-evaluator | 真实近邻检索、差异轴、资源匹配和可检验性 | 改为科学问题/机理/辨识性评估；不用统一生命周期与性能否决 |
| figure-designer | 图的论证职责、面板、标注与图注 | 扩展到对象、机理、验证、条件图谱；允许必要栅格影像，保留本机绘图风格 |
| tech-paper-template | 检查问题、方法、证据和贡献关系 | 允许多对多支持，不固定挑战与模块数量 |
| intro-drafter | 背景—缺口—目标—研究思路—贡献闭环 | 不固定六段、篇幅或引用数量，适配机理发现与不同期刊 |
| deep-research | 研究问题、多视角检索、条件比较和矛盾解释 | 本地库边界清楚、多标签综合、无代理时串行、覆盖满足后停止 |

上游根许可为 CC BY-NC-SA 4.0，部分文件 frontmatter 标识与根许可不一致。本体系对上述方法作出的新改编按 CC BY-NC-SA 4.0 提供，保留署名和改编说明；原文快照及根许可已归档。完整许可见 [Supervisor 许可](licenses/supervisor-skills.txt)。

## Defensive Writing 与 Humanizer

本次在 GitHub 实际检索并阅读下列仓库的技能与许可。版本固定，快照位于本次整合文档的 `sources/`。

| 来源及固定提交 | 提炼的内容 | 未采纳的做法 |
|---|---|---|
| [Adkid-Zephyr/anti-defensive-writing-Skill](https://github.com/Adkid-Zephyr/anti-defensive-writing-Skill) `e65bd9d8bf8ed8b9af809e5aff8237d76370876d` | 用真实贡献组织叙事，实验有论证职责 | 不采纳绝对“不说输”或删除影响核心结论的负面证据 |
| [Kiterlin/anti-defensive-writing](https://github.com/Kiterlin/anti-defensive-writing) `f516147d017a3fe43ae99192cb89d8261b0c8679` | 正面陈述范围、保留必要精度、删除重复自我辩护 | 不把必要方法限制和操作条件当冗词 |
| [Worigin0314/academic-defensive-writing-auditor](https://github.com/Worigin0314/academic-defensive-writing-auditor) `89f26b8a7f8149e6458f657010d354587d42cfe9` | 先判断限定是否影响有效性，再决定删除/保留/改写 | 不把文体问题一律升级成科研致命问题 |
| [blader/humanizer](https://github.com/blader/humanizer) `b48c832f0f809c1b5658edbb838c2521b72f2413` | 空泛拔高、宣传语、伪深度、机械三段式与重复句式识别 | 不给学术论文注入虚构个性、闲聊或生活经历 |
| [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh) `f4518a8eab97b8bfebc66a89d34320a89bef6930` | 中文缺主语、套话、叠词、机械连接和“进行+动词”等检查 | 不机械替换术语、被动句或专业表达 |
| [AIScientists-Dev/academic-humanizer](https://github.com/AIScientists-Dev/academic-humanizer) `94b88b23703bed7df507acae7d6d5876209a0cdf` | 保护数字、引文、证据强度；论文与方案语气有别 | 不套用“一律禁破折号”、固定段落数或示例中不存在的数据 |

以上六仓库本次读取的 LICENSE 均包含 MIT 授权；API 对最后一项曾标 NOASSERTION，已以实际 LICENSE 文本确认，不依赖该 API 标签。对应版权与许可文本保留在 [licenses/](licenses/)。它们不会被整体重新标成无署名的原创内容。

## 本机已有资源

整合并退出并列发现的旧入口：`nature-polishing`、`论文润色`、`anti-defensive-writing`、`nature-proposal-writer`（researchwrite）、`nature-reviewer`、`nature-response`、`peer-review`、`scientific-writing`、`literature-review`、`nature-academic-search`、`nature-ref-verifier`、`deeppapernote`、`nature-literature-pipeline`、`zotero-literature-review`。

原文件均完整归档并保留 SHA-256 清单。只保留仍需使用的工具、专业参考和模板；去重了两份润色资料，未把通用写作的固定图解摘要、期刊声望筛选、主观评分门槛及缺失流程继续作为要求。

本机 Nature 系列资料原署名 Yuan1z skill；researchwrite 原署名十五（JL Lab）；其他脚本与资源保留原文件内作者、版本和授权说明。没有现存明确许可的材料按用户本机已有资源保留，不声称已取得公开再发布许可。`library/` 中原有材料的权利与许可归原作者，不因入口 frontmatter 而统一改变。若对外发布，应逐项复核这些本机资源的来源与再分发权限。

Zotero/MinerU、数值模型、绘图和文件生成工具仍按其各自约定执行，不在本次整合中重新授权或改写。
