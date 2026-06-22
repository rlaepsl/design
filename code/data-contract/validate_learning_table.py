#!/usr/bin/env python3
"""
validate_learning_table.py — '학습표' 입력 계약 검증기 (결정론적)

학습표(learning table)는 분석 단계가 만들어 제작 단계로 넘기는 구조화된 입력이다.
각 행이 "어느 소스의 / 어느 영역을 / 어떻게 추출할지" 하나의 부품을 정의한다.
잘못된 행이 제작 단계로 들어가면 추출이 깨지므로, 단계 사이에서 이 계약을 먼저 검증한다.

검사:
  - 필수 컬럼 존재
  - part_id 비어있지 않음 + 중복 없음
  - 정규화 좌표 nx, ny, nw, nh 가 0~1 실수
  - recurse_flag 가 true/false
  - color_mode / text_handling 가 허용된 값
  - 영역이 경계를 벗어나지 않음 (nx+nw ≤ 1, ny+nh ≤ 1)

사용:
  python validate_learning_table.py --csv sample_learning_table.csv
  python validate_learning_table.py --csv sample_learning_table.csv --json

이 검증기/스키마는 공개용으로 작성한 것이며, 합성 샘플만 포함한다(회사/고객 데이터 없음).
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

REQUIRED_COLUMNS = [
    "part_id", "name", "category", "source_name", "norm_basis",
    "nx", "ny", "nw", "nh", "recurse_flag", "color_mode", "text_handling",
]
NORM_FIELDS = ["nx", "ny", "nw", "nh"]
COLOR_MODES = {"as_is", "light_on_dark"}
TEXT_HANDLING = {"include", "exclude"}
BOOLS = {"true", "false"}


def _num(value: str):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def validate_rows(rows: list[dict], columns: list[str]) -> dict:
    errors: list[str] = []

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in columns]
    if missing_cols:
        errors.append(f"missing_columns:{','.join(missing_cols)}")
        return {"verdict": "fail", "row_count": len(rows), "errors": errors}

    seen_ids: set[str] = set()
    for i, row in enumerate(rows, start=1):
        pid = (row.get("part_id") or "").strip()
        if not pid:
            errors.append(f"row{i}:empty_part_id")
        elif pid in seen_ids:
            errors.append(f"row{i}:duplicate_part_id:{pid}")
        else:
            seen_ids.add(pid)

        coords = {}
        for f in NORM_FIELDS:
            v = _num(row.get(f, ""))
            coords[f] = v
            if v is None:
                errors.append(f"row{i}:{f}_not_number:{row.get(f)}")
            elif not (0.0 <= v <= 1.0):
                errors.append(f"row{i}:{f}_out_of_range:{v}")

        if coords["nx"] is not None and coords["nw"] is not None and coords["nx"] + coords["nw"] > 1.0001:
            errors.append(f"row{i}:x_overflow:nx+nw>1")
        if coords["ny"] is not None and coords["nh"] is not None and coords["ny"] + coords["nh"] > 1.0001:
            errors.append(f"row{i}:y_overflow:ny+nh>1")

        if (row.get("recurse_flag") or "").strip().lower() not in BOOLS:
            errors.append(f"row{i}:recurse_flag_not_bool:{row.get('recurse_flag')}")
        if (row.get("color_mode") or "").strip() not in COLOR_MODES:
            errors.append(f"row{i}:invalid_color_mode:{row.get('color_mode')}")
        if (row.get("text_handling") or "").strip() not in TEXT_HANDLING:
            errors.append(f"row{i}:invalid_text_handling:{row.get('text_handling')}")

    return {
        "verdict": "pass" if not errors else "fail",
        "row_count": len(rows),
        "errors": errors,
    }


def load_csv(path: Path) -> tuple[list[dict], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        rows = list(reader)
        return rows, (reader.fieldnames or [])


def main() -> int:
    parser = argparse.ArgumentParser(description="학습표 입력 계약 검증기")
    parser.add_argument("--csv", required=True, help="학습표 CSV 경로")
    parser.add_argument("--json", action="store_true", help="JSON으로 출력")
    args = parser.parse_args()

    rows, columns = load_csv(Path(args.csv))
    result = validate_rows(rows, columns)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"verdict : {result['verdict']}")
        print(f"rows    : {result['row_count']}")
        for e in result["errors"]:
            print(f"  ERROR: {e}")
        if not result["errors"]:
            print("  (모든 행이 계약을 통과)")

    return 0 if result["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
