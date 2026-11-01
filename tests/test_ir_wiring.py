"""Property-based and algebraic-law tests for Plan 3: Operadic Pipeline Wiring Compiler.

Tests:
  1. 80 randomized trials of 3-pass sequential wiring (seq_passes), verifying
     strict associativity:
       eval(seq(seq(A, B), C)) == eval(seq(A, seq(B, C))) == eval(seq(A, B, C))
     across admitted, canonical_terminal, executed_specs_count, elided_specs_count,
     loss_chain_head_digest, and counterexamples, plus fail-closed short-circuiting.
  2. 80 randomized trials of parallel fan-out/fan-in wiring (par_passes), verifying
     commutativity of terminal severity join, loss_chain_head_digest, and
     counterexample aggregation:
       eval(par(A, B)) == eval(par(B, A)).
  3. Multi-hop Merkle loss-chain sensitivity across chained CODA_MUR projections,
     verifying that mutating any single erased attribute value alters
     loss_chain_head_digest.
  4. Epistemic authority firewall matrix on guard_pass (certified_implies_authorized
     == False).

AuthorityEffect: None.
certified_implies_authorized: false.
"""

from __future__ import annotations

import random
import unittest
from typing import Any, Dict, List

from normal_forms.domain.relational import FunctionalDependency
from normal_forms.ir_kernel import (
    lower_coda_mur_to_kernel_spec,
    lower_fd_to_kernel_spec,
)
from normal_forms.ir_wiring import (
    evaluate_wiring_dag,
    guard_pass,
    join_canonical_terminals,
    leaf_pass,
    par_passes,
    seq_passes,
)


class TestIrWiring(unittest.TestCase):
    """Verification suite for normal_forms.ir_wiring (Plan 3 / PR #14)."""

    def test_seq_associativity_and_short_circuit_equivalence_80_trials(self) -> None:
        rng = random.Random(20261105)
        heading = ("row_id", "k1", "k2", "v1", "v2", "audit_tag")

        admitted_trials = 0
        halted_trials = 0

        for trial in range(80):
            # Pass A: FD {k1} -> {k2, v1} under BCNF
            spec_a = lower_fd_to_kernel_spec(
                FunctionalDependency(frozenset({"k1"}), frozenset({"k2", "v1"})),
                key_field="row_id",
                heading=heading,
                contract_id="nf.classical.bcnf",
            )
            # Pass B: either a subsumed FD {k1, k2} -> {v1} (3NF) or independent FD {v1} -> {v2} (BCNF)
            if trial % 2 == 0:
                spec_b = lower_fd_to_kernel_spec(
                    FunctionalDependency(frozenset({"k1", "k2"}), frozenset({"v1"})),
                    key_field="row_id",
                    heading=heading,
                    contract_id="nf.classical.3nf",
                )
            else:
                spec_b = lower_fd_to_kernel_spec(
                    FunctionalDependency(frozenset({"v1"}), frozenset({"v2"})),
                    key_field="row_id",
                    heading=heading,
                    contract_id="nf.classical.bcnf",
                )
            # Pass C: CODA_MUR projection dropping audit_tag (or dropping protected k1 on every 5th trial)
            drop_prot = (trial % 5 == 4)
            tgt_c = ("row_id", "v1", "v2") if drop_prot else ("row_id", "k1", "k2", "v1", "v2")
            spec_c = lower_coda_mur_to_kernel_spec(
                source_fields=heading,
                target_fields=tgt_c,
                key_field="row_id",
                protected_fields=("row_id", "k1"),
            )

            node_a = leaf_pass(spec_a)
            node_b = leaf_pass(spec_b)
            node_c = leaf_pass(spec_c)

            num_rows = rng.randint(4, 10)
            rows: List[Dict[str, Any]] = []
            for idx in range(num_rows):
                k1_val = f"k1_{idx // 2}"
                rows.append(
                    {
                        "row_id": f"r_{trial}_{idx}",
                        "k1": k1_val,
                        "k2": f"k2_{k1_val}",
                        "v1": f"v1_{k1_val}",
                        "v2": f"v2_{k1_val}",
                        "audit_tag": f"tag_{rng.randint(100, 999)}",
                    }
                )

            # Inject failure at A (mode 1) or at B when independent (mode 2)
            fail_mode = trial % 4
            if fail_mode == 1 and len(rows) >= 2:
                rows[1]["k1"] = rows[0]["k1"]
                rows[1]["v1"] = "conflict_at_a"
            elif fail_mode == 2 and (trial % 2 == 1) and len(rows) >= 2:
                rows[0]["k1"] = "ga"
                rows[0]["k2"] = "k2_ga"
                rows[0]["v1"] = "shared_v1"
                rows[0]["v2"] = "v2_one"
                rows[1]["k1"] = "gb"
                rows[1]["k2"] = "k2_gb"
                rows[1]["v1"] = "shared_v1"
                rows[1]["v2"] = "v2_two_conflict"

            use_dce = (trial % 3 != 0)
            dag_left = seq_passes(
                seq_passes(node_a, node_b, enable_dce=use_dce),
                node_c,
                enable_dce=use_dce,
            )
            dag_right = seq_passes(
                node_a,
                seq_passes(node_b, node_c, enable_dce=use_dce),
                enable_dce=use_dce,
            )
            dag_flat = seq_passes(node_a, node_b, node_c, enable_dce=use_dce)

            res_left = evaluate_wiring_dag(dag_left, rows)
            res_right = evaluate_wiring_dag(dag_right, rows)
            res_flat = evaluate_wiring_dag(dag_flat, rows)

            # Associativity checks across all three bracketings
            for other in (res_right, res_flat):
                self.assertEqual(res_left.admitted, other.admitted)
                self.assertEqual(res_left.certified, other.certified)
                self.assertEqual(res_left.canonical_terminal, other.canonical_terminal)
                self.assertEqual(res_left.executed_specs_count, other.executed_specs_count)
                self.assertEqual(res_left.elided_specs_count, other.elided_specs_count)
                self.assertEqual(res_left.loss_chain_head_digest, other.loss_chain_head_digest)
                self.assertEqual(res_left.counterexamples, other.counterexamples)

            if res_flat.admitted:
                admitted_trials += 1
                self.assertEqual(res_flat.canonical_terminal, "Quarantine")
                self.assertIsNotNone(res_flat.loss_chain_head_digest)
            else:
                halted_trials += 1
                self.assertEqual(res_flat.canonical_terminal, "Reject")
                self.assertGreaterEqual(len(res_flat.counterexamples), 1)
                # When Pass A failed, Pass B and C must have been short-circuited
                if fail_mode == 1:
                    self.assertEqual(res_flat.executed_specs_count, 1)

        self.assertGreaterEqual(admitted_trials, 20)
        self.assertGreaterEqual(halted_trials, 25)

    def test_par_commutativity_idempotence_and_counterexample_aggregation_80_trials(self) -> None:
        rng = random.Random(20261106)
        heading = ("row_id", "k1", "v1", "v2", "meta_a", "meta_b")

        for trial in range(80):
            spec_1 = lower_fd_to_kernel_spec(
                FunctionalDependency(frozenset({"k1"}), frozenset({"v1"})),
                key_field="row_id",
                heading=heading,
            )
            spec_2 = lower_coda_mur_to_kernel_spec(
                source_fields=heading,
                target_fields=("row_id", "k1", "v1", "v2", "meta_b"),
                key_field="row_id",
                protected_fields=("row_id", "k1"),
            )
            spec_3 = lower_coda_mur_to_kernel_spec(
                source_fields=heading,
                target_fields=("row_id", "k1", "v1", "v2", "meta_a"),
                key_field="row_id",
                protected_fields=("row_id", "k1"),
            )

            rows: List[Dict[str, Any]] = [
                {
                    "row_id": f"r_{trial}_{i}",
                    "k1": f"k_{i // 2}",
                    "v1": f"v1_{i // 2}",
                    "v2": i * 5,
                    "meta_a": f"ma_{rng.randint(1, 50)}",
                    "meta_b": f"mb_{rng.randint(1, 50)}",
                }
                for i in range(6)
            ]

            if trial % 3 == 1:
                # Inject FD violation in spec_1
                rows[1]["k1"] = rows[0]["k1"]
                rows[1]["v1"] = "fd_broken"
            elif trial % 3 == 2:
                # Inject duplicate protected key in spec_2 and spec_3
                rows[1]["row_id"] = rows[0]["row_id"]
                rows[1]["k1"] = rows[0]["k1"]

            n1 = leaf_pass(spec_1)
            n2 = leaf_pass(spec_2)
            n3 = leaf_pass(spec_3)

            res_123 = evaluate_wiring_dag(par_passes(n1, n2, n3), rows)
            res_321 = evaluate_wiring_dag(par_passes(n3, n2, n1), rows)

            self.assertEqual(res_123.admitted, res_321.admitted)
            self.assertEqual(res_123.certified, res_321.certified)
            self.assertEqual(res_123.canonical_terminal, res_321.canonical_terminal)
            self.assertEqual(res_123.loss_chain_head_digest, res_321.loss_chain_head_digest)
            self.assertEqual(res_123.counterexamples, res_321.counterexamples)

        # Also check join_canonical_terminals ordering directly
        self.assertEqual(
            join_canonical_terminals(["Preserve", "Quarantine", "Repair"]),
            "Quarantine",
        )
        self.assertEqual(
            join_canonical_terminals(["Quarantine", "Reject", "Invalidate"]),
            "Reject",
        )
        self.assertEqual(
            join_canonical_terminals(["Reject", "Refuse"]),
            "Refuse",
        )

    def test_multi_hop_merkle_loss_chain_tamper_and_sensitivity(self) -> None:
        s_all = ("id", "doc_id", "body", "debug_1", "debug_2")
        hop_1 = leaf_pass(
            lower_coda_mur_to_kernel_spec(
                source_fields=s_all,
                target_fields=("id", "doc_id", "body", "debug_2"),
                key_field="id",
                protected_fields=("id", "doc_id"),
            )
        )
        hop_2 = leaf_pass(
            lower_coda_mur_to_kernel_spec(
                source_fields=s_all,
                target_fields=("id", "doc_id", "body"),
                key_field="id",
                protected_fields=("id", "doc_id"),
            )
        )

        rows_a = [
            {"id": "1", "doc_id": "d1", "body": "x", "debug_1": "alpha", "debug_2": "beta"},
            {"id": "2", "doc_id": "d2", "body": "y", "debug_1": "gamma", "debug_2": "delta"},
        ]
        rows_b = [
            {"id": "1", "doc_id": "d1", "body": "x", "debug_1": "alpha", "debug_2": "beta_mutated"},
            {"id": "2", "doc_id": "d2", "body": "y", "debug_1": "gamma", "debug_2": "delta"},
        ]

        dag = seq_passes(hop_1, hop_2, enable_dce=False)
        res_a = evaluate_wiring_dag(dag, rows_a)
        res_b = evaluate_wiring_dag(dag, rows_b)

        self.assertTrue(res_a.admitted)
        self.assertEqual(len(res_a.loss_chain), 2)
        self.assertIsNotNone(res_a.loss_chain_head_digest)
        self.assertNotEqual(res_a.loss_chain_head_digest, res_b.loss_chain_head_digest)
        self.assertEqual(
            res_a.loss_chain[0].ledger_digest,
            res_b.loss_chain[0].ledger_digest,
            msg="Hop 1 only drops debug_1 (unchanged), so hop 1 digest must match.",
        )
        self.assertNotEqual(
            res_a.loss_chain[1].ledger_digest,
            res_b.loss_chain[1].ledger_digest,
            msg="Hop 2 drops debug_2 (mutated), so hop 2 digest and cumulative head must differ.",
        )

    def test_guard_pass_epistemic_authority_firewall_matrix(self) -> None:
        heading = ("id", "k", "v", "trace")
        spec = lower_coda_mur_to_kernel_spec(
            source_fields=heading,
            target_fields=("id", "k", "v"),
            key_field="id",
            protected_fields=("id", "k"),
        )
        rows = [
            {"id": "1", "k": "a", "v": 10, "trace": "t1"},
            {"id": "2", "k": "b", "v": 20, "trace": "t2"},
        ]
        inner_node = leaf_pass(spec)

        # 1. Unguarded leaf is certified, NOT authorized
        res_unguarded = evaluate_wiring_dag(inner_node, rows)
        self.assertTrue(res_unguarded.admitted)
        self.assertTrue(res_unguarded.certified)
        self.assertFalse(res_unguarded.authorized)
        self.assertEqual(res_unguarded.authorization_status, "certified_not_authorized")

        # 2. Guard with None verifier -> certified, NOT authorized, Refuse
        res_none = evaluate_wiring_dag(guard_pass(inner_node, None), rows)
        self.assertTrue(res_none.certified)
        self.assertFalse(res_none.authorized)
        self.assertEqual(res_none.canonical_terminal, "Refuse")
        self.assertEqual(res_none.authorization_status, "certified_not_authorized")

        # 3. Guard with bare string verifier -> Refuse
        res_str = evaluate_wiring_dag(guard_pass(inner_node, "authorized"), rows)
        self.assertFalse(res_str.admitted)
        self.assertFalse(res_str.authorized)
        self.assertEqual(res_str.canonical_terminal, "Refuse")
        self.assertEqual(res_str.authorization_status, "unauthenticated_verifier_string")

        # 4. Guard with self-authorizing verifier (verifier_identity == producer_identity) -> Refuse
        res_self = evaluate_wiring_dag(
            guard_pass(
                inner_node,
                {"verifier_identity": "agent_prod", "outcome": "authorized"},
                producer_identity="agent_prod",
            ),
            rows,
        )
        self.assertFalse(res_self.admitted)
        self.assertFalse(res_self.authorized)
        self.assertEqual(res_self.canonical_terminal, "Refuse")
        self.assertEqual(res_self.authorization_status, "self_authorized_violation")

        # 5. Guard with independent verifier and outcome="authorized" -> authorized=True
        res_auth = evaluate_wiring_dag(
            guard_pass(
                inner_node,
                {"verifier_identity": "independent_policy_guard", "outcome": "authorized"},
                producer_identity="agent_prod",
            ),
            rows,
        )
        self.assertTrue(res_auth.admitted)
        self.assertTrue(res_auth.certified)
        self.assertTrue(res_auth.authorized)
        self.assertEqual(res_auth.canonical_terminal, "Quarantine")
        self.assertEqual(res_auth.authorization_status, "authorized")
        self.assertFalse(res_auth.certified_implies_authorized)
        self.assertEqual(res_auth.authority_effect, "None")


if __name__ == "__main__":
    unittest.main()
