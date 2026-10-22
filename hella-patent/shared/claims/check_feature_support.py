#!/usr/bin/env python3
"""Map claim features to supporting description paragraphs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

STOP = {"所述", "一种", "包括", "包含", "具有", "用于", "其中", "通过", "根据"}


def terms(text: str) -> list[str]:
    cleaned = re.sub(r"[，。；、：,.()\[\]（）\s]", "", text)
    chunks = [
        item
        for item in re.split("|".join(map(re.escape, sorted(STOP, key=len, reverse=True))), cleaned)
        if len(item) >= 2
    ]
    candidates: set[str] = set()
    for chunk in chunks:
        candidates.add(chunk)
        if len(chunk) > 6:
            candidates.update(chunk[i : i + 4] for i in range(len(chunk) - 3))
    return sorted(candidates, key=len, reverse=True)


def map_support(claims: dict, description: dict) -> list[dict]:
    paragraphs = description.get("paragraphs") or []
    output: list[dict] = []
    for claim in claims.get("claims") or []:
        for feature in claim.get("features") or []:
            feature_terms = terms(feature.get("text") or "")
            matches = []
            for para in paragraphs:
                text = para.get("text") or ""
                hits = [term for term in feature_terms if term in text]
                if not hits:
                    continue
                ratio = len(hits) / max(len(feature_terms), 1)
                matches.append(
                    {
                        "paragraph_id": para.get("id"),
                        "section": para.get("section", ""),
                        "matched_terms": hits[:10],
                        "score": round(ratio, 3),
                        "quote": text[:240],
                    }
                )
            matches.sort(key=lambda item: item["score"], reverse=True)
            best = matches[0]["score"] if matches else 0
            output.append(
                {
                    "claim_no": claim.get("claim_no"),
                    "feature_id": feature.get("id"),
                    "feature": feature.get("text"),
                    "support": (
                        "exact_candidate"
                        if best >= 0.8
                        else "partial_candidate"
                        if best > 0
                        else "not_found"
                    ),
                    "needs_human": True,
                    "matches": matches[:5],
                }
            )
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--claims", type=Path, required=True)
    parser.add_argument("--description", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.claims.is_file() or not args.description.is_file():
        print("CLAIM_SUPPORT: ok=0 missing_input=1")
        return 2
    claims = json.loads(args.claims.read_text(encoding="utf-8"))
    description = json.loads(args.description.read_text(encoding="utf-8"))
    result = map_support(claims, description)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    missing = sum(item["support"] == "not_found" for item in result)
    print(f"CLAIM_SUPPORT: ok={int(missing == 0)} features={len(result)} missing={missing}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
