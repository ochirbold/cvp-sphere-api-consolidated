from types import SimpleNamespace

from main import FormulaOptimizeRequest, FormulaRequest, _run_formula_calculate_subprocess
from formula.core.orchestrator import table_has_column


def test_formula_request_passes_scenario_code_to_subprocess_env(monkeypatch):
    captured = {}

    def fake_run(cmd, capture_output, text, cwd, env):
        captured["cmd"] = cmd
        captured["env"] = env
        return SimpleNamespace(
            returncode=0,
            stdout="[INFO] Updated rows: 0\n[INFO] Update errors: 0\n",
            stderr="",
        )

    monkeypatch.setattr("main.subprocess.run", fake_run)

    _run_formula_calculate_subprocess(
        FormulaRequest(indicator_id=232819585, id_column="ID", scenario_code="base")
    )

    assert captured["cmd"][-2:] == ["232819585", "ID"]
    assert captured["env"]["CVP_SCENARIO_CODE"] == "base"


def test_formula_request_omits_scenario_env_when_filter_is_null(monkeypatch):
    captured = {}

    def fake_run(cmd, capture_output, text, cwd, env):
        captured["env"] = env
        return SimpleNamespace(
            returncode=0,
            stdout="[INFO] Updated rows: 0\n[INFO] Update errors: 0\n",
            stderr="",
        )

    monkeypatch.setattr("main.subprocess.run", fake_run)

    _run_formula_calculate_subprocess(FormulaRequest(indicator_id=232819585, id_column="ID"))

    assert "CVP_SCENARIO_CODE" not in captured["env"]


def validate_model(model, values):
    if hasattr(model, "model_validate"):
        return model.model_validate(values)
    return model.parse_obj(values)


def test_formula_request_accepts_scenario_code_aliases():
    req_from_legacy_case = validate_model(FormulaRequest, {
        "indicator_id": 1785914826386441,
        "id_column": "ID",
        "scenario_Code": "base",
    })
    req_from_camel_case = validate_model(FormulaOptimizeRequest, {
        "indicator_id": 1785914826386441,
        "id_column": "ID",
        "scenarioCode": "optimistic",
    })

    assert req_from_legacy_case.scenario_code == "base"
    assert req_from_camel_case.scenario_code == "optimistic"


class FakeCursor:
    def __init__(self, row):
        self.row = row
        self.query = None
        self.params = None

    def execute(self, query, params):
        self.query = query
        self.params = params

    def fetchone(self):
        return self.row


def test_table_has_column_checks_qualified_oracle_object():
    cur = FakeCursor((1,))

    assert table_has_column(cur, "VT_DATA.V_232819585", "SCENARIO_CODE") is True
    assert "ALL_TAB_COLUMNS" in cur.query
    assert cur.params == {
        "owner": "VT_DATA",
        "table_name": "V_232819585",
        "column_name": "SCENARIO_CODE",
    }


def test_table_has_column_returns_false_when_metadata_missing():
    cur = FakeCursor(None)

    assert table_has_column(cur, "VT_DATA.V_232819585", "SCENARIO_CODE") is False
