from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any
import numpy as np
from scipy.optimize import linprog
import subprocess
import os
import sys
import json

try:
    from formula.core.volume_optimizer import optimize_volume
except Exception:
    from core.volume_optimizer import optimize_volume

app = FastAPI(title="CVP Optimization & Formula Engine API", version="2.0.0")


class Product(BaseModel):
    itemName: str
    itemCode: str
    p: Optional[str] = None
    c: Optional[str] = None
    xmin: Optional[str] = None
    xmax: Optional[str] = None
    avgVolume: Optional[str] = None
    avgPrice: Optional[str] = None
    cost: Optional[str] = None
    pmin: Optional[str] = None
    pmax: Optional[str] = None
    cmin: Optional[str] = None
    cmax: Optional[str] = None


class OptimizeRequest(BaseModel):
    case: Literal["volume", "price", "cost", "robust"]
    fixedCost: str
    products: List[Product]


FormulaMode = Literal["indicator_current"]


class SolverConfig(BaseModel):
    method: Optional[str] = None
    options: Optional[Dict[str, Any]] = None



class FormulaRequest(BaseModel):
    indicator_id: int
    id_column: str = "ID"
    formulas: Optional[List[str]] = None
    mode: Optional[FormulaMode] = None
    persist: Optional[bool] = None
    solver: Optional[SolverConfig] = None


class DirectFormulaRequest(BaseModel):
    table_name: str
    id_column: str
    formulas: Dict[str, str]
    data: List[Dict[str, Any]]


class FormulaOptimizeRequest(BaseModel):
    indicator_id: int
    id_column: str = "ID"
    formulas: Optional[List[str]] = None
    mode: Optional[str] = None
    persist: Optional[bool] = None
    solver: Optional[SolverConfig] = None



VALID_LP_METHODS = {
    "highs",
    "highs-ds",
    "highs-ipm",
    "simplex",
    "revised simplex",
}

class FormulaRequestError(ValueError):
    """Raised when the unified formula request is invalid."""


def f(x, field):
    if x is None:
        raise HTTPException(status_code=422, detail=f"Missing field: {field}")
    return float(x)


def no_safe_region(case, reason, details=None, suggestion=None):
    return {
        "status": "NO_SAFE_REGION",
        "case": case,
        "reason": reason,
        "details": details or {},
        "suggestion": suggestion or "Adjust input parameters",
    }


def precheck_volume(req):
    for p in req.products:
        if f(p.p, "p") <= f(p.c, "c"):
            return no_safe_region(
                "volume",
                "Unit price is not greater than unit cost",
                {"itemCode": p.itemCode},
                "Increase price or reduce cost",
            )
        if f(p.xmin, "xmin") > f(p.xmax, "xmax"):
            return no_safe_region(
                "volume",
                "xmin is greater than xmax",
                {"itemCode": p.itemCode},
                "Fix volume bounds",
            )
    return None


def precheck_price(req):
    F = f(req.fixedCost, "fixedCost")
    revenue = sum(f(p.avgVolume, "avgVolume") * f(p.pmax, "pmax") for p in req.products)
    cost = sum(f(p.avgVolume, "avgVolume") * f(p.cost, "cost") for p in req.products)

    if revenue - cost <= F:
        return no_safe_region(
            "price",
            "Even max price cannot cover fixed cost",
            {"maxRevenue": revenue, "totalCost": cost, "fixedCost": F},
            "Increase volume or reduce fixed cost",
        )
    return None


def precheck_cost(req):
    F = f(req.fixedCost, "fixedCost")
    revenue = sum(f(p.avgVolume, "avgVolume") * f(p.avgPrice, "avgPrice") for p in req.products)

    if revenue <= F:
        return no_safe_region(
            "cost",
            "Total revenue does not exceed fixed cost",
            {"totalRevenue": revenue, "fixedCost": F},
            "Reduce fixed cost or increase price/volume",
        )
    return None


def precheck_robust(req):
    F = f(req.fixedCost, "fixedCost")
    worst_revenue = sum(f(p.avgVolume, "avgVolume") * f(p.pmin, "pmin") for p in req.products)
    worst_cost = sum(f(p.avgVolume, "avgVolume") * f(p.cmax, "cmax") for p in req.products)

    if worst_revenue - worst_cost <= F:
        return no_safe_region(
            "robust",
            "Worst-case scenario is not profitable",
            {"worstRevenue": worst_revenue, "worstCost": worst_cost, "fixedCost": F},
            "Improve worst-case price or reduce worst-case cost",
        )
    return None


def solve_volume(req):
    fail = precheck_volume(req)
    if fail:
        return fail

    products = [
        {
            "itemName": x.itemName,
            "itemCode": x.itemCode,
            "p": f(x.p, "p"),
            "c": f(x.c, "c"),
            "xmin": f(x.xmin, "xmin"),
            "xmax": f(x.xmax, "xmax"),
        }
        for x in req.products
    ]

    return optimize_volume(products, f(req.fixedCost, "fixedCost"))


def solve_price(req):
    fail = precheck_price(req)
    if fail:
        return fail

    F = f(req.fixedCost, "fixedCost")
    x = np.array([f(p.avgVolume, "avgVolume") for p in req.products])
    c = np.array([f(p.cost, "cost") for p in req.products])
    pmin = np.array([f(p.pmin, "pmin") for p in req.products])
    pmax = np.array([f(p.pmax, "pmax") for p in req.products])

    n = len(x)
    norm_x = np.linalg.norm(x)

    c_obj = np.zeros(n + 1)
    c_obj[-1] = -1

    A = [np.hstack([-x, norm_x])]
    b = [-(np.dot(c, x) + F)]

    for j in range(n):
        for sign, bound in [(-1, pmin[j]), (1, pmax[j])]:
            row = np.zeros(n + 1)
            row[j], row[-1] = sign, 1
            A.append(row)
            b.append(sign * bound)

    res = linprog(c_obj, A_ub=A, b_ub=b, bounds=[(None, None)] * n + [(0, None)], method="highs")

    if not res.success or res.x is None or res.x[-1] <= 0:
        return no_safe_region("price", "No feasible safe price region")

    p0, r = res.x[:-1], res.x[-1]
    delta = r / np.sqrt(n)

    return {
        "status": "OK",
        "case": "price",
        "products": [
            {
                "itemName": req.products[i].itemName,
                "itemCode": req.products[i].itemCode,
                "priceCenter": float(p0[i]),
                "safePriceRange": {"min": float(p0[i] - delta), "max": float(p0[i] + delta)},
            }
            for i in range(n)
        ],
    }


def solve_cost(req):
    fail = precheck_cost(req)
    if fail:
        return fail

    F = f(req.fixedCost, "fixedCost")
    x = np.array([f(p.avgVolume, "avgVolume") for p in req.products])
    p = np.array([f(p.avgPrice, "avgPrice") for p in req.products])
    cmin = np.array([f(p.cmin, "cmin") for p in req.products])
    cmax = np.array([f(p.cmax, "cmax") for p in req.products])

    n = len(x)
    norm_x = np.linalg.norm(x)

    c_obj = np.zeros(n + 1)
    c_obj[-1] = -1

    A = [np.hstack([x, norm_x])]
    b = [np.dot(p, x) - F]

    for j in range(n):
        for sign, bound in [(-1, cmin[j]), (1, cmax[j])]:
            row = np.zeros(n + 1)
            row[j], row[-1] = sign, 1
            A.append(row)
            b.append(sign * bound)

    res = linprog(c_obj, A_ub=A, b_ub=b, bounds=[(None, None)] * n + [(0, None)], method="highs")

    if not res.success or res.x is None or res.x[-1] <= 0:
        return no_safe_region("cost", "No feasible safe cost region")

    c0, r = res.x[:-1], res.x[-1]
    delta = r / np.sqrt(n)

    return {
        "status": "OK",
        "case": "cost",
        "products": [
            {
                "itemName": req.products[i].itemName,
                "itemCode": req.products[i].itemCode,
                "costCenter": float(c0[i]),
                "safeCostRange": {"min": float(c0[i] - delta), "max": float(c0[i] + delta)},
            }
            for i in range(n)
        ],
    }


def solve_robust(req):
    fail = precheck_robust(req)
    if fail:
        return fail

    return {
        "status": "OK",
        "case": "robust",
        "message": "System is robustly profitable under all given ranges",
        "products": [{"itemName": p.itemName, "itemCode": p.itemCode} for p in req.products],
    }


def _normalize_solver_config(solver: Optional[SolverConfig]) -> Optional[Dict[str, Any]]:
    if solver is None:
        return None

    normalized: Dict[str, Any] = {}
    if solver.method is not None:
        method = solver.method.strip()
        if method not in VALID_LP_METHODS:
            raise FormulaRequestError(
                f"Unsupported solver method: {method}. Supported: {sorted(VALID_LP_METHODS)}"
            )
        normalized["method"] = method

    if solver.options is not None:
        if not isinstance(solver.options, dict):
            raise FormulaRequestError("solver.options must be an object")
        normalized["options"] = solver.options

    return normalized or None


def _run_formula_calculate_subprocess(request: FormulaRequest) -> Dict[str, Any]:
    cmd = [sys.executable, "-m", "formula.pythoncode", str(request.indicator_id), request.id_column]
    if request.formulas:
        cmd.extend(request.formulas)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    env = os.environ.copy()
    solver_config = _normalize_solver_config(request.solver)
    if solver_config is not None:
        if "method" in solver_config:
            env["CVP_LP_METHOD"] = solver_config["method"]
        if "options" in solver_config:
            env["CVP_LP_OPTIONS_JSON"] = json.dumps(solver_config["options"])

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=current_dir, env=env)

    if result.returncode == 0:
        lines = result.stdout.split("\n")
        updated_rows = 0
        errors = 0
        for line in lines:
            if "Updated rows:" in line:
                updated_rows = int(line.split(":")[1].strip())
            elif "Errors:" in line:
                errors = int(line.split(":")[1].strip())
        return {
            "success": True,
            "updated_rows": updated_rows,
            "errors": errors,
            "output": result.stdout,
            "command": " ".join(cmd),
            "solver": solver_config,
        }

    return {
        "success": False,
        "updated_rows": 0,
        "errors": 1,
        "error": result.stderr,
        "output": result.stdout,
        "command": " ".join(cmd),
        "solver": solver_config,
    }

def _normalize_formula_mode(mode: Optional[str]) -> Optional[str]:
    if mode is None:
        return None
    if mode == "indicator_current":
        return mode
    raise FormulaRequestError(
        "Only mode='indicator_current' is supported. Optimizer-only modes were retired."
    )


def _resolve_persist(mode: Optional[str], persist: Optional[bool]) -> bool:
    if persist is not None:
        return persist
    return True


def _execute_formula_request(request: FormulaRequest) -> Dict[str, Any]:
    mode = _normalize_formula_mode(request.mode)
    persist = _resolve_persist(mode, request.persist)

    if mode in (None, "indicator_current"):
        legacy_result = _run_formula_calculate_subprocess(request)
        if mode is None:
            return legacy_result
        return {
            "success": legacy_result.get("success", False),
            "mode": "indicator_current",
            "persist": persist,
            "solver": _normalize_solver_config(request.solver),
            "indicator_id": request.indicator_id,
            "id_column": request.id_column,
            "execution": {
                "path": "formula_engine",
                "updated_rows": legacy_result.get("updated_rows", 0),
                "errors": legacy_result.get("errors", 0),
                "command": legacy_result.get("command"),
            },
            "result": legacy_result,
        }

    raise FormulaRequestError(f"Unsupported formula mode: {mode}")


@app.post("/formula/calculate")
async def calculate_formulas(request: FormulaRequest):
    """Unified formula endpoint for legacy calculate and indicator-current execution."""
    try:
        return _execute_formula_request(request)
    except FormulaRequestError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/formula/optimize")
async def optimize_formula_indicator(request: FormulaOptimizeRequest):
    """Compatibility alias that now forwards only to indicator_current execution."""
    try:
        if request.mode not in (None, "indicator_current"):
            raise FormulaRequestError(
                "POST /formula/optimize no longer supports optimizer-only modes. "
                "Use POST /formula/calculate with mode='indicator_current' or omit mode."
            )
        unified_request = FormulaRequest(
            indicator_id=request.indicator_id,
            id_column=request.id_column,
            formulas=request.formulas,
            mode="indicator_current",
            persist=request.persist,
            solver=request.solver,
        )
        response = _execute_formula_request(unified_request)
        if isinstance(response, dict):
            response.setdefault(
                "note",
                "POST /formula/optimize is kept only as a compatibility alias for indicator_current.",
            )
        return response
    except FormulaRequestError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/formula/calculate/direct")
async def calculate_direct_formulas(request: DirectFormulaRequest):
    try:
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fobj:
            data = {
                "table_name": request.table_name,
                "id_column": request.id_column,
                "formulas": request.formulas,
                "data": request.data,
            }
            json.dump(data, fobj)
            temp_file = fobj.name

        try:
            return {
                "success": True,
                "message": "Direct calculation endpoint - requires refactoring",
                "note": "Need to extract core logic from PYTHONCODE.PY into reusable functions",
                "data_summary": {
                    "table": request.table_name,
                    "rows": len(request.data),
                    "formulas": len(request.formulas),
                },
            }
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/formula/health")
async def formula_health():
    return {
        "status": "healthy",
        "service": "CVP Formula Engine API",
        "version": "2.0.0",
        "endpoints": [
            "POST /formula/calculate",
            "POST /formula/calculate/direct",
            "POST /formula/optimize",
            "GET /formula/health",
        ],
        "modes": ["indicator_current"],
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "CVP Optimization & Formula Engine API",
        "version": "2.0.0",
    }


@app.post("/optimize")
def optimize(req: OptimizeRequest):
    if req.case == "volume":
        return solve_volume(req)
    if req.case == "price":
        return solve_price(req)
    if req.case == "cost":
        return solve_cost(req)
    if req.case == "robust":
        return solve_robust(req)
    raise HTTPException(status_code=400, detail="Invalid case")


@app.get("/")
async def root():
    return {
        "message": "CVP Optimization & Formula Engine API",
        "version": "2.0.0",
        "documentation": "/docs",
        "endpoints": {
            "optimization": {
                "POST /optimize": "CVP optimization (volume, price, cost, robust)",
            },
            "formula_engine": {
                "POST /formula/calculate": "Unified formula endpoint with legacy and indicator_current execution",
                "POST /formula/calculate/direct": "Direct calculation with provided data",
                "POST /formula/optimize": "Compatibility alias for indicator_current",
                "GET /formula/health": "Formula engine health check",
            },
            "system": {
                "GET /health": "Overall API health",
                "GET /": "This documentation",
            },
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)









