"""Volume optimization service for API layer.

Keeps optimization execution out of main.py so API handlers stay thin.
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
from scipy.optimize import linprog

try:
    from formula.lp.parser import LPModelParser
    from formula.lp_matrix_builder_deterministic_complete import LPMatrixBuilder
    from formula.lp.solver import LPSolver
    from formula.excel_sheet_models import volume_case_dsl
    LP_RUNTIME_AVAILABLE = True
except Exception:
    LP_RUNTIME_AVAILABLE = False


def _no_safe_region(reason: str) -> Dict[str, Any]:
    return {
        "status": "NO_SAFE_REGION",
        "case": "volume",
        "reason": reason,
        "details": {},
        "suggestion": "Adjust input parameters",
    }


def _projection_factors(products: List[Dict[str, Any]]) -> List[float]:
    """Return Sheet2-style projection factors alpha_j = p_j / ||p||."""
    p_values = np.array([float(x["p"]) for x in products], dtype=float)
    p_norm = float(np.linalg.norm(p_values))
    if p_norm <= 1e-12:
        return [1.0 for _ in products]
    return [float(v / p_norm) for v in p_values]


def _build_product_output(
    products: List[Dict[str, Any]],
    centers: List[float],
    r_value: float,
) -> List[Dict[str, Any]]:
    """Build API response rows with both classic and projected ranges."""
    factors = _projection_factors(products)
    out_rows = []
    for i, product in enumerate(products):
        center = float(centers[i])
        alpha = float(factors[i])
        out_rows.append(
            {
                "itemName": product["itemName"],
                "itemCode": product["itemCode"],
                "center": center,
                "safeRange": {
                    "min": float(center - r_value),
                    "max": float(center + r_value),
                },
                # Sheet2 I/K-equivalent projected interval
                "projectedRange": {
                    "min": float(center - alpha * r_value),
                    "max": float(center + alpha * r_value),
                },
            }
        )
    return out_rows


def _solve_legacy(products: List[Dict[str, Any]], fixed_cost: float) -> Dict[str, Any]:
    p = np.array([x["p"] for x in products], dtype=float)
    c = np.array([x["c"] for x in products], dtype=float)
    xmin = np.array([x["xmin"] for x in products], dtype=float)
    xmax = np.array([x["xmax"] for x in products], dtype=float)

    d = p - c
    n = len(d)
    norm_d = np.linalg.norm(d)

    c_obj = np.zeros(n + 1)
    c_obj[-1] = -1

    A = [np.hstack([-d, norm_d])]
    b = [-fixed_cost]

    for j in range(n):
        for sign, bound in [(-1, xmin[j]), (1, xmax[j])]:
            row = np.zeros(n + 1)
            row[j], row[-1] = sign, 1
            A.append(row)
            b.append(sign * bound)

    res = linprog(
        c_obj,
        A_ub=A,
        b_ub=b,
        bounds=[(None, None)] * n + [(0, None)],
        method="highs",
    )

    if (not res.success) or (res.x is None) or (res.x[-1] <= 0):
        return _no_safe_region("No feasible safe volume region")

    x0, r = res.x[:-1], float(res.x[-1])

    return {
        "status": "OK",
        "case": "volume",
        "products": _build_product_output(products, [float(v) for v in x0], r),
    }


def optimize_volume(products: List[Dict[str, Any]], fixed_cost: float) -> Dict[str, Any]:
    """Solve volume optimization through DSL LP pipeline, with legacy fallback."""
    if not LP_RUNTIME_AVAILABLE:
        return _solve_legacy(products, fixed_cost)

    try:
        cm_j = [x["p"] - x["c"] for x in products]
        xmin = [x["xmin"] for x in products]
        xmax = [x["xmax"] for x in products]

        formulas = volume_case_dsl(cm_j, fixed_cost)
        if len(cm_j) == 1:
            scenario_context = {
                "CM_J": cm_j,
                "F": fixed_cost,
                "XMIN1": xmin[0],
                "XMAX1": xmax[0],
            }
        else:
            scenario_context = {
                "CM_J": cm_j,
                "F": fixed_cost,
                "XMIN": xmin,
                "XMAX": xmax,
            }

        parser = LPModelParser()
        lp_spec = parser.detect_lp_formulas(formulas)

        builder = LPMatrixBuilder(scenario_context)
        lp_matrices = builder.build_from_formulas(formulas, lp_spec)

        solver = LPSolver()
        result = solver.solve_from_matrices(lp_matrices, maximize=True)

        if not result.get("success") or not result.get("x"):
            return _no_safe_region("No feasible safe volume region")

        variables = lp_matrices.get("variables", [])
        x_pairs = []
        for idx, var_name in enumerate(variables):
            if var_name.startswith("x"):
                suffix = var_name[1:]
                order = int(suffix) if suffix.isdigit() else 0
                x_pairs.append((order, float(result["x"][idx])))

        x_pairs.sort(key=lambda item: item[0])
        x_values = [value for _, value in x_pairs]

        r_index = variables.index("r") if "r" in variables else -1
        r_value = float(result["x"][r_index]) if r_index >= 0 else 0.0

        if r_value <= 0:
            return _no_safe_region("No feasible safe volume region")

        return {
            "status": "OK",
            "case": "volume",
            "products": _build_product_output(products, x_values, r_value),
        }
    except Exception:
        return _solve_legacy(products, fixed_cost)
