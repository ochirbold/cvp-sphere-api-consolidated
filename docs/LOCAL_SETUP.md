# Local Setup (Stage-1)

## Python and venv

```powershell
# from repo root
C:\Users\chogo\AppData\Local\Programs\Python\Python310\python.exe -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pytest
```

## Validation commands

```powershell
.\.venv\Scripts\python.exe scripts/import_smoke.py
.\.venv\Scripts\python.exe scripts/check_no_duplicates.py
.\.venv\Scripts\python.exe -m pytest -q formula/tests/test_lp_regression.py
```

Expected: all commands return exit code `0`.
