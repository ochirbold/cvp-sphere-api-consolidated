# CVP Sphere API Consolidated

FastAPI дээр ажилладаг CVP optimization болон Oracle-backed indicator formula execution service.

Энэ repository-ийн root нь шууд API project. Хуучин зааварт гардаг `cvp-sphere-api/` дэд хавтасны structure одоо хүчинтэй биш.

## Одоогийн Noён Шугам

- `POST /formula/calculate` бол indicator-driven formula engine-ийн canonical endpoint.
- Request дээрх `indicator_id` нь `kpi_indicator.TABLE_NAME`-ээр дамжин ажиллах хүснэгтийг сонгоно.
- Formula definitions нь `kpi_indicator_indicator_map`-аас уншигдана.
- `formula/pythoncode.py` нь backward-compatible shim; бодит execution нь `formula/core/orchestrator.py`.
- Engine selected Oracle table-ээс мөрүүд уншаад, тооцоолсон утгаа тухайн хүснэгт рүү update хийдэг.
- LP шаардлагатай DSL formula дээр deterministic LP pipeline болон `scipy.optimize.linprog` ашиглана.

Agent/Codex ажил хийхдээ эхлээд `CODEX.md`-ийг уншина. Тэнд production path, Git/deploy дүрэм, stale material, cleanup backlog-ийг илүү нарийн заасан.

## Гол Endpoint-ууд

### `POST /formula/calculate`

Production formula endpoint.

```bash
curl -X POST "http://localhost:8000/formula/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "indicator_id": 1785914826386441,
    "id_column": "ID",
    "mode": "indicator_current",
    "scenario_code": "base",
    "solver": {
      "method": "highs"
    },
    "persist": true
  }'
```

Supported mode:

- `mode = "indicator_current"`
- `mode` omitted: legacy compatibility-аар мөн current indicator execution path руу орно

`scenario_code` behavior:

- `scenario_code` байхгүй, `null`, эсвэл хоосон string бол бүх мөр хамрагдана.
- `"base"` гэх мэт non-empty утга өгвөл зөвхөн `SCENARIO_CODE = 'base'` мөрүүд select/update хийгдэнэ.
- Scenario filter хүссэн боловч selected table дээр `SCENARIO_CODE` багана байхгүй бол engine алдаатай зогсоно.
- Backward compatibility зорилгоор `scenario_Code`, `scenarioCode` casing-уудыг мөн хүлээн авна.

Supported solver methods:

- `highs` буюу default/recommended
- `highs-ds`
- `highs-ipm`
- `simplex`
- `revised simplex`

### `POST /formula/optimize`

Compatibility alias only. Шинэ optimizer-only API гэж үзэхгүй.

- `POST /formula/calculate` руу forward хийнэ.
- Зөвхөн `indicator_current` mode-ийг зөвшөөрнө.

### `POST /optimize`

DB шаардахгүй legacy CVP optimizer endpoint.

Supported cases:

- `volume`
- `price`
- `cost`
- `robust`

### `POST /formula/calculate/direct`

Одоогоор production-ready endpoint биш. Request schema байгаа боловч canonical formula execution path биш тул production integration дээр ашиглахгүй.

## Local Ажиллуулах

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Local docs:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health: `http://localhost:8000/health`
- Formula health: `http://localhost:8000/formula/health`

## Database Тохиргоо

Formula engine Oracle DB шаарддаг.

```powershell
Copy-Item formula\.env.example formula\.env
```

Required env values:

```env
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=172.169.88.80
DB_PORT=1521
DB_SID=DEV
```

`formula/.env` дотор real credential байвал commit хийж болохгүй.

## CLI Formula Execution

Indicator mode:

```bash
python -m formula.pythoncode 1785914826386441 ID
```

Scenario filter-ийг API request-ээр дамжуулах нь зөв. CLI шууд ажиллуулах шаардлагатай бол `CVP_SCENARIO_CODE` env ашиглана.

```powershell
$env:CVP_SCENARIO_CODE = "base"
python -m formula.pythoncode 1785914826386441 ID
```

## Verification

Formula engine өөрчилсний дараа хамгийн багадаа:

```bash
python scripts/check_no_duplicates.py
python scripts/import_smoke.py
pytest formula/tests/test_lp_regression.py formula/tests/test_scenario_code_filter.py -q
git diff --check
```

Live `/formula/calculate` run нь DB update хийдэг. Indicator/scenario scope-оо баталгаажуулсны дараа л ажиллуулна.

## Deployment Тэмдэглэл

Одоогийн active source of truth:

- GitHub remote: `origin`
- Default branch: `master`
- Custom host ашиглаж байгаа; Railway active deploy гэж үзэхгүй.

Custom host дээр ерөнхий deploy flow:

```bash
git fetch origin
git checkout master
git pull --ff-only origin master
```

Дараа нь тухайн host-ийн process manager/service-ээр API-г restart хийнэ. Service name, deploy path, restart command нь repo-д authoritative байдлаар бичигдээгүй тул host admin орчноосоо баталгаажуулах хэрэгтэй.

## Docker

Хэрэв custom host container ашигладаг бол:

```bash
docker build -t cvp-sphere-api .
docker run -p 8000:8000 --env-file formula/.env cvp-sphere-api
```

Formula engine хэрэглэхгүй бол `--env-file` заавал биш.

## Known Limitations

- `POST /formula/calculate/direct` production-ready биш.
- Optimizer-only formula modes retired; supported formula mode нь `indicator_current`.
- `scenario_code=null` эсвэл missing request нь бүх мөрийг хамардаг.
- Negative margin бүтээгдэхүүн дээр одоогийн DSL formula-аас `SAFE_X_MIN > SAFE_X_MAX` гарах боломжтой. Энэ нь engine-level normalize хийх шаардлагатай known behavior.
- `railway.json`, `DEPLOYMENT_PACKAGE_README.md`, `docs/archive/**` нь historical/context материал; deploy-ийн source of truth гэж шууд дагахгүй.
- Repo hygiene backlog: tracked `.venv`/`.pyc` generated files-ийг тусдаа cleanup PR-аар tracking-аас гаргах шаардлагатай.
