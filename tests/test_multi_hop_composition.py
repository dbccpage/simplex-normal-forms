"""Property-based and randomized schema-mutation tests for multi-hop composition:
Stage 1 (3NF / BCNF relational synthesis) -> Stage 2 (BQNF streaming CDC repair)
-> Stage 3 (CODA_MUR representation transport).

AuthorityEffect: None.
"""

from __future__ import annotations

import random
import unittest
from typing import Any, Dict, List, Tuple

from normal_forms.domain.bqnf_validator import BqnfBoundary, BqnfCdcEvent
from normal_forms.domain.relational import (
    FunctionalDependency,
    RelationalSchema,
    check_3nf,
    check_bcnf,
    check_dependency_preservation,
    check_lossless_decomposition,
)
from normal_forms.domain.relational_advanced import (
    decompose_bcnf_tree,
    project_functional_dependencies,
    synthesize_3nf_bernstein,
)
from normal_forms.multi_hop_composition import (
    CODA_MUR_TRIGGER_ID,
    CodaMurHopSpec,
    build_sealed_loss_ledger,
    project_and_rejoin,
    run_multi_hop_pipeline,
)


def _generate_random_schema_and_instance(
    rng: random.Random,
) -> Tuple[RelationalSchema, List[Dict[str, Any]]]:
    """Generates a randomized relational schema with partial and transitive FDs and a valid instance."""
    # Attributes: k1, k2 (composite key or single key), t1, t2 (transitive chain), p1 (partial), v1, v2 (payload)
    use_composite_key = rng.choice([True, False])
    attrs = ["order_id", "customer_id", "customer_zip", "region", "status", "amount", "audit_nonce"]
    fds: List[FunctionalDependency] = []

    if use_composite_key:
        attrs.append("line_no")
        key_cols = ["order_id", "line_no"]
        # Partial dependency: order_id -> customer_id (violates 2NF)
        fds.append(FunctionalDependency.from_str("order_id", "customer_id"))
        # Full key determines remaining attributes
        fds.append(
            FunctionalDependency(
                frozenset(key_cols),
                frozenset(["status", "amount", "audit_nonce"]),
            )
        )
    else:
        key_cols = ["order_id"]
        fds.append(
            FunctionalDependency(
                frozenset(key_cols),
                frozenset(["customer_id", "status", "amount", "audit_nonce"]),
            )
        )

    # Transitive chain: customer_id -> customer_zip -> region (violates 3NF & BCNF)
    fds.append(FunctionalDependency.from_str("customer_id", "customer_zip"))
    fds.append(FunctionalDependency.from_str("customer_zip", "region"))

    schema = RelationalSchema(
        attributes=frozenset(attrs),
        dependencies=frozenset(fds),
        attribute_domains={a: "scalar_text_or_num" for a in attrs},
    )

    # Build a consistent instance obeying all FDs
    cust_to_zip = {c: f"ZIP_{1000 + c * 7}" for c in range(1, 7)}
    zip_to_region = {z: f"REG_{idx % 3}" for idx, z in enumerate(cust_to_zip.values())}
    order_to_cust = {oid: rng.randint(1, 6) for oid in range(1, 15)}

    rows: List[Dict[str, Any]] = []
    num_orders = rng.randint(5, 12)
    for oid in range(1, num_orders + 1):
        cid = order_to_cust[oid]
        czip = cust_to_zip[cid]
        reg = zip_to_region[czip]
        row: Dict[str, Any] = {
            "order_id": oid,
            "customer_id": cid,
            "customer_zip": czip,
            "region": reg,
            "status": rng.choice(["paid", "pending"]),
            "amount": float(rng.randint(1, 20) * 10),
            "audit_nonce": f"nonce_{oid}_{rng.randint(100, 999)}",
        }
        if use_composite_key:
            row["line_no"] = 1
        rows.append(row)

    return schema, rows


class TestMultiHopCompositionProperties(unittest.TestCase):
    def test_randomized_3nf_bcnf_synthesis_and_lossless_join_100_trials(self) -> None:
        rng = random.Random(20261029)
        for trial in range(100):
            schema, rows = _generate_random_schema_and_instance(rng)

            # 1. Bernstein 3NF synthesis
            nf3_comps = synthesize_3nf_bernstein(schema)
            self.assertGreaterEqual(len(nf3_comps), 2, f"Trial {trial}: expected decomposition")
            for comp in nf3_comps:
                proj_fds = project_functional_dependencies(schema.dependencies, comp)
                sub_s = RelationalSchema(attributes=comp, dependencies=frozenset(proj_fds))
                ok_3nf, err_3nf = check_3nf(sub_s)
                self.assertTrue(ok_3nf, f"Trial {trial}: 3NF check failed on {comp}: {err_3nf}")

            lossless_3nf, err_l3 = check_lossless_decomposition(schema, nf3_comps)
            self.assertTrue(lossless_3nf, f"Trial {trial}: 3NF not lossless: {err_l3}")
            dep_pres_3nf, err_d3 = check_dependency_preservation(schema, nf3_comps)
            self.assertTrue(dep_pres_3nf, f"Trial {trial}: 3NF lost FDs: {err_d3}")

            # 2. Tsou-Fischer BCNF tree decomposition
            bcnf_rels = decompose_bcnf_tree(schema)
            bcnf_comps = [r.attributes for r in bcnf_rels]
            for r_sub in bcnf_rels:
                ok_b, err_b = check_bcnf(r_sub)
                self.assertTrue(ok_b, f"Trial {trial}: BCNF check failed on {r_sub}: {err_b}")

            lossless_bcnf, err_lb = check_lossless_decomposition(schema, bcnf_comps)
            self.assertTrue(lossless_bcnf, f"Trial {trial}: BCNF not lossless: {err_lb}")

            # 3. Instance-level natural join reconstruction
            inst_ok_3, rejoined_3, spurious_3 = project_and_rejoin(rows, schema.attributes, nf3_comps)
            self.assertTrue(inst_ok_3, f"Trial {trial}: 3NF instance join had spurious rows: {spurious_3}")
            self.assertEqual(len(rejoined_3), len(rows))

            inst_ok_b, rejoined_b, spurious_b = project_and_rejoin(rows, schema.attributes, bcnf_comps)
            self.assertTrue(inst_ok_b, f"Trial {trial}: BCNF instance join had spurious rows: {spurious_b}")
            self.assertEqual(len(rejoined_b), len(rows))

    def test_randomized_end_to_end_3hop_commutation_100_trials(self) -> None:
        rng = random.Random(31415926)
        base_heading = (
            "order_id",
            "customer_id",
            "customer_zip",
            "region",
            "status",
            "amount",
            "audit_nonce",
        )
        schema = RelationalSchema(
            attributes=frozenset(base_heading),
            dependencies=frozenset(
                [
                    FunctionalDependency(
                        frozenset(["order_id"]),
                        frozenset(["customer_id", "status", "amount", "audit_nonce"]),
                    ),
                    FunctionalDependency.from_str("customer_id", "customer_zip"),
                    FunctionalDependency.from_str("customer_zip", "region"),
                ]
            ),
            attribute_domains={a: "scalar" for a in base_heading},
        )
        boundary = BqnfBoundary(
            relations=("Orders",),
            attributes=("customer_id", "status", "amount"),
            predicates=("status = paid",),
            groups=("customer_id",),
            aggregates=("SUM(amount)",),
        )

        for trial in range(100):
            # Consistent lookup tables for transitive FDs
            cust_zip = {c: f"Z{c}00" for c in range(1, 6)}
            zip_reg = {f"Z{c}00": f"R{c % 2}" for c in range(1, 6)}

            rows: List[Dict[str, Any]] = []
            active_by_id: Dict[int, Dict[str, Any]] = {}
            for oid in range(1, 9):
                cid = rng.randint(1, 5)
                cz = cust_zip[cid]
                r = {
                    "order_id": oid,
                    "customer_id": cid,
                    "customer_zip": cz,
                    "region": zip_reg[cz],
                    "status": rng.choice(["paid", "pending"]),
                    "amount": float(rng.randint(1, 15) * 10),
                    "audit_nonce": f"n_{oid}",
                }
                rows.append(r)
                active_by_id[oid] = dict(r)

            # Generate a random stream of 10 CDC events
            cdc_events: List[BqnfCdcEvent] = []
            next_oid = 100
            for _ in range(10):
                op_choice = rng.choice(["UPDATE_VALUE", "UPDATE_NOOP", "INSERT", "DELETE"])
                if op_choice == "INSERT" or not active_by_id:
                    cid = rng.randint(1, 5)
                    cz = cust_zip[cid]
                    new_row = {
                        "order_id": next_oid,
                        "customer_id": cid,
                        "customer_zip": cz,
                        "region": zip_reg[cz],
                        "status": rng.choice(["paid", "pending"]),
                        "amount": float(rng.randint(1, 15) * 10),
                        "audit_nonce": f"n_{next_oid}",
                    }
                    cdc_events.append(BqnfCdcEvent(op="INSERT", relation="Orders", old=None, new=dict(new_row)))
                    active_by_id[next_oid] = new_row
                    next_oid += 1
                elif op_choice == "DELETE" and len(active_by_id) > 2:
                    target_oid = rng.choice(sorted(active_by_id.keys()))
                    old_row = active_by_id.pop(target_oid)
                    cdc_events.append(BqnfCdcEvent(op="DELETE", relation="Orders", old=dict(old_row), new=None))
                elif op_choice == "UPDATE_NOOP":
                    target_oid = rng.choice(sorted(active_by_id.keys()))
                    old_row = dict(active_by_id[target_oid])
                    new_row = dict(old_row)
                    new_row["audit_nonce"] = f"n_{target_oid}_mut_{rng.randint(1, 999)}"
                    cdc_events.append(BqnfCdcEvent(op="UPDATE", relation="Orders", old=old_row, new=new_row))
                    active_by_id[target_oid] = new_row
                else:
                    target_oid = rng.choice(sorted(active_by_id.keys()))
                    old_row = dict(active_by_id[target_oid])
                    new_row = dict(old_row)
                    new_row["status"] = rng.choice(["paid", "pending"])
                    new_row["amount"] = float(rng.randint(1, 25) * 10)
                    cdc_events.append(BqnfCdcEvent(op="UPDATE", relation="Orders", old=old_row, new=new_row))
                    active_by_id[target_oid] = new_row

            # Build a 3-hop CODA_MUR representation transport chain:
            # Hop 1: drops audit_nonce (or keeps all if lossless trial)
            # Hop 2: drops region and customer_zip
            # Hop 3: lossless projection on remaining attributes
            is_lossless_chain = (trial % 5 == 0)
            if is_lossless_chain:
                hops = [
                    CodaMurHopSpec(
                        hop_id="hop1_identity",
                        source_heading=base_heading,
                        target_heading=base_heading,
                        group_attribute="customer_id",
                        value_attribute="amount",
                        predicate_attribute="status",
                        predicate_expected_value="paid",
                        loss_ledger=None,
                        target_verifier={"verifier_id": "v1", "executed": True, "outcome": "verified"},
                    ),
                    CodaMurHopSpec(
                        hop_id="hop2_identity",
                        source_heading=base_heading,
                        target_heading=base_heading,
                        group_attribute="customer_id",
                        value_attribute="amount",
                        predicate_attribute="status",
                        predicate_expected_value="paid",
                        loss_ledger=None,
                        target_verifier={"verifier_id": "v2", "executed": True, "outcome": "verified"},
                    ),
                ]
            else:
                h1_target = ("order_id", "customer_id", "customer_zip", "region", "status", "amount")
                h2_target = ("order_id", "customer_id", "status", "amount")
                ledger_1 = build_sealed_loss_ledger(["audit_nonce"], rows, "order_id")
                ledger_2 = build_sealed_loss_ledger(["customer_zip", "region"], rows, "order_id")
                hops = [
                    CodaMurHopSpec(
                        hop_id="hop1_drop_nonce",
                        source_heading=base_heading,
                        target_heading=h1_target,
                        group_attribute="customer_id",
                        value_attribute="amount",
                        predicate_attribute="status",
                        predicate_expected_value="paid",
                        loss_ledger=ledger_1,
                        target_verifier={"verifier_id": "v_hop1", "executed": True, "outcome": "verified"},
                    ),
                    CodaMurHopSpec(
                        hop_id="hop2_drop_geo",
                        source_heading=h1_target,
                        target_heading=h2_target,
                        group_attribute="customer_id",
                        value_attribute="amount",
                        predicate_attribute="status",
                        predicate_expected_value="paid",
                        loss_ledger=ledger_2,
                        target_verifier={"verifier_id": "v_hop2", "executed": True, "outcome": "verified"},
                    ),
                    CodaMurHopSpec(
                        hop_id="hop3_lossless_analytical",
                        source_heading=h2_target,
                        target_heading=h2_target,
                        group_attribute="customer_id",
                        value_attribute="amount",
                        predicate_attribute="status",
                        predicate_expected_value="paid",
                        loss_ledger=None,
                        target_verifier={"verifier_id": "v_hop3", "executed": True, "outcome": "verified"},
                    ),
                ]

            receipt = run_multi_hop_pipeline(
                schema=schema,
                initial_rows=rows,
                boundary=boundary,
                cdc_events=cdc_events,
                transport_hops=hops,
                pk_attribute="order_id",
            )

            self.assertTrue(receipt.certified, f"Trial {trial} failed certification: {receipt}")
            self.assertTrue(receipt.end_to_end_commutes, f"Trial {trial} failed commutation")
            self.assertFalse(receipt.authorized)
            self.assertFalse(receipt.certified_implies_authorized)
            self.assertEqual(receipt.authority_effect, "None")

            assert receipt.stage2_bqnf is not None
            assert receipt.stage3_coda_mur is not None
            self.assertTrue(receipt.stage2_bqnf.commutes_with_relational_join)

            if is_lossless_chain:
                self.assertEqual(receipt.stage3_coda_mur.local_route, "TransportOk")
                self.assertEqual(receipt.stage3_coda_mur.canonical_terminal, "Preserve")
                self.assertEqual(receipt.stage3_coda_mur.composed_erased_attributes, ())
            else:
                self.assertEqual(receipt.stage3_coda_mur.local_route, "DegradedTransportWithLoss")
                self.assertEqual(receipt.stage3_coda_mur.canonical_terminal, "Quarantine")
                self.assertEqual(
                    receipt.stage3_coda_mur.composed_erased_attributes,
                    ("audit_nonce", "customer_zip", "region"),
                )
                self.assertEqual(
                    receipt.stage3_coda_mur.loss_ledger_triggers,
                    (CODA_MUR_TRIGGER_ID, CODA_MUR_TRIGGER_ID),
                )

    def test_schema_mutation_matrix_stage1_relational_refusals(self) -> None:
        heading = ("order_id", "customer_id", "customer_zip", "status", "amount")
        base_fds = frozenset(
            [
                FunctionalDependency(frozenset(["order_id"]), frozenset(["customer_id", "status", "amount"])),
                FunctionalDependency.from_str("customer_id", "customer_zip"),
            ]
        )
        valid_rows = [
            {"order_id": 1, "customer_id": 10, "customer_zip": "10001", "status": "paid", "amount": 50.0},
            {"order_id": 2, "customer_id": 10, "customer_zip": "10001", "status": "pending", "amount": 30.0},
        ]
        boundary = BqnfBoundary(
            relations=("Orders",),
            attributes=("customer_id", "status", "amount"),
            predicates=("status = paid",),
            groups=("customer_id",),
            aggregates=("SUM(amount)",),
        )
        hops = [
            CodaMurHopSpec(
                hop_id="h1",
                source_heading=heading,
                target_heading=heading,
                group_attribute="customer_id",
                value_attribute="amount",
                predicate_attribute="status",
                predicate_expected_value="paid",
                target_verifier={"verifier_id": "v1", "executed": True, "outcome": "verified"},
            )
        ]

        # Mutation 1A: Non-atomic domain (violates 1NF)
        schema_non_atomic = RelationalSchema(
            attributes=frozenset(heading),
            dependencies=base_fds,
            attribute_domains={a: ("json_array" if a == "amount" else "scalar") for a in heading},
        )
        r1a = run_multi_hop_pipeline(schema_non_atomic, valid_rows, boundary, [], hops)
        self.assertFalse(r1a.certified)
        self.assertEqual(r1a.overall_terminal, "Refuse")
        self.assertEqual(r1a.stage1_relational.terminal_route, "SchemaMutationRefusal")

        # Mutation 1B: Dropped attribute in heading still referenced by FD
        schema_dangling_fd = RelationalSchema(
            attributes=frozenset(["order_id", "customer_id", "status", "amount"]),
            dependencies=base_fds,
        )
        r1b = run_multi_hop_pipeline(schema_dangling_fd, valid_rows, boundary, [], hops)
        self.assertFalse(r1b.certified)
        self.assertEqual(r1b.overall_terminal, "Refuse")
        self.assertEqual(r1b.stage1_relational.terminal_route, "SchemaMutationRefusal")

        # Mutation 1C: Instance violates declared transitive FD (customer_id 10 maps to two zips)
        schema_valid = RelationalSchema(attributes=frozenset(heading), dependencies=base_fds)
        fd_violating_rows = [
            {"order_id": 1, "customer_id": 10, "customer_zip": "10001", "status": "paid", "amount": 50.0},
            {"order_id": 2, "customer_id": 10, "customer_zip": "99999", "status": "paid", "amount": 30.0},
        ]
        r1c = run_multi_hop_pipeline(schema_valid, fd_violating_rows, boundary, [], hops)
        self.assertFalse(r1c.certified)
        self.assertEqual(r1c.overall_terminal, "Refuse")
        self.assertEqual(r1c.stage1_relational.terminal_route, "InstanceFdViolationRefusal")

    def test_schema_mutation_matrix_stage2_bqnf_refusals(self) -> None:
        heading = ("order_id", "customer_id", "customer_zip", "status", "amount")
        schema = RelationalSchema(
            attributes=frozenset(heading),
            dependencies=frozenset(
                [
                    FunctionalDependency(frozenset(["order_id"]), frozenset(["customer_id", "status", "amount"])),
                    FunctionalDependency.from_str("customer_id", "customer_zip"),
                ]
            ),
        )
        rows = [
            {"order_id": 1, "customer_id": 10, "customer_zip": "10001", "status": "paid", "amount": 50.0},
        ]
        boundary = BqnfBoundary(
            relations=("Orders",),
            attributes=("customer_id", "status", "amount"),
            predicates=("status = paid",),
            groups=("customer_id",),
            aggregates=("SUM(amount)",),
        )
        hops = [
            CodaMurHopSpec(
                hop_id="h1",
                source_heading=heading,
                target_heading=heading,
                group_attribute="customer_id",
                value_attribute="amount",
                predicate_attribute="status",
                predicate_expected_value="paid",
                target_verifier={"verifier_id": "v1", "executed": True, "outcome": "verified"},
            )
        ]

        # Mutation 2A: CDC event missing required boundary attribute 'status'
        ev_missing_col = BqnfCdcEvent(
            op="UPDATE",
            relation="Orders",
            old={"order_id": 1, "customer_id": 10, "amount": 50.0},
            new={"order_id": 1, "customer_id": 10, "amount": 80.0},
        )
        r2a = run_multi_hop_pipeline(schema, rows, boundary, [ev_missing_col], hops)
        self.assertFalse(r2a.certified)
        self.assertEqual(r2a.overall_terminal, "Invalidate")

        # Mutation 2B: Schema mutation changes aggregate to MAX(amount) without extremum cochain
        boundary_max = BqnfBoundary(
            relations=("Orders",),
            attributes=("customer_id", "status", "amount"),
            predicates=("status = paid",),
            groups=("customer_id",),
            aggregates=("MAX(amount)",),
        )
        ev_valid = BqnfCdcEvent(
            op="UPDATE",
            relation="Orders",
            old={"order_id": 1, "customer_id": 10, "customer_zip": "10001", "status": "paid", "amount": 50.0},
            new={"order_id": 1, "customer_id": 10, "customer_zip": "10001", "status": "paid", "amount": 80.0},
        )
        r2b = run_multi_hop_pipeline(schema, rows, boundary_max, [ev_valid], hops)
        self.assertFalse(r2b.certified)
        self.assertEqual(r2b.overall_terminal, "Unsupported")

        # Mutation 2C: CDC INSERT violates transitive FD customer_id -> customer_zip
        ev_fd_breach = BqnfCdcEvent(
            op="INSERT",
            relation="Orders",
            old=None,
            new={"order_id": 2, "customer_id": 10, "customer_zip": "BROKEN_ZIP", "status": "paid", "amount": 25.0},
        )
        r2c = run_multi_hop_pipeline(schema, rows, boundary, [ev_fd_breach], hops)
        self.assertFalse(r2c.certified)
        self.assertEqual(r2c.overall_terminal, "ClosureFailure")

    def test_schema_mutation_matrix_stage3_coda_mur_refusals(self) -> None:
        heading = ("order_id", "customer_id", "customer_zip", "status", "amount")
        target_lossy = ("order_id", "customer_id", "status", "amount")
        schema = RelationalSchema(
            attributes=frozenset(heading),
            dependencies=frozenset(
                [
                    FunctionalDependency(frozenset(["order_id"]), frozenset(["customer_id", "status", "amount"])),
                    FunctionalDependency.from_str("customer_id", "customer_zip"),
                ]
            ),
        )
        rows = [
            {"order_id": 1, "customer_id": 10, "customer_zip": "10001", "status": "paid", "amount": 50.0},
        ]
        boundary = BqnfBoundary(
            relations=("Orders",),
            attributes=("customer_id", "status", "amount"),
            predicates=("status = paid",),
            groups=("customer_id",),
            aggregates=("SUM(amount)",),
        )
        ev_valid = BqnfCdcEvent(
            op="UPDATE",
            relation="Orders",
            old={"order_id": 1, "customer_id": 10, "customer_zip": "10001", "status": "paid", "amount": 50.0},
            new={"order_id": 1, "customer_id": 10, "customer_zip": "10001", "status": "paid", "amount": 90.0},
        )

        # Mutation 3A: Dropping customer_zip without a LossLedger -> LossLedgerMissing (Refuse)
        hop_no_ledger = CodaMurHopSpec(
            hop_id="drop_zip_no_ledger",
            source_heading=heading,
            target_heading=target_lossy,
            group_attribute="customer_id",
            value_attribute="amount",
            predicate_attribute="status",
            predicate_expected_value="paid",
            loss_ledger=None,
            target_verifier={"verifier_id": "v1", "executed": True, "outcome": "verified"},
        )
        r3a = run_multi_hop_pipeline(schema, rows, boundary, [ev_valid], [hop_no_ledger])
        self.assertFalse(r3a.certified)
        self.assertEqual(r3a.overall_terminal, "Refuse")
        assert r3a.stage3_coda_mur is not None
        self.assertEqual(r3a.stage3_coda_mur.local_route, "LossLedgerMissing")

        # Mutation 3B: Tampered LossLedger merkle_digest -> LossLedgerMissing (Refuse)
        tampered_ledger = build_sealed_loss_ledger(["customer_zip"], rows, "order_id")
        tampered_ledger["merkle_digest"] = "0" * 64
        hop_tampered_ledger = CodaMurHopSpec(
            hop_id="drop_zip_tampered",
            source_heading=heading,
            target_heading=target_lossy,
            group_attribute="customer_id",
            value_attribute="amount",
            predicate_attribute="status",
            predicate_expected_value="paid",
            loss_ledger=tampered_ledger,
            target_verifier={"verifier_id": "v1", "executed": True, "outcome": "verified"},
        )
        r3b = run_multi_hop_pipeline(schema, rows, boundary, [ev_valid], [hop_tampered_ledger])
        self.assertFalse(r3b.certified)
        self.assertEqual(r3b.overall_terminal, "Refuse")
        assert r3b.stage3_coda_mur is not None
        self.assertEqual(r3b.stage3_coda_mur.local_route, "LossLedgerMissing")

        # Mutation 3C: Pending target verifier -> AuthorityLaundering (Refuse)
        valid_ledger = build_sealed_loss_ledger(["customer_zip"], rows, "order_id")
        hop_pending_verifier = CodaMurHopSpec(
            hop_id="pending_verifier",
            source_heading=heading,
            target_heading=target_lossy,
            group_attribute="customer_id",
            value_attribute="amount",
            predicate_attribute="status",
            predicate_expected_value="paid",
            loss_ledger=valid_ledger,
            target_verifier={"verifier_id": "v1", "executed": False, "outcome": "pending"},
        )
        r3c = run_multi_hop_pipeline(schema, rows, boundary, [ev_valid], [hop_pending_verifier])
        self.assertFalse(r3c.certified)
        self.assertEqual(r3c.overall_terminal, "Refuse")
        assert r3c.stage3_coda_mur is not None
        self.assertEqual(r3c.stage3_coda_mur.local_route, "AuthorityLaundering")

        # Mutation 3D: Dropping protected boundary attribute 'amount' -> TransportViolation (Reject)
        bad_target = ("order_id", "customer_id", "status")
        ledger_drop_amount = build_sealed_loss_ledger(["customer_zip", "amount"], rows, "order_id")
        hop_drop_protected = CodaMurHopSpec(
            hop_id="drop_protected_amount",
            source_heading=heading,
            target_heading=bad_target,
            group_attribute="customer_id",
            value_attribute="amount",
            predicate_attribute="status",
            predicate_expected_value="paid",
            loss_ledger=ledger_drop_amount,
            target_verifier={"verifier_id": "v1", "executed": True, "outcome": "verified"},
        )
        r3d = run_multi_hop_pipeline(schema, rows, boundary, [ev_valid], [hop_drop_protected])
        self.assertFalse(r3d.certified)
        self.assertEqual(r3d.overall_terminal, "Reject")
        assert r3d.stage3_coda_mur is not None
        self.assertEqual(r3d.stage3_coda_mur.local_route, "TransportViolation")

        # Mutation 3E: Commutation square drift (D_target(F(r)) != F_bar(D_source(r))) -> TransportViolation (Reject)
        hop_drift = CodaMurHopSpec(
            hop_id="commutation_drift",
            source_heading=heading,
            target_heading=target_lossy,
            group_attribute="customer_id",
            value_attribute="amount",
            predicate_attribute="status",
            predicate_expected_value="paid",
            loss_ledger=valid_ledger,
            target_verifier={"verifier_id": "v1", "executed": True, "outcome": "verified"},
            injected_target_tamper_delta=5.0,
        )
        r3e = run_multi_hop_pipeline(schema, rows, boundary, [ev_valid], [hop_drift])
        self.assertFalse(r3e.certified)
        self.assertEqual(r3e.overall_terminal, "Reject")
        assert r3e.stage3_coda_mur is not None
        self.assertEqual(r3e.stage3_coda_mur.local_route, "TransportViolation")


if __name__ == "__main__":
    unittest.main()
