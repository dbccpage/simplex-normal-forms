"""Property-based and poset-law verification suite for Plan 2: Subsumption Lattice & Dead-Check Elimination.

Tests:
  1. Poset reflexivity, antisymmetry (cycle detection), and transitivity across
     classical relational, WDP/derivation, and CODA_MUR transport hierarchies.
  2. 80 randomized trials of FD kernel pipelines with dead-check elimination
     (run_kernel_pipeline_with_dce), checking that DCE reduces executed_pass_count
     when subsumed passes follow admitted passes and agrees 100% with unoptimized
     execution on admitted and final_terminal across both valid and failing instances.
  3. 80 randomized trials of CODA_MUR representation transport and WDNF kernel
     chains under DCE, verifying that DCE never masks a TransportViolation (Reject)
     or SubsingletonCollapseRefusal (Refuse).
  4. Epistemic authority firewall invariants (authorized == False,
     authority_effect == "None", certified_implies_authorized == False).

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
    lower_coda_mur_to_kernel_spec,
    lower_fd_to_kernel_spec,
)
from normal_forms.ir_subsumption import (
    CANONICAL_SUBSUMPTION_EDGES,
    SubsumptionEdge,
    run_kernel_pipeline_with_dce,
    subsumes_contract,
    subsumes_kernel_spec,
    verify_subsumption_poset_laws,
)


class TestIrSubsumption(unittest.TestCase):
    """Verification suite for normal_forms.ir_subsumption (Plan 2 / PR #13)."""

    def test_subsumption_poset_reflexivity_antisymmetry_and_transitivity(self) -> None:
        ok, violations = verify_subsumption_poset_laws()
        self.assertTrue(ok, msg=f"Canonical subsumption poset violated laws: {violations}")

        # Classical transitive chain: 6NF <= 5NF <= 4NF <= BCNF <= 3NF <= 2NF <= 1NF <= 0NF
        self.assertTrue(subsumes_contract("nf.classical.6nf", "nf.classical.1nf"))
        self.assertTrue(subsumes_contract("nf.classical.bcnf", "nf.classical.3nf"))
        self.assertTrue(subsumes_contract("nf.classical.bcnf", "nf.classical.1nf"))
        self.assertFalse(subsumes_contract("nf.classical.1nf", "nf.classical.bcnf"))
        self.assertFalse(subsumes_contract("nf.classical.3nf", "nf.classical.bcnf"))

        # Derivation / WDP chain: APNF <= WDNF <= PDNF <= OBNF
        self.assertTrue(subsumes_contract("nf.derivation.apnf", "nf.wdp.wdnf"))
        self.assertTrue(subsumes_contract("nf.derivation.apnf", "nf.derivation.pdnf"))
        self.assertTrue(subsumes_contract("nf.wdp.wdnf", "nf.derivation.obnf"))
        self.assertFalse(subsumes_contract("nf.derivation.pdnf", "nf.derivation.apnf"))

        # Representation transport chain: SERNF <= TransportOk <= DegradedTransportWithLoss
        self.assertTrue(
            subsumes_contract(
                "nf.derivation.sernf",
                "nf.coda.mur.transport:DegradedTransportWithLoss",
            )
        )
        self.assertFalse(
            subsumes_contract(
                "nf.coda.mur.transport:DegradedTransportWithLoss",
                "nf.coda.mur.transport:TransportOk",
            )
        )

        # Cross-family non-edges must be False
        self.assertFalse(subsumes_contract("nf.classical.bcnf", "nf.coda.mur.transport"))

        # Negative control: injecting a cycle breaks antisymmetry
        cyclic_edges = list(CANONICAL_SUBSUMPTION_EDGES) + [
            SubsumptionEdge(
                stronger_id="nf.classical.1nf",
                weaker_id="nf.classical.bcnf",
                family="classical",
                condition="synthetic cycle",
            )
        ]
        ok_cyc, cyc_violations = verify_subsumption_poset_laws(edges=cyclic_edges)
        self.assertFalse(ok_cyc)
        self.assertTrue(any("Antisymmetry violation" in v for v in cyc_violations))

    def test_fd_kernel_subsumption_dead_check_elimination_equivalence_80_trials(self) -> None:
        rng = random.Random(20261103)
        heading = ("row_id", "k1", "k2", "v1", "v2", "v3")

        elision_observed_trials = 0
        rejected_trials = 0

        for trial in range(80):
            # Stronger FD: {k1} -> {k2, v1, v2} under BCNF
            fd_strong = FunctionalDependency(
                frozenset({"k1"}),
                frozenset({"k2", "v1", "v2"}),
            )
            # Weaker FD 1 (subsumed): {k1, k2} -> {v1} under 3NF (det superset, dep subset)
            fd_weak_1 = FunctionalDependency(
                frozenset({"k1", "k2"}),
                frozenset({"v1"}),
            )
            # Weaker FD 2 (subsumed): {k1} -> {v1, v2} under 1NF
            fd_weak_2 = FunctionalDependency(
                frozenset({"k1"}),
                frozenset({"v1", "v2"}),
            )
            # Independent FD (not subsumed): {v2} -> {v3} under BCNF
            fd_indep = FunctionalDependency(
                frozenset({"v2"}),
                frozenset({"v3"}),
            )

            spec_strong = lower_fd_to_kernel_spec(
                fd_strong,
                key_field="row_id",
                heading=heading,
                contract_id="nf.classical.bcnf",
            )
            spec_weak_1 = lower_fd_to_kernel_spec(
                fd_weak_1,
                key_field="row_id",
                heading=heading,
                contract_id="nf.classical.3nf",
            )
            spec_weak_2 = lower_fd_to_kernel_spec(
                fd_weak_2,
                key_field="row_id",
                heading=heading,
                contract_id="nf.classical.1nf",
            )
            spec_indep = lower_fd_to_kernel_spec(
                fd_indep,
                key_field="row_id",
                heading=heading,
                contract_id="nf.classical.bcnf",
            )

            sub_ok_1, _ = subsumes_kernel_spec(spec_strong, spec_weak_1)
            sub_ok_2, _ = subsumes_kernel_spec(spec_strong, spec_weak_2)
            sub_indep, _ = subsumes_kernel_spec(spec_strong, spec_indep)
            self.assertTrue(sub_ok_1)
            self.assertTrue(sub_ok_2)
            self.assertFalse(sub_indep)

            pipeline_specs = [spec_strong, spec_weak_1, spec_indep, spec_weak_2]

            num_rows = rng.randint(4, 12)
            mode = trial % 3  # 0 = all valid, 1 = fail on spec_strong, 2 = fail on spec_indep

            rows: List[Dict[str, Any]] = []
            for idx in range(num_rows):
                k1_val = f"k1_{idx // 2}"
                # Satisfy both fd_strong ({k1} -> {k2, v1, v2}) and fd_indep ({v2} -> {v3})
                rows.append(
                    {
                        "row_id": f"r_{trial}_{idx}",
                        "k1": k1_val,
                        "k2": f"k2_for_{k1_val}",
                        "v1": f"v1_for_{k1_val}",
                        "v2": f"v2_for_{k1_val}",
                        "v3": f"v3_for_v2_{k1_val}",
                    }
                )

            if mode == 1 and len(rows) >= 2:
                # Break fd_strong on first pair
                rows[1]["k1"] = rows[0]["k1"]
                rows[1]["v1"] = "broken_v1"
            elif mode == 2 and len(rows) >= 2:
                # Keep fd_strong intact, break fd_indep across two distinct k1 groups
                rows[0]["k1"] = "group_a"
                rows[0]["k2"] = "k2_a"
                rows[0]["v1"] = "v1_a"
                rows[0]["v2"] = "shared_v2"
                rows[0]["v3"] = "v3_alpha"

                rows[1]["k1"] = "group_b"
                rows[1]["k2"] = "k2_b"
                rows[1]["v1"] = "v1_b"
                rows[1]["v2"] = "shared_v2"
                rows[1]["v3"] = "v3_beta_conflict"

            res_dce = run_kernel_pipeline_with_dce(
                pipeline_specs,
                rows,
                enable_dce=True,
            )
            res_unopt = run_kernel_pipeline_with_dce(
                pipeline_specs,
                rows,
                enable_dce=False,
            )

            # Semantic equivalence check
            self.assertEqual(res_dce.admitted, res_unopt.admitted)
            self.assertEqual(res_dce.certified, res_unopt.certified)
            self.assertEqual(res_dce.final_terminal, res_unopt.final_terminal)

            if mode == 0:
                elision_observed_trials += 1
                self.assertTrue(res_dce.admitted)
                self.assertEqual(res_dce.elided_pass_count, 2)
                self.assertEqual(res_dce.executed_pass_count, 2)
                self.assertEqual(res_unopt.executed_pass_count, 4)
            else:
                rejected_trials += 1
                self.assertFalse(res_dce.admitted)
                self.assertEqual(res_dce.final_terminal, "Reject")

        self.assertGreaterEqual(elision_observed_trials, 25)
        self.assertGreaterEqual(rejected_trials, 50)

    def test_coda_mur_and_wdnf_subsumption_dce_80_trials(self) -> None:
        rng = random.Random(20261104)
        src_fields = ("id", "doc_id", "amount", "debug_meta")

        for trial in range(80):
            num_rows = rng.randint(1, 6)
            rows = [
                {
                    "id": f"id_{trial}_{i}",
                    "doc_id": f"doc_{i}",
                    "amount": i * 10,
                    "debug_meta": f"m_{i}",
                }
                for i in range(num_rows)
            ]

            require_floor = (trial % 2 == 0)
            drop_protected = (trial % 5 == 0)
            tgt_fields = ("id", "amount") if drop_protected else ("id", "doc_id", "amount")

            spec_sernf = lower_coda_mur_to_kernel_spec(
                source_fields=src_fields,
                target_fields=tgt_fields,
                key_field="id",
                protected_fields=("id", "doc_id"),
                contract_id="nf.derivation.sernf",
                require_support_floor=require_floor,
            )
            spec_coda = lower_coda_mur_to_kernel_spec(
                source_fields=src_fields,
                target_fields=tgt_fields,
                key_field="id",
                protected_fields=("id", "doc_id"),
                contract_id="nf.coda.mur.transport",
                require_support_floor=require_floor,
            )

            res_dce = run_kernel_pipeline_with_dce(
                [spec_sernf, spec_coda],
                rows,
                enable_dce=True,
            )
            res_unopt = run_kernel_pipeline_with_dce(
                [spec_sernf, spec_coda],
                rows,
                enable_dce=False,
            )

            self.assertEqual(res_dce.admitted, res_unopt.admitted)
            self.assertEqual(res_dce.final_terminal, res_unopt.final_terminal)
            if res_dce.admitted:
                self.assertEqual(res_dce.elided_pass_count, 1)
                self.assertEqual(res_dce.executed_pass_count, 1)
            else:
                self.assertIn(res_dce.final_terminal, ("Refuse", "Reject"))

    def test_subsumption_authority_firewall_invariants(self) -> None:
        rows = [
            {"id": "1", "k": "a", "v": 10},
            {"id": "2", "k": "b", "v": 20},
        ]
        s1 = NFKernelSpec(
            contract_id="nf.classical.bcnf",
            key_field="id",
            distinction_fields=("id", "k", "v"),
            collapse_fields=("k",),
            protected_law_fields=("v",),
        )
        s2 = NFKernelSpec(
            contract_id="nf.classical.3nf",
            key_field="id",
            distinction_fields=("id", "k", "v"),
            collapse_fields=("k",),
            protected_law_fields=("v",),
        )
        receipt = run_kernel_pipeline_with_dce([s1, s2], rows, enable_dce=True)
        self.assertTrue(receipt.certified)
        self.assertFalse(receipt.authorized)
        self.assertEqual(receipt.authority_effect, "None")
        self.assertFalse(receipt.certified_implies_authorized)


if __name__ == "__main__":
    unittest.main()
