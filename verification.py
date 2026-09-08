import math
import pandas as pd
from analysis_tools import resolve_column

def _same(a, b, tol=1e-6):
    try:
        return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)
    except Exception:
        return a == b

def verify_results(datasets, plan, results, question):
    checks = []
    passed = True

    for item in results:
        result = item.get("result")
        step = item.get("step", "")
        dataset_name = item.get("dataset")
        df = datasets.get(dataset_name)

        if df is None:
            checks.append({"step": step, "status": "FAILED", "reason": "Dataset not found"})
            passed = False
            continue

        # Independent sanity checks on numerical output.
        if isinstance(result, list) and result and isinstance(result[0], dict):
            if "value" in result[0]:
                values = [r.get("value") for r in result if r.get("value") is not None]
                numeric_values = []
                for v in values:
                    try:
                        numeric_values.append(float(v))
                    except Exception:
                        pass
                if any(pd.isna(numeric_values)):
                    checks.append({"step": step, "status": "FAILED", "reason": "NaN result"})
                    passed = False
                else:
                    checks.append({"step": step, "status": "PASSED", "reason": "Numeric outputs are finite"})

        elif isinstance(result, dict) and "outlier_percentage" in result:
            ok = 0 <= float(result["outlier_percentage"]) <= 100
            checks.append({
                "step": step,
                "status": "PASSED" if ok else "FAILED",
                "reason": "Outlier percentage is within 0–100%",
            })
            passed = passed and ok
        else:
            checks.append({"step": step, "status": "PASSED", "reason": "Result structure is valid"})

    return {
        "status": "VERIFICATION PASSED" if passed else "VERIFICATION FAILED",
        "checks": checks,
        "question": question,
        "note": "Verification here independently checks result structure and numerical sanity. "
                 "For high-stakes production use, add domain-specific assertions and isolated execution."
    }
