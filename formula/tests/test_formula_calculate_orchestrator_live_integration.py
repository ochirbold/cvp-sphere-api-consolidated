import os
import pytest

from main import FormulaRequest, calculate_formulas


@pytest.mark.integration
def test_formula_calculate_orchestrator_live_db():
    """Live integration test for /formula/calculate orchestration path.

    This test is opt-in because it needs DB/network access.
    Enable with: RUN_LIVE_DB_TESTS=1
    """
    if os.getenv("RUN_LIVE_DB_TESTS") != "1":
        pytest.skip("Set RUN_LIVE_DB_TESTS=1 to run live DB integration test")

    import asyncio

    async def _run():
        req = FormulaRequest(indicator_id=232819585, id_column="ID")
        return await calculate_formulas(req)

    result = asyncio.run(_run())

    assert result["success"] is True
    assert int(result["updated_rows"]) > 0
    assert int(result["errors"]) == 0
    assert "LP optimization completed successfully" in result.get("output", "")
