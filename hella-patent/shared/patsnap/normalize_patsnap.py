#!/usr/bin/env python3
"""Normalize saved PatSnap MCP responses without accessing credentials."""

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


def _iso(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value)
    if re.fullmatch(r"\d{8}", text):
        return f"{text[:4]}-{text[4:6]}-{text[6:]}"
    return text


def patent_type(kind_code: str | None) -> str:
    kind = (kind_code or "").upper()
    if kind.startswith(("A", "B", "C")):
        return "invention"
    if kind.startswith(("U", "Y")):
        return "utility_model"
    if kind.startswith(("S", "D")):
        return "design"
    return "unknown"


def legal_status(
    search_value: str | None,
    simple_value: str | None,
    events: list[str] | None,
    estimated_expiry: str | None,
    *,
    today: date | None = None,
) -> str:
    today = today or date.today()
    values = {str(search_value or "").lower(), str(simple_value or "").lower()}
    if values & {"active", "granted", "valid"}:
        return "active"
    if values & {"pending", "examining", "application"}:
        return "pending"
    expiry = _iso(estimated_expiry)
    event_text = " ".join(events or []).lower()
    expired_signal = any(word in event_text for word in ("expired", "expiry", "期满", "届满"))
    if expiry:
        try:
            expired_signal = expired_signal or date.fromisoformat(expiry) < today
        except ValueError:
            pass
    return "expired" if expired_signal else "lapsed"


class ClaimsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.claims: list[dict[str, Any]] = []
        self.current: dict[str, Any] | None = None
        self.segment: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        classes = set((values.get("class") or "").split())
        if tag == "div" and classes & {"indep-clm", "dep-clm"}:
            self.current = {
                "claim_no": int(values.get("num") or len(self.claims) + 1),
                "type": "independent" if "indep-clm" in classes else "dependent",
                "segments": {"preamble": [], "transition": [], "features": []},
            }
        elif self.current is not None and tag in {"seg-con", "seg-trans", "seg-refi"}:
            self.segment = tag

    def handle_data(self, data: str) -> None:
        if self.current is None or self.segment is None:
            return
        key = {
            "seg-con": "preamble",
            "seg-trans": "transition",
            "seg-refi": "features",
        }[self.segment]
        self.current["segments"][key].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"seg-con", "seg-trans", "seg-refi"}:
            self.segment = None
        elif tag == "div" and self.current is not None:
            segments = self.current["segments"]
            preamble = "".join(segments["preamble"]).strip()
            feature_text = "".join(segments["features"]).strip()
            depends = [int(n) for n in re.findall(r"权利要求\s*(\d+)", preamble)]
            features = []
            if feature_text:
                features.append(
                    {
                        "id": "F1",
                        "text": feature_text,
                        "text_original": "",
                        "uncertain": False,
                        "translation": "original",
                    }
                )
            self.claims.append(
                {
                    "claim_no": self.current["claim_no"],
                    "type": self.current["type"],
                    "category": "product",
                    "depends_on": depends,
                    "preamble": preamble,
                    "features": features
                    or [
                        {
                            "id": "F1",
                            "text": preamble,
                            "text_original": "",
                            "uncertain": True,
                            "translation": "original",
                        }
                    ],
                }
            )
            self.current = None


def parse_claims(claims_html: str) -> list[dict[str, Any]]:
    parser = ClaimsParser()
    parser.feed(claims_html or "")
    return parser.claims


def parse_description(description_html: str) -> list[dict[str, str]]:
    source = description_html or ""
    marker = re.compile(r'<b[^>]*class="d_n"[^>]*>(\[\d+\])</b>', re.I)
    matches = list(marker.finditer(source))
    paragraphs: list[dict[str, str]] = []
    section = ""
    previous = 0
    for index, match in enumerate(matches):
        prefix = html.unescape(re.sub(r"<[^>]+>", "", source[previous : match.start()])).strip()
        if prefix:
            section = prefix.splitlines()[-1].strip()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        text = html.unescape(re.sub(r"<[^>]+>", "", source[match.end() : end])).strip()
        paragraphs.append({"id": match.group(1), "section": section, "text": text})
        previous = match.end()
    if not paragraphs and source.strip():
        text = html.unescape(re.sub(r"<[^>]+>", "", source)).strip()
        paragraphs.append({"id": "P1", "section": "", "text": text})
    return paragraphs


def unwrap(raw: dict[str, Any]) -> dict[str, Any]:
    response = raw.get("response", raw)
    if isinstance(response, dict) and "response" in response and len(response) <= 4:
        response = response["response"]
    return response


def normalize(
    raw: dict[str, Any],
    lifecycle_raw: dict[str, Any] | None = None,
    *,
    fetched_at: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    response = unwrap(raw)
    bibliography = response.get("bibliography", {})
    lifecycle = unwrap(lifecycle_raw or {})
    events = lifecycle.get("legal_events", [])
    publication = bibliography.get("publication_number") or ""
    kind = bibliography.get("kind_code")
    status = legal_status(
        None,
        bibliography.get("simple_legal_status"),
        events,
        response.get("estimated_expiry_date"),
    )
    relations = response.get("relations", {})
    family = relations.get("simple_family", [])
    patent = {
        "pub_no": publication,
        "app_no": bibliography.get("application_number"),
        "family_id": publication if family else None,
        "title": bibliography.get("title") or "",
        "applicants": bibliography.get("current_assignees") or [],
        "patent_type": patent_type(kind),
        "kind_code": kind,
        "patsnap_id": raw.get("input", {}).get("patent_id"),
        "jurisdiction": bibliography.get("patent_office") or publication[:2],
        "app_date": _iso(bibliography.get("application_date")),
        "pub_date": _iso(bibliography.get("publication_date")),
        "grant_date": _iso(bibliography.get("grant_date")),
        "est_expiry": _iso(response.get("estimated_expiry_date")),
        "legal_status": status,
        "legal_status_raw": {
            "search": None,
            "simple": bibliography.get("simple_legal_status"),
            "events": events,
        },
        "ipc": bibliography.get("ipc_classes") or [],
        "cpc": bibliography.get("cpc_classes") or [],
        "standardized_assignees": response.get("standardized_current_assignees") or [],
        "claims_available": bool(response.get("claims")),
        "claims_lang": "zh" if re.search(r"[\u4e00-\u9fff]", response.get("claims") or "") else "original",
        "source": "patsnap_mcp",
        "found_by": [],
        "fetched_at": fetched_at or raw.get("executed_at") or raw.get("saved_at") or datetime.now().astimezone().isoformat(timespec="seconds"),
        "relevance_rank": None,
        "vendor_summary": {
            "problem": response.get("technical_problem"),
            "solution": response.get("technical_solution"),
            "effect": response.get("technical_effect"),
        },
        "lifecycle": {
            "license_transfer": len(lifecycle.get("license_transfer_pledge_records", [])),
            "invalidity_records": len(lifecycle.get("reexamination_invalidity_records", [])),
        },
        "grade": None,
        "grade_reason": "",
        "family_members": family,
        "conflicts": [],
    }
    claims = {
        "doc_id": publication,
        "doc_role": "prior_art",
        "lang": patent["claims_lang"],
        "claims": parse_claims(response.get("claims") or ""),
    }
    paragraphs = {
        "doc_id": publication,
        "source": "patsnap_mcp",
        "source_url": "",
        "paragraphs": parse_description(response.get("description") or ""),
    }
    return patent, claims, paragraphs


def main() -> int:
    parser = argparse.ArgumentParser(description="归一智慧芽 MCP 原始返回")
    parser.add_argument("--patent", type=Path, required=True)
    parser.add_argument("--lifecycle", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if not args.patent.is_file():
        print(f"PATSNAP_NORMALIZE: ok=0 missing={args.patent}")
        return 2
    raw = json.loads(args.patent.read_text(encoding="utf-8"))
    lifecycle = (
        json.loads(args.lifecycle.read_text(encoding="utf-8"))
        if args.lifecycle and args.lifecycle.is_file()
        else None
    )
    patent, claims, paragraphs = normalize(raw, lifecycle)
    if not patent["pub_no"]:
        print("PATSNAP_NORMALIZE: ok=0 error=missing_publication_number")
        return 1
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "patent.json").write_text(
        json.dumps(patent, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "claim_features.json").write_text(
        json.dumps(claims, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "description_paragraphs.json").write_text(
        json.dumps(paragraphs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "PATSNAP_NORMALIZE: "
        f"ok=1 pub_no={patent['pub_no']} claims={len(claims['claims'])} "
        f"paragraphs={len(paragraphs['paragraphs'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
