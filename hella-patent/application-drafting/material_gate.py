#!/usr/bin/env python3
"""W6 material gate aligned with the Hella case contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=Path, required=True)
    args = parser.parse_args()
    if not args.case.is_file():
        print(f"APPLICATION_GATE: ok=0 missing={args.case}")
        return 2
    case = json.loads(args.case.read_text(encoding="utf-8"))
    params = case.get("params") or {}
    inputs = case.get("inputs") or []
    gates = {gate.get("gate") for gate in case.get("gates") or []}
    kinds = {item.get("kind") for item in inputs}
    missing: list[str] = []
    if "disclosure_confirmed" not in gates and not params.get("signed_disclosure"):
        missing.append("已确认交底（disclosure_confirmed 或 signed_disclosure）")
    if params.get("patent_type", "invention") == "utility_model" and "drawing" not in kinds:
        missing.append("发明人提供的结构图")
    print(
        f"APPLICATION_GATE: ok={int(not missing)} "
        f"patent_type={params.get('patent_type', 'invention')} missing={len(missing)}"
    )
    for item in missing:
        print(f"MISSING: {item}")
    return 2 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
