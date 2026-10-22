#!/usr/bin/env python3
"""Deterministic first-pass checks for Chinese invention disclosures."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SECTION_RULES = (
    ("IDF-001", "背景技术", ("背景技术", "现有技术")),
    ("IDF-001", "技术问题", ("技术问题", "需要解决的问题", "发明目的")),
    ("IDF-001", "技术方案", ("技术方案", "发明内容", "实用新型内容")),
    ("IDF-001", "有益效果", ("有益效果", "技术效果", "优点")),
    ("IDF-001", "附图说明", ("附图", "图1", "图 1")),
    ("IDF-001", "具体实施方式", ("具体实施", "实施例")),
)
VAGUE_CONTROL = re.compile(
    r"([\u4e00-\u9fffA-Za-z0-9_-]{1,16})(?:模块|单元|控制器)?"
    r"(?:控制|处理|优化|提高|改善)"
    r"([\u4e00-\u9fffA-Za-z0-9_-]{1,16})[。；\n]"
)
PLACEHOLDER = re.compile(r"(?:\[\s*待确认[^\]]*\]|【\s*待确认[^】]*】|TBD|TODO)", re.I)
ABSOLUTE = re.compile(r"(?:唯一|最佳|最优|所有情况下|完全避免|百分之百)")


def finding(
    index: int,
    rule_id: str,
    level: str,
    problem: str,
    suggestion: str,
    *,
    quote: str = "",
    needs_human: bool = False,
) -> dict:
    return {
        "id": f"R{index}",
        "rule_id": rule_id,
        "level": level,
        "location": {"section": "", "paragraph": 0},
        "quote": quote,
        "problem": problem,
        "suggestion": suggestion,
        "audience": "inventor",
        "needs_human": needs_human,
    }


def audit(text: str) -> list[dict]:
    findings: list[dict] = []
    for _, label, aliases in SECTION_RULES:
        if not any(alias in text for alias in aliases):
            findings.append(
                finding(
                    len(findings) + 1,
                    "IDF-001",
                    "must",
                    f"未识别到“{label}”内容。",
                    f"按海拉交底模板补充“{label}”，没有内容时说明原因，不能留空。",
                    needs_human=True,
                )
            )
    for match in VAGUE_CONTROL.finditer(text):
        quote = match.group(0).strip()
        if len(quote) > 80:
            continue
        findings.append(
            finding(
                len(findings) + 1,
                "IDF-002",
                "must",
                "疑似只有功能或控制关系，没有披露输入、触发条件和执行步骤。",
                "补充信号或数据来源、触发条件、处理步骤、执行主体和输出。",
                quote=quote,
                needs_human=True,
            )
        )
    for match in PLACEHOLDER.finditer(text):
        findings.append(
            finding(
                len(findings) + 1,
                "IDF-009",
                "must",
                "正文仍含待确认占位内容。",
                "由发明人补充事实和出处后再进入确认版。",
                quote=match.group(0),
                needs_human=True,
            )
        )
    for match in ABSOLUTE.finditer(text):
        findings.append(
            finding(
                len(findings) + 1,
                "IDF-006",
                "should",
                "含绝对化表述，可能不必要地限制或夸大方案。",
                "改为可核验的技术限定，或使用“优选”“在一些实施例中”。",
                quote=match.group(0),
            )
        )
    if len(re.findall(r"实施例", text)) < 2:
        findings.append(
            finding(
                len(findings) + 1,
                "IDF-005",
                "should",
                "未见两个以上实施例。",
                "在资料有依据时补充主路径实施例和至少一个分支实施例。",
                needs_human=True,
            )
        )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="海拉交底清晰性机械检查")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.input.is_file():
        print(f"IDF_AUDIT: ok=0 missing={args.input}")
        return 2
    text = args.input.read_text(encoding="utf-8", errors="replace")
    findings = audit(text)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(findings, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    must = sum(item["level"] == "must" for item in findings)
    should = sum(item["level"] == "should" for item in findings)
    print(f"IDF_AUDIT: ok={int(must == 0)} must={must} should={should}")
    return 1 if must else 0


if __name__ == "__main__":
    raise SystemExit(main())
