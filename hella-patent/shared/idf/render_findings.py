#!/usr/bin/env python3
"""Render findings.json to a stable Markdown review draft."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

LEVEL = {"must": "必须修改", "should": "建议修改", "info": "提示"}


def render(findings: list[dict], title: str) -> str:
    lines = [
        f"# {title}",
        "",
        "> 本文件为草稿。正式结论由海拉专利专员复核并签字。",
        "",
        "## 审核结果概览",
        "",
    ]
    counts = {key: sum(x.get("level") == key for x in findings) for key in LEVEL}
    lines.append(
        f"- 必须修改：{counts['must']} 项；建议修改：{counts['should']} 项；提示：{counts['info']} 项。"
    )
    lines.extend(["", "## 给发明人的修改清单", ""])
    if not findings:
        lines.append("本轮机械检查未发现问题；仍须专员做语义和可专利性审核。")
    for item in findings:
        lines.extend(
            [
                f"### {item.get('id')} · {LEVEL.get(item.get('level'), item.get('level'))} · {item.get('rule_id')}",
                "",
                f"- **问题：** {item.get('problem', '')}",
                f"- **建议：** {item.get('suggestion', '')}",
            ]
        )
        if item.get("quote"):
            lines.append(f"- **原文：** {item['quote']}")
        if item.get("needs_human"):
            lines.append("- **需要发明人确认：** 是")
        lines.append("")
    lines.extend(
        [
            "## 专员复核",
            "",
            "- [ ] 清晰性结论",
            "- [ ] 形式规范结论",
            "- [ ] 新颖性初判（如已检索）",
            "- [ ] 创造性初判（如已检索）",
            "- [ ] 不确定点和业务事实",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="把 findings.json 渲染为交底审核意见 Markdown")
    parser.add_argument("findings", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--title", default="交底审核意见")
    args = parser.parse_args()
    if not args.findings.is_file():
        print(f"IDF_REPORT: ok=0 missing={args.findings}")
        return 2
    data = json.loads(args.findings.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(data, args.title), encoding="utf-8")
    print(f"IDF_REPORT: ok=1 path={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
