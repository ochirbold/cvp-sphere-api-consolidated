import math
import sys
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
FORMULA_DIR = THIS_FILE.parents[1]
REPO_ROOT = THIS_FILE.parents[2]

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(FORMULA_DIR))

from formula.core.volume_optimizer import optimize_volume


def test_volume_optimizer_sheet1_like_case():
    products = [
        {
            "itemName": "P1",
            "itemCode": "P1",
            "p": 15.0,
            "c": 7.0,
            "xmin": 0.0,
            "xmax": 500.0,
        }
    ]

    result = optimize_volume(products, 1000.0)

    assert result["status"] == "OK"
    assert result["case"] == "volume"
    assert len(result["products"]) == 1

    row = result["products"][0]
    center = row["center"]
    smin = row["safeRange"]["min"]
    smax = row["safeRange"]["max"]

    assert math.isclose(center, 312.5, rel_tol=1e-6, abs_tol=1e-6)
    assert math.isclose(smin, 125.0, rel_tol=1e-6, abs_tol=1e-6)
    assert math.isclose(smax, 500.0, rel_tol=1e-6, abs_tol=1e-6)

    # For single-product case alpha=1, projected range equals safe range.
    assert math.isclose(row["projectedRange"]["min"], smin, rel_tol=1e-6, abs_tol=1e-6)
    assert math.isclose(row["projectedRange"]["max"], smax, rel_tol=1e-6, abs_tol=1e-6)


def test_volume_optimizer_projected_range_multi_product():
    products = [
        {
            "itemName": "P1",
            "itemCode": "P1",
            "p": 20.0,
            "c": 10.0,
            "xmin": 0.0,
            "xmax": 4800.0,
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

    result = optimize_volume(products, 2700.0)
    assert result["status"] == "OK"

    rows = result["products"]
    p_norm = math.sqrt(20.0 ** 2 + 17.0 ** 2)
    alphas = [20.0 / p_norm, 17.0 / p_norm]

    for i, row in enumerate(rows):
        center = float(row["center"])
        safe_min = float(row["safeRange"]["min"])
        safe_max = float(row["safeRange"]["max"])
        projected_min = float(row["projectedRange"]["min"])
        projected_max = float(row["projectedRange"]["max"])

        r_value = (safe_max - safe_min) / 2.0
        alpha = alphas[i]

        assert math.isclose(projected_min, center - alpha * r_value, rel_tol=1e-6, abs_tol=1e-6)
        assert math.isclose(projected_max, center + alpha * r_value, rel_tol=1e-6, abs_tol=1e-6)


def test_volume_optimizer_no_safe_region_case():
    products = [
        {
            "itemName": "P1",
            "itemCode": "P1",
            "p": 15.0,
            "c": 14.9,
            "xmin": 0.0,
            "xmax": 100.0,
        }
    ]

    result = optimize_volume(products, 1000.0)

    assert result["status"] == "NO_SAFE_REGION"
    assert result["case"] == "volume"
