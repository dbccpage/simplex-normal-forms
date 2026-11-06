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
    assert r.headers.get("cache-control") == "no-cache"

    studio = client.get("/studio/")
    assert studio.status_code == 200
    assert "Simplex-NF Studio" in studio.text
    assert studio.headers.get("cache-control") == "no-cache"
    assert "Experimental" in studio.text

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
        assert "sql_ddl_postgres" in data
        assert "sql_ddl_sqlserver" in data
        assert "PRIMARY KEY" in data["sql_ddl_postgres"]
        assert "PRIMARY KEY" in data["sql_ddl_sqlserver"]
        for step in data["chase"]["steps"]:
            assert "changed_cells" in step
            assert len(step["changed_cells"]) >= 1
        if name == "lossy_decomposition":
            assert data["chase"]["is_implied"] is False
            assert data["chase"]["spurious_tuple_witness"] is not None
            assert (
                "this row is in the join of the pieces but not in the original"
                in data["chase"]["spurious_tuple_explanation"]
            )
        else:
            assert data["chase"]["is_implied"] is True
            assert "FOREIGN KEY" in data["sql_ddl_postgres"]
            assert "FOREIGN KEY" in data["sql_ddl_sqlserver"]



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


def test_ddl_topological_order_and_sqlite_fk_execution():
    import sqlite3

    # Parent table (y -> u1, u2, u3) has 4 attributes while child table (x -> y) has 2 attributes.
    # Parent table must still be created before child table in both PostgreSQL and SQL Server DDL.
    req = {
        "attributes": ["x", "y", "u1", "u2", "u3"],
        "dependencies": ["x -> y", "y -> u1, u2, u3"],
    }
    r = client.post("/api/relational/normalize", json=req)
    assert r.status_code == 200, r.text
    data = r.json()
    pg_ddl = data["sql_ddl_postgres"]
    ms_ddl = data["sql_ddl_sqlserver"]

    assert pg_ddl.index('CREATE TABLE "rel_3nf_table_2"') < pg_ddl.index('CREATE TABLE "rel_3nf_table_1"')
    assert ms_ddl.index("CREATE TABLE [rel_3nf_table_2]") < ms_ddl.index("CREATE TABLE [rel_3nf_table_1]")

    for ddl in (pg_ddl, ms_ddl):
        conn = sqlite3.connect(":memory:")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(ddl)
        conn.execute('INSERT INTO "rel_3nf_table_2" ("u1", "u2", "u3", "y") VALUES (\'a\', \'b\', \'c\', \'p1\');')
        conn.execute('INSERT INTO "rel_3nf_table_1" ("x", "y") VALUES (\'c1\', \'p1\');')
        try:
            conn.execute('INSERT INTO "rel_3nf_table_1" ("x", "y") VALUES (\'c2\', \'missing_parent\');')
            raise AssertionError("Expected FOREIGN KEY constraint failure for orphan child row")
        except sqlite3.IntegrityError:
            pass
        conn.close()

    # Secondary candidate key columns (such as ssn in healthcare) must also be marked NOT NULL
    hc = PRESETS["healthcare"]
    r_hc = client.post(
        "/api/relational/normalize",
        json={"attributes": hc["attributes"], "dependencies": hc["dependencies"]},
    )
    assert r_hc.status_code == 200
    hc_data = r_hc.json()
    assert '"ssn" TEXT NOT NULL' in hc_data["sql_ddl_postgres"]
    assert "[ssn] NVARCHAR(128) NOT NULL" in hc_data["sql_ddl_sqlserver"]

    for name, p in PRESETS.items():
        r_p = client.post(
            "/api/relational/normalize",
            json={
                "attributes": p["attributes"],
                "dependencies": p["dependencies"],
                "custom_components": p.get("custom_components"),
            },
        )
        assert r_p.status_code == 200
        p_data = r_p.json()
        for ddl in (p_data["sql_ddl_postgres"], p_data["sql_ddl_sqlserver"]):
            conn = sqlite3.connect(":memory:")
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.executescript(ddl)
            conn.close()


def test_ddl_live_postgresql_validation():
    import os
    import shutil
    import subprocess
    import pytest

    require_live = os.environ.get("REQUIRE_LIVE_DB_TESTS") == "1"
    if shutil.which("psql") is None:
        if require_live:
            pytest.fail("REQUIRE_LIVE_DB_TESTS=1 but psql is not available")
        pytest.skip("PostgreSQL instance / psql not available in local sandbox; DDL live execution not run")
    probe = subprocess.run(
        ["psql", "-c", "SELECT 1;"],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        if require_live:
            pytest.fail(f"REQUIRE_LIVE_DB_TESTS=1 but PostgreSQL server unreachable: {probe.stderr or probe.stdout}")
        pytest.skip("PostgreSQL server unreachable in local sandbox; DDL live execution not run")

    for name, p in PRESETS.items():
        r = client.post(
            "/api/relational/normalize",
            json={
                "attributes": p["attributes"],
                "dependencies": p["dependencies"],
                "custom_components": p.get("custom_components"),
            },
        )
        assert r.status_code == 200
        sql = "BEGIN;\n" + r.json()["sql_ddl_postgres"] + "\nROLLBACK;\n"
        res = subprocess.run(
            ["psql", "-v", "ON_ERROR_STOP=1"],
            input=sql,
            capture_output=True,
            text=True,
        )
        assert res.returncode == 0, f"PostgreSQL DDL execution failed for {name}: {res.stderr}"

    fk_req = {
        "attributes": ["x", "y", "u1", "u2", "u3"],
        "dependencies": ["x -> y", "y -> u1, u2, u3"],
    }
    r_fk = client.post("/api/relational/normalize", json=fk_req)
    assert r_fk.status_code == 200
    pg_fk_ddl = r_fk.json()["sql_ddl_postgres"]
    valid_sql = (
        "BEGIN;\n"
        + pg_fk_ddl
        + '\nINSERT INTO "rel_3nf_table_2" ("u1", "u2", "u3", "y") VALUES (\'a\', \'b\', \'c\', \'p1\');'
        + '\nINSERT INTO "rel_3nf_table_1" ("x", "y") VALUES (\'c1\', \'p1\');'
        + "\nROLLBACK;\n"
    )
    res_valid = subprocess.run(
        ["psql", "-v", "ON_ERROR_STOP=1"],
        input=valid_sql,
        capture_output=True,
        text=True,
    )
    assert res_valid.returncode == 0, f"PostgreSQL valid FK insert failed: {res_valid.stderr}"

    orphan_sql = (
        "BEGIN;\n"
        + pg_fk_ddl
        + '\nINSERT INTO "rel_3nf_table_1" ("x", "y") VALUES (\'c2\', \'missing_parent\');'
        + "\nROLLBACK;\n"
    )
    res_orphan = subprocess.run(
        ["psql", "-v", "ON_ERROR_STOP=1"],
        input=orphan_sql,
        capture_output=True,
        text=True,
    )
    assert res_orphan.returncode != 0, "Expected PostgreSQL FOREIGN KEY violation on orphan row"
    assert "foreign key" in (res_orphan.stderr + res_orphan.stdout).lower(), (
        f"Expected foreign key constraint diagnostic from PostgreSQL, got: {res_orphan.stderr or res_orphan.stdout}"
    )

    hc = PRESETS["healthcare"]
    r_hc = client.post(
        "/api/relational/normalize",
        json={"attributes": hc["attributes"], "dependencies": hc["dependencies"]},
    )
    assert r_hc.status_code == 200
    pg_hc_ddl = r_hc.json()["sql_ddl_postgres"]
    dup_ssn_sql = (
        "BEGIN;\n"
        + pg_hc_ddl
        + '\nINSERT INTO "rel_3nf_table_1" ("ward_id", "ward_building", "head_nurse") VALUES (\'W1\', \'North\', \'Smith\');'
        + '\nINSERT INTO "rel_3nf_table_2" ("patient_id", "patient_name", "ssn", "ward_id") VALUES (\'P1\', \'Ada\', \'123-45-6789\', \'W1\');'
        + '\nINSERT INTO "rel_3nf_table_2" ("patient_id", "patient_name", "ssn", "ward_id") VALUES (\'P2\', \'Grace\', \'123-45-6789\', \'W1\');'
        + "\nROLLBACK;\n"
    )
    res_dup_pg = subprocess.run(
        ["psql", "-v", "ON_ERROR_STOP=1"],
        input=dup_ssn_sql,
        capture_output=True,
        text=True,
    )
    assert res_dup_pg.returncode != 0 and "unique" in (res_dup_pg.stderr + res_dup_pg.stdout).lower(), (
        f"Expected PostgreSQL UNIQUE constraint violation on duplicate ssn, got: {res_dup_pg.stderr or res_dup_pg.stdout}"
    )

    null_ssn_sql = (
        "BEGIN;\n"
        + pg_hc_ddl
        + '\nINSERT INTO "rel_3nf_table_1" ("ward_id", "ward_building", "head_nurse") VALUES (\'W1\', \'North\', \'Smith\');'
        + '\nINSERT INTO "rel_3nf_table_2" ("patient_id", "patient_name", "ssn", "ward_id") VALUES (\'P3\', \'Alan\', NULL, \'W1\');'
        + "\nROLLBACK;\n"
    )
    res_null_pg = subprocess.run(
        ["psql", "-v", "ON_ERROR_STOP=1"],
        input=null_ssn_sql,
        capture_output=True,
        text=True,
    )
    assert res_null_pg.returncode != 0 and "null" in (res_null_pg.stderr + res_null_pg.stdout).lower(), (
        f"Expected PostgreSQL NOT NULL constraint violation on null ssn, got: {res_null_pg.stderr or res_null_pg.stdout}"
    )


def test_ddl_live_sqlserver_validation():
    import os
    import shutil
    import subprocess
    import pytest

    require_live = os.environ.get("REQUIRE_LIVE_DB_TESTS") == "1"
    if shutil.which("sqlcmd") is None:
        if require_live:
            pytest.fail("REQUIRE_LIVE_DB_TESTS=1 but sqlcmd is not available")
        pytest.skip("sqlcmd not available; SQL Server DDL live execution not run")

    server = os.environ.get("MSSQL_SERVER")
    if not server and os.name == "nt":
        server = r"(localdb)\MSSQLLocalDB"
    base_cmd = ["sqlcmd"]
    if server:
        base_cmd.extend(["-S", server])
    if os.environ.get("MSSQL_USER") and os.environ.get("MSSQL_PASSWORD"):
        base_cmd.extend(["-U", os.environ["MSSQL_USER"], "-P", os.environ["MSSQL_PASSWORD"]])

    probe = subprocess.run(
        base_cmd + ["-l", "5", "-Q", "SELECT 1"],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        if require_live:
            pytest.fail(f"REQUIRE_LIVE_DB_TESTS=1 but SQL Server unreachable: {probe.stderr or probe.stdout}")
        pytest.skip("SQL Server LocalDB instance unreachable in sandbox; DDL live execution not run")

    for name, p in PRESETS.items():
        r = client.post(
            "/api/relational/normalize",
            json={
                "attributes": p["attributes"],
                "dependencies": p["dependencies"],
                "custom_components": p.get("custom_components"),
            },
        )
        assert r.status_code == 200
        sql = "BEGIN TRANSACTION;\n" + r.json()["sql_ddl_sqlserver"] + "\nROLLBACK TRANSACTION;\nGO\n"
        res = subprocess.run(
            base_cmd + ["-b"],
            input=sql,
            capture_output=True,
            text=True,
        )
        assert res.returncode == 0, f"SQL Server DDL execution failed for {name}: {res.stderr or res.stdout}"

    fk_req = {
        "attributes": ["x", "y", "u1", "u2", "u3"],
        "dependencies": ["x -> y", "y -> u1, u2, u3"],
    }
    r_fk = client.post("/api/relational/normalize", json=fk_req)
    assert r_fk.status_code == 200
    ms_fk_ddl = r_fk.json()["sql_ddl_sqlserver"]
    valid_sql = (
        "BEGIN TRANSACTION;\n"
        + ms_fk_ddl
        + "\nINSERT INTO [rel_3nf_table_2] ([u1], [u2], [u3], [y]) VALUES ('a', 'b', 'c', 'p1');"
        + "\nINSERT INTO [rel_3nf_table_1] ([x], [y]) VALUES ('c1', 'p1');"
        + "\nROLLBACK TRANSACTION;\nGO\n"
    )
    res_valid = subprocess.run(
        base_cmd + ["-b"],
        input=valid_sql,
        capture_output=True,
        text=True,
    )
    assert res_valid.returncode == 0, f"SQL Server valid FK insert failed: {res_valid.stderr or res_valid.stdout}"

    orphan_sql = (
        "BEGIN TRANSACTION;\n"
        + ms_fk_ddl
        + "\nINSERT INTO [rel_3nf_table_1] ([x], [y]) VALUES ('c2', 'missing_parent');"
        + "\nROLLBACK TRANSACTION;\nGO\n"
    )
    res_orphan = subprocess.run(
        base_cmd + ["-b"],
        input=orphan_sql,
        capture_output=True,
        text=True,
    )
    assert res_orphan.returncode != 0, "Expected SQL Server FOREIGN KEY violation on orphan row"
    assert "foreign key" in (res_orphan.stderr + res_orphan.stdout).lower(), (
        f"Expected foreign key constraint diagnostic from SQL Server, got: {res_orphan.stderr or res_orphan.stdout}"
    )

    hc = PRESETS["healthcare"]
    r_hc = client.post(
        "/api/relational/normalize",
        json={"attributes": hc["attributes"], "dependencies": hc["dependencies"]},
    )
    assert r_hc.status_code == 200
    ms_hc_ddl = r_hc.json()["sql_ddl_sqlserver"]
    dup_ssn_ms_sql = (
        "BEGIN TRANSACTION;\n"
        + ms_hc_ddl
        + "\nINSERT INTO [rel_3nf_table_1] ([ward_id], [ward_building], [head_nurse]) VALUES ('W1', 'North', 'Smith');"
        + "\nINSERT INTO [rel_3nf_table_2] ([patient_id], [patient_name], [ssn], [ward_id]) VALUES ('P1', 'Ada', '123-45-6789', 'W1');"
        + "\nINSERT INTO [rel_3nf_table_2] ([patient_id], [patient_name], [ssn], [ward_id]) VALUES ('P2', 'Grace', '123-45-6789', 'W1');"
        + "\nROLLBACK TRANSACTION;\nGO\n"
    )
    res_dup_ms = subprocess.run(
        base_cmd + ["-b"],
        input=dup_ssn_ms_sql,
        capture_output=True,
        text=True,
    )
    assert res_dup_ms.returncode != 0 and "unique" in (res_dup_ms.stderr + res_dup_ms.stdout).lower(), (
        f"Expected SQL Server UNIQUE constraint violation on duplicate ssn, got: {res_dup_ms.stderr or res_dup_ms.stdout}"
    )

    null_ssn_ms_sql = (
        "BEGIN TRANSACTION;\n"
        + ms_hc_ddl
        + "\nINSERT INTO [rel_3nf_table_1] ([ward_id], [ward_building], [head_nurse]) VALUES ('W1', 'North', 'Smith');"
        + "\nINSERT INTO [rel_3nf_table_2] ([patient_id], [patient_name], [ssn], [ward_id]) VALUES ('P3', 'Alan', NULL, 'W1');"
        + "\nROLLBACK TRANSACTION;\nGO\n"
    )
    res_null_ms = subprocess.run(
        base_cmd + ["-b"],
        input=null_ssn_ms_sql,
        capture_output=True,
        text=True,
    )
    assert res_null_ms.returncode != 0 and "null" in (res_null_ms.stderr + res_null_ms.stdout).lower(), (
        f"Expected SQL Server NOT NULL constraint violation on null ssn, got: {res_null_ms.stderr or res_null_ms.stdout}"
    )


def test_live_mongodb_validation():
    import json
    import os
    import shutil
    import subprocess
    import pytest

    require_live = os.environ.get("REQUIRE_LIVE_DB_TESTS") == "1"
    if shutil.which("mongosh") is None:
        if require_live:
            pytest.fail("REQUIRE_LIVE_DB_TESTS=1 but mongosh is not available")
        pytest.skip("mongosh not available; MongoDB live validation not run")

    probe = subprocess.run(
        ["mongosh", "--quiet", "--eval", "db.runCommand({ ping: 1 }).ok"],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        if require_live:
            pytest.fail(f"REQUIRE_LIVE_DB_TESTS=1 but MongoDB server unreachable: {probe.stderr or probe.stdout}")
        pytest.skip("MongoDB server unreachable in sandbox; MongoDB live validation not run")

    hc = PRESETS["healthcare"]
    r = client.post(
        "/api/relational/normalize",
        json={"attributes": hc["attributes"], "dependencies": hc["dependencies"]},
    )
    assert r.status_code == 200
    tables = r.json()["synthesized_3nf"]
    patient_table = next(t for t in tables if "patient_id" in t["attributes"] and "ssn" in t["attributes"])
    required_cols = sorted({col for key in patient_table["candidate_keys"] for col in key})
    assert "patient_id" in required_cols and "ssn" in required_cols

    mongo_script = f"""
    const collName = "smplxnf_patient_3nf_check";
    db.getCollection(collName).drop();
    db.createCollection(collName, {{
      validator: {{
        $jsonSchema: {{
          bsonType: "object",
          required: {json.dumps(required_cols)}
        }}
      }}
    }});
    const okRes = db.getCollection(collName).insertOne({{ patient_id: "P1", ssn: "123-45-6789", patient_name: "Ada", ward_id: "W1" }});
    if (!okRes.acknowledged) {{ throw new Error("Expected valid 3NF document insert to succeed"); }}
    let rejected = false;
    try {{
      db.getCollection(collName).insertOne({{ patient_id: "P2", patient_name: "MissingSecondaryKey" }});
    }} catch (e) {{
      rejected = true;
    }}
    db.getCollection(collName).drop();
    if (!rejected) {{ throw new Error("Expected missing candidate key attribute ssn to be rejected by validator"); }}
    print("MONGODB_3NF_VALIDATOR_OK");
    """
    res = subprocess.run(
        ["mongosh", "--quiet"],
        input=mongo_script,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0 and "MONGODB_3NF_VALIDATOR_OK" in res.stdout, (
        f"MongoDB live validation failed: {res.stderr or res.stdout}"
    )


if __name__ == "__main__":
    print("Running web smoke tests...")
    test_healthz()
    print("  [PASS] healthz passed")
    test_frontend_serving()
    print("  [PASS] frontend serving passed")
    test_relational_presets()
    print("  [PASS] relational presets passed")
    test_ddl_topological_order_and_sqlite_fk_execution()
    print("  [PASS] ddl topological order and sqlite fk execution passed")
    test_bqnf_simulation()
    print("  [PASS] bqnf simulation passed")
    test_compiler_lowering()
    print("  [PASS] compiler lowering passed")
    test_ai_lossledger()
    print("  [PASS] ai lossledger passed")
    print("All smoke tests passed cleanly!")
