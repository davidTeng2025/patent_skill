#!/usr/bin/env python3
"""Save an MCP tool response in the immutable work/raw layout."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="JSON file; default stdin")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        text = (
            args.input.read_text(encoding="utf-8")
            if args.input
            else sys.stdin.read()
        )
        data = json.loads(text)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"RAW_SAVE: ok=0 error={exc}")
        return 2
    if args.output.exists():
        stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        args.output = args.output.with_name(
            f"{args.output.stem}_{stamp}{args.output.suffix}"
        )
    data.setdefault("saved_at", datetime.now().astimezone().isoformat(timespec="seconds"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"RAW_SAVE: ok=1 path={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
