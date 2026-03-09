# Orchestrator API Test Report (2026-03-09)

## Goal
Test `POST http://localhost:8000/formula/calculate` with payload:

```json
{
  "indicator_id": "232819585",
  "id_column": "ID"
}
```

and report:
- end-to-end orchestrator execution result
- encountered errors and fixes
- reproducible test command

## Request Validation
- API model (`FormulaRequest`) expects:
  - `indicator_id: int`
  - `id_column: str`
- Sent value `"232819585"` (string) is accepted by Pydantic and coerced to integer.

## Execution Path Tested
`/formula/calculate` endpoint calls:

```txt
python -m formula.pythoncode <indicator_id> <id_column>
```

which resolves to orchestrator flow in `formula/core/orchestrator.py`.

## Step-by-step Test Results

### Step 1: Direct localhost call (server availability)
Attempted:
- `POST http://localhost:8000/formula/calculate`

Result:
- Failed: `No connection could be made because the target machine actively refused it`

Cause:
- Local API server was not running on port 8000 in this environment.

Fix/Workaround:
- Executed the same endpoint handler directly (`calculate_formulas`) to validate orchestrator logic without relying on an externally running server process.

### Step 2: TestClient attempt
Attempted:
- FastAPI `TestClient(app).post("/formula/calculate", json=...)`

Result:
- Failed: `RuntimeError: starlette.testclient requires httpx`

Cause:
- `httpx` package is not installed in the virtual environment.

Fix/Workaround:
- Called endpoint handler coroutine directly using `asyncio`.
- This still executes the exact same subprocess orchestration path.

### Step 3: Orchestrator run (successful)
Handler call:
- `calculate_formulas(FormulaRequest(indicator_id=232819585, id_column="ID"))`

Returned JSON summary:

```json
{
  "success": true,
  "updated_rows": 40,
  "errors": 0,
  "command": "...\\python.exe -m formula.pythoncode 232819585 ID"
}
```

Key runtime evidence from output log:
- DB connect succeeded: `172.169.88.80:1521/DEV`
- Table detected: `VT_DATA.V_232819585`
- Formulas loaded from DB: `10 formulas`
- LP detected and solved:
  - `LP optimization completed successfully`
  - `r = 1750.0`
  - `x1=28250, x2=23250, ..., x10=5250` (internal solver variable order mapping applied)
- Phase 3 row formulas computed:
  - `SAFE_X_MIN`, `SAFE_X_MAX`
- DB update:
  - `Updated rows: 40`
  - `Update errors: 0`

## Added Automated Integration Test
New file:
- `formula/tests/test_formula_calculate_orchestrator_live_integration.py`

Test behavior:
- Opt-in live DB integration test
- Requires env var: `RUN_LIVE_DB_TESTS=1`
- Asserts:
  - `success == true`
  - `updated_rows > 0`
  - `errors == 0`
  - output contains `LP optimization completed successfully`

## Warning Encountered and Fix
Issue:
- `PytestUnknownMarkWarning: Unknown pytest.mark.integration`

Fix:
- Added `pytest.ini` and registered marker:
  - `integration: live integration tests that require DB/network access`

Re-run result after fix:

```txt
1 passed in 2.34s
```

## Repro Commands

### Run live integration test
```powershell
$env:RUN_LIVE_DB_TESTS='1'
.\.venv\Scripts\python.exe -m pytest -q formula/tests/test_formula_calculate_orchestrator_live_integration.py
```

### Direct handler execution (no TestClient dependency)
```powershell
.\.venv\Scripts\python.exe - <<'PY'
import asyncio
from main import calculate_formulas, FormulaRequest

async def run():
    req = FormulaRequest(indicator_id=232819585, id_column='ID')
    res = await calculate_formulas(req)
    print(res)

asyncio.run(run())
PY
```

## Practical Notes
- If you specifically need `curl`/Postman against `http://localhost:8000`, ensure the API service is actively running in a separate terminal session:
  - `.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000`
- In this run environment, direct socket access to localhost service startup was inconsistent, so handler-level orchestration validation was used as the reliable path.
