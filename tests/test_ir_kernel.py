"""Property-based and refusal-matrix tests for Plan 1: Primitive WDP/OBNF Witness Micro-Kernel.

Verifies:
  1. Level 00 WDNF/PDNF and OBNF refusal matrix and minimal counterexample extraction
     (subsingleton collapse, irreflexivity, ghost distinctions, missing protected law,
     admissible vs obstructed collisions).
  2. 80 randomized trials of relational functional dependency lowering
     (lower_fd_to_kernel_spec / evaluate_fds_via_kernel), checking 100% agreement with
     check_instance_satisfies_fds and verifying that every rejected instance yields a
     valid 2-row ConstructiveWitnessPair where r_1[X] == r_2[X] and r_1[Y] != r_2[Y].
  3. 80 randomized trials of CODA_MUR representation lowering
     (lower_coda_mur_to_kernel_spec), checking terminal routing (Preserve, Quarantine,
     Reject) and SHA-256 Merkle LossLedger integrity.
  4. Epistemic authority firewall invariants (authorized == False,
     authority_effect == "None", certified_implies_authorized == False) on all receipts.

AuthorityEffect: None.
certified_implies_authorized: false.
"""

from __future__ import annotations

import random
import unittest
from typing import Any, Dict, List

from normal_forms.domain.relational import FunctionalDependency
from normal_forms.ir_kernel import (
    NFKernelSpec,
    evaluate_fds_via_kernel,
    evaluate_nf_kernel,
    lower_coda_mur_to_kernel_spec,
    lower_fd_to_kernel_spec,
)
from normal_forms.multi_hop_composition import check_instance_satisfies_fds
from normal_forms.reconciliation_example import verify_loss_ledger_integrity


class TestIrKernel(unittest.TestCase):
    """Verification suite for normal_forms.ir_kernel (Plan 1 / PR #12)."""

    def test_wdnf_and_obnf_kernel_refusal_and_witness_matrix(self) -> None:
        base_spec = NFKernelSpec(
            contract_id="nf.wdp.wdnf",
            key_field="id",
            distinction_fields=("a", "b"),
            collapse_fields=("a",),
            protected_law_fields=("b",),
            law_mode="functional_dependency",
            require_support_floor=True,
        )

        # 1. Subsingleton carrier (|X| < 2) -> SubsingletonCollapseRefusal -> Refuse
        sub_res = evaluate_nf_kernel(base_spec, [{"id": "r1", "a": 1, "b": 10}])
        self.assertFalse(sub_res.admitted)
        self.assertEqual(sub_res.local_terminal, "SubsingletonCollapseRefusal")
        self.assertEqual(sub_res.canonical_terminal, "Refuse")
        self.assertIsNotNone(sub_res.minimal_counterexample)
        assert sub_res.minimal_counterexample is not None
        self.assertEqual(sub_res.minimal_counterexample.witness_kind, "subsingleton_carrier")

        # 2. Undeclared irreflexivity -> RequireIrreflexivityDeclaration -> Refuse
        rows_ok = [
            {"id": "r1", "a": 1, "b": 10},
            {"id": "r2", "a": 2, "b": 20},
        ]
        irref_undeclared = evaluate_nf_kernel(
            base_spec,
            rows_ok,
            irreflexivity_declared=False,
        )
        self.assertFalse(irref_undeclared.admitted)
        self.assertEqual(irref_undeclared.local_terminal, "RequireIrreflexivityDeclaration")
        self.assertEqual(irref_undeclared.canonical_terminal, "Refuse")

        # 3. Self-difference assertion (x, x) -> IrreflexivityViolation -> Reject
        self_diff = evaluate_nf_kernel(
            base_spec,
            rows_ok,
            asserted_pairs=[("r1", "r1")],
        )
        self.assertFalse(self_diff.admitted)
        self.assertEqual(self_diff.local_terminal, "IrreflexivityViolation")
        self.assertEqual(self_diff.canonical_terminal, "Reject")
        assert self_diff.minimal_counterexample is not None
        self.assertEqual(self_diff.minimal_counterexample.left_id, "r1")
        self.assertEqual(self_diff.minimal_counterexample.right_id, "r1")
        self.assertEqual(self_diff.minimal_counterexample.witness_kind, "self_difference")

        # 4. Ghost distinction (asserted pair with identical distinction_fields) -> Reject
        ghost_rows = [
            {"id": "r1", "a": 5, "b": 50},
            {"id": "r2", "a": 5, "b": 50},
        ]
        ghost_res = evaluate_nf_kernel(
            base_spec,
            ghost_rows,
            asserted_pairs=[("r1", "r2")],
        )
        self.assertFalse(ghost_res.admitted)
        self.assertEqual(ghost_res.local_terminal, "GhostDistinctionViolation")
        self.assertEqual(ghost_res.canonical_terminal, "Reject")
        assert ghost_res.minimal_counterexample is not None
        self.assertEqual(ghost_res.minimal_counterexample.witness_kind, "ghost_distinction")

        # 5. Missing protected law declaration -> RequireProtectedLawDeclaration -> Refuse
        unrel_spec = NFKernelSpec(
            contract_id="nf.derivation.obnf",
            key_field="id",
            distinction_fields=("a", "b"),
            collapse_fields=("a",),
            protected_law_fields=(),
            require_protected_law_declaration=True,
        )
        unrel_res = evaluate_nf_kernel(unrel_spec, rows_ok)
        self.assertFalse(unrel_res.admitted)
        self.assertEqual(unrel_res.local_terminal, "RequireProtectedLawDeclaration")
        self.assertEqual(unrel_res.canonical_terminal, "Refuse")

        # 6. Admissible collision (F(r1) == F(r2) and protected law b agrees) -> Preserve
        adm_rows = [
            {"id": "r1", "a": 1, "b": 10, "c": "x"},
            {"id": "r2", "a": 1, "b": 10, "c": "y"},
        ]
        adm_spec = NFKernelSpec(
            contract_id="nf.derivation.obnf",
            key_field="id",
            distinction_fields=("a", "b", "c"),
            collapse_fields=("a",),
            protected_law_fields=("b",),
        )
        adm_res = evaluate_nf_kernel(adm_spec, adm_rows)
        self.assertTrue(adm_res.admitted)
        self.assertEqual(adm_res.local_terminal, "AcceptAdmissibleCollision")
        self.assertEqual(adm_res.canonical_terminal, "Preserve")
        self.assertEqual(len(adm_res.admissible_collisions), 1)
        self.assertEqual(adm_res.admissible_collisions[0].left_id, "r1")
        self.assertEqual(adm_res.admissible_collisions[0].right_id, "r2")

        # 7. Obstructed collision (F(r1) == F(r2) but protected law b disagrees) -> Reject
        obs_rows = [
            {"id": "r1", "a": 1, "b": 10, "c": "x"},
            {"id": "r2", "a": 1, "b": 99, "c": "y"},
        ]
        obs_res = evaluate_nf_kernel(adm_spec, obs_rows)
        self.assertFalse(obs_res.admitted)
        self.assertEqual(obs_res.local_terminal, "PromoteToObstruction")
        self.assertEqual(obs_res.canonical_terminal, "Reject")
        assert obs_res.minimal_counterexample is not None
        self.assertEqual(obs_res.minimal_counterexample.left_id, "r1")
        self.assertEqual(obs_res.minimal_counterexample.right_id, "r2")
        self.assertEqual(obs_res.minimal_counterexample.feature, "b")
        self.assertEqual(obs_res.minimal_counterexample.left_value, 10)
        self.assertEqual(obs_res.minimal_counterexample.right_value, 99)

    def test_relational_fd_lowering_equivalence_and_minimal_witness_80_trials(self) -> None:
        rng = random.Random(20261101)
        heading = ("row_id", "dept", "role", "band", "salary", "office")
        candidate_cols = ("dept", "role", "band", "salary", "office")

        satisfied_trials = 0
        violated_trials = 0

        for trial in range(80):
            det_size = rng.randint(1, 2)
            det_cols = tuple(sorted(rng.sample(candidate_cols[:3], det_size)))
            rem_cols = [c for c in candidate_cols if c not in det_cols]
            dep_cols = tuple(sorted(rng.sample(rem_cols, rng.randint(1, 2))))
            fd = FunctionalDependency(frozenset(det_cols), frozenset(dep_cols))

            num_rows = rng.randint(5, 16)
            inject_violation = (trial % 2 == 1)

            det_map: Dict[tuple[Any, ...], Dict[str, Any]] = {}
            rows: List[Dict[str, Any]] = []
            by_id: Dict[str, Dict[str, Any]] = {}

            for r_idx in range(num_rows):
                rid = f"t{trial}_r{r_idx}"
                row: Dict[str, Any] = {
                    "row_id": rid,
                    "dept": rng.choice(["eng", "sales", "ops"]),
                    "role": rng.choice(["ic", "mgr", "dir"]),
                    "band": rng.choice(["L4", "L5", "L6"]),
                    "salary": rng.choice([100, 120, 150, 180]),
                    "office": rng.choice(["NYC", "SFO", "LON"]),
                }
                det_key = tuple(row[c] for c in det_cols)
                if not inject_violation:
                    if det_key in det_map:
                        for dc in dep_cols:
                            row[dc] = det_map[det_key][dc]
                    else:
                        det_map[det_key] = {dc: row[dc] for dc in dep_cols}
                rows.append(row)
                by_id[rid] = row

            # Force at least one explicit FD violation when inject_violation is True
            if inject_violation and len(rows) >= 2:
                for dc in det_cols:
                    rows[1][dc] = rows[0][dc]
                target_dep = dep_cols[0]
                rows[1][target_dep] = f"{rows[0][target_dep]}_conflict"

            ref_ok, _ = check_instance_satisfies_fds(rows, [fd])
            kern_res = evaluate_fds_via_kernel(
                rows=rows,
                dependencies=[fd],
                key_field="row_id",
                heading=heading,
            )

            self.assertEqual(
                kern_res.admitted,
                ref_ok,
                msg=f"Trial {trial}: kernel admitted={kern_res.admitted} != check_instance_satisfies_fds={ref_ok}",
            )

            if ref_ok:
                satisfied_trials += 1
                self.assertEqual(kern_res.canonical_terminal, "Preserve")
                self.assertIsNone(kern_res.minimal_counterexample)
            else:
                violated_trials += 1
                self.assertEqual(kern_res.canonical_terminal, "Reject")
                self.assertIsNotNone(kern_res.minimal_counterexample)
                cx = kern_res.minimal_counterexample
                assert cx is not None
                r_left = by_id[cx.left_id]
                r_right = by_id[cx.right_id]
                # Verify the witness pair genuinely collides on determinant X and disagrees on dependent feature
                for dc in det_cols:
                    self.assertEqual(r_left[dc], r_right[dc])
                self.assertIn(cx.feature, dep_cols)
                self.assertNotEqual(r_left[cx.feature], r_right[cx.feature])
                self.assertEqual(cx.left_value, r_left[cx.feature])
                self.assertEqual(cx.right_value, r_right[cx.feature])

        self.assertEqual(satisfied_trials, 40)
        self.assertEqual(violated_trials, 40)

    def test_coda_mur_lowering_equivalence_and_loss_ledger_80_trials(self) -> None:
        rng = random.Random(20261102)
        source_fields = ("rec_id", "tenant_id", "amount", "audit_nonce", "debug_note")

        preserve_count = 0
        quarantine_count = 0
        reject_count = 0

        for trial in range(80):
            num_rows = rng.randint(3, 10)
            rows: List[Dict[str, Any]] = []
            for idx in range(num_rows):
                rows.append(
                    {
                        "rec_id": f"rec_{trial}_{idx}",
                        "tenant_id": f"ten_{idx}",
                        "amount": rng.randint(10, 500),
                        "audit_nonce": f"nonce_{rng.randint(1000, 9999)}",
                        "debug_note": f"note_{idx}",
                    }
                )

            mode = trial % 4
            if mode == 0:
                # Lossless transport
                target_fields = source_fields
                protected_fields = ("rec_id", "tenant_id")
            elif mode == 1:
                # Lossy transport with sealed LossLedger
                target_fields = ("rec_id", "tenant_id", "amount")
                protected_fields = ("rec_id", "tenant_id")
            elif mode == 2:
                # Protected field dropped from target_fields -> TransportViolation -> Reject
                target_fields = ("rec_id", "amount")
                protected_fields = ("rec_id", "tenant_id")
            else:
                # Duplicate protected determinant key across distinct rows -> TransportViolation -> Reject
                target_fields = ("rec_id", "tenant_id", "amount")
                protected_fields = ("tenant_id",)
                rows[1]["tenant_id"] = rows[0]["tenant_id"]

            spec = lower_coda_mur_to_kernel_spec(
                source_fields=source_fields,
                target_fields=target_fields,
                key_field="rec_id",
                protected_fields=protected_fields,
            )
            res = evaluate_nf_kernel(spec, rows)

            if mode == 0:
                preserve_count += 1
                self.assertTrue(res.admitted)
                self.assertEqual(res.local_terminal, "TransportOk")
                self.assertEqual(res.canonical_terminal, "Preserve")
                self.assertIsNone(res.loss_ledger)
            elif mode == 1:
                quarantine_count += 1
                self.assertTrue(res.admitted)
                self.assertEqual(res.local_terminal, "DegradedTransportWithLoss")
                self.assertEqual(res.canonical_terminal, "Quarantine")
                self.assertIsNotNone(res.loss_ledger)
                assert res.loss_ledger is not None
                ok_seal, err_seal = verify_loss_ledger_integrity(res.loss_ledger)
                self.assertTrue(ok_seal, msg=err_seal)
                self.assertEqual(
                    res.loss_ledger["erased_attributes"],
                    ["audit_nonce", "debug_note"],
                )
            else:
                reject_count += 1
                self.assertFalse(res.admitted)
                self.assertEqual(res.local_terminal, "TransportViolation")
                self.assertEqual(res.canonical_terminal, "Reject")
                self.assertIsNotNone(res.minimal_counterexample)

        self.assertEqual(preserve_count, 20)
        self.assertEqual(quarantine_count, 20)
        self.assertEqual(reject_count, 40)

    def test_authority_firewall_invariants_across_all_kernel_receipts(self) -> None:
        rows = [
            {"id": "1", "k": "a", "v": 10, "extra": "x"},
            {"id": "2", "k": "b", "v": 20, "extra": "y"},
        ]
        specs = [
            lower_fd_to_kernel_spec(
                FunctionalDependency(frozenset({"k"}), frozenset({"v"})),
                key_field="id",
                heading=("id", "k", "v", "extra"),
            ),
            lower_coda_mur_to_kernel_spec(
                source_fields=("id", "k", "v", "extra"),
                target_fields=("id", "k", "v"),
                key_field="id",
                protected_fields=("id", "k"),
            ),
        ]
        for spec in specs:
            receipt = evaluate_nf_kernel(spec, rows)
            self.assertTrue(receipt.certified)
            self.assertFalse(receipt.authorized)
            self.assertEqual(receipt.authority_effect, "None")
            self.assertFalse(receipt.certified_implies_authorized)


if __name__ == "__main__":
    unittest.main()
