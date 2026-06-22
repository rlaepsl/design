#!/usr/bin/env python3
"""
verify_claims.py — claim-labeling 검증 하네스 데모 (결정론적, 외부 의존성 없음)

AI가 만든 모든 주장(claim)에 '출처 라벨'을 강제하고, 근거 없는 위험한 주장(환각)을
규칙 기반으로 잡아내는 품질 게이트. LLM 채점이 아니라 결정론적 검사라 매번 같은 판정이 나온다.

라벨 체계:
  관찰 / 출처확인 / 추론   → source_ids 필수 (근거 없는 사실 단정 금지)
  확인 필요 / 제안          → source_ids 선택 (불확실/제안임을 명시)

검사 항목:
  1) 필수 키 존재 + 라벨 유효성
  2) source_ids 커버리지 점수 (근거가 필요한 claim 중 실제 근거가 달린 비율)
  3) 위험 패턴 탐지 — 공식 브랜드 단정 / 가짜 전화 플레이스홀더 / 출처 없는 QR /
     법적 문구 / 근거 없는 날짜·마감
  4) verdict(pass / pass_with_warnings / fail) + score(0~100)

사용:
  python verify_claims.py --claims sample_claims.jsonl
  python verify_claims.py --claims sample_claims.jsonl --json

이 파일은 제 개인 프로젝트(멀티에이전트 디자인 파이프라인)의 환각 차단 기법을
공개용으로 새로 작성한 데모입니다. 회사/고객 데이터는 포함하지 않습니다.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

LABELS = ["관찰", "출처확인", "추론", "확인 필요", "제안"]
SOURCE_OPTIONAL_LABELS = {"확인 필요", "제안"}
REQUIRED_KEYS = ["claim_id", "label", "claim_text", "source_ids", "risk_field"]
MIN_SOURCE_COVERAGE = 0.8

# 근거 없이 나오면 위험한 주장 패턴 (디자인 도메인 환각의 단골 유형)
RISKY_PATTERNS = [
    ("official_brand_claim", r"공식\s*(색상|서체|폰트|로고|브랜드|규정|가이드)"),
    ("invented_phone_placeholder", r"0{2,3}[-\s]?0{3,4}[-\s]?0{4}|02-0000-0000"),
    ("qr_without_source", r"QR|큐알"),
    ("legal_or_policy_claim", r"법적|정책|의무|필수\s*고지"),
    ("ungrounded_date", r"(마감|행사|접수|신청|일정).{0,20}\d{1,2}\s*월\s*\d{1,2}\s*일"),
]
EVIDENCE_TERMS = ["출처", "source", "src-", "http", "확인 필요", "자료에", "원문", "명시"]


def has_evidence(text: str) -> bool:
    low = text.lower()
    return any(term.lower() in low for term in EVIDENCE_TERMS)


def validate(claims: list[dict]) -> dict:
    failures: list[str] = []
    warnings: list[str] = []
    risky: list[dict] = []
    score = 100

    support_required = 0
    source_backed = 0

    for i, claim in enumerate(claims, start=1):
        cid = str(claim.get("claim_id", f"line_{i}"))

        for key in REQUIRED_KEYS:
            if key not in claim:
                failures.append(f"missing_key:{cid}:{key}")
                score -= 5

        label = claim.get("label")
        if label not in LABELS:
            failures.append(f"invalid_label:{cid}:{label}")
            score -= 8

        source_ids = claim.get("source_ids", [])
        if not isinstance(source_ids, list):
            failures.append(f"source_ids_not_list:{cid}")
            source_ids = []

        # 근거 필요 라벨인데 source_ids 가 비면 실패
        if label not in SOURCE_OPTIONAL_LABELS:
            support_required += 1
            if source_ids:
                source_backed += 1
            else:
                failures.append(f"missing_source_ids:{cid}")
                score -= 6

        # 위험 패턴: 근거 표지도 없고 '확인 필요' 라벨도 아니면 환각 위험
        text = str(claim.get("claim_text", ""))
        for risk_id, pattern in RISKY_PATTERNS:
            if re.search(pattern, text) and not has_evidence(text) and label != "확인 필요":
                risky.append({"claim_id": cid, "risk": risk_id, "text": text[:80]})
                score -= 7

    coverage = 1.0 if support_required == 0 else round(source_backed / support_required, 4)
    if coverage < MIN_SOURCE_COVERAGE:
        warnings.append(f"source_coverage_below_threshold:{coverage:.2f}<{MIN_SOURCE_COVERAGE:.2f}")
        score -= 5

    score = max(0, min(100, score))
    if failures or risky:
        verdict = "fail"
    elif warnings or score < 90:
        verdict = "pass_with_warnings"
    else:
        verdict = "pass"

    return {
        "verdict": verdict,
        "score": score,
        "claim_count": len(claims),
        "source_coverage": coverage,
        "failures": failures,
        "warnings": warnings,
        "risky_claims": risky,
    }


def load_claims(path: Path) -> list[dict]:
    claims = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            claims.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"invalid_json: {path.name}:{line_no}: {exc.msg}")
    return claims


def main() -> int:
    parser = argparse.ArgumentParser(description="claim-labeling 검증 하네스 데모")
    parser.add_argument("--claims", required=True, help="claims.jsonl 경로")
    parser.add_argument("--json", action="store_true", help="JSON으로 출력")
    args = parser.parse_args()

    result = validate(load_claims(Path(args.claims)))

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"verdict : {result['verdict']}")
        print(f"score   : {result['score']}")
        print(f"claims  : {result['claim_count']}  (source_coverage={result['source_coverage']})")
        for f in result["failures"]:
            print(f"  FAIL: {f}")
        for r in result["risky_claims"]:
            print(f"  RISK: {r['claim_id']}:{r['risk']} :: {r['text']}")
        for w in result["warnings"]:
            print(f"  WARN: {w}")

    return 1 if result["verdict"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
