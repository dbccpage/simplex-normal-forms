"""Unit and integration tests for Simplex Normal Forms Studio Web API.

Tests the FastAPI endpoints:
  - GET /healthz
  - GET /
  - GET /api/presets
  - POST /api/relational/normalize (preset, custom, lossy decomposition counterexample)
  - POST /api/bqnf/simulate (CDC events, priority-queue cochain, dyadic quantile buckets)
  - POST /api/compiler/lower (NF-IR lowering, subsumption DCE, SQLite DDL, Python guards)
  - POST /api/ai/lossledger (TBNF token accounting, SHA-256 Merkle LossLedger, epistemic firewall)
  - Error handling: 400 Bad Request on empty/invalid inputs, 422 Unprocessable Entity on schema mismatch

Epistemic Standard: Landau Rigor / Claim Discipline Compliant.
AuthorityEffect: None.
certified_implies_authorized: false.
"""

from __future__ import annotations

import unittest
from typing import Any, Dict

from starlette.testclient import TestClient

from web.app import AI_PRESETS, BQNF_PRESETS, COMPILER_PRESETS, PRESETS, app


class TestWebApi(unittest.TestCase):
    """Test suite exercising all REST and UI routes exposed by web.app."""

    def setUp(self) -> None:
        self.client = TestClient(app)

    # =========================================================================
    # Health and Index Routes
    # =========================================================================

    def test_healthz_endpoint(self) -> None:
        """Verifies GET /healthz returns 200 OK with expected service payload."""
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload.get("status"), "ok")
        self.assertEqual(payload.get("service"), "smplxnf-studio")
        self.assertEqual(payload.get("version"), "0.1.0")

    def test_index_html_renders_all_tabs(self) -> None:
        """Verifies GET /studio/ renders the studio SPA with all five workbench tabs."""
        response = self.client.get("/studio/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        html = response.text

        # Verify page title and custom domain
        self.assertIn("Simplex Normal Forms Studio", html)
        self.assertIn("smplxnf.anomalon.com", html)

        # Verify navigation tabs are present in HTML DOM
        self.assertIn("Relational Synthesis & Chase", html)
        self.assertIn("Streaming BQNF Delta Repair", html)
        self.assertIn("NF-IR Compiler Explorer", html)
        self.assertIn("AI Context LossLedger Gateway", html)
        self.assertIn("Quickstart & Import Guide", html)

    def test_presets_catalog_endpoint(self) -> None:
        """Verifies GET /api/presets returns catalogs for all 4 workbench modules."""
        response = self.client.get("/api/presets")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("relational", data)
        self.assertIn("bqnf", data)
        self.assertIn("compiler", data)
        self.assertIn("ai", data)

        self.assertIn("ecommerce", data["relational"])
        self.assertIn("lossy_decomposition", data["relational"])
        self.assertIn("financial_ledger", data["bqnf"])
        self.assertIn("employee_bcnf", data["compiler"])
        self.assertIn("rag_research_context", data["ai"])

    # =========================================================================
    # Module 1: Relational Synthesis & Chase Tableau
    # =========================================================================

    def test_relational_normalize_preset_mode(self) -> None:
        """Tests POST /api/relational/normalize with the e-commerce 3NF violation preset."""
        preset = PRESETS["ecommerce"]
        payload = {
            "attributes": preset["attributes"],
            "dependencies": preset["dependencies"],
        }
        response = self.client.post("/api/relational/normalize", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Attribute partition verification
        self.assertEqual(data["attributes"], sorted(preset["attributes"]))
        self.assertIn(["item_id", "order_id"], data["candidate_keys"])
        self.assertIn("item_id", data["prime_attributes"])
        self.assertIn("order_id", data["prime_attributes"])
        self.assertIn("customer_email", data["non_prime_attributes"])
        self.assertIn("city", data["non_prime_attributes"])

        # Normal form violation detection
        normal_forms = data["normal_forms"]
        self.assertTrue(normal_forms["1NF"]["passed"])
        self.assertFalse(normal_forms["2NF"]["passed"])
        self.assertFalse(normal_forms["3NF"]["passed"])
        self.assertFalse(normal_forms["BCNF"]["passed"])

        # Canonical cover non-empty
        self.assertGreater(len(data["minimal_cover"]), 0)

        # Bernstein 3NF synthesis
        synthesized = data["synthesized_3nf"]
        self.assertGreaterEqual(len(synthesized), 3)
        for table in synthesized:
            self.assertIn("table_name", table)
            self.assertIn("attributes", table)
            self.assertIn("candidate_keys", table)

        # Chase tableau lossless join verification
        chase = data["chase"]
        self.assertTrue(chase["is_implied"])
        self.assertGreater(chase["steps_count"], 0)
        self.assertIsInstance(chase["distinguished_row_index"], int)
        self.assertIsNone(chase["spurious_tuple_witness"])

        # Generated SQL DDL check
        self.assertIn("CREATE TABLE", data["sql_ddl"])
        self.assertIn("PRIMARY KEY", data["sql_ddl"])

    def test_relational_normalize_custom_mode_with_dict_dependencies(self) -> None:
        """Tests POST /api/relational/normalize using dictionary-structured dependencies."""
        payload = {
            "attributes": ["A", "B", "C"],
            "dependencies": [
                {"determinant": ["A"], "dependent": ["B"]},
                {"determinant": ["B"], "dependent": ["C"]},
            ],
        }
        response = self.client.post("/api/relational/normalize", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["candidate_keys"], [["A"]])
        self.assertEqual(data["prime_attributes"], ["A"])
        self.assertEqual(sorted(data["non_prime_attributes"]), ["B", "C"])
        self.assertFalse(data["normal_forms"]["3NF"]["passed"])
        self.assertTrue(data["chase"]["is_implied"])

    def test_relational_normalize_lossy_decomposition_generates_counterexample(self) -> None:
        """Tests POST /api/relational/normalize on a lossy decomposition producing a spurious tuple."""
        preset = PRESETS["lossy_decomposition"]
        payload = {
            "attributes": preset["attributes"],
            "dependencies": preset["dependencies"],
            "custom_components": preset["custom_components"],
        }
        response = self.client.post("/api/relational/normalize", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        chase = data["chase"]
        self.assertFalse(chase["is_implied"])
        self.assertIsNone(chase["distinguished_row_index"])
        self.assertIsNotNone(chase["spurious_tuple_witness"])
        # Witness maps attributes to their tableau symbols
        self.assertIn("A", chase["spurious_tuple_witness"])
        self.assertIn("B", chase["spurious_tuple_witness"])
        self.assertIn("C", chase["spurious_tuple_witness"])

    # =========================================================================
    # Module 2: Streaming BQNF Delta Repair
    # =========================================================================

    def test_bqnf_simulate_with_priority_queue_cochain(self) -> None:
        """Tests POST /api/bqnf/simulate executing CDC event stream with extremum cochains."""
        preset = BQNF_PRESETS["financial_ledger"]
        payload = {
            "boundary": preset["boundary"],
            "events": preset["events"],
            "initial_sales": preset["initial_sales"],
            "use_cochain": True,
            "bucket_width": 20.0,
            "split_threshold": 4,
            "merge_threshold": 1,
            "min_bucket_width": 2.5,
        }
        response = self.client.post("/api/bqnf/simulate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["events_evaluated"], 3)
        decisions = data["event_decisions"]
        self.assertEqual(len(decisions), 3)
        self.assertEqual(decisions[0]["op"], "INSERT")
        self.assertEqual(decisions[1]["op"], "UPDATE")
        self.assertEqual(decisions[2]["op"], "DELETE")

        # Extrema repair log and tally verification
        repair_log = data["extrema_repair_log"]
        self.assertGreater(len(repair_log), 0)
        tally = data["repair_tally"]
        self.assertGreaterEqual(tally["extrema_repairs"], 1)

        # Quantile rebalancing receipts
        reb = data["quantile_rebalance_receipt"]
        self.assertEqual(reb["region"], "North")
        self.assertIn("active_bucket_count", reb)

        buckets = data["quantile_buckets"]
        self.assertGreater(len(buckets), 0)
        for b in buckets:
            self.assertIn("lower_bound", b)
            self.assertIn("upper_bound", b)
            self.assertGreaterEqual(b["upper_bound"], b["lower_bound"])

        self.assertIn("O(log K)", data["cochain_speedup"])

    def test_bqnf_simulate_fallback_without_cochain(self) -> None:
        """Tests POST /api/bqnf/simulate without extremum cochains exercising fallback scan."""
        preset = BQNF_PRESETS["financial_ledger"]
        payload = {
            "boundary": preset["boundary"],
            "events": preset["events"],
            "initial_sales": preset["initial_sales"],
            "use_cochain": False,
        }
        response = self.client.post("/api/bqnf/simulate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["events_evaluated"], 3)
        tally = data["repair_tally"]
        self.assertGreaterEqual(tally["fallback_recomputations"], 1)
        self.assertIn("O(N)", data["cochain_speedup"])

    # =========================================================================
    # Module 3: NF-IR Compiler Playground
    # =========================================================================

    def test_compiler_lower_bcnf_rule(self) -> None:
        """Tests POST /api/compiler/lower compiling BCNF contract to SQLite DDL and Python guard."""
        preset = COMPILER_PRESETS["employee_bcnf"]
        payload = {
            "contract_id": preset["contract_id"],
            "key_field": preset["key_field"],
            "heading": preset["heading"],
            "determinant": preset["determinant"],
            "dependent": preset["dependent"],
            "table_name": preset["table_name"],
            "test_carrier": preset["test_carrier"],
        }
        response = self.client.post("/api/compiler/lower", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Kernel spec AST check
        kernel = data["kernel_spec"]
        self.assertEqual(kernel["contract_id"], "nf.classical.bcnf")
        self.assertEqual(kernel["key_field"], "employee_id")
        self.assertEqual(kernel["collapse_fields"], ["dept_id"])
        self.assertEqual(kernel["protected_law_fields"], ["manager_id"])

        # Poset subsumption analysis
        sub = data["subsumption_analysis"]
        self.assertEqual(sub["compared_against"], "nf.classical.3nf")
        self.assertIn("executed_specs_count", sub)
        self.assertIn("elided_specs_count", sub)
        self.assertIsInstance(sub["is_subsumed"], bool)

        # SQLite DDL lowering
        ddl = data["sqlite_ddl"]
        self.assertEqual(ddl["table_name"], "employees")
        self.assertIn("CREATE TABLE", ddl["create_table_sql"])
        self.assertIn("CREATE TRIGGER", ddl["before_insert_trigger_sql"])
        self.assertIn("NF_VIOLATION:nf.classical.bcnf", ddl["before_insert_trigger_sql"])
        self.assertIn("CREATE TRIGGER", ddl["before_update_trigger_sql"])

        # In-memory SQLite verification against valid carrier
        sqlite_ver = data["sqlite_verification"]
        self.assertTrue(sqlite_ver["verified"])
        self.assertIsNone(sqlite_ver["error"])

        # Python guard code snippet
        self.assertIn("@compile_to_python_decorator", data["python_guard_code"])

        # Counterexample synthesis
        counterexamples = data["synthesized_counterexamples"]
        self.assertGreater(len(counterexamples), 0)

        # Carrier evaluation
        carrier_eval = data["carrier_evaluation"]
        self.assertTrue(carrier_eval["admitted"])
        self.assertTrue(carrier_eval["certified"])
        self.assertFalse(carrier_eval["authorized"])

    def test_compiler_lower_detects_carrier_violation(self) -> None:
        """Tests POST /api/compiler/lower when supplied carrier violates functional dependency."""
        violating_carrier = [
            {"employee_id": "E101", "dept_id": "D1", "manager_id": "Alice", "office_location": "B1"},
            {"employee_id": "E102", "dept_id": "D1", "manager_id": "Bob", "office_location": "B2"},
        ]
        payload = {
            "contract_id": "nf.classical.bcnf",
            "key_field": "employee_id",
            "heading": ["employee_id", "dept_id", "manager_id", "office_location"],
            "determinant": ["dept_id"],
            "dependent": ["manager_id"],
            "table_name": "employees",
            "test_carrier": violating_carrier,
        }
        response = self.client.post("/api/compiler/lower", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # In-memory SQLite trigger intercepts conflict
        sqlite_ver = data["sqlite_verification"]
        self.assertFalse(sqlite_ver["verified"])
        self.assertIn("NF_VIOLATION:nf.classical.bcnf", sqlite_ver["error"])

        # Carrier evaluation marks admission false
        carrier_eval = data["carrier_evaluation"]
        self.assertFalse(carrier_eval["admitted"])
        self.assertIsNotNone(carrier_eval["witness_pair"])

    # =========================================================================
    # Module 4: AI Agent LossLedger Gateway
    # =========================================================================

    def test_ai_lossledger_token_accounting_and_merkle_seal(self) -> None:
        """Tests POST /api/ai/lossledger checking token conservation and Merkle root."""
        preset = AI_PRESETS["rag_research_context"]
        payload = {
            "source_chunks": preset["source_chunks"],
            "target_fields": preset["target_fields"],
            "max_token_budget": preset["max_token_budget"],
            "key_field": preset["key_field"],
            "protected_fields": preset["protected_fields"],
            "score_field": preset["score_field"],
            "text_field": preset["text_field"],
        }
        response = self.client.post("/api/ai/lossledger", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data["admitted"])
        self.assertTrue(data["certified"])
        self.assertFalse(data["authorized"])
        # Lossy context transport is certified under Quarantine terminal
        self.assertEqual(data["canonical_terminal"], "Quarantine")
        self.assertEqual(data["local_route"], "DegradedTransportWithLoss")

        # Token conservation arithmetic
        tokens = data["token_accounting"]
        source_tok = tokens["source_token_count"]
        retained_tok = tokens["retained_token_count"]
        truncated_tok = tokens["truncated_token_count"]
        self.assertEqual(source_tok, retained_tok + truncated_tok)
        self.assertTrue(tokens["token_conservation_commutes"])

        # Cryptographic SHA-256 Merkle LossLedger verification
        self.assertTrue(data["loss_ledger_integrity_verified"])
        self.assertIsNone(data["loss_ledger_error"])
        digest = data["merkle_digest"]
        self.assertIsInstance(digest, str)
        self.assertEqual(len(digest), 64)

        # Attribute erasure tracking
        erased = data["erased_attributes"]
        self.assertIn("internal_debug_trace", erased)
        self.assertIn("vector_norm", erased)

        # Epistemic authority firewall
        firewall = data["epistemic_firewall"]
        self.assertEqual(firewall["authority_effect"], "None")
        self.assertFalse(firewall["certified_implies_authorized"])

    def test_ai_lossledger_lossless_projection_preserves_structure(self) -> None:
        """Tests POST /api/ai/lossledger when projection is lossless without token truncation."""
        chunk = {
            "chunk_id": "c1",
            "doc_title": "Title 1",
            "text": "Short atomic statement.",
            "relevance_score": 0.99,
        }
        payload = {
            "source_chunks": [chunk],
            "target_fields": ["chunk_id", "doc_title", "text", "relevance_score"],
            "max_token_budget": 50,
            "key_field": "chunk_id",
            "protected_fields": ["chunk_id"],
            "score_field": "relevance_score",
            "text_field": "text",
        }
        response = self.client.post("/api/ai/lossledger", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data["admitted"])
        self.assertEqual(data["canonical_terminal"], "Preserve")
        self.assertEqual(data["local_route"], "TransportOk")
        self.assertEqual(data["token_accounting"]["truncated_token_count"], 0)

    # =========================================================================
    # Error Handling and Edge Cases
    # =========================================================================

    def test_error_handling_empty_schema(self) -> None:
        """Verifies POST /api/relational/normalize rejects empty attribute sets with 400."""
        payload = {"attributes": [], "dependencies": []}
        response = self.client.post("/api/relational/normalize", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("cannot be empty", response.json().get("detail", ""))

    def test_error_handling_malformed_dependency_string(self) -> None:
        """Verifies POST /api/relational/normalize rejects dependencies without '->' with 400."""
        payload = {
            "attributes": ["A", "B"],
            "dependencies": ["A implies B"],
        }
        response = self.client.post("/api/relational/normalize", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("must contain '->'", response.json().get("detail", ""))

    def test_error_handling_malformed_json_types_return_422(self) -> None:
        """Verifies invalid JSON structure returns standard 422 Unprocessable Entity."""
        # Non-list attributes
        response = self.client.post(
            "/api/relational/normalize",
            json={"attributes": "not_a_list", "dependencies": []},
        )
        self.assertEqual(response.status_code, 422)

        # Missing required target_fields in AI request
        response = self.client.post(
            "/api/ai/lossledger",
            json={"source_chunks": [{"id": 1}]},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
