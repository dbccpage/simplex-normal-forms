"""Property-based and cross-target equivalence tests for Plan 4: Multi-Target Lowering & Counterexample Fuzzer.

Tests:
  1. 80 randomized trials of cross-target lowering (`compile_to_python_decorator`
     vs `compile_to_sqlite_triggers` + `install_and_verify_sqlite_bundle`),
     checking 100% agreement between Python kernel evaluation and in-memory
     SQLite BEFORE INSERT triggers across `functional_dependency` and
     `representation_transport` modes.
  2. 80 randomized trials of `synthesize_counterexample_fixtures`, checking that
     every synthesized `valid_rows` fixture is admitted by both the Python kernel
     and SQLite trigger, and every synthesized `SynthesizedCounterexampleFixture`
     is rejected (`admitted == False`, matching `expected_canonical_terminal`)
     with a concrete `minimal_counterexample`.
  3. SQLite `BEFORE UPDATE` trigger verification, confirming that in-place SQL
     `UPDATE` statements violating an FD or duplicating a protected key are
     aborted with `NF_VIOLATION:<contract_id>` while valid updates succeed.
  4. Epistemic authority firewall matrix on `compile_to_python_decorator`
     (`certified_implies_authorized == False`).

AuthorityEffect: None.
certified_implies_authorized: false.
"""

from __future__ import annotations

import random
import sqlite3
import unittest
from typing import Any, Dict, List, Mapping, Sequence

from normal_forms.domain.relational import FunctionalDependency
from normal_forms.ir_kernel import (
    NFKernelSpec,
    evaluate_nf_kernel,
    lower_coda_mur_to_kernel_spec,
    lower_fd_to_kernel_spec,
)
from normal_forms.ir_lowering import (
    compile_to_python_decorator,
    compile_to_sqlite_triggers,
    install_and_verify_sqlite_bundle,
    synthesize_counterexample_fixtures,
)


class TestIrLowering(unittest.TestCase):
    """Verification suite for normal_forms.ir_lowering (Plan 4 / PR #15)."""

    def test_sqlite_trigger_and_python_kernel_cross_target_equivalence_80_trials(self) -> None:
        rng = random.Random(20261107)
        conn = sqlite3.connect(":memory:")
        self.addCleanup(conn.close)

        admitted_count = 0
        rejected_count = 0

        for trial in range(80):
            if trial % 2 == 0:
                # functional_dependency mode
                all_cols = ("row_id", "c1", "c2", "p1", "p2", "extra")
                det_cols = ("c1",) if trial % 4 == 0 else ("c1", "c2")
                dep_cols = ("p1",) if trial % 6 == 0 else ("p1", "p2")
                spec = lower_fd_to_kernel_spec(
                    FunctionalDependency(frozenset(det_cols), frozenset(dep_cols)),
                    key_field="row_id",
                    heading=all_cols,
                    contract_id="nf.classical.bcnf",
                    require_support_floor=(trial % 8 == 0),
                )
            else:
                # representation_transport mode
                all_cols = ("row_id", "doc_id", "tenant_id", "amount", "debug_meta")
                drop_prot = (trial % 7 == 0)
                tgt_cols = (
                    ("row_id", "amount")
                    if drop_prot
                    else ("row_id", "doc_id", "tenant_id", "amount")
                )
                spec = lower_coda_mur_to_kernel_spec(
                    source_fields=all_cols,
                    target_fields=tgt_cols,
                    key_field="row_id",
                    protected_fields=("row_id", "doc_id"),
                    contract_id="nf.coda.mur.transport",
                    require_support_floor=(trial % 8 == 1),
                )

            num_rows = 1 if (spec.require_support_floor and trial % 16 in (0, 1)) else rng.randint(3, 8)
            rows: List[Dict[str, Any]] = []
            for idx in range(num_rows):
                rows.append(
                    {
                        col: f"{col}_{trial}_{idx}"
                        for col in all_cols
                    }
                )

            # Inject deterministic violations on odd-indexed violation buckets
            violation_mode = trial % 5
            if violation_mode == 1 and len(rows) >= 2:
                if spec.law_mode == "functional_dependency":
                    for cf in spec.collapse_fields:
                        rows[1][cf] = rows[0][cf]
                    rows[1][spec.protected_law_fields[0]] = "fd_conflict_val"
                else:
                    for pf in spec.protected_law_fields:
                        rows[1][pf] = rows[0][pf]
                    rows[1]["row_id"] = "distinct_row_id_collision"
                    if "row_id" in spec.protected_law_fields and len(spec.protected_law_fields) > 1:
                        # Make protected_law_fields collide on all protected fields while row_id differs
                        spec = lower_coda_mur_to_kernel_spec(
                            source_fields=all_cols,
                            target_fields=("row_id", "doc_id", "tenant_id", "amount"),
                            key_field="row_id",
                            protected_fields=("doc_id",),
                        )
                        rows[1]["doc_id"] = rows[0]["doc_id"]
            elif violation_mode == 2 and len(rows) >= 2:
                # Missing / null protected field
                bad_col = spec.protected_law_fields[0]
                if spec.law_mode == "representation_transport":
                    rows[0][bad_col] = None
                else:
                    del rows[0][bad_col]

            @compile_to_python_decorator(spec)
            def process_batch(batch: Sequence[Mapping[str, Any]]) -> int:
                return len(batch)

            py_res = process_batch(rows)
            bundle = compile_to_sqlite_triggers(spec, table_name=f"tbl_trial_{trial}")
            sql_ok, sql_err = install_and_verify_sqlite_bundle(conn, bundle, rows)

            self.assertEqual(
                py_res.admitted,
                sql_ok,
                msg=(
                    f"Trial {trial}: Python admitted={py_res.admitted} "
                    f"({py_res.wiring_receipt.reason}) != SQLite sql_ok={sql_ok} ({sql_err})"
                ),
            )
            self.assertEqual(py_res.function_executed, py_res.admitted)

            if py_res.admitted:
                admitted_count += 1
                self.assertEqual(py_res.function_output, len(rows))
                self.assertIsNone(sql_err)
            else:
                rejected_count += 1
                self.assertIsNone(py_res.function_output)
                self.assertIsNotNone(sql_err)
                assert sql_err is not None
                self.assertIn(f"NF_VIOLATION:{spec.contract_id}", sql_err)

        self.assertGreaterEqual(admitted_count, 25)
        self.assertGreaterEqual(rejected_count, 25)

    def test_automated_counterexample_fuzzer_completeness_80_trials(self) -> None:
        conn = sqlite3.connect(":memory:")
        self.addCleanup(conn.close)

        total_synthesized_cxs = 0

        for trial in range(80):
            if trial % 2 == 0:
                spec = NFKernelSpec(
                    contract_id="nf.classical.bcnf",
                    key_field="id",
                    distinction_fields=("k1", "v1", "extra"),
                    collapse_fields=("k1",),
                    protected_law_fields=("v1",),
                    law_mode="functional_dependency",
                    require_support_floor=(trial % 4 == 0),
                )
            else:
                spec = NFKernelSpec(
                    contract_id="nf.coda.mur.transport",
                    key_field="id",
                    distinction_fields=("doc_id", "amount", "secret_note"),
                    collapse_fields=("id", "doc_id", "amount"),
                    protected_law_fields=("doc_id",),
                    law_mode="representation_transport",
                    require_support_floor=(trial % 4 == 1),
                    require_loss_ledger_on_admissible_collision=True,
                )

            valid_rows, cx_fixtures = synthesize_counterexample_fixtures(spec, seed=trial)
            bundle = compile_to_sqlite_triggers(spec, table_name=f"fuzz_tbl_{trial}")

            # 1. Valid baseline fixture must be admitted by both Python kernel and SQLite trigger
            valid_kern = evaluate_nf_kernel(spec, valid_rows)
            self.assertTrue(valid_kern.admitted)
            sql_valid_ok, sql_valid_err = install_and_verify_sqlite_bundle(
                conn,
                bundle,
                valid_rows,
            )
            self.assertTrue(sql_valid_ok, msg=sql_valid_err)

            # 2. Every synthesized counterexample fixture must fail closed on Python kernel
            self.assertGreaterEqual(len(cx_fixtures), 4)
            for cx_fix in cx_fixtures:
                total_synthesized_cxs += 1
                cx_res = evaluate_nf_kernel(
                    spec,
                    cx_fix.carrier_rows,
                    asserted_pairs=cx_fix.asserted_pairs,
                )
                self.assertFalse(
                    cx_res.admitted,
                    msg=f"Synthesized {cx_fix.failure_kind} unexpectedly admitted on trial {trial}",
                )
                self.assertEqual(
                    cx_res.canonical_terminal,
                    cx_fix.expected_canonical_terminal,
                )
                self.assertIsNotNone(cx_res.minimal_counterexample)

                # Row-level counterexamples (without asserted_pairs) must also be aborted by SQLite trigger
                if cx_fix.asserted_pairs is None:
                    sql_cx_ok, sql_cx_err = install_and_verify_sqlite_bundle(
                        conn,
                        bundle,
                        cx_fix.carrier_rows,
                    )
                    self.assertFalse(
                        sql_cx_ok,
                        msg=f"SQLite trigger failed to block {cx_fix.failure_kind} on trial {trial}",
                    )
                    assert sql_cx_err is not None
                    self.assertIn(f"NF_VIOLATION:{spec.contract_id}", sql_cx_err)

        self.assertGreaterEqual(total_synthesized_cxs, 320)

    def test_sqlite_before_update_trigger_blocks_in_place_fd_and_transport_corruption(self) -> None:
        conn = sqlite3.connect(":memory:")
        self.addCleanup(conn.close)

        # 1. FD BEFORE UPDATE trigger
        fd_spec = lower_fd_to_kernel_spec(
            FunctionalDependency(frozenset({"dept"}), frozenset({"budget"})),
            key_field="id",
            heading=("id", "dept", "budget"),
        )
        fd_bundle = compile_to_sqlite_triggers(fd_spec, table_name="dept_budgets")
        ok, err = install_and_verify_sqlite_bundle(
            conn,
            fd_bundle,
            [
                {"id": "r1", "dept": "eng", "budget": "100"},
                {"id": "r2", "dept": "sales", "budget": "200"},
            ],
        )
        self.assertTrue(ok, msg=err)

        # Updating r2 to dept='eng' while keeping budget='200' violates dept -> budget
        with self.assertRaises(sqlite3.IntegrityError) as ctx:
            conn.execute("UPDATE dept_budgets SET dept = 'eng' WHERE id = 'r2';")
        self.assertIn("NF_VIOLATION:nf.classical.bcnf:PromoteToObstruction:budget", str(ctx.exception))

        # Valid update: updating r2 to dept='eng' AND budget='100' preserves dept -> budget
        conn.execute("UPDATE dept_budgets SET dept = 'eng', budget = '100' WHERE id = 'r2';")

        # 2. CODA_MUR BEFORE UPDATE trigger
        coda_spec = lower_coda_mur_to_kernel_spec(
            source_fields=("id", "doc_id", "title"),
            target_fields=("id", "doc_id", "title"),
            key_field="id",
            protected_fields=("doc_id",),
        )
        coda_bundle = compile_to_sqlite_triggers(coda_spec, table_name="coda_docs")
        ok2, err2 = install_and_verify_sqlite_bundle(
            conn,
            coda_bundle,
            [
                {"id": "1", "doc_id": "doc_alpha", "title": "A"},
                {"id": "2", "doc_id": "doc_beta", "title": "B"},
            ],
        )
        self.assertTrue(ok2, msg=err2)

        # Updating row '2' to doc_id='doc_alpha' collides on protected doc_id
        with self.assertRaises(sqlite3.IntegrityError) as ctx2:
            conn.execute("UPDATE coda_docs SET doc_id = 'doc_alpha' WHERE id = '2';")
        self.assertIn("NF_VIOLATION:nf.coda.mur.transport:TransportViolation:doc_id", str(ctx2.exception))

    def test_lowered_decorator_epistemic_authority_firewall_matrix(self) -> None:
        spec = lower_coda_mur_to_kernel_spec(
            source_fields=("id", "k", "v", "internal_note"),
            target_fields=("id", "k", "v"),
            key_field="id",
            protected_fields=("id", "k"),
        )
        rows = [
            {"id": "1", "k": "a", "v": "10", "internal_note": "n1"},
            {"id": "2", "k": "b", "v": "20", "internal_note": "n2"},
        ]

        @compile_to_python_decorator(
            spec,
            require_authorization=True,
            producer_identity="nf_producer",
        )
        def sensitive_sink(batch: Sequence[Mapping[str, Any]]) -> str:
            return f"processed_{len(batch)}"

        # 1. No verifier -> certified=True, authorized=False, function_executed=False
        res_none = sensitive_sink(rows)
        self.assertTrue(res_none.certified)
        self.assertFalse(res_none.authorized)
        self.assertFalse(res_none.function_executed)
        self.assertIsNone(res_none.function_output)
        self.assertEqual(res_none.canonical_terminal, "Refuse")

        # 2. Self-authorization -> function_executed=False
        res_self = sensitive_sink(
            rows,
            policy_verifier_override={
                "verifier_identity": "nf_producer",
                "outcome": "authorized",
            },
        )
        self.assertFalse(res_self.authorized)
        self.assertFalse(res_self.function_executed)

        # 3. Independent verifier with outcome="authorized" -> function_executed=True
        res_auth = sensitive_sink(
            rows,
            policy_verifier_override={
                "verifier_identity": "external_policy_engine",
                "outcome": "authorized",
            },
        )
        self.assertTrue(res_auth.admitted)
        self.assertTrue(res_auth.certified)
        self.assertTrue(res_auth.authorized)
        self.assertTrue(res_auth.function_executed)
        self.assertEqual(res_auth.function_output, "processed_2")
        self.assertEqual(res_auth.authority_effect, "None")
        self.assertFalse(res_auth.certified_implies_authorized)


if __name__ == "__main__":
    unittest.main()
