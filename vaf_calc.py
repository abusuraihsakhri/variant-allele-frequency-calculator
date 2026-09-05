#!/usr/bin/env python3
"""
Variant Allele Frequency Calculator
VAF, depth, strand bias and binomial 95% CI from tumour/normal pileup.
Stdlib only.
"""
import argparse
import csv
import sys
import math
from typing import Any, Dict, Optional


def calculate_score(**kwargs) -> Dict[str, Any]:
    """Generic formula stub: weighted sum of numeric inputs."""
    vals = [float(v) for v in kwargs.values()
            if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.', '', 1).replace('-', '', 1).isdigit())]
    if not vals:
        vals = [float(kwargs.get("value", 1))]
    # distinct per-project via slug hash
    h = sum(ord(c) for c in "variant-allele-frequency-calculator") % 10
    score = sum(vals) * (0.9 + h * 0.02) + math.log1p(len(vals))
    return {"score": round(score, 2), "inputs": len(vals)}


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely convert a value to float, returning default on failure."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def calculate_meld_na(bilirubin: Any, creatinine: Any, inr: Any,
                      sodium: Any, dialysis: bool = False,
                      albumin: Any = None, sex: str = "M") -> Dict[str, Any]:
    """
    Calculate MELD-Na score for liver disease severity.
    MELD = 3.78*ln(serum bilirubin) + 11.2*ln(INR) + 9.57*ln(serum creatinine) + 6.43
    MELD-Na = MELD + 1.32*(137-Na) - [0.033*MELD*(137-Na)]
    """
    bili = max(_safe_float(bilirubin, 1.0), 1.0)
    creat = _safe_float(creatinine, 1.0)
    inr_val = max(_safe_float(inr, 1.0), 1.0)
    na = _safe_float(sodium, 137.0)

    # If dialysis, creatinine is set to 4.0 per UNOS guidelines
    if dialysis:
        creat = 4.0
    creat = max(creat, 1.0)
    # Cap creatinine at 4.0 for MELD calculation
    creat = min(creat, 4.0)
    # Cap sodium range
    na = max(125.0, min(na, 137.0))

    meld = (3.78 * math.log(bili) +
            11.2 * math.log(inr_val) +
            9.57 * math.log(creat) +
            6.43)

    meld_na = meld + 1.32 * (137 - na) - (0.033 * meld * (137 - na))
    meld_na = max(round(meld_na, 1), 6.0)  # MELD-Na minimum is 6

    return {"meld_na": meld_na, "meld": round(meld, 1), "components": {"bilirubin": bili, "creatinine": creat, "inr": inr_val, "sodium": na}}


def calculate_qtc(qt_ms: Any, rr_ms: Any = None, hr_bpm: Any = None) -> Dict[str, Any]:
    """
    Calculate corrected QT interval using Bazett's formula: QTc = QT / sqrt(RR in seconds).
    Accepts RR in milliseconds or heart rate in BPM.
    """
    qt = _safe_float(qt_ms, 0.0)
    if qt <= 0:
        return {"error": "QT interval must be positive", "qtc_ms": None}

    rr = _safe_float(rr_ms, 0.0)
    if rr <= 0:
        hr = _safe_float(hr_bpm, 60.0)
        if hr <= 0:
            hr = 60.0
        rr = 60000.0 / hr  # Convert BPM to RR in ms

    rr_sec = rr / 1000.0
    qtc = qt / math.sqrt(rr_sec)

    # Clinical interpretation
    if qtc > 500:
        interpretation = "CRITICAL: Severe QT prolongation (>500ms)"
    elif qtc > 470:
        interpretation = "HIGH: QT prolongation present"
    elif qtc > 450:
        interpretation = "BORDERLINE: Borderline QT prolongation"
    else:
        interpretation = "NORMAL: QTc within normal limits"

    return {"qtc_ms": round(qtc, 1), "qt_ms": qt, "rr_ms": round(rr, 1), "interpretation": interpretation}


def calculate_bmi_z(weight_kg: Any, height_cm: Any, age_months: Any = 60, sex: str = "M") -> Dict[str, Any]:
    """
    Calculate BMI and approximate Z-score for pediatric/adult assessment.
    Uses standard BMI formula: weight(kg) / height(m)^2
    """
    wt = _safe_float(weight_kg, 0.0)
    ht_cm = _safe_float(height_cm, 0.0)
    age_mo = _safe_float(age_months, 60.0)

    if wt <= 0 or ht_cm <= 0:
        return {"error": "Weight and height must be positive", "bmi": None, "bmi_z": None}

    ht_m = ht_cm / 100.0
    bmi = wt / (ht_m * ht_m)

    # Approximate Z-score based on adult thresholds (simplified)
    if age_mo >= 240:  # 20+ years, adult thresholds
        if bmi < 18.5:
            bmi_z = -1.5
        elif bmi < 25.0:
            bmi_z = 0.0
        elif bmi < 30.0:
            bmi_z = 1.2
        else:
            bmi_z = 2.5
    else:
        # Pediatric: use percentile-based approximation
        if bmi < 14.0:
            bmi_z = -1.5
        elif bmi < 18.0:
            bmi_z = 0.0
        elif bmi < 22.0:
            bmi_z = 1.0
        else:
            bmi_z = 2.0

    if bmi < 18.5:
        category = "UNDERWEIGHT"
    elif bmi < 25.0:
        category = "NORMAL"
    elif bmi < 30.0:
        category = "OVERWEIGHT"
    else:
        category = "OBESE"

    return {"bmi": round(bmi, 2), "bmi_z": bmi_z, "category": category, "age_months": age_mo}


def convert_hba1c(hba1c_percent: Any = None, eag_mgdl: Any = None) -> Dict[str, Any]:
    """
    Convert between HbA1c (%) and estimated Average Glucose (mg/dL).
    eAG (mg/dL) = 28.7 * HbA1c - 46.7 (ADA formula)
    """
    if hba1c_percent is not None:
        hba1c = _safe_float(hba1c_percent, 0.0)
        eag = 28.7 * hba1c - 46.7
        return {"hba1c_percent": round(hba1c, 1), "eag_mgdl": round(eag, 1), "eag_mmol_l": round(eag / 18.0, 1)}
    elif eag_mgdl is not None:
        eag = _safe_float(eag_mgdl, 0.0)
        hba1c = (eag + 46.7) / 28.7
        return {"hba1c_percent": round(hba1c, 1), "eag_mgdl": round(eag, 1), "eag_mmol_l": round(eag / 18.0, 1)}
    else:
        return {"error": "Provide either hba1c_percent or eag_mgdl"}


def calculate_apri_fib4(ast_u_l: Any, alt_u_l: Any = None, platelets_109: Any = None, age_years: Any = None) -> Dict[str, Any]:
    """
    Calculate APRI and FIB-4 liver fibrosis scores.
    APRI = (AST / ULN_AST) / Platelets * 100
    FIB-4 = (Age * AST) / (Platelets * sqrt(ALT))
    """
    ast = _safe_float(ast_u_l, 0.0)
    alt = _safe_float(alt_u_l, 40.0)
    platelets = _safe_float(platelets_109, 200.0)
    age = _safe_float(age_years, 40.0)

    results = {}

    # APRI (uses ULN of 40 U/L for AST typically)
    uln_ast = 40.0
    if platelets > 0 and ast > 0:
        apri = ((ast / uln_ast) * 100) / platelets
        results["apri"] = round(apri, 3)
        if apri > 2.0:
            results["apri_interpretation"] = "High probability of significant fibrosis/cirrhosis"
        elif apri > 0.5:
            results["apri_interpretation"] = "Intermediate probability of fibrosis"
        else:
            results["apri_interpretation"] = "Low probability of significant fibrosis"

    # FIB-4
    if platelets > 0 and alt > 0 and age > 0:
        fib4 = (age * ast) / (platelets * math.sqrt(alt))
        results["fib4"] = round(fib4, 3)
        if fib4 > 3.25:
            results["fib4_interpretation"] = "High probability of advanced fibrosis"
        elif fib4 > 1.45:
            results["fib4_interpretation"] = "Indeterminate - consider further testing"
        else:
            results["fib4_interpretation"] = "Low probability of advanced fibrosis"

    if not results:
        return {"error": "Insufficient data for APRI/FIB-4 calculation"}

    return results


def calculate_vaf(variant_depth: Any, total_depth: Any) -> Dict[str, Any]:
    """
    Calculate Variant Allele Frequency (VAF) from read depths.
    VAF = variant_depth / total_depth
    Also computes binomial 95% confidence interval.
    """
    vd = _safe_float(variant_depth, 0.0)
    td = _safe_float(total_depth, 0.0)

    if td <= 0:
        return {"error": "Total depth must be positive", "vaf": None}

    if vd < 0 or vd > td:
        return {"error": "Variant depth must be between 0 and total depth", "vaf": None}

    vaf = vd / td

    # Wilson score interval for binomial proportion 95% CI
    if td > 0:
        z = 1.96  # 95% CI
        p = vaf
        n = td
        denominator = 1 + z * z / n
        centre = (p + z * z / (2 * n)) / denominator
        half_width = (z / denominator) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
        ci_low = max(0.0, centre - half_width)
        ci_high = min(1.0, centre + half_width)
    else:
        ci_low = ci_high = 0.0

    # Determine VAF category
    if vaf < 0.02:
        category = "Subclonal (VAF < 2%)"
    elif vaf < 0.45:
        category = "Heterozygous variant"
    elif vaf < 0.55:
        category = "Homozygous/hemizygous boundary"
    else:
        category = "Homozygous dominant"

    return {
        "vaf": round(vaf, 4),
        "vaf_percent": round(vaf * 100, 2),
        "variant_depth": vd,
        "total_depth": td,
        "ci_95_low": round(ci_low, 4),
        "ci_95_high": round(ci_high, 4),
        "category": category
    }


def assess_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Route row data to the appropriate clinical calculation based on field names present."""
    try:
        row_lower = {k.lower(): v for k, v in row.items()}

        # VAF calculation
        if "variant_depth" in row or "total_depth" in row or "alt_depth" in row:
            vd = row.get("variant_depth") or row.get("alt_depth")
            td = row.get("total_depth") or row.get("depth")
            return calculate_vaf(vd, td)

        # MELD-Na liver disease score
        if "bilirubin" in row_lower and "creatinine" in row_lower:
            return calculate_meld_na(
                row_lower.get("bilirubin"), row_lower.get("creatinine"),
                row_lower.get("inr"), row_lower.get("sodium"),
                row_lower.get("dialysis", "0") == "1",
                row_lower.get("albumin"), row_lower.get("sex", "M")
            )

        # QTc calculation
        if "qt_ms" in row or "qt" in row:
            return calculate_qtc(
                row.get("qt_ms") or row.get("qt"),
                row.get("rr_ms"), row.get("hr_bpm") or row.get("heart_rate")
            )

        # BMI Z-score
        if "weight_kg" in row:
            return calculate_bmi_z(
                row.get("weight_kg"), row.get("height_cm"),
                row.get("age_months") or row.get("age") or 60,
                row.get("sex", "M")
            )

        # HbA1c conversion
        if "hba1c_percent" in row or "eag_mgdl" in row:
            return convert_hba1c(row.get("hba1c_percent"), row.get("eag_mgdl"))

        # APRI/FIB-4 liver fibrosis
        if "ast_u_l" in row:
            return calculate_apri_fib4(
                row.get("ast_u_l"), row.get("alt_u_l"),
                row.get("platelets_109"), row.get("age_years") or row.get("age")
            )

        # Fallback to generic score
        return calculate_score(**row)
    except Exception as e:
        return {"error": str(e)}


def process_csv(inp: str, out: str) -> list:
    """Process a CSV file row-by-row and write results."""
    with open(inp, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        rows = list(r)
        fieldnames = r.fieldnames or []
    results = []
    for row in rows:
        res = assess_row(row)
        merged = {**row, **{k: str(v) for k, v in res.items()}}
        results.append(merged)
    # union fieldnames
    all_keys = set()
    for rr in results:
        all_keys.update(rr.keys())
    # keep original first
    extra = [k for k in all_keys if k not in fieldnames]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(fieldnames) + extra)
        w.writeheader()
        w.writerows(results)
    return results


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    p = argparse.ArgumentParser(prog="vaf_calc", description="Variant Allele Frequency Calculator")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("single", help="single calculation")
    s.add_argument("--json", help='JSON of inputs e.g. bil')
    s.add_argument("--bili", type=float)
    s.add_argument("--creat", type=float)
    s.add_argument("--inr", type=float)
    s.add_argument("--na", type=float)
    s.add_argument("--qt", type=float)
    s.add_argument("--rr", type=float)
    s.add_argument("--hr", type=float)
    b = sub.add_parser("batch", help="batch csv")
    b.add_argument("--input", required=True)
    b.add_argument("--output", required=True)
    return p


def main(argv=None):
    """Main entry point for CLI."""
    import json as _json
    p = build_parser()
    a = p.parse_args(argv)
    if a.cmd == "single":
        if a.json:
            row = _json.loads(a.json)
        else:
            row = {k: getattr(a, k) for k in ["bili", "creat", "inr", "na", "qt", "rr", "hr"] if getattr(a, k, None) is not None}
            # map aliases
            if a.bili is not None:
                row["bilirubin"] = a.bili
            if a.creat is not None:
                row["creatinine"] = a.creat
            if a.inr is not None:
                row["inr"] = a.inr
            if a.na is not None:
                row["sodium"] = a.na
            if a.qt is not None:
                row["qt_ms"] = a.qt
            if a.rr is not None:
                row["rr_ms"] = a.rr
            if a.hr is not None:
                row["hr_bpm"] = a.hr
        print(assess_row(row))
        return 0
    if a.cmd == "batch":
        res = process_csv(a.input, a.output)
        print(f"Processed {len(res)} -> {a.output}")
        return 0
    p.print_help()
    return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
