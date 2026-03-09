import math
import sys
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
FORMULA_DIR = THIS_FILE.parents[1]
REPO_ROOT = THIS_FILE.parents[2]

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(FORMULA_DIR))

from formula.core import volume_optimizer as vo


def test_optimizer_sheet2_fixed_xr_matches_excel(monkeypatch):
    """
    Validate that optimizer response projection logic matches Excel Sheet2 formulas
    for a fixed point x1=x2=1900, r=1900.
    """

    class DummySolver:
        def solve_from_matrices(self, lp_matrices, maximize=True):
            # Force the exact point requested by the user.
            # Expected variable order from DSL for 2 products: [x1, x2, r]
            return {
                "success": True,
                "x": [1900.0, 1900.0, 1900.0],
                "fun": None,
                "message": "forced test point",
            }

    # Ensure optimizer uses LP path and our forced solver output.
    monkeypatch.setattr(vo, "LP_RUNTIME_AVAILABLE", True)
    monkeypatch.setattr(vo, "LPSolver", DummySolver)

    products = [
        {
            "itemName": "P1",
            "itemCode": "P1",
            "p": 15.0,
            "c": 7.0,
            "xmin": 0.0,
            "xmax": 3800.0,
        },
        {
            "itemName": "P2",
            "itemCode": "P2",
            "p": 17.0,
            "c": 11.0,
            "xmin": 0.0,
            "xmax": 7800.0,
        },
    ]

    result = vo.optimize_volume(products, fixed_cost=2700.0)

    assert result["status"] == "OK"
    assert result["case"] == "volume"
    assert len(result["products"]) == 2

    r = 1900.0
    p_norm = math.sqrt(15.0 ** 2 + 17.0 ** 2)

    expected = {
        "P1": {
            "xmin": 1900.0 - r * (15.0 / p_norm),
            "xmax": 1900.0 + r * (15.0 / p_norm),
        },
        "P2": {
            "xmin": 1900.0 - r * (17.0 / p_norm),
            "xmax": 1900.0 + r * (17.0 / p_norm),
        },
    }

    for row in result["products"]:
        code = row["itemCode"]
        pr_min = float(row["projectedRange"]["min"])
        pr_max = float(row["projectedRange"]["max"])

        assert math.isclose(pr_min, expected[code]["xmin"], rel_tol=1e-6, abs_tol=1e-6)
        assert math.isclose(pr_max, expected[code]["xmax"], rel_tol=1e-6, abs_tol=1e-6)

    # Explicit rounded checks against the user-provided Excel values.
    p1 = next(x for x in result["products"] if x["itemCode"] == "P1")
    p2 = next(x for x in result["products"] if x["itemCode"] == "P2")

    assert round(p1["projectedRange"]["min"], 4) == 642.9189
    assert round(p1["projectedRange"]["max"], 3) == 3157.081
    assert round(p2["projectedRange"]["min"], 4) == 475.3081
    assert round(p2["projectedRange"]["max"], 3) == 3324.692
