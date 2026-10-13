"""
Focused tests for core VAF calculation and clinical scoring functions.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import math
import pytest
from vaf_calc import (
    calculate_vaf,
    calculate_meld_na,
    calculate_qtc,
    calculate_bmi_z,
    convert_hba1c,
    calculate_apri_fib4,
    calculate_score,
    assess_row,
    _safe_float,
)


class TestSafeFloat:
    def test_valid_float(self):
        assert _safe_float("3.14") == 3.14
        assert _safe_float(42) == 42.0
        assert _safe_float(3.14) == 3.14

    def test_none_returns_default(self):
        assert _safe_float(None) == 0.0
        assert _safe_float(None, 5.0) == 5.0

    def test_invalid_returns_default(self):
        assert _safe_float("not_a_number") == 0.0
        assert _safe_float("", 1.0) == 1.0


class TestCalculateVAF:
    def test_basic_vaf(self):
        result = calculate_vaf(30, 100)
        assert result["vaf"] == 0.3
        assert result["vaf_percent"] == 30.0
        assert result["variant_depth"] == 30.0
        assert result["total_depth"] == 100.0

    def test_vaf_with_confidence_interval(self):
        result = calculate_vaf(50, 200)
        assert "ci_95_low" in result
        assert "ci_95_high" in result
        assert result["ci_95_low"] < result["vaf"]
        assert result["ci_95_high"] > result["vaf"]

    def test_vaf_zero_variant(self):
        result = calculate_vaf(0, 100)
        assert result["vaf"] == 0.0

    def test_vaf_all_variant(self):
        result = calculate_vaf(100, 100)
        assert result["vaf"] == 1.0

    def test_vaf_invalid_total_depth(self):
        result = calculate_vaf(10, 0)
        assert "error" in result

    def test_vaf_negative_variant(self):
        result = calculate_vaf(-5, 100)
        assert "error" in result

    def test_vaf_variant_exceeds_total(self):
        result = calculate_vaf(150, 100)
        assert "error" in result

    def test_vaf_category_subclonal(self):
        result = calculate_vaf(1, 100)
        assert result["category"] == "VAF below 2%"

    def test_vaf_category_heterozygous(self):
        result = calculate_vaf(40, 100)
        assert result["category"] == "VAF 2% to below 45%"

    def test_vaf_category_homozygous(self):
        result = calculate_vaf(80, 100)
        assert result["category"] == "VAF 55% or above"


class TestCalculateMELDNa:
    def test_basic_meld(self):
        result = calculate_meld_na(1.0, 1.0, 1.0, 137.0)
        assert "meld_na" in result
        assert "meld" in result
        assert result["meld_na"] >= 6.0

    def test_meld_with_dialysis(self):
        result = calculate_meld_na(2.0, 1.0, 1.2, 135.0, dialysis=True)
        assert result["components"]["creatinine"] == 4.0

    def test_meld_high_values(self):
        result = calculate_meld_na(15.0, 5.0, 3.0, 125.0)
        assert result["meld_na"] > 20

    def test_meld_caps_creatinine(self):
        result = calculate_meld_na(1.0, 10.0, 1.0, 137.0)
        assert result["components"]["creatinine"] == 4.0


class TestCalculateQTc:
    def test_basic_qtc(self):
        result = calculate_qtc(400, rr_ms=1000)
        assert "qtc_ms" in result
        assert result["qtc_ms"] > 0

    def test_qtc_from_heart_rate(self):
        result = calculate_qtc(400, hr_bpm=60)
        assert "qtc_ms" in result
        assert result["qtc_ms"] > 0

    def test_qtc_critical_prolongation(self):
        result = calculate_qtc(550, rr_ms=1000)
        assert "CRITICAL" in result["interpretation"]

    def test_qtc_normal(self):
        result = calculate_qtc(380, rr_ms=1000)
        assert "NORMAL" in result["interpretation"]

    def test_qtc_invalid_qt(self):
        result = calculate_qtc(0, rr_ms=1000)
        assert "error" in result

    def test_qtc_negative_qt(self):
        result = calculate_qtc(-100, rr_ms=1000)
        assert "error" in result


class TestCalculateBMIZ:
    def test_basic_bmi(self):
        result = calculate_bmi_z(70, 175, age_months=240)
        assert "bmi" in result
        assert "bmi_z" in result
        assert "category" in result

    def test_bmi_normal(self):
        result = calculate_bmi_z(70, 175, age_months=240)
        assert result["category"] == "NORMAL"

    def test_bmi_overweight(self):
        result = calculate_bmi_z(85, 175, age_months=240)
        assert result["category"] == "OVERWEIGHT"

    def test_bmi_obese(self):
        result = calculate_bmi_z(110, 175, age_months=240)
        assert result["category"] == "OBESE"

    def test_bmi_underweight(self):
        result = calculate_bmi_z(50, 175, age_months=240)
        assert result["category"] == "UNDERWEIGHT"

    def test_bmi_invalid_input(self):
        result = calculate_bmi_z(0, 175)
        assert "error" in result

    def test_bmi_negative_height(self):
        result = calculate_bmi_z(70, -10)
        assert "error" in result


class TestConvertHbA1c:
    def test_hba1c_to_eag(self):
        result = convert_hba1c(hba1c_percent=7.0)
        assert result["hba1c_percent"] == 7.0
        expected_eag = 28.7 * 7.0 - 46.7
        assert abs(result["eag_mgdl"] - round(expected_eag, 1)) < 0.1

    def test_eag_to_hba1c(self):
        result = convert_hba1c(eag_mgdl=154.0)
        assert "hba1c_percent" in result
        assert "eag_mgdl" in result

    def test_no_input(self):
        result = convert_hba1c()
        assert "error" in result

    def test_mmol_conversion(self):
        result = convert_hba1c(hba1c_percent=7.0)
        assert "eag_mmol_l" in result


class TestCalculateAPRIFIB4:
    def test_basic_apri(self):
        result = calculate_apri_fib4(40, 40, 200, 40)
        assert "apri" in result
        assert "apri_interpretation" in result

    def test_basic_fib4(self):
        result = calculate_apri_fib4(40, 40, 200, 40)
        assert "fib4" in result
        assert "fib4_interpretation" in result

    def test_high_ast_apri(self):
        result = calculate_apri_fib4(200, 40, 100, 50)
        assert result["apri"] > 1.0

    def test_zero_platelets(self):
        result = calculate_apri_fib4(40, 40, 0, 40)
        assert "error" in result or "fib4" not in result


class TestAssessRow:
    def test_vaf_row(self):
        result = assess_row({"variant_depth": 30, "total_depth": 100})
        assert "vaf" in result

    def test_meld_row(self):
        result = assess_row({"bilirubin": 2.0, "creatinine": 1.5, "inr": 1.2})
        assert "meld_na" in result

    def test_qtc_row(self):
        result = assess_row({"qt_ms": 400, "rr_ms": 1000})
        assert "qtc_ms" in result

    def test_bmi_row(self):
        result = assess_row({"weight_kg": 70, "height_cm": 175})
        assert "bmi" in result

    def test_hba1c_row(self):
        result = assess_row({"hba1c_percent": 7.0})
        assert "eag_mgdl" in result

    def test_apri_row(self):
        result = assess_row({"ast_u_l": 40, "alt_u_l": 40, "platelets_109": 200, "age_years": 40})
        assert "apri" in result

    def test_generic_row(self):
        result = assess_row({"value": 10})
        assert "score" in result

    def test_empty_row(self):
        result = assess_row({})
        assert isinstance(result, dict)


class TestCalculateScore:
    def test_basic_score(self):
        result = calculate_score(value=10, qty=2)
        assert "score" in result
        assert "inputs" in result
        assert result["inputs"] >= 1

    def test_no_numeric_values(self):
        result = calculate_score(name="test")
        assert "score" in result
        assert result["inputs"] == 1

    def test_multiple_values(self):
        result = calculate_score(a=1, b=2, c=3)
        assert result["inputs"] == 3
