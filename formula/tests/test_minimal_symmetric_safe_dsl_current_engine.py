import math

from formula.core.orchestrator import classify_and_execute_formulas


def test_minimal_symmetric_safe_dsl_current_engine():
    formulas = {
        "CM_J": "P_J - C_J",
        "CM_NORM": "NORM(vector(CM_J))",
        "DECISION_X": "DECISION(x, size=3)",
        "DECISION_R": "DECISION(r)",
        "OBJ": "OBJECTIVE(r)",
        "BOUND_X": "BOUND(x,XMIN,XMAX)",
        "BOUND_R": "BOUND(r,0,None)",
        "CONSTRAINT_LP": "-DOT(vector(CM_J),x)+NORM(vector(CM_J))*r<=-F",
        # Minimal symmetric safe-range formula that works in current phase splitter:
        # `+ 0*CM_NORM` forces Phase-3 dependency on scenario target `CM_NORM`.
        "SAFE_X_MIN": "X0_J - (r0/1.7320508075688772) + 0*CM_NORM",
        "SAFE_X_MAX": "X0_J + (r0/1.7320508075688772) + 0*CM_NORM",
    }

    rows = [
        {"ID": 1, "P_J": 700.0, "C_J": 280.0, "F": 14000.0, "XMIN": 6.66, "XMAX": 26.66},
        {"ID": 2, "P_J": 1120.0, "C_J": 420.0, "F": 14000.0, "XMIN": 4.0, "XMAX": 16.0},
        {"ID": 3, "P_J": 4480.0, "C_J": 2240.0, "F": 14000.0, "XMIN": 1.25, "XMAX": 5.0},
    ]

    computed_rows, errors = classify_and_execute_formulas(formulas, rows, [1, 2, 3])
    assert errors == []

    r0 = float(computed_rows[0]["r0"])
    delta = r0 / math.sqrt(3.0)

    # Current LP model gives r*=1.875 for this case.
    assert math.isclose(r0, 1.875, rel_tol=1e-9, abs_tol=1e-9)

    for row in computed_rows:
        x0 = float(row["X0_J"])
        safe_min = float(row["SAFE_X_MIN"])
        safe_max = float(row["SAFE_X_MAX"])

        assert math.isclose(safe_min, x0 - delta, rel_tol=1e-9, abs_tol=1e-9)
        assert math.isclose(safe_max, x0 + delta, rel_tol=1e-9, abs_tol=1e-9)

    # For row3 center 3.125, the well-known symmetric range is ~[2.04, 4.21]
    row3 = computed_rows[2]
    assert round(float(row3["SAFE_X_MIN"]), 2) == 2.04
    assert round(float(row3["SAFE_X_MAX"]), 2) == 4.21
