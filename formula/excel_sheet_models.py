"""
Excel Sheet1/Sheet2 exact LP models encoded as DSL test fixtures.

These fixtures are used for regression tests against the original workbook
structure (objective, constraints row layout, and expected solution behavior).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass(frozen=True)
class ExcelDSLModel:
    name: str
    formulas: Dict[str, str]
    scenario_context: Dict[str, Any]
    expected_variables: List[str]
    expected_c: List[float]
    expected_A_ub: List[List[float]]
    expected_b_ub: List[float]
    expected_solution: Dict[str, float]
    objective_constant: float = 0.0


def sheet1_exact_model() -> ExcelDSLModel:
    """
    Exact LP abstraction from Excel Sheet1.

    Source workbook formulas (Sheet1):
    - Objective cell: (p-c)*x0 - F - r*(p-c)
    - Constraints:
      x0 - r >= xmin
      x0 + r <= xmax
    """
    p = 15.0
    c = 7.0
    f_cost = 1000.0
    xmin = 0.0
    xmax = 500.0
    cm = p - c

    formulas = {
        "DECISION_X": "DECISION(x1)",
        "DECISION_R": "DECISION(r)",
        # Keep `+ -` form to match current deterministic parser behavior.
        "OBJ": f"OBJECTIVE({cm}*x1 + -{cm}*r)",
        "BOUND_R": "BOUND(r,0,None)",
        "C_XMIN": "-x1 + r <= -xmin",
        "C_XMAX": "x1 + r <= xmax",
    }
    scenario_context = {
        "xmin": xmin,
        "xmax": xmax,
    }

    expected_solution = {
        "x1": 500.0,
        "r": 0.0,
        "excel_objective": cm * 500.0 - f_cost - cm * 0.0,
    }

    return ExcelDSLModel(
        name="sheet1_exact",
        formulas=formulas,
        scenario_context=scenario_context,
        expected_variables=["x1", "r"],
        expected_c=[cm, -cm],
        expected_A_ub=[
            [-1.0, 1.0],
            [1.0, 1.0],
        ],
        expected_b_ub=[-xmin, xmax],
        expected_solution=expected_solution,
        objective_constant=-f_cost,
    )


def sheet2_exact_model() -> ExcelDSLModel:
    """
    Exact LP abstraction from Excel Sheet2.

    Source workbook formulas (Sheet2):
    - Objective cell:
      (p1-c1)*x1 + (p2-c2)*x2 - F - r*sqrt((p1-c1)^2 + (p2-c2)^2)
    - Constraints:
      x1 - r*(p1/sqrt(p1^2+p2^2)) >= xmin1
      x1 + r*(p1/sqrt(p1^2+p2^2)) <= xmax1
      x2 - r*(p2/sqrt(p1^2+p2^2)) >= xmin2
      x2 + r*(p2/sqrt(p1^2+p2^2)) <= xmax2
    """
    p1, c1 = 15.0, 7.0
    p2, c2 = 17.0, 11.0
    f_cost = 2700.0
    xmin1, xmax1 = 0.0, 3800.0
    xmin2, xmax2 = 0.0, 7800.0

    cm1 = p1 - c1
    cm2 = p2 - c2
    cm_norm = math.sqrt(cm1 ** 2 + cm2 ** 2)
    p_norm = math.sqrt(p1 ** 2 + p2 ** 2)
    alpha = p1 / p_norm
    beta = p2 / p_norm

    formulas = {
        "DECISION_X": "DECISION(x,size=2)",
        "DECISION_R": "DECISION(r)",
        "OBJ": f"OBJECTIVE({cm1}*x1 + {cm2}*x2 - {cm_norm}*r)",
        "BOUND_R": "BOUND(r,0,None)",
        "C_MAIN": f"-{cm1}*x1 - {cm2}*x2 + {cm_norm}*r <= -{f_cost}",
        "C_X1MIN": f"-x1 + {alpha}*r <= -{xmin1}",
        "C_X1MAX": f"x1 + {alpha}*r <= {xmax1}",
        "C_X2MIN": f"-x2 + {beta}*r <= -{xmin2}",
        "C_X2MAX": f"x2 + {beta}*r <= {xmax2}",
    }

    expected_solution = {
        "x1": xmax1,
        "x2": xmax2,
        "r": 0.0,
        "excel_objective": cm1 * xmax1 + cm2 * xmax2 - f_cost,
    }

    return ExcelDSLModel(
        name="sheet2_exact",
        formulas=formulas,
        scenario_context={},
        expected_variables=["x1", "x2", "r"],
        expected_c=[cm1, cm2, -cm_norm],
        expected_A_ub=[
            [-cm1, -cm2, cm_norm],
            [-1.0, 0.0, alpha],
            [1.0, 0.0, alpha],
            [0.0, -1.0, beta],
            [0.0, 1.0, beta],
        ],
        expected_b_ub=[-f_cost, -xmin1, xmax1, -xmin2, xmax2],
        expected_solution=expected_solution,
        objective_constant=-f_cost,
    )


def volume_case_dsl(cm_j: List[float], fixed_cost: float) -> Dict[str, str]:
    """
    Runtime DSL model used by /optimize volume.
    """
    size = len(cm_j)
    if size == 1:
        cm = float(cm_j[0])
        cm_norm = abs(cm)
        return {
            "DECISION_X": "DECISION(x1)",
            "DECISION_R": "DECISION(r)",
            "OBJ": "OBJECTIVE(1*r)",
            "BOUND_R": "BOUND(r,0,None)",
            "CONSTRAINT_LP": f"-{cm}*x1 + {cm_norm}*r <= -F",
            "C_XMIN": "-x1 + r <= -XMIN1",
            "C_XMAX": "x1 + r <= XMAX1",
        }

    return {
        "DECISION_X": f"DECISION(x,size={size})",
        "DECISION_R": "DECISION(r)",
        "OBJ": "OBJECTIVE(1*r)",
        "BOUND_R": "BOUND(r,0,None)",
        "CONSTRAINT_LP": "-DOT(vector(CM_J),x)+NORM(vector(CM_J))*r<=-F",
    }

