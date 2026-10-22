# 海拉专利技能

这是给 Cursor 用的海拉中国区专利技能。把它装进项目或个人技能目录后，在对话里说明要审交底、做风险排查、审权利要求、写审查意见或写交底，根技能会按流程往下做。Agent 出草稿，专员复核并签字。

技能包含七条工作流：

| 说法 | 工作流 | 结果 |
|---|---|---|
| 审交底、交底自查 | W1 | 审核意见、查新与区别定位、可专利性对照表 |
| FTO、风险排查、附件一、附件二 | W2 | 风险排查初稿 |
| 审权利要求、审保护范围 | W3 | 权利要求审核意见 |
| 审查意见、OA | W4 | 答复要点 |
| 写交底、改交底初稿 | W5 | 中文交底草稿和确认版 |
| 写申请文件、申请底稿 | W6 | 给代理机构的申请底稿 |
| 按审核意见改代理人稿 | W7 | 修改建议稿和修改对照表 |

交底只出中文，不生成英文交底书。中文交底模板和蓝色填写说明已放在 `templates/idf-zh.docx`，蓝色字是填写说明，不是正文。

## 环境

- Python 3.9 或更高版本
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Cursor
- 能访问已购买的智慧芽 MCP（只在检索、取专利全文时需要；交底清晰性审核不依赖它）

脚本需要的第三方包写在对应 `.py` 文件顶部。第一次执行 `uv run` 时由 uv 安装，不需要事先 `pip install`。

## 安装

在仓库根目录执行。

### 1. 准备 uv

本机安装一次 uv 即可。技能商店或 `install.py` 不会代替这一步。

### 2. 让 Cursor 加载技能

用 Cursor 打开本仓库时，技能已经在 `.cursor/skills/hella-patent`，新开一个对话即可。`code/hella-patent` 是同一份技能的安装包，用来装到别的项目或别的电脑。

装到另一个项目：

```bash
python code/hella-patent/install.py --project /path/to/your-project
```

装到当前用户，使所有项目都能用：

```bash
python code/hella-patent/install.py --user
```

目标目录里已有同名技能时，加上 `--force` 覆盖。

如果某个项目里还没有 `.cursor/skills/hella-patent`，在该项目根目录执行：

```bash
python /path/to/patent/code/hella-patent/install.py
```

这会把技能复制到该项目的 `.cursor/skills/hella-patent`。复制时不带 `__pycache__`。安装包本身不会被改掉。

在本仓库里改技能时，改 `code/hella-patent`，再在仓库根目录执行 `python code/hella-patent/install.py --force`。这样 Cursor 加载的 `.cursor/skills/hella-patent` 会和安装包保持一致。

### 3. 检查安装

```bash
python code/hella-patent/tests/validate_skill.py
uv run code/hella-patent/tests/test_skill.py
```

`SKILL_VALIDATE: ok=1` 表示技能结构完整。测试通过后，在 Cursor 里新开对话，提一句“审一下这份交底”，应走 W1，而不是泛泛讨论。

## 在 Cursor 里使用

1. 用 Cursor 打开装有该技能的项目。
2. 把交底、产品资料或代理人稿放进对话，或先放到案件的 `input/` 目录。
3. 直接说要做的事，例如：
   - “审一下这份交底，先做清晰性审核。”
   - “对这份交底做可专利性初筛。”
   - “根据这份设计说明写交底。”
   - “审一下代理人这一稿的权利要求。”
4. 遇到确认点时，技能会停下来说明在等谁确认什么。检索开始前必须确认检索式。未签字的稿件都带“草稿”。

一句话里同时要求“审”和“改”时，先出审核意见，再确认是否进入改写。

真实未公开交底、客户图纸和联合开发资料，只在公司批准的模型部署上处理。发往智慧芽的内容默认只有关键词、分类号和公开号。

## 命令行

在项目根目录建案：

```bash
python code/hella-patent/shared/case/init_case.py \
  --workflow idf_review \
  --title "执行器控制方案交底审核"
```

`workflow` 可以是 `idf_review`、`fto`、`claim_scope`、`office_action`、`idf_drafting`、`application_drafting`、`draft_revision`。

只跑 W1 的清晰性检查：

```bash
uv run code/hella-patent/idf-review/run_clarity.py \
  input/交底书.docx \
  --case-dir cases/IDF-2026-0001
```

退出码 `1` 表示有必须修改的问题，审核意见仍会生成。退出码 `2` 表示缺少输入文件。

案件目录默认是当前目录下的 `cases/`。其中可能有未公开技术，不要提交到 Git。本仓库已忽略 `cases/`。

## 智慧芽 MCP

检索、法律状态、权利要求和说明书原文通过 Cursor 里配置的智慧芽 MCP 获取。密钥只放在 Cursor 的 MCP 配置或密钥库，不要写进仓库、提示词或案件文件。

工具用途见 `shared/patsnap/MCP.md`。脚本不保存密钥，只处理已经落盘的返回。MCP 尚未配置时，仍可做交底清晰性审核；需要检索的步骤会停住，并写明尚未检索。

## 目前的边界

- 不生成英文交底书。
- 申请底稿和代理人稿改写可以在内部出草稿。与代理所约定底稿用法之前，不把稿件发给代理机构。
- 附件一、附件二模板尚未放进 `templates/`。FTO 正式报告要等模板到位后再套版。
- 历史交底不是运行 W1 的输入。有专员定稿之后，才用来验收漏报和误报。

## 目录

```text
code/hella-patent/
  SKILL.md                 根技能，负责选择工作流
  idf-review/              W1
  fto/                     W2
  claim-scope/             W3
  office-action/           W4
  idf-drafting/            W5
  application-drafting/    W6
  draft-revision/          W7
  shared/                  解析、检索门禁、对照表、撰写门禁
  rules/                   审核规则
  schemas/                 案件和中间结果格式
  templates/idf-zh.docx    中文交底模板
  tests/                   结构检查和单元测试
  install.py               安装到其他项目或用户目录
```

第三方代码的许可和改动边界见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
