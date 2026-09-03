# CVP Sphere API Consolidated

FastAPI дээр ажилладаг CVP optimization болон formula execution service. Энэ repository-ийн одоогийн root нь шууд API project бөгөөд хуучин README дээр байсан `cvp-sphere-api/` гэсэн дэд хавтасны заавар одоо хүчинтэй биш.

## Одоогийн боломжууд

- `POST /optimize` endpoint нь `volume`, `price`, `cost`, `robust` case-уудыг дэмжинэ.
- `POST /formula/calculate` нь indicator-driven formula engine-ийн canonical endpoint.
- `POST /formula/calculate` одоогоор зөвхөн `mode="indicator_current"`-ийг дэмжинэ; optimizer-only mode-ууд retired болсон.
- `POST /formula/optimize` endpoint нь шинэ optimize engine биш, `indicator_current` руу forward хийдэг compatibility alias.
- `scenario_code` request field ашиглан `SCENARIO_CODE` баганатай хүснэгт дээр scenario-level мөрүүдийг шүүн ажиллуулж болно.
- Formula engine нь Oracle DB-ээс DSL уншиж, LP solve шаардлагатай үед `scipy.optimize.linprog` ашигладаг.
- `POST /formula/calculate/direct` endpoint одоогоор placeholder; бодит direct execution хараахан бүрэн хийгдээгүй.

## Төслийн бүтэц

- `main.py`: FastAPI entrypoint
- `formula/core/volume_optimizer.py`: legacy volume optimization logic
- `formula/core/orchestrator.py`: Oracle DB-тэй formula execution engine
- `formula/pythoncode.py`: backward-compatible shim
- `formula/tests/`: optimizer болон DSL regression тестүүд
- `docs/`: migration, audit, archive материалууд
- `CODEX.md`: Codex agent ажиллах project rules, production noён шугам, cleanup/deploy сэрэмжлүүлэг

## Хурдан эхлүүлэх

### 1. Dependency суулгах

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Database тохируулах

Formula engine ашиглах бол `formula/.env.example` файлыг `formula/.env` болгон хуулж бодит утгуудаа оруулна.

```powershell
Copy-Item formula\.env.example formula\.env
```

Шаардлагатай хувьсагчууд:

```env
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=172.169.88.80
DB_PORT=1521
DB_SID=DEV
```

`/optimize` endpoint өөрөө database шаардахгүй. Харин `/formula/calculate` Oracle холболт шаарддаг.

### 3. API ажиллуулах

```bash
uvicorn main:app --reload --port 8000
```

Документаци:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health: `http://localhost:8000/health`

## Optimizer API

### `POST /optimize`

Request body:

```json
{
  "case": "volume",
  "fixedCost": "10000",
  "products": [
    {
      "itemName": "Product A",
      "itemCode": "PA001",
      "p": "150",
      "c": "100",
      "xmin": "50",
      "xmax": "200"
    }
  ]
}
```

Volume response-ийн үндсэн бүтэц:

```json
{
  "status": "OK",
  "case": "volume",
  "products": [
    {
      "itemName": "Product A",
      "itemCode": "PA001",
      "center": 125.0,
      "safeRange": {
        "min": 50.0,
        "max": 200.0
      },
      "projectedRange": {
        "min": 50.0,
        "max": 200.0
      }
    }
  ]
}
```

Case бүрийн шаардлагатай талбар:

- `volume`: `p`, `c`, `xmin`, `xmax`
- `price`: `avgVolume`, `cost`, `pmin`, `pmax`
- `cost`: `avgVolume`, `avgPrice`, `cmin`, `cmax`
- `robust`: `avgVolume`, `pmin`, `cmax`

Precheck амжилтгүй бол `NO_SAFE_REGION` статус буцна.

## Formula Engine API

### `POST /formula/calculate`

Энэ endpoint нь subprocess-оор `python -m formula.pythoncode` ажиллуулж, DB дээрх indicator formula execution-г trigger хийнэ.

Хамгийн түгээмэл request:

```bash
curl -X POST "http://localhost:8000/formula/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "indicator_id": 232819585,
    "id_column": "ID",
    "mode": "indicator_current",
    "persist": true
  }'
```

`mode`-ийг өгөхгүй орхивол мөн `indicator_current` behavior руу орно.

Scenario-level тооцоолол хэрэгтэй бол `scenario_code` өгч болно:

```bash
curl -X POST "http://localhost:8000/formula/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "indicator_id": 1785914826386441,
    "id_column": "ID",
    "mode": "indicator_current",
    "persist": true,
    "scenario_code": "base"
  }'
```

`scenario_code` behavior:

- `scenario_code` өгөхгүй, `null`, эсвэл хоосон string байвал бүх мөр хамрагдана.
- `"base"` гэх мэт утга өгвөл зөвхөн `SCENARIO_CODE = 'base'` мөрүүд select/update хийгдэнэ.
- Тухайн indicator-ийн сонгосон хүснэгт дээр `SCENARIO_CODE` багана байхгүй үед scenario filter хүсвэл алдаатай зогсоно.
- Backward compatibility зорилгоор `scenario_Code` болон `scenarioCode` casing-уудыг мөн хүлээн авна.

Request-level solver override ашиглаж болно:

```json
{
  "indicator_id": 232819585,
  "id_column": "ID",
  "mode": "indicator_current",
  "persist": true,
  "solver": {
    "method": "revised simplex"
  }
}
```

Дэмжигдэх `solver.method` утгууд:

- `highs`
- `highs-ds`
- `highs-ipm`
- `simplex`
- `revised simplex`

Тэмдэглэл:

- `highs` бол default ба production-д хамгийн аюулгүй сонголт.
- `revised simplex` нь олон optimal center-тэй LP дээр seminar / hand-built script-тэй ижил vertex сонгох тохиолдол байдаг.
- Solver method өөрчлөгдөхөд ихэнхдээ `r` ижил хэвээр үлдэж, `x` center өөр сонгогдож болно.

### `POST /formula/optimize`

Энэ endpoint одоо compatibility alias.

- `POST /formula/calculate` руу forward хийнэ
- зөвхөн `mode="indicator_current"`-ийг зөвшөөрнө
- шинэ optimizer-only API гэж үзэхгүй байх нь зөв

### `POST /formula/calculate/direct`

Одоогийн байдал:

- request schema бэлэн
- temporary file үүсгэдэг
- бодит formula evaluation хийхгүй
- placeholder summary буцаадаг

Иймээс production direct-calculation endpoint гэж үзэж ашиглахгүй байх нь зөв.

## CLI Formula ажиллуулах

Compatibility shim:

```bash
python -m formula.pythoncode 17687947217601 ID
```

Manual mode:

```bash
python -m formula.pythoncode VT_DATA.V_17687947217601 ID "CM_J:P_J - C_J" "X0_J:(X_MIN_J + X_MAX_J) / 2"
```

Жинхэнэ хэрэгжилт нь `formula/core/orchestrator.py` дотор байрлаж байгаа.

## DSL тэмдэглэл

### `DECISION(x)` auto-size

Одоо vector decision variable-ийн хэмжээг гараар тогтоохгүй байж болно.

Өмнөх хэлбэр:

```text
DECISION_X  DECISION(x, size=3)
```

Шинэ зөвлөмжит хэлбэр:

```text
DECISION_X  DECISION(x)
```

Engine нь тухайн indicator-ийн fetch хийсэн мөрийн тоогоор `x1..xN`-ийг автоматаар resolve хийнэ.

Дэмжигдэх хэлбэрүүд:

- `DECISION(x)`
- `DECISION(x, size=3)`
- `DECISION(x, size=AUTO)`

### `X0_J` ба `R0`-г DB-д хадгалах

Хэрэв LP solve-ийн center болон radius-ийг шууд DB баганад хадгалах шаардлагатай бол DSL дээр target болгож өгч болно:

```text
CM_J            P_J - C_J
X0_J            X0_J
R0              r0
CM_NORM         NORM(vector(CM_J))
SAFE_X_MIN      X0_J - r0*(CM_J/CM_NORM)
SAFE_X_MAX      X0_J + r0*(CM_J/CM_NORM)
DECISION_X      DECISION(x)
DECISION_R      DECISION(r)
OBJ             OBJECTIVE(1*r)
BOUND_X         BOUND(x,XMIN,XMAX)
BOUND_R         BOUND(r,0,None)
CONSTRAINT_LP   -DOT(vector(CM_J),x)+NORM(vector(CM_J))*r<=-F
```

Энд:

- `X0_J  X0_J` нь LP propagation-аар мөр бүрт үүссэн харгалзах `x` утгыг DB target column руу бичнэ.
- `R0    r0` нь scenario-level solve-оос гарсан radius-ийг DB target column руу бичнэ.

Анхаарах зүйл:

- `X0_J = X0_J` гэж `=` давхар бичихгүй.
- `R0` target-ийн expression нь `R0` биш, жижиг `r0` байна.
- DB дээр `X0_J`, `R0` гэсэн writable column заавал байх ёстой.

## Тест ажиллуулах

Бүх тест:

```bash
pytest
```

Optimizer-т чиглэсэн тест:

```bash
pytest formula/tests/test_volume_optimizer_service.py
pytest formula/tests/test_sheet2_fixed_xr_projection.py
pytest formula/tests/test_user_10_product_dsl_optimizer.py
```

Эдгээр тестүүд нь:

- single-product volume safe range
- multi-product projected range
- 10-product DSL LP solve
- Sheet2 projection consistency

гэсэн гол behavior-уудыг шалгадаг.

## Docker

```bash
docker build -t cvp-sphere-api .
docker run -p 8000:8000 --env-file formula/.env cvp-sphere-api
```

Хэрэв formula engine хэрэглэхгүй бол `--env-file` заавал биш.

## Project Rules

Codex болон agent-based өөрчлөлт хийхдээ root-ийн `CODEX.md`-ийг эхэлж уншина. Тэнд:

- production formula execution-ийн noён шугам
- stale болон authoritative биш deployment материалууд
- GitHub/custom host deploy дээр анхаарах зүйлс
- dirty worktree болон generated file-уудтай харьцах дүрэм
- formula engine өөрчлөхөд ажиллуулах verification checks

тодорхой бичигдсэн.

Одоогийн deployment-ийн хувьд custom host ашиглаж байгаа гэж үзнэ. `railway.json` болон Railway-тэй холбоотой хуучин тэмдэглэлүүдийг host-ийн бодит тохиргоо гэж шууд дагаж болохгүй.

## Хязгаарлалт ба тэмдэглэл

- `formula/.env` файлд жинхэнэ credential хадгалж байгаа бол repository руу commit хийж болохгүй.
- `POST /formula/calculate/direct` бүрэн хийгдээгүй.
- `POST /formula/calculate` болон `POST /formula/optimize` дээр optimizer-only mode-уудыг ашиглахгүй; одоогийн дэмжигдэх mode нь `indicator_current`.
- `scenario_code=null` эсвэл field байхгүй request нь бүх мөрийг хамардаг тул live DB дээр ажиллуулахдаа scope-оо анхаарна.
- README дээрх хуучин `PYTHONCODE.py` том үсэгтэй нэршлийг шинэчилсэн; одоо canonical entry нь `python -m formula.pythoncode`.
- Railway болон deployment нэмэлт тэмдэглэлүүдийг root README-д биш, тусдаа deployment doc дээр хадгалах нь илүү зөв.
