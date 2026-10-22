# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "jsonschema>=4.18",
#   "mammoth>=1.6.0",
#   "openpyxl>=3.1.0",
#   "PyMuPDF>=1.23.0,<2",
#   "pytest>=7.0",
#   "python-docx>=1.1.0",
#   "PyYAML>=6.0",
# ]
# ///
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def load(relative: str, name: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "directory",
    [
        ".",
        "idf-review",
        "fto",
        "claim-scope",
        "office-action",
        "idf-drafting",
        "application-drafting",
        "draft-revision",
    ],
)
def test_skill_frontmatter_and_length(directory: str):
    path = ROOT / directory / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "\nname:" in text
    assert "\ndescription:" in text
    assert len(text.splitlines()) < 500


def test_all_schemas_are_valid():
    for path in (ROOT / "schemas").glob("*.schema.json"):
        Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))


def test_init_case_validates(tmp_path: Path):
    script = ROOT / "shared/case/init_case.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--workflow",
            "idf_review",
            "--title",
            "测试案件",
            "--cases-dir",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.startswith("CASE_DIR:")
    case_file = next(tmp_path.glob("IDF-*/case.json"))
    case = json.loads(case_file.read_text(encoding="utf-8"))
    schema = json.loads(
        (ROOT / "schemas/case.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(case)


def test_query_guard_rejects_unconfirmed_semantic():
    module = load("shared/patsnap/guard_query.py", "guard_query")
    errors = module.inspect_plan(
        {
            "queries": [
                {
                    "id": "Q1",
                    "status": "draft",
                    "mode": "semantic",
                    "semantic_query": "客户：吉利，项目代号 X1，间隙 0.2 mm",
                }
            ]
        }
    )
    assert len(errors) >= 3


def test_normalize_patsnap_fulltext():
    module = load("shared/patsnap/normalize_patsnap.py", "normalize_patsnap")
    raw = {
        "input": {"patent_id": "CN123A"},
        "executed_at": "2026-10-21T10:00:00+08:00",
        "response": {
            "bibliography": {
                "publication_number": "CN123A",
                "application_number": "CN2026X",
                "kind_code": "A",
                "title": "测试专利",
                "patent_office": "CN",
                "current_assignees": ["测试公司"],
                "application_date": "2026-01-01",
                "publication_date": "2026-07-01",
                "grant_date": None,
                "ipc_classes": ["F16H1/00"],
                "cpc_classes": [],
                "simple_legal_status": "Pending",
            },
            "claims": (
                '<div class="indep-clm" num="1">'
                "<seg-con>1.一种装置，</seg-con>"
                "<seg-trans>其特征在于，</seg-trans>"
                "<seg-refi>包括壳体和齿轮。</seg-refi></div>"
            ),
            "description": (
                '技术领域<b class="d_n">[0001]</b>本发明涉及执行器。'
                '背景技术<b class="d_n">[0002]</b>现有装置存在问题。'
            ),
            "estimated_expiry_date": None,
            "relations": {"simple_family": []},
        },
    }
    patent, claims, paragraphs = module.normalize(raw)
    assert patent["patent_type"] == "invention"
    assert patent["legal_status"] == "pending"
    assert claims["claims"][0]["features"][0]["text"] == "包括壳体和齿轮。"
    assert paragraphs["paragraphs"][0]["id"] == "[0001]"


def test_idf_audit_detects_missing_sections_and_placeholder():
    module = load("shared/idf/audit_idf.py", "audit_idf")
    findings = module.audit("技术方案\n控制器控制电机。\n【待确认：阈值】")
    rules = {item["rule_id"] for item in findings}
    assert "IDF-001" in rules
    assert "IDF-009" in rules


def test_orbit_csv_normalizer(tmp_path: Path):
    module = load("shared/patsnap/normalize_orbit.py", "normalize_orbit")
    path = tmp_path / "orbit.csv"
    path.write_text(
        "公开号,标题,申请人,法律状态,IPC\n"
        "CN123U,测试结构,测试公司,有效,F16H1/00\n",
        encoding="utf-8-sig",
    )
    source = module.rows(path)[0]
    patent = module.normalize(source)
    assert patent["pub_no"] == "CN123U"
    assert patent["patent_type"] == "utility_model"
    assert patent["legal_status"] == "active"


def test_w1_clarity_pipeline_writes_docx(tmp_path: Path):
    source = tmp_path / "idf.md"
    source.write_text("技术方案\n控制器控制电机。\n", encoding="utf-8")
    case = tmp_path / "IDF-2026-0001"
    script = ROOT / "idf-review/run_clarity.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            str(source),
            "--case-dir",
            str(case),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert (case / "work/findings.json").is_file()
    assert list((case / "output").glob("*.docx"))


def test_feature_support_maps_paragraph():
    module = load(
        "shared/claims/check_feature_support.py", "check_feature_support"
    )
    claims = {
        "claims": [
            {
                "claim_no": 1,
                "features": [{"id": "F1", "text": "壳体内设置输出齿轮"}],
            }
        ]
    }
    description = {
        "paragraphs": [
            {"id": "[0021]", "section": "实施方式", "text": "壳体内设置输出齿轮和电机。"}
        ]
    }
    result = module.map_support(claims, description)
    assert result[0]["matches"][0]["paragraph_id"] == "[0021]"
    assert result[0]["needs_human"] is True


def test_chart_emits_specialist_columns(tmp_path: Path):
    payload = {
        "scene": "fto",
        "left": {"doc_id": "CN123A", "claim_no": 1},
        "features": [{"id": "F1", "claim_no": 1, "text": "壳体"}],
        "columns": [{"id": "C1", "label": "本产品", "doc_id": "product"}],
        "highlights": [],
        "cells": [
            {
                "feature_id": "F1",
                "column_id": "C1",
                "strength": "强",
                "covered": ["壳体"],
                "missing": [],
                "analysis": {"对应": "存在壳体", "差别": "未见", "依据": "第1页"},
                "cite": "第1页",
                "quote": "产品包括壳体。",
                "reviewer_judgement": "相同",
                "reviewer_note": "待签字",
            }
        ],
        "claim_summary": [
            {"claim_no": 1, "agent_reading": "全部对应，须人审", "reviewer_risk": "高"}
        ],
        "rejections": [],
    }
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "shared/chart/emit_chart.py"),
            "--json",
            str(payload_path),
            "--into",
            str(tmp_path / "chart"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert list((tmp_path / "chart").glob("*.xlsx"))
    chart = json.loads((tmp_path / "chart/chart.json").read_text(encoding="utf-8"))
    assert chart["cells"][0]["reviewer_judgement"] == "相同"


def test_source_trace_blocks_unconfirmed_release():
    module = load(
        "shared/drafting/check_source_trace.py", "check_source_trace"
    )
    errors = module.check(
        [
            {
                "para_id": "3.2-01",
                "status": "needs_confirm",
                "sources": [],
                "question": "请确认阈值",
            }
        ],
        confirmed=True,
    )
    assert errors


def test_revision_gate_requires_basis_and_location():
    module = load("draft-revision/validate_plan.py", "validate_revision_plan")
    errors = module.check(
        {
            "items": [
                {
                    "id": "V1",
                    "selected": True,
                    "action": "replace",
                    "before": "弹性件",
                    "after": "弹片",
                    "basis_src": "",
                    "location": {},
                }
            ]
        }
    )
    assert len(errors) == 2


def test_audit_claims_reports_forward_reference():
    module = load("shared/claims/audit_claims.py", "audit_claims")
    findings = module.audit(
        "1. 一种装置，其特征在于，包括壳体和齿轮。\n"
        "2. 根据权利要求3所述的装置，其特征在于，还包括电机。\n"
        "3. 根据权利要求1所述的装置，其特征在于，还包括控制器。"
    )
    assert any(item.code == "FORWARD_REFERENCE" for item in findings)


def test_compile_patsnap_boolean_query():
    module = load("shared/query/compile_patsnap.py", "compile_patsnap")
    query = {
        "logic": "E1 AND E2",
        "region": ["CN"],
        "pub_date_before": "2026-10-21",
    }
    elements = {
        "E1": {"zh": ["输出齿轮"], "en": ["output gear"]},
        "E2": {"zh": ["弹片"], "en": ["spring plate"]},
    }
    result = module.compile_query(query, elements)
    assert 'TAC_ALL:("输出齿轮" OR "output gear")' in result
    assert "AUTHORITY:(CN)" in result
    assert "PBD:[19000101 TO 20261021]" in result


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q", *sys.argv[1:]]))
