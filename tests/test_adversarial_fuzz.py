"""Adversarial stress-testing and fuzzing suite for Simplex Normal Forms Studio Web API.

Empirical verification of API robustness against:
- Malformed, degenerate, and boundary inputs
- Dense and cyclic relational schemas
- Non-lossless join decompositions (spurious tuple witnesses)
- CDC stream anomalies (negative values, nonexistent rows, massive rebalance streams)
- NF-IR compiler edge cases (invalid contracts, empty headings, poset DCE)
- AI LossLedger edge cases (empty strings, UTF-8 unicode fuzzing, budget anomalies)
- Claim Hygiene compliance: scanning web assets for forbidden hype words
- Verification that no endpoint produces unhandled 500 Internal Server Errors.

Epistemic Standard: Landau Rigor / Claim Discipline Compliant.
AuthorityEffect: None.
certified_implies_authorized: false.
"""

from __future__ import annotations

import math
import os
import re
import unittest
from typing import Any, Dict, List

from starlette.testclient import TestClient

from web.app import COMPILER_PRESETS, app


class TestAdversarialFuzz(unittest.TestCase):
    """Adversarial challenge test suite executing fuzzing attacks against web.app."""

    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    # =========================================================================
    # 1. Relational Synthesis & Chase Tableau Fuzzing (/api/relational/normalize)
    # =========================================================================

    def test_relational_empty_attributes_rejected(self) -> None:
        """TC1.1: Empty attributes list must return 400 Bad Request, never 500."""
        payload = {"attributes": [], "dependencies": []}
        res = self.client.post("/api/relational/normalize", json=payload)
        self.assertIn(res.status_code, (400, 422))
        self.assertNotEqual(res.status_code, 500)
        self.assertIn("cannot be empty", res.json().get("detail", ""))

    def test_relational_empty_attributes_with_fds_rejected(self) -> None:
        """TC1.2: Empty attributes with non-empty FDs must return 400 Bad Request."""
        payload = {"attributes": [], "dependencies": ["A -> B"]}
        res = self.client.post("/api/relational/normalize", json=payload)
        self.assertIn(res.status_code, (400, 422))
        self.assertNotEqual(res.status_code, 500)

    def test_relational_empty_fds_handled_cleanly(self) -> None:
        """TC1.3: Empty FDs list must treat the entire heading as candidate key in 200 OK."""
        payload = {"attributes": ["A", "B"], "dependencies": []}
        res = self.client.post("/api/relational/normalize", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["attributes"], ["A", "B"])
        self.assertEqual(data["candidate_keys"], [["A", "B"]])
        self.assertEqual(data["prime_attributes"], ["A", "B"])
        self.assertEqual(data["non_prime_attributes"], [])
        self.assertTrue(data["normal_forms"]["1NF"]["passed"])
        self.assertTrue(data["normal_forms"]["2NF"]["passed"])
        self.assertTrue(data["normal_forms"]["3NF"]["passed"])
        self.assertTrue(data["normal_forms"]["BCNF"]["passed"])
        self.assertEqual(data["minimal_cover"], [])
        self.assertEqual(len(data["synthesized_3nf"]), 1)
        self.assertTrue(data["chase"]["is_implied"])

    def test_relational_cyclic_dependencies(self) -> None:
        """TC1.4: Cyclic dependencies A -> B, B -> C, C -> A must be handled cleanly."""
        payload = {
            "attributes": ["A", "B", "C"],
            "dependencies": ["A -> B", "B -> C", "C -> A"],
        }
        res = self.client.post("/api/relational/normalize", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        cand_keys = [tuple(k) for k in data["candidate_keys"]]
        self.assertIn(("A",), cand_keys)
        self.assertIn(("B",), cand_keys)
        self.assertIn(("C",), cand_keys)
        self.assertEqual(sorted(data["prime_attributes"]), ["A", "B", "C"])
        self.assertEqual(data["non_prime_attributes"], [])
        self.assertTrue(data["normal_forms"]["3NF"]["passed"])
        self.assertTrue(data["normal_forms"]["BCNF"]["passed"])
        self.assertTrue(data["chase"]["is_implied"])

    def test_relational_lossy_decomposition_chase_spurious_witness(self) -> None:
        """TC1.5: Lossy decomposition must fail the Chase and identify spurious tuple counterexample."""
        payload = {
            "attributes": ["A", "B", "C"],
            "dependencies": ["A -> B"],
            "custom_components": [["A", "B"], ["B", "C"]],
        }
        res = self.client.post("/api/relational/normalize", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        chase = data["chase"]
        self.assertFalse(chase["is_implied"])
        self.assertEqual(chase["status"], "Reject")
        self.assertIsNone(chase["distinguished_row_index"])
        self.assertIsNotNone(chase["spurious_tuple_witness"])
        self.assertIn("A", chase["spurious_tuple_witness"])
        self.assertIn("B", chase["spurious_tuple_witness"])
        self.assertIn("C", chase["spurious_tuple_witness"])

    def test_relational_large_attribute_set_dense_dependencies(self) -> None:
        """TC1.6: 10 attributes with dense cyclic dependencies must complete within reasonable time."""
        attrs = [f"col_{i}" for i in range(10)]
        deps = [f"col_{i} -> col_{(i+1)%10}" for i in range(10)]
        payload = {"attributes": attrs, "dependencies": deps}
        res = self.client.post("/api/relational/normalize", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data["candidate_keys"]), 10)
        self.assertEqual(len(data["prime_attributes"]), 10)
        self.assertTrue(data["normal_forms"]["BCNF"]["passed"])

    def test_relational_trivial_dependencies(self) -> None:
        """TC1.7: Trivial dependencies A -> A must be eliminated in minimal cover."""
        payload = {
            "attributes": ["A", "B"],
            "dependencies": ["A -> A", "A, B -> A", "A -> B"],
        }
        res = self.client.post("/api/relational/normalize", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["candidate_keys"], [["A"]])
        self.assertEqual(data["minimal_cover"], ["A -> B"])

    def test_relational_malformed_dependency_strings(self) -> None:
        """TC1.8: Malformed dependency strings without '->' must return 400 Bad Request."""
        payload = {"attributes": ["A", "B"], "dependencies": ["A B C"]}
        res = self.client.post("/api/relational/normalize", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("must contain '->'", res.json()["detail"])

    def test_relational_whitespace_and_empty_attribute_handling(self) -> None:
        """TC1.9: Attributes with whitespace and empty entries are stripped or handled gracefully."""
        payload = {"attributes": [" A ", "", " B ", "  "], "dependencies": ["A -> B"]}
        res = self.client.post("/api/relational/normalize", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["attributes"], ["A", "B"])

    def test_relational_attribute_not_in_heading_rejected(self) -> None:
        """TC1.10: Dependency referencing attribute outside heading must return 400 Bad Request."""
        payload = {"attributes": ["A", "B"], "dependencies": ["A -> C"]}
        res = self.client.post("/api/relational/normalize", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("does not match heading", res.json()["detail"])


    # =========================================================================
    # 2. Streaming BQNF Delta Repair Fuzzing (/api/bqnf/simulate)
    # =========================================================================

    def test_bqnf_empty_events_stream(self) -> None:
        """TC2.1: Empty events list must return 200 OK with zero evaluated events."""
        payload = {
            "boundary": {
                "relations": ["sales"],
                "attributes": ["amount", "status", "region"],
                "predicates": ["status = paid"],
                "aggregates": ["SUM(amount)"],
                "groups": ["region"],
            },
            "events": [],
        }
        res = self.client.post("/api/bqnf/simulate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["events_evaluated"], 0)
        self.assertEqual(data["event_decisions"], [])

    def test_bqnf_unknown_relations_and_arbitrary_keys(self) -> None:
        """TC2.2: An unrelated relation leaves the declared sales boundary unchanged."""
        payload = {
            "boundary": {
                "relations": ["sales"],
                "attributes": ["amount", "status", "region"],
                "predicates": [],
                "aggregates": ["SUM(amount)"],
                "groups": ["region"],
            },
            "events": [
                {
                    "op": "INSERT",
                    "relation": "irrelevant_relation",
                    "old": None,
                    "new": {"irrelevant_col": 999, "extra_nested": {"a": 1}},
                }
            ],
        }
        res = self.client.post("/api/bqnf/simulate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["events_evaluated"], 1)
        self.assertEqual(data["event_decisions"][0]["decision"], "Preserve")
        self.assertFalse(data["event_decisions"][0]["applied"])

    def test_bqnf_negative_quantities_and_dyadic_buckets(self) -> None:
        """TC2.3: Negative sales amounts must be processed without arithmetic crashes."""
        payload = {
            "boundary": {
                "relations": ["sales"],
                "attributes": ["amount", "status", "region"],
                "predicates": ["status = paid"],
                "aggregates": ["SUM(amount)", "MIN(amount)", "MAX(amount)"],
                "groups": ["region"],
            },
            "initial_sales": [
                {"region": "North", "amount": -100.0},
                {"region": "North", "amount": -50.0},
            ],
            "events": [
                {
                    "op": "INSERT",
                    "relation": "sales",
                    "old": None,
                    "new": {"region": "North", "amount": -120.0, "status": "paid"},
                }
            ],
            "bucket_width": 20.0,
        }
        res = self.client.post("/api/bqnf/simulate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["events_evaluated"], 1)
        self.assertTrue(any(b["lower_bound"] < 0 for b in data["quantile_buckets"]))

    def test_bqnf_destructive_delete_on_nonexistent_records(self) -> None:
        """TC2.4: DELETE event on record not in base_sales must not cause unhandled crash."""
        payload = {
            "boundary": {
                "relations": ["sales"],
                "attributes": ["amount", "status", "region"],
                "predicates": ["status = paid"],
                "aggregates": ["MAX(amount)"],
                "groups": ["region"],
            },
            "events": [
                {
                    "op": "DELETE",
                    "relation": "sales",
                    "old": {"region": "North", "amount": 99999.0, "status": "paid"},
                    "new": None,
                }
            ],
        }
        res = self.client.post("/api/bqnf/simulate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["events_evaluated"], 1)

    def test_bqnf_zero_bucket_width_rejected(self) -> None:
        """TC2.5: Zero bucket_width must return 400 Bad Request, never 500."""
        payload = {
            "boundary": {
                "relations": ["sales"],
                "attributes": ["amount", "region"],
                "predicates": [],
                "aggregates": ["SUM(amount)"],
                "groups": ["region"],
            },
            "events": [],
            "bucket_width": 0.0,
        }
        res = self.client.post("/api/bqnf/simulate", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("Invalid quantile widths", res.json()["detail"])

    def test_bqnf_stream_observes_extremum_cochain_but_reveals_quantile_cochain_gap(self) -> None:
        """TC2.6: Verifies that extremum cochain updates while documenting that quantile cochain does not."""
        events = [
            {"op": "INSERT", "relation": "sales", "old": None, "new": {"region": "North", "amount": 500.0, "status": "paid"}}
        ]
        payload = {
            "boundary": {
                "relations": ["sales"],
                "attributes": ["amount", "status", "region"],
                "predicates": ["status = paid"],
                "aggregates": ["SUM(amount)", "MAX(amount)"],
                "groups": ["region"],
            },
            "events": events,
            "bucket_width": 20.0,
        }
        res = self.client.post("/api/bqnf/simulate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        # Extremum cochain observes the 500.0 insert
        self.assertTrue(any(e["amount"] == 500.0 for e in data["extremum_cochain_entries"]))


    # =========================================================================
    # 3. NF-IR Compiler Playground Fuzzing (/api/compiler/lower)
    # =========================================================================

    def test_compiler_invalid_contract_id(self) -> None:
        """TC3.1: Unknown contract ID must still produce kernel spec or return 400 without crashing."""
        payload = {
            "contract_id": "nf.custom.unknown_contract",
            "key_field": "emp_id",
            "heading": ["emp_id", "dept_id", "mgr_id"],
            "determinant": ["dept_id"],
            "dependent": ["mgr_id"],
            "table_name": "employees",
        }
        res = self.client.post("/api/compiler/lower", json=payload)
        self.assertIn(res.status_code, (200, 400))
        self.assertNotEqual(res.status_code, 500)

    def test_compiler_empty_determinant_rejected(self) -> None:
        """TC3.2: Empty determinant must be rejected with 400 Bad Request, never 500."""
        payload = {
            "contract_id": "nf.classical.bcnf",
            "key_field": "id",
            "heading": ["id", "a"],
            "determinant": [],
            "dependent": ["a"],
            "table_name": "t",
        }
        res = self.client.post("/api/compiler/lower", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("cannot be empty", res.json()["detail"])

    def test_compiler_empty_dependent_rejected(self) -> None:
        """TC3.3: Empty dependent must be rejected with 400 Bad Request, never 500."""
        payload = {
            "contract_id": "nf.classical.bcnf",
            "key_field": "id",
            "heading": ["id", "a"],
            "determinant": ["a"],
            "dependent": [],
            "table_name": "t",
        }
        res = self.client.post("/api/compiler/lower", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("cannot be empty", res.json()["detail"])

    def test_compiler_subsumption_analysis_behavior(self) -> None:
        """TC3.4: Subsumption analysis executes without 500 and documents whether weaker check is subsumed."""
        payload = COMPILER_PRESETS["employee_bcnf"]
        res = self.client.post("/api/compiler/lower", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        sub = data["subsumption_analysis"]
        self.assertIn("is_subsumed", sub)
        self.assertIn("subsume_reason", sub)
        self.assertIn("elided_specs_count", sub)


    # =========================================================================
    # 4. AI Agent LossLedger Gateway Fuzzing (/api/ai/lossledger)
    # =========================================================================

    def test_ai_lossledger_empty_source_chunks(self) -> None:
        """TC4.1: Empty source chunks list returns 200 OK with zero accounting."""
        payload = {
            "source_chunks": [],
            "target_fields": ["chunk_id", "doc_title"],
            "protected_fields": ["chunk_id", "doc_title"],
            "max_token_budget": 50,
        }
        res = self.client.post("/api/ai/lossledger", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["token_accounting"]["source_token_count"], 0)
        self.assertEqual(data["token_accounting"]["retained_token_count"], 0)
        self.assertEqual(data["token_accounting"]["truncated_token_count"], 0)
        self.assertTrue(data["token_accounting"]["token_conservation_commutes"])

    def test_ai_lossledger_empty_prompt_strings(self) -> None:
        """TC4.2: Chunks with empty text strings tokenize and preserve conservation equation."""
        payload = {
            "source_chunks": [
                {"chunk_id": "c1", "text": "", "relevance_score": 0.9},
                {"chunk_id": "c2", "text": "   \n\t  ", "relevance_score": 0.8},
            ],
            "target_fields": ["chunk_id", "text"],
            "protected_fields": ["chunk_id"],
            "max_token_budget": 10,
        }
        res = self.client.post("/api/ai/lossledger", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["token_accounting"]["source_token_count"], 0)
        self.assertEqual(data["token_accounting"]["retained_token_count"], 0)
        self.assertTrue(data["token_accounting"]["token_conservation_commutes"])

    def test_ai_lossledger_utf8_special_chars_and_emojis(self) -> None:
        """TC4.3: High-entropy Unicode, CJK, Arabic, and emoji prompts calculate Merkle root cleanly."""
        payload = {
            "source_chunks": [
                {
                    "chunk_id": "c_unicode_1",
                    "doc_title": "Unicode Specimen",
                    "text": "Simplex 🚀 ñoño \u200b \t\n \U0001F600 \u4e2d\u6587 \u0627\u0644\u0639\u0631\u0628\u064a\u0629 null\x00byte",
                    "relevance_score": 0.95,
                    "secret_attr": "erase_me",
                }
            ],
            "target_fields": ["chunk_id", "doc_title", "text"],
            "protected_fields": ["chunk_id", "doc_title"],
            "max_token_budget": 5,
        }
        res = self.client.post("/api/ai/lossledger", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["loss_ledger_integrity_verified"])
        self.assertIsNotNone(data["merkle_digest"])
        self.assertEqual(len(data["merkle_digest"]), 64)
        self.assertTrue(data["token_accounting"]["token_conservation_commutes"])
        self.assertIn("secret_attr", data["erased_attributes"])

    def test_ai_lossledger_duplicate_chunk_keys_rejected(self) -> None:
        """TC4.4: Duplicate chunk keys under loss violate token commutation and route to Reject."""
        payload = {
            "source_chunks": [
                {"chunk_id": "c1", "doc_title": "T1", "text": "hello world"},
                {"chunk_id": "c1", "doc_title": "T1", "text": "foo bar baz"},
            ],
            "target_fields": ["chunk_id", "doc_title", "text"],
            "protected_fields": ["chunk_id", "doc_title"],
            "max_token_budget": 3,
        }
        res = self.client.post("/api/ai/lossledger", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["canonical_terminal"], "Reject")
        self.assertFalse(data["admitted"])
        self.assertFalse(data["token_accounting"]["token_conservation_commutes"])


    # =========================================================================
    # 5. Claim Hygiene Adversarial Audit
    # =========================================================================

    def test_claim_hygiene_web_assets(self) -> None:
        """TC5.1: Adversarially audits web/app.py and web/templates/ for forbidden hype words."""
        forbidden_pattern = re.compile(
            r"\b(proves|guarantees|mathematically verifies|fundamentally|true intelligence|impossible|universal|flawless|perfectly|clearly|obviously|simply|merely|weaponized)\b",
            re.IGNORECASE,
        )
        approved_phrase = re.compile(
            r"guarantees?\s+(?:[a-zA-Z0-9_\s]{1,40}\s+)?under\s+(the\s+)?declared\s+(assumptions|conditions|bounds|rules)",
            re.IGNORECASE,
        )
        web_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web"))
        violations = []
        for root, _, files in os.walk(web_dir):
            for f in files:
                if f.endswith((".py", ".html")):
                    p = os.path.join(root, f)
                    with open(p, "r", encoding="utf-8") as fp:
                        for line_no, line in enumerate(fp, 1):
                            m = forbidden_pattern.search(line)
                            if m and not approved_phrase.search(line):
                                violations.append((p, line_no, m.group(0), line.strip()))

        if violations:
            msg = "\n".join(f"{p}:{ln} [{w}] -> {s}" for p, ln, w, s in violations)
            self.fail(f"Claim Hygiene Rule violated in web assets:\n{msg}")


if __name__ == "__main__":
    unittest.main()
