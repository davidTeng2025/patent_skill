# PatSnap MCP 调用规范

## 工具映射

- `search_patent`：布尔/关键词/结构化检索。初筛默认 `collapse_family=true`，单页最多 100，`offset + limit <= 1000`。
- `fetch_patent`：一次取著录项、权利要求 HTML、说明书。仅在进入比对后取全文。
- `fetch_patent` + `relations`：简单同族、引用、被引、相似专利。
- `fetch_patent` + `media`：PDF/附图临时链接，当次下载，不把链接写进交付物。
- `fetch_patent_lifecycle`：法律事件、许可转让、质押、复审无效。
- `get_standard_assignee_name` / `get_corptree_hierarchy`：标准申请人和集团范围。

## 调用流程

1. 读取已确认的 `query_plan.json`，执行 `guard_query.py`。
2. Agent 调用 MCP；脚本不得直接调用、不得读取密钥。
3. 把完整返回原样存到 `work/raw/{search|patent|lifecycle}/`。
4. 在 `search_log.jsonl` 追加工具、输入摘要、命中、调用次数和 raw 路径。
5. 运行 `normalize_patsnap.py` 生成归一文件。

## 保密门禁

未公开交底和客户产品默认只用布尔/关键词检索。禁止把交底、产品说明、代码或客户图纸原文放进任何检索参数。确需语义检索时，短句不超过 200 字且不得含客户名、项目代号或具体参数，并须专员确认。
