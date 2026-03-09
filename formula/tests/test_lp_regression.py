import math
import sys
from pathlib import Path

# Make both repo root and formula folder importable
THIS_FILE = Path(__file__).resolve()
FORMULA_DIR = THIS_FILE.parents[1]
REPO_ROOT = THIS_FILE.parents[2]

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(FORMULA_DIR))

from lp_solver import LPSolver
from formula.lp.solver import solve_lp_matrices


def test_lp_feasible_case_optimal():
    # maximize 3x + 2y
    # s.t. x + y <= 4, x <= 2, y <= 3, x,y >=0
    c = [3.0, 2.0]
    A_ub = [
        [1.0, 1.0],
        [1.0, 0.0],
        [0.0, 1.0],
    ]
    b_ub = [4.0, 2.0, 3.0]
    bounds = [(0.0, None), (0.0, None)]

    solver = LPSolver()
    res = solver.solve(c=c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, maximize=True)

    assert res["success"] is True
    assert res["x"] is not None
    assert math.isclose(res["x"][0], 2.0, rel_tol=1e-6, abs_tol=1e-6)
    assert math.isclose(res["x"][1], 2.0, rel_tol=1e-6, abs_tol=1e-6)
    assert math.isclose(res["fun"], 10.0, rel_tol=1e-6, abs_tol=1e-6)


def test_lp_infeasible_case_detected():
    # infeasible: x <= 0 and x >= 1
    c = [1.0]
    A_ub = [
        [1.0],
        [-1.0],
    ]
    b_ub = [0.0, -1.0]
    bounds = [(None, None)]

    solver = LPSolver()
    res = solver.solve(c=c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, maximize=False)

    assert res["success"] is False
    assert res["status"] in (2, 4, -1) or "infeasible" in str(res["message"]).lower()


def test_lp_unbounded_case_detected():
    # unbounded minimization: minimize -x subject to x>=1
    c = [-1.0]
    A_ub = [[-1.0]]
    b_ub = [-1.0]
    bounds = [(0.0, None)]

    solver = LPSolver()
    res = solver.solve(c=c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, maximize=False)

    assert res["success"] is False
    assert res["status"] in (3, 4, -1) or "unbounded" in str(res["message"]).lower()


def test_solver_engine_status_mapping_regression():
    matrices = {
        "c": [1.0],
        "A_ub": [[1.0], [-1.0]],
        "b_ub": [0.0, -1.0],
        "bounds": [(None, None)],
        "variables": ["x1"],
    }
    result = solve_lp_matrices(matrices, objective_type="minimize")
    assert result["status"] in {"infeasible", "failed"}
