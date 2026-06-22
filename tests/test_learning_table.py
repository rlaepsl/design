"""학습표 입력 계약 검증기 테스트."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code", "data-contract"))

from validate_learning_table import REQUIRED_COLUMNS, validate_rows  # noqa: E402


def _row(**overrides):
    base = {
        "part_id": "P-1", "name": "로고", "category": "logo",
        "source_name": "src_a", "norm_basis": "design_bounds",
        "nx": "0.1", "ny": "0.1", "nw": "0.2", "nh": "0.2",
        "recurse_flag": "false", "color_mode": "as_is", "text_handling": "include",
    }
    base.update(overrides)
    return base


def test_valid_rows_pass():
    result = validate_rows([_row()], REQUIRED_COLUMNS)
    assert result["verdict"] == "pass"
    assert result["errors"] == []


def test_missing_column_fails():
    cols = [c for c in REQUIRED_COLUMNS if c != "nx"]
    result = validate_rows([_row()], cols)
    assert result["verdict"] == "fail"
    assert any(e.startswith("missing_columns") for e in result["errors"])


def test_out_of_range_coordinate_fails():
    result = validate_rows([_row(nx="1.4")], REQUIRED_COLUMNS)
    assert result["verdict"] == "fail"
    assert any("nx_out_of_range" in e for e in result["errors"])


def test_region_overflow_fails():
    result = validate_rows([_row(nx="0.9", nw="0.5")], REQUIRED_COLUMNS)
    assert any("x_overflow" in e for e in result["errors"])


def test_duplicate_part_id_fails():
    result = validate_rows([_row(part_id="P-1"), _row(part_id="P-1")], REQUIRED_COLUMNS)
    assert any("duplicate_part_id" in e for e in result["errors"])


def test_invalid_enum_fails():
    result = validate_rows([_row(color_mode="rainbow", text_handling="maybe")], REQUIRED_COLUMNS)
    assert any("invalid_color_mode" in e for e in result["errors"])
    assert any("invalid_text_handling" in e for e in result["errors"])
