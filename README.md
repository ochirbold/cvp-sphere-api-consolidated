# CVP Sphere API Consolidated

FastAPI дээр ажилладаг CVP optimization болон formula execution service. Энэ repository-ийн одоогийн root нь шууд API project бөгөөд хуучин README дээр байсан `cvp-sphere-api/` гэсэн дэд хавтасны заавар одоо хүчинтэй биш.

## Одоогийн боломжууд

- `POST /optimize` endpoint нь `volume`, `price`, `cost`, `robust` case-уудыг дэмжинэ.
- `volume` optimizer нь шинэ DSL + LP pipeline ашиглахыг оролдоно, боломжгүй үед legacy `scipy.optimize.linprog` fallback руу орно.
- `volume` хариуд `safeRange`-аас гадна Sheet2-тэй таарах `projectedRange` буцаадаг.
- `POST /formula/calculate` endpoint нь `formula.pythoncode` shim-ээр дамжин `formula/core/orchestrator.py`-г ажиллуулна.
- `POST /formula/calculate/direct` endpoint одоогоор placeholder; бодит direct execution хараахан бүрэн хийгдээгүй.

## Төслийн бүтэц

- `main.py`: FastAPI entrypoint
- `formula/core/volume_optimizer.py`: volume optimization service
- `formula/core/orchestrator.py`: Oracle DB-тэй formula execution engine
- `formula/pythoncode.py`: backward-compatible shim
- `formula/tests/`: optimizer болон DSL regression тестүүд
- `docs/`: migration, audit, archive материалууд

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

Энэ endpoint нь subprocess-оор `python -m formula.pythoncode` ажиллуулж, DB дээрх formula execution-г trigger хийнэ.

```bash
curl -X POST "http://localhost:8000/formula/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "indicator_id": 17687947217601,
    "id_column": "ID",
    "formulas": [
      "CM_J:P_J - C_J",
      "X0_J:(X_MIN_J + X_MAX_J) / 2"
    ]
  }'
```

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

## Хязгаарлалт ба тэмдэглэл

- `formula/.env` файлд жинхэнэ credential хадгалж байгаа бол repository руу commit хийж болохгүй.
- `POST /formula/calculate/direct` бүрэн хийгдээгүй.
- README дээрх хуучин `PYTHONCODE.py` том үсэгтэй нэршлийг шинэчилсэн; одоо canonical entry нь `python -m formula.pythoncode`.
- Railway болон deployment нэмэлт тэмдэглэлүүдийг root README-д биш, тусдаа deployment doc дээр хадгалах нь илүү зөв.
