# Research-Suite Skill 安装确认

**安装时间**: 2026-11-16  
**版本**: 1.1.0  
**状态**: ✓ 已全局安装

## 安装信息

| 项 | 值 |
|---|---|
| Skill 名称 | `research-suite` |
| 显示名称 | "科研与写作" |
| 调用方式 | `$research-suite` |
| 安装目录 | `C:\Users\USERNAME\.codex\skills\research-suite` |
| 入口文件 | `SKILL.md` (v1.0.0) → 对应实现 v1.1.0 |
| 发现机制 | 自动 (agents/openai.yaml 配置) |
| 隐式调用 | 支持 |

## 包含内容

- **核心入口**: SKILL.md (任务驱动的模块路由)
- **11个内部模块**: idea、literature、reading、writing、introduction、figures、style、review、response、citations、digest
- **参考资料**: core.md (证据标准)、workflow-contracts.md (模块衔接与权限)、resources.md (工具索引)
- **执行资源**: library/ (脚本、模板、参考资料)
- **许可记录**: NOTICE.md、licenses/

## 前置检查结果

- ✓ SKILL.md 配置完整
- ✓ agents/openai.yaml 界面配置
- ✓ 11 个模块文件
- ✓ 核心参考文档
- ✓ 修改记录 (v1.1.0 补充)

## v1.1.0 补充内容

### 五项关键改进

1. **模块衔接**: workflow-contracts.md 表格明确8种任务的自动衔接规则
   - 精读后写作无需再问
   - 单独精读不自动启动其他模块

2. **Zotero 边界**: 明确读写权限
   - 精读与日报默认只读
   - 建议标签/笔记只输出提议
   - 明确授权后才执行写回

3. **旧资源整合**: library/README.md + interfaces.json
   - 明确脚本职责与完成边界
   - 7个CLI接口验证通过
   - 避免旧工具名歧义

4. **修改验证范围**: workflow-contracts.md §修改后怎样验证
   - 措辞改动 → 结构与链接检查
   - 模块权限改动 → 典型场景走读
   - 脚本逻辑改动 → 接口与流程验证

5. **语言处理**: 交流/成品/精读语言分别解析
   - 诊断可用用户对话语言
   - 成品按指定或任务语言
   - 精读语言贯穿所有工件

### 验证状态

| 范围 | 状态 | 结果 |
|---|---|---|
| 结构 & 链接 | ✓ | 118个本地链接通过 |
| CLI接口 | ✓ | 7个接口检查通过 |
| 场景走读 | ✓ | 10类场景已覆盖 |
| 真实库写回 | ⏳ | 未对真实库试写 |
| 完整精读流程 | ⏳ | 未实际执行 |

已知限制清晰记录于 modifications/CHANGES.md

## 后续使用

### 立即可用

```
请使用 $research-suite 完成当前科研或写作任务
```

### 修改规则

修改 research-suite 后，在 `modifications/CHANGES.md` 中记录：
- 改动的文件
- 改动内容与影响
- 实际执行的验证范围
- 已知未验证的部分

验证策略参考 `references/workflow-contracts.md` 的表：修改后怎样验证

### 旧入口

以下14个旧入口已整合进 research-suite，已从自动发现中退出：
- nature-polishing
- 论文润色
- anti-defensive-writing
- nature-proposal-writer (researchwrite)
- nature-reviewer
- nature-response
- peer-review
- scientific-writing
- literature-review
- nature-academic-search
- nature-ref-verifier
- deeppapernote
- nature-literature-pipeline
- zotero-literature-review

完整备份: `E:\projects\codex 项目\闲聊\doc\科研写作技能体系\2026年11月16日-统一科研写作体系-v1\backups\original-skills\`

## 许可

- CC-BY-NC-SA-4.0 (本体系改编与新内容)
- 集成来源: Supervisor-Skills、GitHub 防御性写作仓库、Humanizer系列
- 详见 NOTICE.md 与 licenses/

## 联系方式

遇到问题或需要扩展功能时，参考：
- 核心规则: `references/core.md`
- 约定边界: `references/workflow-contracts.md`
- 资源索引: `references/resources.md`
- 修改记录: `../modifications/CHANGES.md`
