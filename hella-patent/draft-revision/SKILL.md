---
name: hella-draft-revision
description: 按专员确认的审核意见改写代理人稿，输出修订模式、干净版和修改对照表。用户要求改代理人稿或按审核意见改稿时使用。
disable-model-invocation: true
---

# hella-draft-revision

## 用途

执行 W7：按专员勾选的审核意见修改代理人稿。

## 何时用

用户要求按 W3 意见改稿、改代理人稿、生成修订模式或修改对照表。

## 输入

代理人稿 docx、原交底、可选 W3 案件或 `findings.json`。没有审核意见时先运行 W3。

## 步骤

1. 把 must/should 意见转换成 `revision_plan.json` 候选项。
2. 等待专员逐项勾选并记录 `revision_scope_confirmed`。
3. 只执行 `selected: true` 且有 `basis_src` 的条目。
4. 联动调整编号、引用和“所述”基础。
5. 重跑 W3 检查；引入新问题则回退该条并写 issues。
6. 输出修订模式、干净版和修改对照表。

## 护栏

不得新增交底或原说明书中没有的技术事实。修改建议稿由代理人定稿；不兼容修订模式时交付干净版加对照表。

## 产出物

`revision_plan.json`、修订模式 docx、干净版 docx、修改对照表 xlsx、未执行问题清单。
