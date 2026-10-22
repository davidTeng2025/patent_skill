#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from datetime import datetime
from pathlib import Path

PREFIX={"idf_review":"IDF","fto":"FTO","claim_scope":"CLM","office_action":"OA","idf_drafting":"DSC","application_drafting":"APP","draft_revision":"REV"}

def next_id(cases: Path, workflow: str, year: int) -> str:
    prefix=PREFIX[workflow]
    used=[]
    for p in cases.glob(f"{prefix}-{year}-[0-9][0-9][0-9][0-9]"):
        try: used.append(int(p.name.rsplit("-",1)[1]))
        except ValueError: pass
    return f"{prefix}-{year}-{max(used, default=0)+1:04d}"

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--workflow", required=True, choices=sorted(PREFIX))
    ap.add_argument("--title", required=True)
    ap.add_argument("--cases-dir", type=Path, default=Path("cases"))
    ap.add_argument("--owner", default="待填写")
    args=ap.parse_args()
    now=datetime.now().astimezone()
    case_id=next_id(args.cases_dir,args.workflow,now.year)
    base=args.cases_dir/case_id
    for d in ["input","work/raw/search","work/raw/patent","work/raw/lifecycle","work/raw/pdf","work/claim_features","work/description_paragraphs","drafts","chart","output"]:
        (base/d).mkdir(parents=True,exist_ok=True)
    data={"case_id":case_id,"workflow":args.workflow,"title":args.title,"owner":args.owner,"created_at":now.isoformat(timespec="seconds"),"confidentiality":"confidential","status":"intake","params":{},"inputs":[],"gates":[],"outputs":[],"rounds":[]}
    (base / "case.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (base / "issues.md").write_text(
        "# 问题清单\n\n"
        "| ID | 级别 | 位置 | 问题 | 依据 | 需要谁 |\n"
        "|---|---|---|---|---|---|\n",
        encoding="utf-8",
    )
    (base / "revision_log.md").write_text(
        "# 修订记录\n\n"
        "| 时间 | 操作人 | 原因 | 新文件 | 闸门 |\n"
        "|---|---|---|---|---|\n",
        encoding="utf-8",
    )
    print(f"CASE_DIR: path={base.as_posix()} case_id={case_id}")
    return 0
if __name__=="__main__": raise SystemExit(main())
