"""Integration and developer adoption test suite for Simplex Normal Forms.

Directly verifies the four external developer onboarding blueprints documented in
IMPORT_GUIDE.md and SCOPE.md:
  - Blueprint 1: Relational Schema Normalizer (3NF Synthesis & Tableau Chase)
  - Blueprint 2: Streaming BQNF Delta Repair (Extremum Cochain & Dyadic Quantile Sketches)
  - Blueprint 3: 4-Layer NF-IR Verification (Python Guards & SQLite Trigger DDL)
  - Blueprint 4: AI Agent LossLedger (Token Conservation & SHA-256 Merkle Proofs)

Epistemic Standard: Landau Rigor / Claim Discipline Compliant.
AuthorityEffect: None.
certified_implies_authorized: false.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
import unittest
from typing import Any, Dict, List, Mapping

# -----------------------------------------------------------------------------
# Blueprint 1 Imports
# -----------------------------------------------------------------------------
from normal_forms.domain.relational import (
    FunctionalDependency,
    RelationalSchema,
    check_3nf,
    chase_join_dependency,
)
from normal_forms.domain.relational_advanced import (
    decompose_bcnf_tree,
    synthesize_3nf_bernstein,
)

# -----------------------------------------------------------------------------
# Blueprint 2 Imports
# -----------------------------------------------------------------------------
from normal_forms.domain.bqnf_validator import (
    BqnfBoundary,
    BqnfCdcEvent,
    BqnfValidator,
)
from normal_forms.bqnf_extrema import (
    RepairTally,
    apply_removal,
)
from normal_forms.sales_cochain import (
    cochain_add,
    quantile_cochain_add,
    rebalance_quantile_cochain,
)

# -----------------------------------------------------------------------------
# Blueprint 3 Imports (with compatibility aliases for SCOPE.md interface contracts)
# -----------------------------------------------------------------------------
from normal_forms.ir_kernel import lower_fd_to_kernel_spec
from normal_forms.ir_lowering import (
    compile_to_python_decorator,
    compile_to_sqlite_triggers,
    install_and_verify_sqlite_bundle,
    lower_kernel_to_python_guard,
    lower_kernel_to_sqlite_trigger,
)

# -----------------------------------------------------------------------------
# Blueprint 4 Imports (with compatibility alias for LossLedger representation)
# -----------------------------------------------------------------------------
from normal_forms.ai import (
    LossLedger,
    build_context_loss_ledger,
    coda_mur_projection,
    verify_loss_ledger_integrity,
)


class TestBlueprint1RelationalSchemaNormalizer(unittest.TestCase):
    """Verifies Blueprint 1: Relational Schema Normalizer in migrations/APIs."""

    def test_ecommerce_schema_migration_normalization_and_chase(self) -> None:
        """Verifies candidate key derivation, 3NF synthesis, and Chase lossless join proof."""
        attrs = frozenset(
            ["order_id", "customer_id", "customer_zip", "item_id", "unit_price", "quantity"]
        )
        fds = frozenset(
            [
                FunctionalDependency(frozenset(["order_id"]), frozenset(["customer_id"])),
                FunctionalDependency(frozenset(["customer_id"]), frozenset(["customer_zip"])),
                FunctionalDependency(frozenset(["item_id"]), frozenset(["unit_price"])),
                FunctionalDependency(frozenset(["order_id", "item_id"]), frozenset(["quantity"])),
            ]
        )

        schema = RelationalSchema(attributes=attrs, dependencies=fds)

        # 1. Candidate Key Derivation
        cand_keys = [sorted(k) for k in schema.candidate_keys()]
        self.assertEqual(cand_keys, [["item_id", "order_id"]])
        self.assertEqual(sorted(schema.prime_attributes()), ["item_id", "order_id"])

        # 2. 3NF Compliance Check (Fails due to partial dependency item_id -> unit_price)
        is_3nf, reason = check_3nf(schema)
        self.assertFalse(is_3nf)
        self.assertIn("Partial Dependency Violation", reason)

        # 3. Bernstein 3NF Synthesis
        synthesized = synthesize_3nf_bernstein(schema)
        subschemas = [sorted(s) for s in synthesized]
        self.assertGreaterEqual(len(subschemas), 3)

        # Verify dependency preservation: all attributes are covered
        all_synthesized_attrs = set().union(*synthesized)
        self.assertEqual(all_synthesized_attrs, set(attrs))

        # 4. Deterministic Tableau Chase Lossless Join Verification
        chase_result = chase_join_dependency(schema.attributes, schema.dependencies, synthesized)
        self.assertTrue(chase_result.is_implied)
        self.assertEqual(chase_result.status, "Accept")
        self.assertGreater(len(chase_result.steps), 0)
        self.assertIsInstance(chase_result.distinguished_row_index, int)
        self.assertIsNone(chase_result.spurious_tuple_witness)

    def test_bcnf_tree_decomposition(self) -> None:
        """Verifies Tsou-Fischer BCNF decomposition on classic transitive schema."""
        attrs = frozenset(["student_id", "advisor_id", "department"])
        fds = frozenset(
            [
                FunctionalDependency(frozenset(["student_id"]), frozenset(["advisor_id"])),
                FunctionalDependency(frozenset(["advisor_id"]), frozenset(["department"])),
            ]
        )
        schema = RelationalSchema(attributes=attrs, dependencies=fds)

        bcnf_leaves = decompose_bcnf_tree(schema)
        self.assertEqual(len(bcnf_leaves), 2)
        leaf_attrs = [sorted(leaf.attributes) for leaf in bcnf_leaves]
        self.assertIn(["advisor_id", "department"], leaf_attrs)
        self.assertIn(["advisor_id", "student_id"], leaf_attrs)


class TestBlueprint2StreamingBqnfDeltaRepair(unittest.TestCase):
    """Verifies Blueprint 2: Streaming BQNF Delta Repair in CDC Pipelines."""

    def test_streaming_cdc_delta_repair_and_quantile_rebalancing(self) -> None:
        """Verifies CDC routing, O(log K) extremum tracking, and dyadic quantile updates."""
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        self.addCleanup(conn.close)
        cur = conn.cursor()

        # 1. Initialize schema matching Blueprint 2
        cur.execute("CREATE TABLE base_sales (id INTEGER PRIMARY KEY, region TEXT, amount REAL);")
        cur.execute(
            """
            CREATE TABLE region_sales_cache (
                region TEXT PRIMARY KEY,
                total_sales REAL,
                sale_count INTEGER,
                min_amount REAL,
                max_amount REAL,
                median_amount REAL
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE region_extremum_cochain (
                region TEXT,
                amount REAL,
                frequency INTEGER,
                PRIMARY KEY (region, amount)
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE region_quantile_cochain (
                region TEXT,
                bucket_id INTEGER,
                lower_bound REAL,
                upper_bound REAL,
                count INTEGER,
                PRIMARY KEY (region, bucket_id)
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE extrema_repair_log (
                region TEXT, op_type TEXT, affected_amount REAL, is_destructive INTEGER,
                cochain_available INTEGER, terminal_route TEXT, old_min REAL, new_min REAL,
                old_max REAL, new_max REAL, recomputation_fallback_executed INTEGER
            );
            """
        )

        # 2. Seed baseline data for region 'EMEA'
        region = "EMEA"
        initial_sales = [20.0, 45.0, 80.0, 150.0]
        for val in initial_sales:
            cur.execute("INSERT INTO base_sales (region, amount) VALUES (?, ?);", (region, val))
            cochain_add(conn, region, val)
            quantile_cochain_add(conn, region, val, bucket_width=10.0)

        cur.execute(
            "INSERT INTO region_sales_cache VALUES (?, 295.0, 4, 20.0, 150.0, 62.5);",
            (region,),
        )
        conn.commit()

        # 3. CDC Event Boundary Routing via BqnfValidator
        boundary = BqnfBoundary(
            relations=("orders",),
            attributes=("amount", "status"),
            predicates=("status = completed",),
            aggregates=("SUM(amount)",),
        )
        cdc_event = BqnfCdcEvent(
            op="UPDATE",
            relation="orders",
            old={"amount": 45.0, "status": "completed"},
            new={"amount": 85.0, "status": "completed"},
        )
        eval_result = BqnfValidator.evaluate(boundary, cdc_event)
        self.assertEqual(eval_result.decision, "Repair")
        self.assertEqual(eval_result.repair.get("delta_revenue"), 40.0)

        # 4. Destructive Deletion of Max Element (150.0) via Priority-Queue Extremum Cochain
        cache_state: Dict[str, Dict[str, Any]] = {
            region: {
                "total_sales": 295.0,
                "sale_count": 4,
                "min_amount": 20.0,
                "max_amount": 150.0,
            }
        }
        tally = RepairTally()

        # Invalidate the deleted 150.0 element from the extremum cochain
        cur.execute(
            "DELETE FROM region_extremum_cochain WHERE region = ? AND amount = ?;",
            (region, 150.0),
        )

        # apply_removal executes O(log K) query: SELECT amount FROM region_extremum_cochain ... LIMIT 1
        apply_removal(cur, cache_state, region, 150.0, use_cochain=True, tally=tally)

        self.assertEqual(cache_state[region]["max_amount"], 80.0)
        self.assertGreaterEqual(tally.extrema_repairs, 1)
        self.assertEqual(tally.fallback_recomputations, 0)

        # 5. Dynamic Dyadic Quantile Cochain Rebalancing
        rebalance_receipt = rebalance_quantile_cochain(
            conn, region, split_threshold=4, merge_threshold=1, bucket_width=10.0
        )
        self.assertEqual(rebalance_receipt["region"], region)
        self.assertIn("splits_executed", rebalance_receipt)
        self.assertIn("merges_executed", rebalance_receipt)
        self.assertGreater(rebalance_receipt["active_bucket_count"], 0)


class TestBlueprint3NfIrVerification(unittest.TestCase):
    """Verifies Blueprint 3: 4-Layer NF-IR Verification in ORM / SQLite."""

    def test_nf_ir_lowering_python_guard_and_sqlite_trigger(self) -> None:
        """Verifies compiling FD department_id -> manager_id into Python guard & SQLite trigger."""
        fd = FunctionalDependency(frozenset({"department_id"}), frozenset({"manager_id"}))
        spec = lower_fd_to_kernel_spec(
            fd=fd,
            key_field="employee_id",
            heading=("employee_id", "department_id", "manager_id"),
            contract_id="nf.classical.bcnf",
        )

        self.assertEqual(spec.contract_id, "nf.classical.bcnf")
        self.assertEqual(spec.key_field, "employee_id")
        self.assertEqual(spec.collapse_fields, ("department_id",))
        self.assertEqual(spec.protected_law_fields, ("manager_id",))

        # Target A: In-memory Python Guard Decorator
        @lower_kernel_to_python_guard(spec)
        def persist_employee_batch(records: List[Dict[str, Any]]) -> str:
            return f"Successfully committed {len(records)} employee records."

        # Valid batch conforming to department_id -> manager_id
        valid_batch = [
            {"employee_id": "E101", "department_id": "D1", "manager_id": "Alice"},
            {"employee_id": "E102", "department_id": "D1", "manager_id": "Alice"},
            {"employee_id": "E103", "department_id": "D2", "manager_id": "Bob"},
        ]
        valid_receipt = persist_employee_batch(valid_batch)
        self.assertTrue(valid_receipt.function_executed)
        self.assertTrue(valid_receipt.admitted)
        self.assertEqual(valid_receipt.canonical_terminal, "Preserve")
        self.assertEqual(valid_receipt.function_output, "Successfully committed 3 employee records.")

        # Conflicting batch violating department_id -> manager_id (D1 assigned to both Alice and Carol)
        violating_batch = [
            {"employee_id": "E101", "department_id": "D1", "manager_id": "Alice"},
            {"employee_id": "E102", "department_id": "D1", "manager_id": "Carol"},
        ]
        invalid_receipt = persist_employee_batch(violating_batch)
        self.assertFalse(invalid_receipt.function_executed)
        self.assertFalse(invalid_receipt.admitted)
        self.assertEqual(invalid_receipt.canonical_terminal, "Reject")
        self.assertIsNone(invalid_receipt.function_output)

        # Target B: Compile to SQLite Triggers
        bundle = lower_kernel_to_sqlite_trigger(spec, table_name="employee_directory")
        self.assertIn("CREATE TABLE", bundle.create_table_sql)
        self.assertIn("CREATE TRIGGER", bundle.before_insert_trigger_sql)
        self.assertIn("NF_VIOLATION:nf.classical.bcnf", bundle.before_insert_trigger_sql)

        # Verify SQLite trigger blocks violating insert in an in-memory database
        test_conn = sqlite3.connect(":memory:")
        self.addCleanup(test_conn.close)
        success, error_msg = install_and_verify_sqlite_bundle(
            conn=test_conn, bundle=bundle, rows=violating_batch
        )
        self.assertFalse(success)
        self.assertIn("NF_VIOLATION:nf.classical.bcnf", error_msg)


class TestBlueprint4AiAgentLossLedger(unittest.TestCase):
    """Verifies Blueprint 4: AI Agent LossLedger in LangChain / LlamaIndex / MCP Workflows."""

    def test_ai_context_lossledger_token_conservation_and_merkle_proof(self) -> None:
        """Verifies @coda_mur_projection token conservation and cryptographic LossLedger integrity."""
        # 1. Wrap prompt context compression with @coda_mur_projection
        @coda_mur_projection(
            source_fields=("chunk_id", "text", "doc_title", "internal_score", "doc_url"),
            target_fields=("chunk_id", "text", "doc_title"),
            key_field="chunk_id",
            protected_fields=("chunk_id",),
            max_token_budget=16,
        )
        def prepare_llm_prompt_context(chunks: List[Mapping[str, Any]]) -> None:
            # Return None to trigger canonical projection onto target_fields
            return None

        retrieved_chunks = [
            {
                "chunk_id": "doc_01",
                "text": "PostgreSQL uses multi-version concurrency control with write-ahead logging.",
                "doc_title": "PostgreSQL Architecture",
                "internal_score": 0.98,
                "doc_url": "https://docs.postgresql.org",
            },
            {
                "chunk_id": "doc_02",
                "text": "ClickHouse utilizes vectorized columnar execution for high-throughput analytical query processing.",
                "doc_title": "ClickHouse Internals",
                "internal_score": 0.94,
                "doc_url": "https://clickhouse.com/docs",
            },
        ]

        envelope = prepare_llm_prompt_context(retrieved_chunks)

        # 2. Context Envelope Assertions
        self.assertTrue(envelope.admitted)
        self.assertEqual(envelope.canonical_terminal, "Quarantine")
        self.assertEqual(envelope.local_route, "DegradedTransportWithLoss")

        # Exact token conservation equation: source == retained + truncated
        source_tok = envelope.source_token_count
        retained_tok = envelope.retained_token_count
        truncated_tok = envelope.truncated_token_count
        self.assertEqual(source_tok, retained_tok + truncated_tok)
        self.assertTrue(envelope.token_conservation_commutes)

        # 3. Sealed LossLedger Assertions
        loss_ledger = envelope.loss_ledger
        self.assertIsNotNone(loss_ledger)
        self.assertTrue(isinstance(loss_ledger, LossLedger))
        self.assertTrue(loss_ledger["sealed"])
        self.assertEqual(loss_ledger["record_count"], 2)

        # Merkle digest verification
        merkle_digest = loss_ledger["merkle_digest"]
        self.assertEqual(len(merkle_digest), 64)

        # Independent cryptographic integrity verification
        is_valid, err_msg = verify_loss_ledger_integrity(loss_ledger)
        self.assertTrue(is_valid)
        self.assertIsNone(err_msg)

        # 4. Adversarial Tamper Verification
        tampered_ledger = copy.deepcopy(loss_ledger)
        # Modify an erased token count entry to simulate tampered audit log
        tampered_ledger["entries"][0]["erased_fields"]["__truncated_token_count__"] = 9999
        tampered_valid, tampered_err = verify_loss_ledger_integrity(tampered_ledger)
        self.assertFalse(tampered_valid)
        self.assertIn("Digest mismatch", tampered_err)

        # 5. Epistemic Authority Firewall Assertions
        self.assertTrue(envelope.certified)
        self.assertFalse(envelope.authorized)
        self.assertFalse(envelope.certified_implies_authorized)
        self.assertEqual(envelope.authority_effect, "None")


if __name__ == "__main__":
    unittest.main()
