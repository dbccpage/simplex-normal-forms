"""Run with a wheel-installed virtualenv Python using -I, outside the checkout."""

from pathlib import Path
import json
import sqlite3
import sys

from fastapi.testclient import TestClient

import normal_forms
import web
from normal_forms.catalog import check_catalog, _contract_paths
from normal_forms.contract_paths import CONTRACTS_DIR
from normal_forms.schema_sql import install_schema
from web.app import app, PRESETS, BQNF_PRESETS, COMPILER_PRESETS, AI_PRESETS


def main():
    assert sys.prefix != sys.base_prefix, "Use a separate virtualenv to verify the installed wheel."
    for module in (normal_forms, web):
        assert Path(module.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()), module.__file__
    assert CONTRACTS_DIR.is_relative_to(Path(normal_forms.__file__).resolve().parent)
    assert len(_contract_paths(CONTRACTS_DIR)) == 112
    assert check_catalog() == []
    for fixture in (CONTRACTS_DIR / "data").glob("*.json"):
        json.loads(fixture.read_text(encoding="utf-8"))
    assert (CONTRACTS_DIR / "data" / "cdc_events.json").is_file()
    with sqlite3.connect(":memory:") as conn:
        install_schema(conn)
        assert conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0] > 0
    with TestClient(app) as client:
        for path in ("/healthz", "/", "/static/app.js", "/static/style.css"):
            assert client.get(path).status_code == 200, path
        for endpoint, preset in (
            ("relational/normalize", PRESETS["ecommerce"]),
            ("bqnf/simulate", BQNF_PRESETS["financial_ledger"]),
            ("compiler/lower", COMPILER_PRESETS["employee_bcnf"]),
            ("ai/lossledger", AI_PRESETS["rag_research_context"]),
        ):
            result = client.post("/api/" + endpoint, json=preset)
            assert result.status_code == 200, result.text
            data = result.json()
            if endpoint == "relational/normalize":
                assert data["chase"]["is_implied"]
            elif endpoint == "bqnf/simulate":
                assert data["final_cache"]["North"]["total_sales"] == 280
                assert data["final_cache"]["North"]["sale_count"] == 4
            elif endpoint == "compiler/lower":
                assert data["sqlite_verification"]["verified"]
            else:
                assert data["token_accounting"]["token_conservation_commutes"]
                assert data["loss_ledger_integrity_verified"]
    print("Installed wheel: 112 contracts, fixtures, SQL schema, assets, and four API workbenches passed.")


if __name__ == "__main__":
    main()
