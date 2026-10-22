#!/usr/bin/env python3
"""Validate a confirmed PatSnap query plan before an MCP call."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SENSITIVE_PATTERNS = (
    re.compile(r"(客户|customer)\s*[:：]?\s*[A-Za-z\u4e00-\u9fff]{2,}", re.I),
    re.compile(r"(项目|project)\s*(代号|code)?\s*[:：]?\s*[A-Za-z0-9_-]{2,}", re.I),
    re.compile(r"\b\d+(?:\.\d+)?\s*(?:mm|cm|nm|μm|um|MPa|kPa|V|A|Hz|℃)\b", re.I),
)


def inspect_plan(plan: dict) -> list[str]:
    errors: list[str] = []
    for query in plan.get("queries", []):
        qid = query.get("id", "?")
        if query.get("status") != "confirmed":
            errors.append(f"{qid}: status 必须为 confirmed")
        if int(query.get("hit_cap", 500)) > 1000:
            errors.append(f"{qid}: hit_cap 不能超过工具翻页上限 1000")
        if query.get("mode") != "semantic":
            continue
        text = (query.get("semantic_query") or "").strip()
        if not text:
            errors.append(f"{qid}: semantic 模式缺少 semantic_query")
            continue
        if len(text) > 200:
            errors.append(f"{qid}: semantic_query 超过 200 字")
        if any(pattern.search(text) for pattern in SENSITIVE_PATTERNS):
            errors.append(f"{qid}: semantic_query 疑似含客户、项目或具体参数")
        if not query.get("semantic_confirmed_by"):
            errors.append(f"{qid}: semantic_query 缺少专员确认人")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="智慧芽检索计划保密门禁")
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    if not args.plan.is_file():
        print(f"QUERY_GUARD: ok=0 missing={args.plan}")
        return 2
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    errors = inspect_plan(plan)
    print(f"QUERY_GUARD: ok={int(not errors)} errors={len(errors)}")
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
