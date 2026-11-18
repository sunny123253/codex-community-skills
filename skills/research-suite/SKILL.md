---
name: research-suite
description: "Unified research and academic writing workflow for evaluating ideas, searching and synthesizing literature, deep-reading papers, planning arguments and figures, drafting or revising manuscripts and proposals, polishing Chinese or English prose, checking references, reviewing submissions, and responding to reviewers. Use for 科研选题、文献综述、论文精读、学术写作、论文润色、去AI味、反防御性写作、投稿预审、修回回复及文献日报. Numerical solving, data plotting, file rendering and Zotero operations use their dedicated execution tools when needed."
license: CC-BY-NC-SA-4.0
metadata:
  version: "1.1.0"
---

# 科研与写作

一个入口，按任务读取模块。先判断科学内容与证据，再组织论证，最后处理语言；只做用户当前要求的工作，不把润色变为重新开展研究。此入口替代原来并列的通用写作、Nature 润色、反防御、综述、预审和返修技能。

## 使用方式

始终先读 [证据与任务边界](references/core.md)，再从下表选择主模块。只在确有需要时补读其他模块或其深层资源，不全量加载资料库。用户指定的操作、语言、保存位置、环境和代理限制优先。

原任务需要的模块可以自动衔接；新任务和新的写入目标不随模块切换而获授权。精读结束不自动开始论文写作。交接、Zotero 写入、正文/诊断语言和修改后的验证规则见 [模块协作约定](references/workflow-contracts.md)。

| 当前请求 | 读取模块 | 应交付的结果 |
|---|---|---|
| 选题、创新性、方向比较、可行性 | [选题判断](modules/idea.md) | 有依据的差异定位、可检验性和推进建议 |
| 查论文、个人库检索、综述、研究现状 | [文献与综合](modules/literature.md) | 可追溯证据、条件比较、对研究问题的回答 |
| 单篇全文精读、Obsidian 笔记 | [论文精读](modules/reading.md) | 忠实于原文的深度理解或完成保存的笔记 |
| 论文逻辑、起草、改稿、开题和研究方案 | [论证与写作](modules/writing.md) | 科学论证链及用户要求的实际正文 |
| 写引言、重构 Introduction | [引言](modules/introduction.md) | 连贯正文或明确要求的大纲 |
| 图1、机制图、图组、图注及面板规划 | [图件论证](modules/figures.md) | 图的主张、证据、面板与工具方案；要求出图时继续执行 |
| 润色、翻译、压缩、去AI味、反防御写作 | [学术表达](modules/style.md) | 保持科学含义、自然准确的修改文本 |
| 投稿前审阅、模拟审稿、正式评审 | [审稿与预审](modules/review.md) | 有原文依据和优先级的可操作意见 |
| 审稿意见、返修邮件、逐点回复、cover letter | [修回回应](modules/response.md) | 回应策略及所需的完整回复文本 |
| DOI、参考文献、BibTeX、严格他引 | [引文核验](modules/citations.md) | 明确区分书目真实性、字段准确性和论证适切性 |
| 文献日报、定期筛选、已有日报续跑 | [文献日报](modules/digest.md) | 符合既有筛选与归档约定的实际成果 |

## 贯穿全程的判断

- 科学问题与贡献必须具体：解决什么认识缺口，凭什么证据，成立于什么条件。读到全文不等于主张已得到证明。
- 聚焦最有价值且有证据支持的发现；把关键反证、真实不确定性及复现所需信息保留下来。
- 事实、测量、计算、机制推断和研究计划分开。不能靠流畅的语言把假设写成结果。
- 文体和任务优先。学术去AI味侧重准确、自然与作者声音，不注入闲聊、虚构经历或幽默。
- 有旧稿时先判断需要语言修改还是结构重写；完成已授权的修改，并简短说明实质性含义变化。
- 不按固定段数、文献数、评分阈值或“全面领先”目标凑内容。不因一个局部指标不占优就否定整个科学问题。
- 小任务直接给用户需要的文本；复杂项目才按需记录证据表、论证图和术语表。工作记录与可提交正文分开。

## 执行资源

Zotero/MinerU 通过现有 `kb-agent`、Zotero 连接器及只读工具读取；具体顺序与保存边界见文献和精读模块。数值模拟、统计、科学绘图、文生图、Word/PDF/PPT/LaTeX 等继续使用对应专门能力，遵守项目既定环境、科学验证及输出目录规则。

专项资源按 [资源索引](references/resources.md) 读取。模块内容优先于保留资料中不适用的旧流程、工具名、固定配额与风格偏好；脚本的实际输入输出契约及用户保存配置仍须执行。

旧名称（`researchwrite`、`nature-polishing`、`论文润色`、`anti-defensive-writing`、`deep-research` 等）在本体系内按任务映射，不重新建立平行入口。来源、取舍和许可见 [来源记录](NOTICE.md)。
