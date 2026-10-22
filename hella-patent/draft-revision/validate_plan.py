#!/usr/bin/env python3
"""Validate the human-approved scope before W7 modifies a draft."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def check(plan: dict) -> list[str]:
    errors: list[str] = []
    selected = [item for item in plan.get("items", []) if item.get("selected")]
    if not selected:
        errors.append("没有专员勾选的修订条目")
    for item in selected:
        if not str(item.get("basis_src") or "").strip():
            errors.append(f"{item.get('id', '?')}: 缺少 basis_src")
        if item.get("action") == "replace" and not item.get("before"):
            errors.append(f"{item.get('id', '?')}: replace 缺少 before")
        if item.get("action") in {"replace", "insert"} and not item.get("after"):
            errors.append(f"{item.get('id', '?')}: {item.get('action')} 缺少 after")
        if not (item.get("location") or {}).get("quote"):
            errors.append(f"{item.get('id', '?')}: location 缺少 quote，无法唯一定位")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    if not args.plan.is_file():
        print(f"REVISION_GATE: ok=0 missing={args.plan}")
        return 2
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    errors = check(plan)
    selected = sum(bool(item.get("selected")) for item in plan.get("items", []))
    print(f"REVISION_GATE: ok={int(not errors)} selected={selected} errors={len(errors)}")
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
