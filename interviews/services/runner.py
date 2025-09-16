from typing import Dict, Any
import pandas as pd
import io

def run_checks(spec: Dict[str, Any], candidate_answer: Any) -> Dict[str, Any]:
    """
    Deterministic checks for practical questions.
    - spec: may contain dataset name, expected columns, task description
    - candidate_answer: could be JSON with output table or uploaded CSV contents
    This is a stub — extend with your domain logic (openpyxl, duckdb, pandas checks).
    """
    # Example simple check: non-empty and has expected keys
    passed = False
    checks = []
    try:
        if candidate_answer:
            # If candidate_answer contains CSV text
            if isinstance(candidate_answer, str) and '\n' in candidate_answer:
                df = pd.read_csv(io.StringIO(candidate_answer))
                checks.append({"name":"rows_present","passed": len(df)>0, "rows": len(df)})
                passed = len(df)>0
            else:
                # generic presence check
                passed = True
                checks.append({"name":"non_empty_submission","passed": True})
    except Exception as e:
        checks.append({"name":"exception","passed": False, "error": str(e)})
        passed = False

    return {
        "passed": passed,
        "checks": checks,
        "score_runner": 100.0 if passed else 0.0,
    }
