---
name: hella-patent
description: 海拉中国区专利工作助手，负责交底审核、FTO 风险排查、权利要求审核、审查意见答复、交底撰写、申请底稿撰写和代理人稿改写。用户提到专利、交底、IDF、FTO、权利要求、代理人稿、审查意见或 OA 时使用。
compatibility: 需要本机已有 uv。带第三方库的脚本用 uv run 执行，依赖写在脚本内，不需要单独 pip install。
---

# Hella Patent

## 用途

按海拉流程编排七条专利工作流。Agent 出草稿；专员复核并签字。撰写类必须调用审核类规则自审。

## 何时用

| 用户意图 | 工作流 | 入口 |
|---|---|---|
| 审交底、IDF、交底自查 | W1 | [idf-review/SKILL.md](idf-review/SKILL.md) |
| FTO、风险排查、附件一、附件二 | W2 | [fto/SKILL.md](fto/SKILL.md) |
| 审权利要求、审代理人稿、保护范围 | W3 | [claim-scope/SKILL.md](claim-scope/SKILL.md) |
| 审查意见、OA、答复要点 | W4 | [office-action/SKILL.md](office-action/SKILL.md) |
| 写交底、改交底初稿 | W5 | [idf-drafting/SKILL.md](idf-drafting/SKILL.md) |
| 写申请文件、申请底稿 | W6 | [application-drafting/SKILL.md](application-drafting/SKILL.md) |
| 按审核意见改代理人稿 | W7 | [draft-revision/SKILL.md](draft-revision/SKILL.md) |

一句话同时要求“审”和“改”时，先审核，再询问是否进入对应改写工作流。

## 输入

1. 把用户文件原样放入 `cases/{case_id}/input/`；不得修改原件。
2. 创建案件：`python shared/case/init_case.py --workflow <workflow> --title <title>`。
3. 恢复案件时读取 `case.json`、`issues.md`、`revision_log.md`，从当前状态继续。

## 步骤

1. 路由到唯一工作流并读取其 `SKILL.md`。
2. 检查前置门禁；不满足就写 `issues.md` 并停止。
3. 使用 `schemas/` 校验所有结构化输出。
4. 需要专利数据时读取 [shared/patsnap/MCP.md](shared/patsnap/MCP.md)。MCP 原始返回先存 `work/raw/`，脚本不得持有密钥。
5. 到人工闸门时停止，明确说明“等谁确认什么”。
6. 每次重出另存时间戳版本，追加 `revision_log.md`，不覆盖旧稿。

## 护栏

优先级：海拉流程与合规 > 智慧芽 MCP 数据 > 第三方做法。

- 真实未公开案件只在公司批准的模型部署上运行。
- 发往智慧芽的默认只有关键词、分类号和公开号。不得发送交底、产品说明、代码或客户图纸原文。
- 未签字交付物必须标“草稿”。正式结论只来自专员确认列和签字版本。
- 不编造专利号、结构、参数、步骤、实验效果或对比文件。缺失内容进入 `issues.md`。
- 智慧芽技术摘要和相似度只用于排序，不作为证据；证据必须引用专利原文。
- 外文译文标“机器翻译，以原文为准”；相同/等同判断必须同时看原文。
- 不代替代理机构定稿或递交，不做未经许可的浏览器自动化、爬取或批量下载。
- 不生成英文交底书。交底只出中文。
- 带第三方库的脚本用 `uv run` 执行，不要运行 pip install。包括 `idf-review/run_clarity.py`、`shared/docparse/docx_to_md.py`、`shared/docparse/pdf_text.py`、`shared/render/md_to_docx.py`、`shared/schema/validate_json.py`、`shared/patsnap/normalize_orbit.py`、`shared/claims/audit_claims.py`。只使用标准库的脚本仍用 `python`。

## 产出物

案件目录遵循架构文档第 4、5 节。通用格式：`{case_id}_{交付物名}_{草稿|签字}_{YYYYMMDDHHmmss}.{ext}`。脚本首行输出固定机读前缀；退出码 0 成功、1 有错误项、2 缺输入。
