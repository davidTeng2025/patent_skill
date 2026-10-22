#!/usr/bin/env python3
"""Compile confirmed query-plan element logic to PatSnap Boolean syntax."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def quote(term: str) -> str:
    return '"' + term.replace("\\", "\\\\").replace('"', '\\"') + '"'


def compile_query(query: dict, elements: dict[str, dict]) -> str:
    logic = query.get("logic") or ""
    tokens = re.findall(r"E\d+|AND|OR|NOT|\(|\)", logic, re.I)
    if not tokens:
        raise ValueError("logic 为空或无法解析")
    clauses: list[str] = []
    for token in tokens:
        upper = token.upper()
        if re.fullmatch(r"E\d+", upper):
            element = elements.get(upper)
            if not element:
                raise ValueError(f"未知检索要素 {upper}")
            terms = [
                str(item).strip()
                for item in (element.get("zh") or []) + (element.get("en") or [])
                if str(item).strip()
            ]
            if not terms:
                raise ValueError(f"{upper} 没有关键词")
            clauses.append("TAC_ALL:(" + " OR ".join(quote(item) for item in terms) + ")")
        else:
            clauses.append(upper)
    expression = " ".join(clauses)
    regions = query.get("region") or []
    if regions:
        expression += " AND AUTHORITY:(" + " OR ".join(regions) + ")"
    end = str(query.get("pub_date_before") or "").replace("-", "")
    if end:
        expression += f" AND PBD:[19000101 TO {end}]"
    return expression


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.plan.is_file():
        print(f"QUERY_COMPILE: ok=0 missing={args.plan}")
        return 2
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    elements = {item["id"].upper(): item for item in plan.get("elements", [])}
    errors: list[str] = []
    for query in plan.get("queries", []):
        if query.get("mode") != "boolean":
            continue
        try:
            query["patsnap"] = compile_query(query, elements)
        except ValueError as exc:
            errors.append(f"{query.get('id', '?')}: {exc}")
    target = args.output or args.plan
    if not errors:
        target.write_text(
            json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(f"QUERY_COMPILE: ok={int(not errors)} errors={len(errors)} path={target}")
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
