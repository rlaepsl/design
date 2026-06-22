"""claim 검증 하네스 동작 테스트."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code", "claim-verification"))

from verify_claims import validate  # noqa: E402


def test_clean_claims_pass():
    claims = [
        {"claim_id": "A", "label": "관찰", "claim_text": "제목이 자료에 표시되어 있다.",
         "source_ids": ["SRC-1"], "risk_field": "none"},
        {"claim_id": "B", "label": "확인 필요", "claim_text": "마감일은 자료에 없어 확인이 필요하다.",
         "source_ids": [], "risk_field": "date"},
    ]
    result = validate(claims)
    assert result["verdict"] == "pass"
    assert result["failures"] == []
    assert result["risky_claims"] == []


def test_missing_source_ids_fails():
    claims = [
        {"claim_id": "A", "label": "관찰", "claim_text": "배경색은 회색이다.",
         "source_ids": [], "risk_field": "none"},
    ]
    result = validate(claims)
    assert result["verdict"] == "fail"
    assert any(f.startswith("missing_source_ids") for f in result["failures"])


def test_official_brand_claim_is_flagged():
    claims = [
        {"claim_id": "A", "label": "추론", "claim_text": "공식 브랜드 색상은 파란색이다.",
         "source_ids": ["SRC-1"], "risk_field": "brand"},
    ]
    result = validate(claims)
    assert result["verdict"] == "fail"
    assert any(r["risk"] == "official_brand_claim" for r in result["risky_claims"])


def test_invented_phone_placeholder_is_flagged():
    claims = [
        {"claim_id": "A", "label": "관찰", "claim_text": "전화번호는 02-0000-0000 이다.",
         "source_ids": ["SRC-1"], "risk_field": "contact"},
    ]
    result = validate(claims)
    assert any(r["risk"] == "invented_phone_placeholder" for r in result["risky_claims"])


def test_uncertain_label_exempts_risk():
    # '확인 필요' 라벨이면 위험 패턴이어도 환각으로 보지 않는다(불확실을 명시했으므로)
    claims = [
        {"claim_id": "A", "label": "확인 필요", "claim_text": "공식 색상은 별도 확인이 필요하다.",
         "source_ids": [], "risk_field": "brand"},
    ]
    result = validate(claims)
    assert result["risky_claims"] == []
