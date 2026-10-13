"""Regression checks for VAF count handling and Wilson intervals."""
import math

from vaf_calc import calculate_vaf, assess_row, _safe_float
from agents.base import AuditTrail


def test_vaf_wilson_reference():
    result = calculate_vaf(30, 100)
    assert math.isclose(result["vaf"], 0.3)
    assert math.isclose(result["ci_95_low"], 0.218949, abs_tol=2e-6)
    assert math.isclose(result["ci_95_high"], 0.395849, abs_tol=2e-6)


def test_vaf_rejects_invalid_counts():
    for v, total in [(-1, 10), (1.5, 10), (11, 10), (1, 0),
                     ("nan", 10), ("inf", 10), (1, "inf"),
                     (True, 10), (1, 2**53)]:
        assert "error" in calculate_vaf(v, total)


def test_vaf_small_fraction_remains_nonzero():
    result = calculate_vaf(1, 10_000_000)
    assert result["vaf"] == 1e-7
    assert result["vaf_percent"] > 0


def test_vaf_zero_and_case_insensitive_aliases():
    assert assess_row({"ALT_DEPTH": "0", "DEPTH": "100"})["vaf"] == 0
    assert assess_row({"variant_depth": 0, "total_depth": 100})["vaf"] == 0


def test_safe_float_rejects_nonfinite():
    assert _safe_float(float("inf"), 5.0) == 5.0
    assert _safe_float("nan", 7.0) == 7.0


def test_audit_detects_hash_tampering():
    trail = AuditTrail(secret_key="test-key")
    trail.log("actor", "worker", "event", {"status": "SUCCESS"})
    trail.log("actor", "worker", "event", {"status": "SUCCESS"})
    assert trail.verify_integrity()
    snapshot = trail.get_trail()
    snapshot[0]["current_hash"] = "external mutation"
    assert trail.verify_integrity()
    trail.logs[1]["current_hash"] = "0" * 64
    assert not trail.verify_integrity()
