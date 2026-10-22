#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "mammoth>=1.6.0",
#   "PyMuPDF>=1.23.0,<2",
#   "python-docx>=1.1.0",
# ]
# ///
"""Run the deterministic W1 clarity-review pipeline.

用 `uv run run_clarity.py` 执行。子脚本沿用这次装好的环境，所以这里列出它们的依赖。
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]


def run(command: list[str], *, allowed: set[int] = {0}) -> int:
    result = subprocess.run(command, check=False)
    if result.returncode not in allowed:
        raise SystemExit(result.returncode)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="W1 交底清晰性审核基础流水线")
    parser.add_argument("input", type=Path)
    parser.add_argument("--case-dir", type=Path, required=True)
    parser.add_argument("--title", default="交底审核意见")
    args = parser.parse_args()
    if not args.input.is_file():
        print(f"W1_CLARITY: ok=0 missing={args.input}")
        return 2

    work = args.case_dir / "work"
    output = args.case_dir / "output"
    work.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    parsed = work / f"{args.input.stem}.md"

    suffix = args.input.suffix.lower()
    if suffix == ".docx":
        run(
            [
                sys.executable,
                str(SKILL / "shared/docparse/docx_to_md.py"),
                "-i",
                str(args.input),
                "-o",
                str(parsed),
            ]
        )
    elif suffix == ".pdf":
        extracted = work / f"{args.input.stem}.extracted.txt"
        run(
            [
                sys.executable,
                str(SKILL / "shared/docparse/pdf_text.py"),
                "-i",
                str(args.input),
                "-o",
                str(extracted),
            ]
        )
        parsed.write_text(extracted.read_text(encoding="utf-8"), encoding="utf-8")
    elif suffix in {".md", ".txt"}:
        shutil.copyfile(args.input, parsed)
    else:
        print(f"W1_CLARITY: ok=0 unsupported={suffix}")
        return 2

    findings = work / "findings.json"
    audit_code = run(
        [
            sys.executable,
            str(SKILL / "shared/idf/audit_idf.py"),
            str(parsed),
            "--output",
            str(findings),
        ],
        allowed={0, 1},
    )
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    review_md = output / f"{args.case_dir.name}_交底审核意见_草稿_{stamp}.md"
    review_docx = review_md.with_suffix(".docx")
    run(
        [
            sys.executable,
            str(SKILL / "shared/idf/render_findings.py"),
            str(findings),
            "--output",
            str(review_md),
            "--title",
            args.title,
        ]
    )
    run(
        [
            sys.executable,
            str(SKILL / "shared/render/md_to_docx.py"),
            "-i",
            str(review_md),
            "-o",
            str(review_docx),
        ]
    )
    print(
        f"W1_CLARITY: ok={int(audit_code == 0)} "
        f"findings={findings} report={review_docx}"
    )
    return audit_code


if __name__ == "__main__":
    raise SystemExit(main())
