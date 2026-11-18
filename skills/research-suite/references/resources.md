# 按需资源索引

下面是内部资料与执行资源，不是可发现的平行技能。相对路径从当前文件解析。先按需查阅 [library 使用说明](../library/README.md) 和 [实际接口清单](../library/interfaces.json)。保留资料中的旧工具示例不代表当前环境已接入；任务与授权按现行模块判断，命令参数和数据保存按真实脚本/协议执行。二者冲突时先修复不兼容处，不以文字优先级跳过真实接口契约。

## 本地文献工具

首选 Zotero/MinerU 已连接工具及当前 `kb-agent` 的检索协议。需要本地 API fallback 时使用 [只读 Zotero helper](../library/zotero/scripts/zotero_review.py)。它查询个人库并直接读附件中的 Markdown，不修改库。

在本体系根目录下，用已确认的项目 Python 环境执行：

```text
library/zotero/scripts/zotero_review.py search "carbonate self-sealing" --max-results 100
library/zotero/scripts/zotero_review.py markdown ITEMKEY --headings
library/zotero/scripts/zotero_review.py markdown ITEMKEY --start-line 80 --start-column 1 --max-lines 120
```

遵循输出的 `nextResult`、`nextAbstractStart`、`--heading-start`、`--candidate-start` 及行/列游标续读。多候选先确认身份，不猜选。只搜索个人库，不声称覆盖群组库；不添加 Zotero 9.0.6 已知异常的 `qmode=everything`。脚本位置随本体系根目录解析，不依赖已归档旧路径。

## 学术检索与引文工具

普通检索按 [文献模块](../modules/literature.md) 执行；需要专项能力时读相应资源：

- [多源检索](../library/search/references/workflows/wf1-multi-source-search.md)
- [引文核验流程](../library/search/references/workflows/wf2-citation-verification.md)
- [MeSH 检索策略](../library/search/references/workflows/wf3-mesh-strategy.md)
- [引文文件转换](../library/search/references/workflows/wf4-citation-file-mgmt.md)
- [参考文献管理](../library/search/references/workflows/wf5-reference-mgmt.md)
- [严格他引审计](../library/search/references/workflows/wf6-strict-other-citation-impact-audit.md)
- [来源层级](../library/search/references/source-tiers.md)、[标识符去重](../library/search/references/dedup-engine.md)、[RIS/BibTeX 字段](../library/search/references/ris-bibtex-format.md)

实际可用的 stdlib 辅助脚本：

- [发现论文](../library/search/scripts/academic_search.py)：OpenAlex 查询；主题检索结果并不自动代表已核验全文。
- [摘要回查](../library/search/scripts/abstract_lookup.py)：按 DOI、arXiv、OpenAlex、PMID/PMCID 等回查实际公开摘要，记录来源与尝试；缺失时不补造。
- [引用格式转换](../library/search/scripts/format-converter.py)：标识符解析与 .ris/.bib/.enw/.nbib 转换；保留实际字段。

所有脚本使用当前项目确认的环境。MCP 后端源码保留在 `library/search/mcp-server/` 供原功能维护；不默认启动、配置、安装或输出其中凭据。旧资料中的预检与示例配置只在确有需要时采用，不把独立依赖环境命令当成项目环境授权。

## 论证与文稿资源

长项目可选择 [范围](../library/proposal/templates/00_scope.md)、[研究事实](../library/proposal/templates/01_research_canon.md)、[证据表](../library/proposal/templates/02_evidence_table.md)、[论证图](../library/proposal/templates/03_argument_map.md)、[章节契约](../library/proposal/templates/04_section_contracts.md)、[术语与风格](../library/proposal/templates/05_style_guide.md)。按需填写，不要求每个小任务建立全部文件。

期刊和章节细节保留在 `library/polishing/`，按文稿实际情况加载：

- 论文类型：`static/fragments/paper_type/{research,methods,hypothesis,algorithmic,review}.md`
- 章节：`static/fragments/section/{title,abstract,intro,methods,results,discussion,conclusion}.md`
- 语言：`static/fragments/language/{en,zh-to-en}.md`
- 期刊：`static/fragments/journal/{generic,nature,nat-comms}.md`
- 深层参考：[已发表文章模式](../library/polishing/references/published-article-patterns.md)、[段落功能](../library/polishing/references/section-moves.md)、[短语参考](../library/polishing/references/phrasebank-playbook.md)、[风格检查](../library/polishing/references/style-guardrails.md)、[2025 Nat Commun 用词材料](../library/polishing/references/nat-comms-2025-diction.md)。

上述引言片段只补充期刊习惯，本体系 [引言模块](../modules/introduction.md) 负责新整合的结构判断。定量用词规则是参考，不能机械禁止有证据的 demonstrate、必要限定或统计意义上的 significantly。

排版问题直接读 [LaTeX 布局](../library/polishing/references/latex-layout.md)，检查实际渲染页面与日志；不只凭源码判断。现有 [共享术语原则](../library/shared/terminology-ledger.md) 与 [论文类型](../library/shared/paper-type-taxonomy.md) 按需读取。

## 审阅与修回资源

- 指定 Nature 评估时：[来源基础](../library/review/source-basis.md)、[编辑标准](<../library/review/editorial criteria and processes.md>)、[领域判断](../library/review/domain-specific-review-gates.md)。
- 正式报告规范：[报告标准](../library/peer-review/reporting_standards.md)、[常见技术问题](../library/peer-review/common_issues.md)，只选适用学科和研究设计。
- 修回：[输入与任务分类](../library/response/references/intake-and-routing.md)、[意见分类](../library/response/references/comment-taxonomy.md)、[动作映射](../library/response/references/action-mapping.md)、[回复结构](../library/response/references/response-structure.md)、[困难情况](../library/response/references/difficult-cases.md)、[中文作者对齐](../library/response/references/chinese-author-alignment.md)。
- 格式：[LaTeX 模板说明](../library/response/references/latex-templates.md)，对应 [cover letter](../library/response/templates/cover-letter.tex)、[逐点回复](../library/response/templates/response-to-reviewers.tex)、[标红稿](../library/response/templates/revised-manuscript-redline.tex)。

## 精读执行资源

生成完整精读笔记时从 [精读协议](../library/reading/PROTOCOL.md) 开始。脚本与配置参考继续采用其相对位置；本体系只合并入口，不降低原脚本的来源、图表、双语与保存检查。

## 专门执行能力

数值求解、PHREEQC、科学绘图、CMG 图、统计、XRD、文生图、Word/PDF/PPT 与 LaTeX 使用当前已安装的相关技能或工具。调用以用户任务为依据；不因为写论文就自动求解、创建图解摘要或生成演示文稿。
