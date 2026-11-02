"""Smoke tests for Simplex Normal Forms Studio Web API.

AuthorityEffect: None.
certified_implies_authorized: false.
"""

import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from fastapi.testclient import TestClient
from web.app import app, PRESETS, BQNF_PRESETS, COMPILER_PRESETS, AI_PRESETS

client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["service"] == "smplxnf-studio"
    assert data["version"] == "0.1.0"


def test_frontend_serving():
    r = client.get("/")
    assert r.status_code == 200
    assert "Simplex-NF Studio" in r.text

    css = client.get("/static/style.css")
    assert css.status_code == 200

    js = client.get("/static/app.js")
    assert js.status_code == 200


def test_relational_presets():
    for name, p in PRESETS.items():
        req = {
            "attributes": p["attributes"],
            "dependencies": p["dependencies"],
            "custom_components": p.get("custom_components"),
        }
        r = client.post("/api/relational/normalize", json=req)
        assert r.status_code == 200, f"Preset {name} failed: {r.text}"
        data = r.json()
        assert "candidate_keys" in data
        assert "synthesized_3nf" in data
        assert "chase" in data
        if name == "lossy_decomposition":
            assert data["chase"]["is_implied"] is False
            assert data["chase"]["spurious_tuple_witness"] is not None
        else:
            assert data["chase"]["is_implied"] is True


def test_bqnf_simulation():
    for name, p in BQNF_PRESETS.items():
        req = {
            "boundary": p["boundary"],
            "events": p["events"],
            "initial_sales": p.get("initial_sales"),
            "use_cochain": True,
        }
        r = client.post("/api/bqnf/simulate", json=req)
        assert r.status_code == 200, f"BQNF {name} failed: {r.text}"
        data = r.json()
        assert data["events_evaluated"] == len(p["events"])
        assert len(data["extrema_repair_log"]) > 0
        assert len(data["quantile_buckets"]) > 0
        assert data["repair_tally"]["extrema_repairs"] > 0


def test_compiler_lowering():
    for name, p in COMPILER_PRESETS.items():
        req = {
            "contract_id": p["contract_id"],
            "key_field": p["key_field"],
            "heading": p["heading"],
            "determinant": p["determinant"],
            "dependent": p["dependent"],
            "table_name": p["table_name"],
            "test_carrier": p.get("test_carrier"),
        }
        r = client.post("/api/compiler/lower", json=req)
        assert r.status_code == 200, f"Compiler {name} failed: {r.text}"
        data = r.json()
        assert "CREATE TABLE" in data["sqlite_ddl"]["create_table_sql"]
        assert "CREATE TRIGGER" in data["sqlite_ddl"]["before_insert_trigger_sql"]
        assert data["sqlite_verification"]["verified"] is True
        assert len(data["synthesized_counterexamples"]) > 0


def test_ai_lossledger():
    for name, p in AI_PRESETS.items():
        req = {
            "source_chunks": p["source_chunks"],
            "target_fields": p["target_fields"],
            "max_token_budget": p["max_token_budget"],
            "key_field": p["key_field"],
            "protected_fields": p["protected_fields"],
            "score_field": p["score_field"],
            "text_field": p["text_field"],
        }
        r = client.post("/api/ai/lossledger", json=req)
        assert r.status_code == 200, f"AI {name} failed: {r.text}"
        data = r.json()
        assert data["admitted"] is True
        assert data["token_accounting"]["token_conservation_commutes"] is True
        assert data["loss_ledger_integrity_verified"] is True
        assert data["merkle_digest"] is not None


if __name__ == "__main__":
    print("Running web smoke tests...")
    test_healthz()
    print("  [PASS] healthz passed")
    test_frontend_serving()
    print("  [PASS] frontend serving passed")
    test_relational_presets()
    print("  [PASS] relational presets passed")
    test_bqnf_simulation()
    print("  [PASS] bqnf simulation passed")
    test_compiler_lowering()
    print("  [PASS] compiler lowering passed")
    test_ai_lossledger()
    print("  [PASS] ai lossledger passed")
    print("All smoke tests passed cleanly!")
