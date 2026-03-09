import math

from formula.core.orchestrator import classify_and_execute_formulas


def test_three_product_orchestrate_result_and_mismatch_explanation():
    formulas = {
        "CM_J": "P_J - C_J",
        "CM_NORM": "NORM(vector(CM_J))",
        "SAFE_X_MIN": "X0_J - r0*(CM_J/CM_NORM)",
        "SAFE_X_MAX": "X0_J + r0*(CM_J/CM_NORM)",
        "DECISION_X": "DECISION(x, size=3)",
        "DECISION_R": "DECISION(r)",
        "OBJ": "OBJECTIVE(r)",
        "BOUND_X": "BOUND(x,XMIN,XMAX)",
        "BOUND_R": "BOUND(r,0,None)",
        "CONSTRAINT_LP": "-DOT(vector(CM_J),x)+NORM(vector(CM_J))*r<=-F",
    }

    rows = [
        {"ID": 1, "P_J": 700.0, "C_J": 280.0, "F": 14000.0, "XMIN": 6.66, "XMAX": 26.66},
        {"ID": 2, "P_J": 1120.0, "C_J": 420.0, "F": 14000.0, "XMIN": 4.0, "XMAX": 16.0},
        {"ID": 3, "P_J": 4480.0, "C_J": 2240.0, "F": 14000.0, "XMIN": 1.25, "XMAX": 5.0},
    ]

    computed_rows, errors = classify_and_execute_formulas(formulas, rows, [1, 2, 3])
    assert errors == []

    # LP optimum from current orchestrator/model
    r0 = float(computed_rows[0]["r0"])
    x1 = float(computed_rows[0]["x1"])
    x2 = float(computed_rows[0]["x2"])
    x3 = float(computed_rows[0]["x3"])

    assert math.isclose(r0, 1.875, rel_tol=1e-9, abs_tol=1e-9)
    assert math.isclose(x1, 24.785, rel_tol=1e-9, abs_tol=1e-9)
    assert math.isclose(x2, 14.125, rel_tol=1e-9, abs_tol=1e-9)
    assert math.isclose(x3, 3.125, rel_tol=1e-9, abs_tol=1e-9)

    # Directional safe ranges as currently defined by formulas
    row1 = computed_rows[0]
    row2 = computed_rows[1]
    row3 = computed_rows[2]
    assert row1["SAFE_X_MIN"] <= row1["SAFE_X_MAX"]
    assert row2["SAFE_X_MIN"] <= row2["SAFE_X_MAX"]
    assert row3["SAFE_X_MIN"] <= row3["SAFE_X_MAX"]

    # "Matlab-style" symmetric half-width from your document is delta = r/sqrt(3)
    delta = r0 / math.sqrt(3.0)
    assert math.isclose(delta, 1.0825317547305484, rel_tol=1e-12, abs_tol=1e-12)
