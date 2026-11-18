# 内部资源使用说明

本目录保留可复用的脚本、模板和专业资料，不提供第二个 skill 入口。任务从上级 `SKILL.md` 与 `modules/` 开始；只读当前任务所需资源。

## 哪份说明负责什么

| 资源 | 作用与实际写入范围 |
|---|---|
| `polishing/`、`shared/` | 章节、期刊、语言、术语与排版参考；不授权执行脚本或修改文件 |
| `proposal/templates/` | 长项目可选的工作模板，按用户保存要求使用，不强迫小任务生成全部文件 |
| `review/`、`peer-review/`、`response/` | 专业审阅与修回参考、LaTeX 模板；保留真实意见和来源，不自动发送/提交 |
| `search/scripts/` | 公开学术检索、摘要回查、格式转换；读取外部来源，按所选命令可能写本地导出文件，不写 Zotero |
| `zotero/scripts/zotero_review.py` | Zotero 个人库 GET 查询与 ZIP/Markdown 读取，没有标签/笔记写回命令 |
| `reading/scripts/` | 精读的来源、语言、图表与保存处理；写运行产物和已授权本地/Obsidian 笔记，不写回 Zotero |
| `reading/PROTOCOL.md` | 完整精读执行与跨阶段契约；`reading/references/output-language.md` 定义双语 schema |
| `search/mcp-server/` | 维护用后端源码，不能因读取说明而默认启动、安装或改配置 |

## 接口与文档的关系

[interfaces.json](interfaces.json) 列出常用工具入口、需要保持的参数、帮助命令及写入范围。它记录现有接口，不增加新命令，也不替代运行时权限判断。执行脚本使用当前项目已经确认的环境，路径相对本目录。

模块决定是否需要执行；实际脚本的解析器、返回字段和数据契约决定如何执行。先用实际 `--help` 对照参数，不照抄已归档旧技能路径。帮助可运行只说明入口/参数可用，不能证明完整笔记或写入成功。

精读的语言要通过 `--language en` 或 `--language zh-CN` 及既有配置解析，随后绑定每个工件的 `output_language`。本次覆盖不修改永久配置。笔记保存与 Zotero 写回分开，见 [共同工作流规则](../references/workflow-contracts.md)。

`reading/scripts/run_pipeline.py` 当前只运行到证据、图表计划和 `synthesis_bundle`，不会自行完成模型写作、最终审读或 Formal Save。生成完整笔记还须按 `PROTOCOL.md` 完成这些阶段，再使用 `write_obsidian_note.py`；不能把 pipeline 正常结束当作笔记已保存。

模板内既有来源、术语或示例不是当前项目的事实；保留的旧建议与当前任务不适用时不机械执行。若模板要求的字段与脚本实际字段不同，定位并修正后验证，不跳过真实 lint、来源/图表或覆盖检查。

## 维护与验证

资源移动或参数变化后更新接口清单、调用文档与受影响测试。权限、语言或模块衔接改变后执行相应代表场景，脚本逻辑和保存契约改变后补隔离流程或端到端验证。规则见 [修改后的验证范围](../references/workflow-contracts.md#修改后怎样验证)。

对应修改记录保存在本 skill 同级的 `modifications/CHANGES.md`。修改说明与检查记录不会被作为另一个技能加载。来源与许可仍见上级 `NOTICE.md`。
