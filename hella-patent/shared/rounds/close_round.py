#!/usr/bin/env python3
"""Record a drafting/self-review round and enforce the three-round limit."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--draft-dir", required=True)
    parser.add_argument("--findings", type=Path, required=True)
    args = parser.parse_args()
    if not args.case.is_file() or not args.findings.is_file():
        print("ROUND_CLOSE: ok=0 missing_input=1")
        return 2
    case = json.loads(args.case.read_text(encoding="utf-8"))
    findings = json.loads(args.findings.read_text(encoding="utf-8"))
    rounds = case.setdefault("rounds", [])
    if len(rounds) >= 3:
        print("ROUND_CLOSE: ok=0 limit=3 action=write_issues")
        return 1
    must = sum(item.get("level") == "must" for item in findings)
    should = sum(item.get("level") == "should" for item in findings)
    rounds.append(
        {
            "round": len(rounds) + 1,
            "draft_dir": args.draft_dir,
            "must_open": must,
            "should_open": should,
            "ended_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
    )
    case["status"] = "self_review" if must else "review"
    args.case.write_text(
        json.dumps(case, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"ROUND_CLOSE: ok=1 round={len(rounds)} must={must} "
        f"next={'revise' if must and len(rounds) < 3 else 'review'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
