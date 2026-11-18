# Codex Community Skills

个人与社区 Codex 技能合集。2026-11-17 从本机当前安装的非官方技能整理，共 **48 个技能**；原作者、来源与已有许可证保留在各目录内。

## 内容

- `skills/`：34 个个人/社区技能，涉及科研写作、文献检索、Zotero、数值模拟、科研绘图、机器学习和日常开发。
- `superpowers/skills/`：14 个来自 [obra/superpowers](https://github.com/obra/superpowers) 的开发流程技能；许可证见 `superpowers/LICENSE`。
- `skills/_shared/`：技能引用的共享资料，不计作独立技能。
- `catalog.json`：技能名称、位置和现有许可声明。

## 安装与使用

克隆此仓库后，按需把 `skills/` 或 `superpowers/skills/` 中的单个技能目录复制到自己的 `~/.codex/skills/`。引用 `_shared` 的技能需要同时复制该目录。请先检查同名技能，避免覆盖现有版本。

`research-suite` 是科研与写作的统一入口；`kb-agent` 使用本地 Zotero/MinerU 连接器。`tavotto-figure` 需要安装并配置 Tavotto MCP；这里只保存技能文件，不包含其服务运行时。其他技能调用的工具、模型、第三方服务与项目脚本需另外安装或配置。

本仓库是技能文件快照，不包含运行环境或一键安装脚本。Python 环境、API 密钥、文献库位置、模型数据和绘图脚本路径请在使用前按本机实际配置。原机器的个人路径已在发布副本中替换为示例路径。

## 发布范围

已排除 Codex `.system`、OpenAI 官方插件、官方技能 `gh-fix-ci`、`hatch-pet`、`linear`、`pdf`、`playwright`，以及 Anthropic 官方的专有 `docx` 技能。Tavotto 是额外收录的第三方插件技能。

缓存、编译文件、重复嵌套的 `kb-agent`、本地会话记忆、密钥和运行日志不在发布范围内。此次仅检查技能结构、文件清单、路径及凭据模式，未运行全部技能或科学计算。

## 来源与许可

这是一份多来源合集，不对所有内容统一授予新的许可证。请遵循各技能已有的许可与署名；没有明确许可的材料保留原有权利状态。详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)；`research-suite` 的来源和改编记录见其 [NOTICE.md](skills/research-suite/NOTICE.md)。

## 技能目录

| 技能 | 入口 |
|---|---|
| `arxiv-database` | [skills/arxiv-database](skills/arxiv-database/SKILL.md) |
| `biorxiv-database` | [skills/biorxiv-database](skills/biorxiv-database/SKILL.md) |
| `brainstorming` | [superpowers/skills/brainstorming](superpowers/skills/brainstorming/SKILL.md) |
| `bug-hunt` | [skills/bug-hunt](skills/bug-hunt/SKILL.md) |
| `cmg-figure` | [skills/cmg-figure](skills/cmg-figure/SKILL.md) |
| `code-review` | [skills/code-review](skills/code-review/SKILL.md) |
| `dispatching-parallel-agents` | [superpowers/skills/dispatching-parallel-agents](superpowers/skills/dispatching-parallel-agents/SKILL.md) |
| `executing-plans` | [superpowers/skills/executing-plans](superpowers/skills/executing-plans/SKILL.md) |
| `file-organizer` | [skills/file-organizer](skills/file-organizer/SKILL.md) |
| `finishing-a-development-branch` | [superpowers/skills/finishing-a-development-branch](superpowers/skills/finishing-a-development-branch/SKILL.md) |
| `frontend-polish` | [skills/frontend-polish](skills/frontend-polish/SKILL.md) |
| `geniml` | [skills/geniml](skills/geniml/SKILL.md) |
| `git-pushing` | [skills/git-pushing](skills/git-pushing/SKILL.md) |
| `handoff` | [skills/handoff](skills/handoff/SKILL.md) |
| `kb-agent` | [skills/kb-agent](skills/kb-agent/SKILL.md) |
| `latex-posters` | [skills/latex-posters](skills/latex-posters/SKILL.md) |
| `markdown-mermaid-writing` | [skills/markdown-mermaid-writing](skills/markdown-mermaid-writing/SKILL.md) |
| `nature-paper-to-patent` | [skills/nature-paper-to-patent](skills/nature-paper-to-patent/SKILL.md) |
| `nature-statistics` | [skills/nature-statistics](skills/nature-statistics/SKILL.md) |
| `numerical-modeling` | [skills/numerical-modeling](skills/numerical-modeling/SKILL.md) |
| `pathml` | [skills/pathml](skills/pathml/SKILL.md) |
| `phreeqc-modeling` | [skills/phreeqc-modeling](skills/phreeqc-modeling/SKILL.md) |
| `ponytail` | [skills/ponytail](skills/ponytail/SKILL.md) |
| `pytorch-lightning` | [skills/pytorch-lightning](skills/pytorch-lightning/SKILL.md) |
| `pyzotero` | [skills/pyzotero](skills/pyzotero/SKILL.md) |
| `receiving-code-review` | [superpowers/skills/receiving-code-review](superpowers/skills/receiving-code-review/SKILL.md) |
| `release-notes` | [skills/release-notes](skills/release-notes/SKILL.md) |
| `requesting-code-review` | [superpowers/skills/requesting-code-review](superpowers/skills/requesting-code-review/SKILL.md) |
| `research-suite` | [skills/research-suite](skills/research-suite/SKILL.md) |
| `scientific-plotting` | [skills/scientific-plotting](skills/scientific-plotting/SKILL.md) |
| `scientific-slides` | [skills/scientific-slides](skills/scientific-slides/SKILL.md) |
| `scikit-learn` | [skills/scikit-learn](skills/scikit-learn/SKILL.md) |
| `solid-liquid-gas-figure-style` | [skills/solid-liquid-gas-figure-style](skills/solid-liquid-gas-figure-style/SKILL.md) |
| `subagent-driven-development` | [superpowers/skills/subagent-driven-development](superpowers/skills/subagent-driven-development/SKILL.md) |
| `systematic-debugging` | [superpowers/skills/systematic-debugging](superpowers/skills/systematic-debugging/SKILL.md) |
| `tavotto-figure` | [skills/tavotto-figure](skills/tavotto-figure/SKILL.md) |
| `test-driven-development` | [superpowers/skills/test-driven-development](superpowers/skills/test-driven-development/SKILL.md) |
| `timesfm-forecasting` | [skills/timesfm-forecasting](skills/timesfm-forecasting/SKILL.md) |
| `torch-geometric` | [skills/torch-geometric](skills/torch-geometric/SKILL.md) |
| `torchdrug` | [skills/torchdrug](skills/torchdrug/SKILL.md) |
| `transformers` | [skills/transformers](skills/transformers/SKILL.md) |
| `using-git-worktrees` | [superpowers/skills/using-git-worktrees](superpowers/skills/using-git-worktrees/SKILL.md) |
| `using-superpowers` | [superpowers/skills/using-superpowers](superpowers/skills/using-superpowers/SKILL.md) |
| `venue-templates` | [skills/venue-templates](skills/venue-templates/SKILL.md) |
| `verification-before-completion` | [superpowers/skills/verification-before-completion](superpowers/skills/verification-before-completion/SKILL.md) |
| `writing-plans` | [superpowers/skills/writing-plans](superpowers/skills/writing-plans/SKILL.md) |
| `writing-skills` | [superpowers/skills/writing-skills](superpowers/skills/writing-skills/SKILL.md) |
| `xrd-analysis` | [skills/xrd-analysis](skills/xrd-analysis/SKILL.md) |

