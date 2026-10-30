"""Property-based and randomized schema-mutation tests for multi-hop composition:
Stage 1 (3NF / BCNF relational synthesis)
  -> Stage 2 / 2b (BQNF streaming CDC repair, non-invertible MIN/MAX priority-queue
                   cochains, dynamic-bucket epsilon-BQNF quantile sketches under
                   skewed power-law streams, and multi-column composite grouping keys)
  -> Stage 3 (CODA_MUR representation transport)
  -> Stage 4 (nf.epistemic.freshness observer-relative freshness poset chain).

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
from normal_forms.evaluator import NormalFormsEvaluator
from normal_forms.multi_hop_composition import (
    CODA_MUR_TRIGGER_ID,
    CodaMurHopSpec,
    SalesCochainCdcSpec,
    WatermarkSpec,
    build_sealed_loss_ledger,
    decode_composite_group_key,
    encode_composite_group_key,
    evaluate_stage1_relational_synthesis,
    evaluate_stage2b_cochain_extrema_quantiles,
    evaluate_watermarked_cdc_stream_with_observer_poset,
    project_and_rejoin,
    run_extended_multi_hop_pipeline,
    run_multi_hop_pipeline,
)
from normal_forms.observer_freshness_example import ObserverSpec


def _sample_power_law_amount(
    rng: random.Random,
    x_min: float = 10.0,
    scale: float = 1.5,
    alpha: float = 2.4,
    x_max: float = 240.0,
) -> float:
    """Samples a skewed Pareto / power-law value X = x_min + scale * ((1 - U)^(-1/alpha) - 1)."""
    u = rng.uniform(0.01, 0.985)
    raw = x_min + scale * ((1.0 - u) ** (-1.0 / alpha) - 1.0)
    return round(min(raw, x_max), 4)


def _generate_random_schema_and_instance(
    rng: random.Random,
) -> Tuple[RelationalSchema, List[Dict[str, Any]]]:
    """Generates a randomized relational schema with partial and transitive FDs and a valid instance."""
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


def _build_sales_cochain_schema() -> Tuple[Tuple[str, ...], RelationalSchema]:
    heading = ("sale_id", "customer_id", "customer_zip", "region", "amount", "audit_nonce")
    schema = RelationalSchema(
        attributes=frozenset(heading),
        dependencies=frozenset(
            [
                FunctionalDependency(
                    frozenset(["sale_id"]),
                    frozenset(["customer_id", "amount", "audit_nonce"]),
                ),
                FunctionalDependency.from_str("customer_id", "customer_zip"),
                FunctionalDependency.from_str("customer_zip", "region"),
            ]
        ),
        attribute_domains={a: "scalar" for a in heading},
    )
    return heading, schema


def _build_composite_group_sales_schema() -> Tuple[Tuple[str, ...], RelationalSchema]:
    """Schema with two independent transitive chains:
      1. customer_id -> customer_zip -> region
      2. merchant_id -> channel, tier
    supporting 2-column (region, channel) and 3-column (region, channel, tier) composite group keys.
    """
    heading = (
        "sale_id",
        "customer_id",
        "customer_zip",
        "merchant_id",
        "region",
        "channel",
        "tier",
        "amount",
        "audit_nonce",
    )
    schema = RelationalSchema(
        attributes=frozenset(heading),
        dependencies=frozenset(
            [
                FunctionalDependency(
                    frozenset(["sale_id"]),
                    frozenset(["customer_id", "merchant_id", "amount", "audit_nonce"]),
                ),
                FunctionalDependency.from_str("customer_id", "customer_zip"),
                FunctionalDependency.from_str("customer_zip", "region"),
                FunctionalDependency(
                    frozenset(["merchant_id"]),
                    frozenset(["channel", "tier"]),
                ),
            ]
        ),
        attribute_domains={a: "scalar" for a in heading},
    )
    return heading, schema


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

    def test_randomized_extrema_cochain_vs_fallback_recomputation_80_trials(self) -> None:
        """Verifies non-invertible MIN/MAX priority-queue cochain O(log K) repair vs bounded
        fallback recomputation across 80 randomized CDC streams containing destructive deletions.
        """
        rng = random.Random(27182818)
        _, schema = _build_sales_cochain_schema()
        cust_zip = {1: "10001", 2: "20002", 3: "30003", 4: "40004"}
        zip_reg = {"10001": "REG_EAST", "20002": "REG_EAST", "30003": "REG_WEST", "40004": "REG_WEST"}

        for trial in range(80):
            initial_rows: List[Dict[str, Any]] = []
            active_by_id: Dict[int, Dict[str, Any]] = {}
            for sid in range(1, 9):
                cid = (sid % 4) + 1
                cz = cust_zip[cid]
                r = {
                    "sale_id": sid,
                    "customer_id": cid,
                    "customer_zip": cz,
                    "region": zip_reg[cz],
                    "amount": float(rng.randint(2, 40) * 5 + sid),
                    "audit_nonce": f"n_{sid}",
                }
                initial_rows.append(r)
                active_by_id[sid] = dict(r)

            s1_receipt, rejoined_init = evaluate_stage1_relational_synthesis(schema, initial_rows)
            self.assertTrue(s1_receipt.certified)

            # Build a stream of 6 CDC events where the first event is a destructive deletion of
            # the current maximum in REG_EAST (while REG_EAST still has remaining rows)
            east_rows = [r for r in active_by_id.values() if r["region"] == "REG_EAST"]
            max_east_row = max(east_rows, key=lambda x: float(x["amount"]))
            del active_by_id[int(max_east_row["sale_id"])]

            cochain_events: List[SalesCochainCdcSpec] = [
                SalesCochainCdcSpec(
                    op_type="DELETE",
                    sale_id=int(max_east_row["sale_id"]),
                    old_region=str(max_east_row["region"]),
                    old_amount=float(max_east_row["amount"]),
                )
            ]

            next_sid = 100
            for _ in range(5):
                op = rng.choice(["INSERT", "UPDATE", "DELETE_EXTREMUM"])
                if op == "INSERT" or len(active_by_id) <= 3:
                    cid = rng.randint(1, 4)
                    cz = cust_zip[cid]
                    reg = zip_reg[cz]
                    amt = float(rng.randint(1, 50) * 4 + rng.randint(1, 3))
                    new_r = {
                        "sale_id": next_sid,
                        "customer_id": cid,
                        "customer_zip": cz,
                        "region": reg,
                        "amount": amt,
                        "audit_nonce": f"n_{next_sid}",
                    }
                    cochain_events.append(
                        SalesCochainCdcSpec(
                            op_type="INSERT",
                            sale_id=next_sid,
                            new_region=reg,
                            new_amount=amt,
                            new_row=new_r,
                        )
                    )
                    active_by_id[next_sid] = new_r
                    next_sid += 1
                elif op == "DELETE_EXTREMUM":
                    west_rows = [r for r in active_by_id.values() if r["region"] == "REG_WEST"]
                    if len(west_rows) >= 2:
                        min_west = min(west_rows, key=lambda x: float(x["amount"]))
                        del active_by_id[int(min_west["sale_id"])]
                        cochain_events.append(
                            SalesCochainCdcSpec(
                                op_type="DELETE",
                                sale_id=int(min_west["sale_id"]),
                                old_region=str(min_west["region"]),
                                old_amount=float(min_west["amount"]),
                            )
                        )
                    else:
                        target_sid = rng.choice(sorted(active_by_id.keys()))
                        old_r = dict(active_by_id[target_sid])
                        new_r = dict(old_r)
                        new_r["amount"] = float(rng.randint(1, 60) * 3)
                        active_by_id[target_sid] = new_r
                        cochain_events.append(
                            SalesCochainCdcSpec(
                                op_type="UPDATE",
                                sale_id=target_sid,
                                old_region=str(old_r["region"]),
                                new_region=str(new_r["region"]),
                                old_amount=float(old_r["amount"]),
                                new_amount=float(new_r["amount"]),
                                old_row=old_r,
                                new_row=new_r,
                            )
                        )
                else:
                    target_sid = rng.choice(sorted(active_by_id.keys()))
                    old_r = dict(active_by_id[target_sid])
                    new_r = dict(old_r)
                    new_r["amount"] = float(rng.randint(1, 60) * 3)
                    active_by_id[target_sid] = new_r
                    cochain_events.append(
                        SalesCochainCdcSpec(
                            op_type="UPDATE",
                            sale_id=target_sid,
                            old_region=str(old_r["region"]),
                            new_region=str(new_r["region"]),
                            old_amount=float(old_r["amount"]),
                            new_amount=float(new_r["amount"]),
                            old_row=old_r,
                            new_row=new_r,
                        )
                    )

            # 1. Evaluate WITH priority-queue extremum cochain (use_cochain=True)
            res_cochain, _ = evaluate_stage2b_cochain_extrema_quantiles(
                schema=schema,
                nf3_components=s1_receipt.nf3_components,
                initial_rows=rejoined_init,
                cochain_cdc_events=cochain_events,
                use_cochain=True,
                track_quantiles=False,
                pk_attribute="sale_id",
            )
            self.assertTrue(res_cochain.certified, f"Trial {trial}: cochain repair failed certification")
            self.assertTrue(res_cochain.verified_consistent)
            self.assertTrue(res_cochain.commutes_with_3nf_rejoin)
            self.assertEqual(res_cochain.fallback_recomputations, 0)
            self.assertGreaterEqual(res_cochain.extrema_repairs, 1)
            self.assertEqual(res_cochain.terminal_route, "Repair")

            # 2. Evaluate WITHOUT priority-queue extremum cochain (use_cochain=False)
            res_fallback, _ = evaluate_stage2b_cochain_extrema_quantiles(
                schema=schema,
                nf3_components=s1_receipt.nf3_components,
                initial_rows=rejoined_init,
                cochain_cdc_events=cochain_events,
                use_cochain=False,
                track_quantiles=False,
                pk_attribute="sale_id",
            )
            self.assertTrue(res_fallback.certified, f"Trial {trial}: fallback recomputation failed certification")
            self.assertTrue(res_fallback.verified_consistent)
            self.assertTrue(res_fallback.commutes_with_3nf_rejoin)
            self.assertGreaterEqual(res_fallback.fallback_recomputations, 1)
            self.assertEqual(res_fallback.terminal_route, "Recompute")

            # Both paths must converge to identical totals, counts, and MIN/MAX extrema
            self.assertEqual(res_cochain.cached_state, res_fallback.cached_state)
            self.assertEqual(res_cochain.cached_extrema, res_fallback.cached_extrema)

    def test_randomized_epsilon_bqnf_quantile_sketch_tolerance_regimes_80_trials(self) -> None:
        """Verifies epsilon-BQNF quantile sketch O(B) repair when |q_hat - q_true| <= epsilon
        vs bounded fallback recomputation when |q_hat - q_true| > epsilon across 80 randomized trials.
        """
        rng = random.Random(16180339)
        _, schema = _build_sales_cochain_schema()
        cust_zip = {1: "10001", 2: "20002"}
        zip_reg = {"10001": "REG_NORTH", "20002": "REG_SOUTH"}

        for trial in range(80):
            base_b = rng.randint(1, 8) * 10
            initial_rows: List[Dict[str, Any]] = [
                {
                    "sale_id": 1,
                    "customer_id": 1,
                    "customer_zip": "10001",
                    "region": "REG_NORTH",
                    "amount": float(base_b + 1),
                    "audit_nonce": "n_1",
                },
                {
                    "sale_id": 2,
                    "customer_id": 1,
                    "customer_zip": "10001",
                    "region": "REG_NORTH",
                    "amount": float(base_b + 3),
                    "audit_nonce": "n_2",
                },
                {
                    "sale_id": 3,
                    "customer_id": 1,
                    "customer_zip": "10001",
                    "region": "REG_NORTH",
                    "amount": float(base_b + 42),
                    "audit_nonce": "n_3",
                },
                {
                    "sale_id": 4,
                    "customer_id": 2,
                    "customer_zip": "20002",
                    "region": "REG_SOUTH",
                    "amount": float(base_b + 14),
                    "audit_nonce": "n_4",
                },
                {
                    "sale_id": 5,
                    "customer_id": 2,
                    "customer_zip": "20002",
                    "region": "REG_SOUTH",
                    "amount": float(base_b + 28),
                    "audit_nonce": "n_5",
                },
            ]
            s1_receipt, rejoined_init = evaluate_stage1_relational_synthesis(schema, initial_rows)
            self.assertTrue(s1_receipt.certified)

            cochain_events: List[SalesCochainCdcSpec] = []
            for step in range(4):
                sid = 10 + step
                cid = rng.choice([1, 2])
                cz = cust_zip[cid]
                reg = zip_reg[cz]
                amt = float(rng.randint(1, 12) * 10 + rng.choice([1, 2, 3, 4, 6, 7, 8, 9]))
                cochain_events.append(
                    SalesCochainCdcSpec(
                        op_type="INSERT",
                        sale_id=sid,
                        new_region=reg,
                        new_amount=amt,
                        new_row={
                            "sale_id": sid,
                            "customer_id": cid,
                            "customer_zip": cz,
                            "region": reg,
                            "amount": amt,
                            "audit_nonce": f"n_{sid}",
                        },
                    )
                )

            # Regime A: Generous quotient tolerance epsilon = 120.0 (all sketch interpolations within tolerance)
            res_eps_ok, _ = evaluate_stage2b_cochain_extrema_quantiles(
                schema=schema,
                nf3_components=s1_receipt.nf3_components,
                initial_rows=rejoined_init,
                cochain_cdc_events=cochain_events,
                use_cochain=True,
                track_quantiles=True,
                quantile_tolerance=120.0,
                pk_attribute="sale_id",
            )
            self.assertTrue(res_eps_ok.certified, f"Trial {trial}: generous tolerance failed certification")
            self.assertTrue(res_eps_ok.quantile_accuracy_verified)
            self.assertEqual(res_eps_ok.quantile_fallback_recomputations, 0)
            self.assertGreaterEqual(res_eps_ok.quantile_repairs, 1)
            self.assertEqual(res_eps_ok.terminal_route, "Repair")

            # Regime B: Intermediate quotient tolerance epsilon = 12.0 (guarantees error <= 12.0 via hybrid repair/fallback)
            res_eps_mid, _ = evaluate_stage2b_cochain_extrema_quantiles(
                schema=schema,
                nf3_components=s1_receipt.nf3_components,
                initial_rows=rejoined_init,
                cochain_cdc_events=cochain_events,
                use_cochain=True,
                track_quantiles=True,
                quantile_tolerance=12.0,
                pk_attribute="sale_id",
            )
            self.assertTrue(res_eps_mid.certified, f"Trial {trial}: intermediate tolerance failed certification")
            self.assertTrue(res_eps_mid.quantile_accuracy_verified)
            for reg, t_med in res_eps_mid.true_medians.items():
                self.assertLessEqual(abs(float(res_eps_mid.cached_medians[reg]) - float(t_med)), 12.0 + 1e-9)

            # Regime C: Zero tolerance epsilon = 0.0 (forces fallback recomputation whenever sketch != exact median)
            res_eps_zero, _ = evaluate_stage2b_cochain_extrema_quantiles(
                schema=schema,
                nf3_components=s1_receipt.nf3_components,
                initial_rows=rejoined_init,
                cochain_cdc_events=cochain_events,
                use_cochain=True,
                track_quantiles=True,
                quantile_tolerance=0.0,
                pk_attribute="sale_id",
            )
            self.assertTrue(res_eps_zero.certified, f"Trial {trial}: zero tolerance failed certification")
            self.assertTrue(res_eps_zero.quantile_accuracy_verified)
            self.assertGreaterEqual(res_eps_zero.quantile_fallback_recomputations, 1)
            self.assertEqual(res_eps_zero.terminal_route, "Recompute")
            for reg, t_med in res_eps_zero.true_medians.items():
                self.assertAlmostEqual(float(res_eps_zero.cached_medians[reg]), float(t_med), places=9)

    def test_randomized_4hop_end_to_end_with_observer_poset_monotonicity_100_trials(self) -> None:
        """100 randomized end-to-end trials chaining:
        Hop 1 (3NF/BCNF synthesis)
          -> Hop 2b (Extrema MIN/MAX priority-queue cochain + epsilon-BQNF quantile sketch)
          -> Hop 3 (CODA_MUR multi-hop representation transport with sealed loss ledgers)
          -> Hop 4 (nf.epistemic.freshness 4-observer poset chain O_1 <= O_2 <= O_3 <= O_4).
        """
        rng = random.Random(14142135)
        heading, schema = _build_sales_cochain_schema()
        cust_zip = {c: f"ZIP_{c}00" for c in range(1, 5)}
        zip_reg = {"ZIP_100": "US-EAST", "ZIP_200": "US-EAST", "ZIP_300": "US-WEST", "ZIP_400": "US-WEST"}

        observer_poset = [
            ObserverSpec(
                observer_id="O1_hft_2s",
                max_lag_seconds=2,
                authorized_scopes=("regional_sales",),
            ),
            ObserverSpec(
                observer_id="O2_ops_10s",
                max_lag_seconds=10,
                authorized_scopes=("regional_sales", "ops_dashboard"),
            ),
            ObserverSpec(
                observer_id="O3_exec_30s",
                max_lag_seconds=30,
                authorized_scopes=("regional_sales", "ops_dashboard", "exec_report"),
            ),
            ObserverSpec(
                observer_id="O4_warehouse_60s",
                max_lag_seconds=60,
                authorized_scopes=("regional_sales", "ops_dashboard", "exec_report", "cold_archive"),
            ),
        ]

        for trial in range(100):
            initial_rows: List[Dict[str, Any]] = []
            active_by_id: Dict[int, Dict[str, Any]] = {}
            for sid in range(1, 8):
                cid = rng.randint(1, 4)
                cz = cust_zip[cid]
                r = {
                    "sale_id": sid,
                    "customer_id": cid,
                    "customer_zip": cz,
                    "region": zip_reg[cz],
                    "amount": float(rng.randint(1, 25) * 8 + rng.randint(1, 7)),
                    "audit_nonce": f"n_{sid}",
                }
                initial_rows.append(r)
                active_by_id[sid] = dict(r)

            cochain_events: List[SalesCochainCdcSpec] = []
            next_sid = 50
            for _ in range(6):
                op = rng.choice(["INSERT", "UPDATE", "DELETE"])
                if op == "INSERT" or len(active_by_id) <= 3:
                    cid = rng.randint(1, 4)
                    cz = cust_zip[cid]
                    reg = zip_reg[cz]
                    amt = float(rng.randint(1, 30) * 6 + rng.randint(1, 5))
                    new_r = {
                        "sale_id": next_sid,
                        "customer_id": cid,
                        "customer_zip": cz,
                        "region": reg,
                        "amount": amt,
                        "audit_nonce": f"n_{next_sid}",
                    }
                    cochain_events.append(
                        SalesCochainCdcSpec(
                            op_type="INSERT",
                            sale_id=next_sid,
                            new_region=reg,
                            new_amount=amt,
                            new_row=new_r,
                        )
                    )
                    active_by_id[next_sid] = new_r
                    next_sid += 1
                elif op == "DELETE":
                    target_sid = rng.choice(sorted(active_by_id.keys()))
                    old_r = active_by_id.pop(target_sid)
                    cochain_events.append(
                        SalesCochainCdcSpec(
                            op_type="DELETE",
                            sale_id=target_sid,
                            old_region=str(old_r["region"]),
                            old_amount=float(old_r["amount"]),
                        )
                    )
                else:
                    target_sid = rng.choice(sorted(active_by_id.keys()))
                    old_r = dict(active_by_id[target_sid])
                    new_r = dict(old_r)
                    new_r["amount"] = float(rng.randint(1, 35) * 5 + rng.randint(1, 4))
                    active_by_id[target_sid] = new_r
                    cochain_events.append(
                        SalesCochainCdcSpec(
                            op_type="UPDATE",
                            sale_id=target_sid,
                            old_region=str(old_r["region"]),
                            new_region=str(new_r["region"]),
                            old_amount=float(old_r["amount"]),
                            new_amount=float(new_r["amount"]),
                            old_row=old_r,
                            new_row=new_r,
                        )
                    )

            h1_target = ("sale_id", "customer_id", "customer_zip", "region", "amount")
            h2_target = ("sale_id", "region", "amount")
            hops = [
                CodaMurHopSpec(
                    hop_id="hop1_strip_nonce",
                    source_heading=heading,
                    target_heading=h1_target,
                    group_attribute="region",
                    value_attribute="amount",
                    loss_ledger=build_sealed_loss_ledger(["audit_nonce"], initial_rows, "sale_id"),
                    target_verifier={"verifier_id": "v_h1", "executed": True, "outcome": "verified"},
                ),
                CodaMurHopSpec(
                    hop_id="hop2_strip_customer",
                    source_heading=h1_target,
                    target_heading=h2_target,
                    group_attribute="region",
                    value_attribute="amount",
                    loss_ledger=build_sealed_loss_ledger(["customer_id", "customer_zip"], initial_rows, "sale_id"),
                    target_verifier={"verifier_id": "v_h2", "executed": True, "outcome": "verified"},
                ),
            ]

            lag_sec = rng.choice([1, 5, 15, 45])
            packet = {
                "value_ref": f"region_sales_cache:trial_{trial}",
                "packet_scope": "regional_sales",
                "replica_lag_seconds": lag_sec,
            }

            use_cochain = (trial % 4 != 0)
            q_tol = 25.0 if (trial % 3 != 0) else 0.0

            receipt = run_extended_multi_hop_pipeline(
                schema=schema,
                initial_rows=initial_rows,
                cochain_cdc_events=cochain_events,
                transport_hops=hops,
                observer_poset=observer_poset,
                freshness_packet=packet,
                use_cochain=use_cochain,
                track_quantiles=True,
                quantile_tolerance=q_tol,
                pk_attribute="sale_id",
            )

            self.assertTrue(receipt.certified, f"Trial {trial} failed certification: {receipt}")
            self.assertTrue(receipt.end_to_end_commutes)
            self.assertFalse(receipt.authorized)
            self.assertFalse(receipt.certified_implies_authorized)
            self.assertEqual(receipt.authority_effect, "None")

            assert receipt.stage2_cochain is not None
            assert receipt.stage3_coda_mur is not None
            assert receipt.stage4_observer_poset is not None

            self.assertTrue(receipt.stage2_cochain.verified_consistent)
            self.assertTrue(receipt.stage2_cochain.commutes_with_3nf_rejoin)
            self.assertTrue(receipt.stage2_cochain.quantile_accuracy_verified)
            self.assertTrue(receipt.stage3_coda_mur.commutation_verified)
            self.assertTrue(receipt.stage4_observer_poset.poset_chain_valid)
            self.assertTrue(receipt.stage4_observer_poset.monotonicity_preserved)

            if lag_sec == 1:
                self.assertEqual(
                    receipt.stage4_observer_poset.admitted_observers,
                    ("O1_hft_2s", "O2_ops_10s", "O3_exec_30s", "O4_warehouse_60s"),
                )
                self.assertEqual(receipt.stage4_observer_poset.terminal_route, "AuthorizedFresh")
            elif lag_sec == 5:
                self.assertEqual(
                    receipt.stage4_observer_poset.admitted_observers,
                    ("O2_ops_10s", "O3_exec_30s", "O4_warehouse_60s"),
                )
                self.assertEqual(receipt.stage4_observer_poset.rejected_observers, ("O1_hft_2s",))
                self.assertEqual(receipt.stage4_observer_poset.terminal_route, "PartialPosetAdmissibility")
            elif lag_sec == 15:
                self.assertEqual(
                    receipt.stage4_observer_poset.admitted_observers,
                    ("O3_exec_30s", "O4_warehouse_60s"),
                )
                self.assertEqual(
                    receipt.stage4_observer_poset.rejected_observers,
                    ("O1_hft_2s", "O2_ops_10s"),
                )
            elif lag_sec == 45:
                self.assertEqual(
                    receipt.stage4_observer_poset.admitted_observers,
                    ("O4_warehouse_60s",),
                )
                self.assertEqual(
                    receipt.stage4_observer_poset.rejected_observers,
                    ("O1_hft_2s", "O2_ops_10s", "O3_exec_30s"),
                )

    def test_dynamic_quantile_bucket_splitting_and_merging_under_skewed_power_law_80_trials(self) -> None:
        """Verifies dynamic dyadic bucket-boundary splitting and bottom-up sibling/cousin
        merging in region_quantile_cochain under skewed Pareto / power-law streams across 80 trials.
        """
        rng = random.Random(20261030)
        for trial in range(80):
            alpha = rng.uniform(1.8, 3.2)
            # Generate 18 skewed power-law samples heavily concentrated in [10.0, 26.0) with occasional tail outliers
            samples = [
                _sample_power_law_amount(rng, x_min=10.0, scale=1.2, alpha=alpha, x_max=150.0)
                for _ in range(18)
            ]

            with NormalFormsEvaluator(in_memory=True) as ev_dyn, NormalFormsEvaluator(in_memory=True) as ev_static:
                splits_observed = 0
                for idx, amt in enumerate(samples, start=1):
                    reb_info = ev_dyn.apply_sales_cdc(
                        op_type="INSERT",
                        sale_id=idx,
                        new_region="POWER_LAW_HEAD",
                        new_amount=amt,
                        maintain_cochain=True,
                        dynamic_buckets=True,
                        bucket_width=16.0,
                        split_threshold=4,
                        merge_threshold=2,
                        min_bucket_width=0.5,
                    )
                    splits_observed += int(reb_info["splits_executed"])
                    ev_static.apply_sales_cdc(
                        op_type="INSERT",
                        sale_id=idx,
                        new_region="POWER_LAW_HEAD",
                        new_amount=amt,
                        maintain_cochain=True,
                        dynamic_buckets=False,
                        bucket_width=16.0,
                    )

                    inv_ok, inv_errs = ev_dyn.verify_quantile_cochain_invariants("POWER_LAW_HEAD")
                    self.assertTrue(inv_ok, f"Trial {trial} step {idx} invariant violation: {inv_errs}")

                # Dynamic splitting must have refined the dense power-law head
                self.assertGreaterEqual(splits_observed, 2, f"Trial {trial}: expected dyadic bucket splits")

                true_med = ev_dyn.compute_true_median("POWER_LAW_HEAD")
                est_dyn = ev_dyn.estimate_quantile("POWER_LAW_HEAD", q=0.5)
                est_static = ev_static.estimate_quantile("POWER_LAW_HEAD", q=0.5)
                assert true_med is not None and est_dyn is not None and est_static is not None

                err_dyn = abs(est_dyn - true_med)
                err_static = abs(est_static - true_med)
                # Because the median bucket in dynamic mode has width <= 16.0 (typically 0.5..4.0),
                # its linear interpolation error is bounded by its refined bucket width and <= static coarse error
                self.assertLessEqual(
                    err_dyn,
                    err_static + 1.0,
                    f"Trial {trial}: dynamic error {err_dyn} exceeded static coarse error {err_static}",
                )

                # Count active buckets at peak before draining
                cur_dyn = ev_dyn.conn.cursor()
                cur_dyn.execute(
                    "SELECT COUNT(*) FROM region_quantile_cochain WHERE region = 'POWER_LAW_HEAD' AND count > 0;"
                )
                peak_buckets = int(cur_dyn.fetchone()[0])
                self.assertGreaterEqual(peak_buckets, 2)

                # Drain phase: delete 17 of the 18 samples so sub-buckets fall <= merge_threshold (2) and coalesce
                merges_observed = 0
                for del_id in range(1, 18):
                    reb_del = ev_dyn.apply_sales_cdc(
                        op_type="DELETE",
                        sale_id=del_id,
                        old_region="POWER_LAW_HEAD",
                        old_amount=samples[del_id - 1],
                        maintain_cochain=True,
                        dynamic_buckets=True,
                        bucket_width=16.0,
                        split_threshold=4,
                        merge_threshold=2,
                        min_bucket_width=0.5,
                    )
                    merges_observed += int(reb_del["merges_executed"])
                    inv_ok_del, inv_errs_del = ev_dyn.verify_quantile_cochain_invariants("POWER_LAW_HEAD")
                    self.assertTrue(
                        inv_ok_del,
                        f"Trial {trial} delete {del_id} invariant violation: {inv_errs_del}",
                    )

                self.assertGreaterEqual(merges_observed, 1, f"Trial {trial}: expected dyadic bucket merges on drain")
                cur_dyn.execute(
                    "SELECT COUNT(*), MIN(upper_bound - lower_bound) FROM region_quantile_cochain "
                    "WHERE region = 'POWER_LAW_HEAD' AND count > 0;"
                )
                drain_row = cur_dyn.fetchone()
                post_drain_buckets = int(drain_row[0])
                post_drain_width = float(drain_row[1])
                self.assertEqual(post_drain_buckets, 1)
                self.assertLess(post_drain_buckets, peak_buckets)
                self.assertAlmostEqual(post_drain_width, 16.0, places=6)

    def test_multi_column_composite_grouping_keys_4hop_power_law_80_trials(self) -> None:
        """Verifies 4-hop composition across 2-column (region, channel) and 3-column
        (region, channel, tier) composite grouping keys under skewed power-law CDC streams
        and dynamic quantile bucket splitting/merging across 80 randomized trials.
        """
        rng = random.Random(987654321)
        heading, schema = _build_composite_group_sales_schema()

        cust_zip = {1: "10001", 2: "20002", 3: "30003", 4: "40004"}
        zip_reg = {"10001": "US-EAST", "20002": "US-EAST", "30003": "US-WEST", "40004": "US-WEST"}
        merch_info = {
            101: ("B2B", "GOLD"),
            102: ("B2B", "SILVER"),
            103: ("RETAIL", "GOLD"),
            104: ("RETAIL", "SILVER"),
        }

        observer_poset = [
            ObserverSpec("O1_rt_2s", max_lag_seconds=2, authorized_scopes=("composite_sales",)),
            ObserverSpec("O2_ops_15s", max_lag_seconds=15, authorized_scopes=("composite_sales", "ops")),
            ObserverSpec("O3_batch_60s", max_lag_seconds=60, authorized_scopes=("composite_sales", "ops", "archive")),
        ]

        for trial in range(80):
            # Alternate between 2-column and 3-column composite grouping keys
            group_attrs: Tuple[str, ...] = (
                ("region", "channel") if (trial % 2 == 0) else ("region", "channel", "tier")
            )

            initial_rows: List[Dict[str, Any]] = []
            active_by_id: Dict[int, Dict[str, Any]] = {}
            for sid in range(1, 13):
                # Concentrate initial rows into 2 composite groups so power-law head triggers splits
                cid = 1 if (sid <= 8) else 3
                mid = 101 if (sid <= 8) else 103
                cz = cust_zip[cid]
                reg = zip_reg[cz]
                chan, tier = merch_info[mid]
                amt = _sample_power_law_amount(rng, x_min=20.0, scale=1.5, alpha=2.5, x_max=180.0)
                row = {
                    "sale_id": sid,
                    "customer_id": cid,
                    "customer_zip": cz,
                    "merchant_id": mid,
                    "region": reg,
                    "channel": chan,
                    "tier": tier,
                    "amount": amt,
                    "audit_nonce": f"n_{sid}",
                }
                initial_rows.append(row)
                active_by_id[sid] = dict(row)

            cochain_events: List[SalesCochainCdcSpec] = []
            next_sid = 100
            for step in range(8):
                op = rng.choice(["INSERT", "UPDATE_CROSS_GROUP", "DELETE"])
                if op == "INSERT" or len(active_by_id) <= 5:
                    cid = rng.choice([1, 2, 3, 4])
                    mid = rng.choice([101, 102, 103, 104])
                    cz = cust_zip[cid]
                    reg = zip_reg[cz]
                    chan, tier = merch_info[mid]
                    amt = _sample_power_law_amount(rng, x_min=20.0, scale=1.5, alpha=2.5, x_max=180.0)
                    new_r = {
                        "sale_id": next_sid,
                        "customer_id": cid,
                        "customer_zip": cz,
                        "merchant_id": mid,
                        "region": reg,
                        "channel": chan,
                        "tier": tier,
                        "amount": amt,
                        "audit_nonce": f"n_{next_sid}",
                    }
                    cochain_events.append(
                        SalesCochainCdcSpec(
                            op_type="INSERT",
                            sale_id=next_sid,
                            new_amount=amt,
                            new_row=new_r,
                        )
                    )
                    active_by_id[next_sid] = new_r
                    next_sid += 1
                elif op == "DELETE":
                    target_sid = rng.choice(sorted(active_by_id.keys()))
                    old_r = active_by_id.pop(target_sid)
                    cochain_events.append(
                        SalesCochainCdcSpec(
                            op_type="DELETE",
                            sale_id=target_sid,
                            old_amount=float(old_r["amount"]),
                            old_row=old_r,
                        )
                    )
                else:
                    # Cross-group UPDATE: reassign customer_id and merchant_id consistently with FDs
                    target_sid = rng.choice(sorted(active_by_id.keys()))
                    old_r = dict(active_by_id[target_sid])
                    new_cid = rng.choice([1, 2, 3, 4])
                    new_mid = rng.choice([101, 102, 103, 104])
                    new_cz = cust_zip[new_cid]
                    new_reg = zip_reg[new_cz]
                    new_chan, new_tier = merch_info[new_mid]
                    new_amt = _sample_power_law_amount(rng, x_min=20.0, scale=1.5, alpha=2.5, x_max=180.0)
                    new_r = {
                        "sale_id": target_sid,
                        "customer_id": new_cid,
                        "customer_zip": new_cz,
                        "merchant_id": new_mid,
                        "region": new_reg,
                        "channel": new_chan,
                        "tier": new_tier,
                        "amount": new_amt,
                        "audit_nonce": f"n_{target_sid}_u{step}",
                    }
                    active_by_id[target_sid] = new_r
                    cochain_events.append(
                        SalesCochainCdcSpec(
                            op_type="UPDATE",
                            sale_id=target_sid,
                            old_amount=float(old_r["amount"]),
                            new_amount=new_amt,
                            old_row=old_r,
                            new_row=new_r,
                        )
                    )

            # Build 2-hop CODA_MUR transport chain preserving group_attrs + amount
            h1_target = (
                "sale_id",
                "customer_id",
                "customer_zip",
                "merchant_id",
                "region",
                "channel",
                "tier",
                "amount",
            )
            h2_target = ("sale_id", "region", "channel", "tier", "amount")
            hops = [
                CodaMurHopSpec(
                    hop_id="hop1_drop_audit_nonce",
                    source_heading=heading,
                    target_heading=h1_target,
                    group_attribute=group_attrs[0],
                    group_attributes=group_attrs,
                    value_attribute="amount",
                    loss_ledger=build_sealed_loss_ledger(["audit_nonce"], initial_rows, "sale_id"),
                    target_verifier={"verifier_id": "v_h1", "executed": True, "outcome": "verified"},
                ),
                CodaMurHopSpec(
                    hop_id="hop2_drop_entity_ids",
                    source_heading=h1_target,
                    target_heading=h2_target,
                    group_attribute=group_attrs[0],
                    group_attributes=group_attrs,
                    value_attribute="amount",
                    loss_ledger=build_sealed_loss_ledger(
                        ["customer_id", "customer_zip", "merchant_id"], initial_rows, "sale_id"
                    ),
                    target_verifier={"verifier_id": "v_h2", "executed": True, "outcome": "verified"},
                ),
            ]

            lag_sec = rng.choice([1, 8, 35])
            packet = {
                "value_ref": f"composite_sales_cache:trial_{trial}",
                "packet_scope": "composite_sales",
                "replica_lag_seconds": lag_sec,
            }

            receipt = run_extended_multi_hop_pipeline(
                schema=schema,
                initial_rows=initial_rows,
                cochain_cdc_events=cochain_events,
                transport_hops=hops,
                observer_poset=observer_poset,
                freshness_packet=packet,
                use_cochain=True,
                track_quantiles=True,
                quantile_tolerance=25.0,
                pk_attribute="sale_id",
                group_attributes=group_attrs,
                dynamic_buckets=True,
                bucket_width=16.0,
                split_threshold=3,
                merge_threshold=1,
                min_bucket_width=0.5,
            )

            self.assertTrue(receipt.certified, f"Trial {trial} failed certification: {receipt}")
            self.assertTrue(receipt.end_to_end_commutes)
            self.assertFalse(receipt.authorized)
            self.assertFalse(receipt.certified_implies_authorized)

            assert receipt.stage2_cochain is not None
            assert receipt.stage3_coda_mur is not None
            assert receipt.stage4_observer_poset is not None

            self.assertEqual(receipt.stage2_cochain.group_attributes, group_attrs)
            self.assertTrue(receipt.stage2_cochain.dynamic_buckets_enabled)
            self.assertTrue(receipt.stage2_cochain.quantile_invariants_verified)
            self.assertTrue(receipt.stage2_cochain.commutes_with_3nf_rejoin)
            self.assertGreaterEqual(receipt.stage2_cochain.bucket_splits_executed, 1)

            # Verify composite key decoding bijectivity on every active group key
            for comp_key in receipt.stage2_cochain.cached_state:
                decoded = decode_composite_group_key(comp_key, group_attrs)
                self.assertEqual(tuple(decoded.keys()), group_attrs)
                self.assertEqual(encode_composite_group_key(decoded, group_attrs), comp_key)

            self.assertTrue(receipt.stage3_coda_mur.commutation_verified)
            self.assertTrue(receipt.stage4_observer_poset.monotonicity_preserved)

    def test_composite_group_key_and_dynamic_bucket_mutation_refusals(self) -> None:
        """Verifies fail-closed refusals when:
        - A CODA_MUR hop drops part of a multi-column composite grouping key -> TransportViolation (Reject)
        - Dynamic bucket thresholds violate 0 <= merge_threshold < split_threshold -> Refuse
        - Undeclared group_attributes column is requested -> Refuse
        - Cross-group UPDATE violates merchant_id -> (channel, tier) FD -> ClosureFailure.
        """
        heading, schema = _build_composite_group_sales_schema()
        initial_rows = [
            {
                "sale_id": 1,
                "customer_id": 1,
                "customer_zip": "10001",
                "merchant_id": 101,
                "region": "US-EAST",
                "channel": "B2B",
                "tier": "GOLD",
                "amount": 25.0,
                "audit_nonce": "n_1",
            },
            {
                "sale_id": 2,
                "customer_id": 1,
                "customer_zip": "10001",
                "merchant_id": 101,
                "region": "US-EAST",
                "channel": "B2B",
                "tier": "GOLD",
                "amount": 75.0,
                "audit_nonce": "n_2",
            },
        ]
        valid_poset = [
            ObserverSpec("O1", max_lag_seconds=5, authorized_scopes=("composite_sales",)),
            ObserverSpec("O2", max_lag_seconds=30, authorized_scopes=("composite_sales", "archive")),
        ]
        valid_packet = {
            "value_ref": "sales:US-EAST|B2B|GOLD",
            "packet_scope": "composite_sales",
            "replica_lag_seconds": 2,
        }
        valid_hops = [
            CodaMurHopSpec(
                hop_id="h1_identity",
                source_heading=heading,
                target_heading=heading,
                group_attribute="region",
                group_attributes=("region", "channel", "tier"),
                value_attribute="amount",
                target_verifier={"verifier_id": "v1", "executed": True, "outcome": "verified"},
            )
        ]

        # Mutation 5A: CODA_MUR hop drops 'tier' from 3-column composite group key ('region', 'channel', 'tier')
        target_missing_tier = (
            "sale_id",
            "customer_id",
            "customer_zip",
            "merchant_id",
            "region",
            "channel",
            "amount",
            "audit_nonce",
        )
        hop_drops_tier = CodaMurHopSpec(
            hop_id="drop_composite_tier",
            source_heading=heading,
            target_heading=target_missing_tier,
            group_attribute="region",
            group_attributes=("region", "channel", "tier"),
            value_attribute="amount",
            loss_ledger=build_sealed_loss_ledger(["tier"], initial_rows, "sale_id"),
            target_verifier={"verifier_id": "v1", "executed": True, "outcome": "verified"},
        )
        r5a = run_extended_multi_hop_pipeline(
            schema=schema,
            initial_rows=initial_rows,
            cochain_cdc_events=[],
            transport_hops=[hop_drops_tier],
            observer_poset=valid_poset,
            freshness_packet=valid_packet,
            group_attributes=("region", "channel", "tier"),
            dynamic_buckets=True,
        )
        self.assertFalse(r5a.certified)
        self.assertEqual(r5a.overall_terminal, "Reject")
        assert r5a.stage3_coda_mur is not None
        self.assertEqual(r5a.stage3_coda_mur.local_route, "TransportViolation")
        self.assertEqual(r5a.stage3_coda_mur.obstruction_class, "[NonZero - ErasedProtectedBoundarySkeleton]")

        # Mutation 5B: Invalid dynamic bucket thresholds (merge_threshold >= split_threshold) -> Refuse
        r5b = run_extended_multi_hop_pipeline(
            schema=schema,
            initial_rows=initial_rows,
            cochain_cdc_events=[],
            transport_hops=valid_hops,
            observer_poset=valid_poset,
            freshness_packet=valid_packet,
            group_attributes=("region", "channel", "tier"),
            dynamic_buckets=True,
            split_threshold=4,
            merge_threshold=4,
        )
        self.assertFalse(r5b.certified)
        self.assertEqual(r5b.overall_terminal, "Refuse")
        assert r5b.stage2_cochain is not None
        self.assertEqual(r5b.stage2_cochain.terminal_route, "Refuse")

        # Mutation 5C: Undeclared attribute in group_attributes -> Refuse
        r5c = run_extended_multi_hop_pipeline(
            schema=schema,
            initial_rows=initial_rows,
            cochain_cdc_events=[],
            transport_hops=valid_hops,
            observer_poset=valid_poset,
            freshness_packet=valid_packet,
            group_attributes=("region", "undeclared_dimension"),
            dynamic_buckets=True,
        )
        self.assertFalse(r5c.certified)
        self.assertEqual(r5c.overall_terminal, "Refuse")

        # Mutation 5D: Cross-group UPDATE violates merchant_id -> (channel, tier) FD -> ClosureFailure
        bad_update = SalesCochainCdcSpec(
            op_type="UPDATE",
            sale_id=2,
            old_amount=75.0,
            new_amount=85.0,
            old_row=dict(initial_rows[1]),
            new_row={
                **initial_rows[1],
                "channel": "CONFLICTING_CHANNEL_FOR_MERCHANT_101",
                "amount": 85.0,
            },
        )
        r5d = run_extended_multi_hop_pipeline(
            schema=schema,
            initial_rows=initial_rows,
            cochain_cdc_events=[bad_update],
            transport_hops=valid_hops,
            observer_poset=valid_poset,
            freshness_packet=valid_packet,
            group_attributes=("region", "channel", "tier"),
            dynamic_buckets=True,
        )
        self.assertFalse(r5d.certified)
        self.assertEqual(r5d.overall_terminal, "ClosureFailure")
        assert r5d.stage2_cochain is not None
        self.assertEqual(r5d.stage2_cochain.terminal_route, "ClosureFailure")

    def test_observer_freshness_and_cochain_mutation_refusal_matrix(self) -> None:
        """Verifies fail-closed terminal routing across Stage 2b (cochain FD/payload mutations)
        and Stage 4 (observer poset order violations, missing scope/lag, and SLA exhaustion).
        """
        heading, schema = _build_sales_cochain_schema()
        initial_rows = [
            {
                "sale_id": 1,
                "customer_id": 10,
                "customer_zip": "10001",
                "region": "US-EAST",
                "amount": 25.0,
                "audit_nonce": "n_1",
            },
            {
                "sale_id": 2,
                "customer_id": 10,
                "customer_zip": "10001",
                "region": "US-EAST",
                "amount": 75.0,
                "audit_nonce": "n_2",
            },
        ]
        valid_events = [
            SalesCochainCdcSpec(
                op_type="DELETE",
                sale_id=2,
                old_region="US-EAST",
                old_amount=75.0,
            )
        ]
        hops = [
            CodaMurHopSpec(
                hop_id="h1_identity",
                source_heading=heading,
                target_heading=heading,
                group_attribute="region",
                value_attribute="amount",
                target_verifier={"verifier_id": "v1", "executed": True, "outcome": "verified"},
            )
        ]
        valid_poset = [
            ObserverSpec("O1_strict", max_lag_seconds=5, authorized_scopes=("regional_sales",)),
            ObserverSpec("O2_relaxed", max_lag_seconds=30, authorized_scopes=("regional_sales", "archive")),
        ]

        # Mutation 4A: Missing/empty packet_scope -> Refuse
        r4a = run_extended_multi_hop_pipeline(
            schema=schema,
            initial_rows=initial_rows,
            cochain_cdc_events=valid_events,
            transport_hops=hops,
            observer_poset=valid_poset,
            freshness_packet={"value_ref": "sales:US-EAST", "packet_scope": "", "replica_lag_seconds": 2},
        )
        self.assertFalse(r4a.certified)
        self.assertEqual(r4a.overall_terminal, "Refuse")
        assert r4a.stage4_observer_poset is not None
        self.assertEqual(r4a.stage4_observer_poset.terminal_route, "Refuse")

        # Mutation 4B: Missing or negative replica_lag_seconds -> ConservativeInvalidate
        r4b = run_extended_multi_hop_pipeline(
            schema=schema,
            initial_rows=initial_rows,
            cochain_cdc_events=valid_events,
            transport_hops=hops,
            observer_poset=valid_poset,
            freshness_packet={"value_ref": "sales:US-EAST", "packet_scope": "regional_sales", "replica_lag_seconds": -1},
        )
        self.assertFalse(r4b.certified)
        self.assertEqual(r4b.overall_terminal, "ConservativeInvalidate")
        assert r4b.stage4_observer_poset is not None
        self.assertEqual(r4b.stage4_observer_poset.terminal_route, "ConservativeInvalidate")

        # Mutation 4C: Unauthorized packet_scope -> Refuse
        r4c = run_extended_multi_hop_pipeline(
            schema=schema,
            initial_rows=initial_rows,
            cochain_cdc_events=valid_events,
            transport_hops=hops,
            observer_poset=valid_poset,
            freshness_packet={"value_ref": "sales:US-EAST", "packet_scope": "restricted_pii", "replica_lag_seconds": 2},
        )
        self.assertFalse(r4c.certified)
        self.assertEqual(r4c.overall_terminal, "Refuse")
        assert r4c.stage4_observer_poset is not None
        self.assertEqual(r4c.stage4_observer_poset.terminal_route, "Refuse")

        # Mutation 4D: Non-monotonic observer poset chain (O_1 has looser max_lag_seconds than O_2) -> PosetOrderViolation
        broken_poset = [
            ObserverSpec("O1_loose", max_lag_seconds=60, authorized_scopes=("regional_sales",)),
            ObserverSpec("O2_tight", max_lag_seconds=5, authorized_scopes=("regional_sales", "archive")),
        ]
        r4d = run_extended_multi_hop_pipeline(
            schema=schema,
            initial_rows=initial_rows,
            cochain_cdc_events=valid_events,
            transport_hops=hops,
            observer_poset=broken_poset,
            freshness_packet={"value_ref": "sales:US-EAST", "packet_scope": "regional_sales", "replica_lag_seconds": 2},
        )
        self.assertFalse(r4d.certified)
        self.assertEqual(r4d.overall_terminal, "Refuse")
        assert r4d.stage4_observer_poset is not None
        self.assertFalse(r4d.stage4_observer_poset.poset_chain_valid)
        self.assertEqual(r4d.stage4_observer_poset.terminal_route, "PosetOrderViolation")

        # Mutation 4E: Replica lag exceeds SLA for all observers in the poset chain -> RefreshRequired (Invalidate)
        r4e = run_extended_multi_hop_pipeline(
            schema=schema,
            initial_rows=initial_rows,
            cochain_cdc_events=valid_events,
            transport_hops=hops,
            observer_poset=valid_poset,
            freshness_packet={"value_ref": "sales:US-EAST", "packet_scope": "regional_sales", "replica_lag_seconds": 120},
        )
        self.assertFalse(r4e.certified)
        self.assertEqual(r4e.overall_terminal, "Invalidate")
        assert r4e.stage4_observer_poset is not None
        self.assertEqual(r4e.stage4_observer_poset.terminal_route, "RefreshRequired")

        # Mutation 4F: Cochain CDC INSERT violates declared 3NF transitive FD (customer_id 10 -> broken zip)
        fd_breach_event = SalesCochainCdcSpec(
            op_type="INSERT",
            sale_id=3,
            new_region="US-EAST",
            new_amount=40.0,
            new_row={
                "sale_id": 3,
                "customer_id": 10,
                "customer_zip": "99999_CONFLICT",
                "region": "US-EAST",
                "amount": 40.0,
                "audit_nonce": "n_3",
            },
        )
        r4f = run_extended_multi_hop_pipeline(
            schema=schema,
            initial_rows=initial_rows,
            cochain_cdc_events=[fd_breach_event],
            transport_hops=hops,
            observer_poset=valid_poset,
            freshness_packet={"value_ref": "sales:US-EAST", "packet_scope": "regional_sales", "replica_lag_seconds": 2},
        )
        self.assertFalse(r4f.certified)
        self.assertEqual(r4f.overall_terminal, "ClosureFailure")
        assert r4f.stage2_cochain is not None
        self.assertEqual(r4f.stage2_cochain.terminal_route, "ClosureFailure")

        # Mutation 4G: Cochain CDC DELETE missing old_amount -> Invalidate
        malformed_delete = SalesCochainCdcSpec(
            op_type="DELETE",
            sale_id=2,
            old_region="US-EAST",
            old_amount=None,
        )
        r4g = run_extended_multi_hop_pipeline(
            schema=schema,
            initial_rows=initial_rows,
            cochain_cdc_events=[malformed_delete],
            transport_hops=hops,
            observer_poset=valid_poset,
            freshness_packet={"value_ref": "sales:US-EAST", "packet_scope": "regional_sales", "replica_lag_seconds": 2},
        )
        self.assertFalse(r4g.certified)
        self.assertEqual(r4g.overall_terminal, "Invalidate")
        assert r4g.stage2_cochain is not None
        self.assertEqual(r4g.stage2_cochain.terminal_route, "Invalidate")

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

    def test_watermarked_out_of_order_late_cdc_quantile_mutations_and_poset_shifts_80_trials(self) -> None:
        """Verifies out-of-order late-arriving watermarked CDC streams across 80 randomized trials
        where delayed events simultaneously mutate historical quantile buckets (dyadic splits and
        merges) and shift observer-relative freshness lag across poset SLA thresholds.
        """
        rng = random.Random(20261030)
        heading, schema = _build_composite_group_sales_schema()

        cust_zip = {1: "10001", 2: "20002", 3: "30003", 4: "40004"}
        zip_reg = {"10001": "US-EAST", "20002": "US-EAST", "30003": "US-WEST", "40004": "US-WEST"}
        merch_info = {
            101: ("B2B", "GOLD"),
            102: ("B2B", "SILVER"),
            103: ("RETAIL", "GOLD"),
            104: ("RETAIL", "SILVER"),
        }

        observer_poset = [
            ObserverSpec("O1_rt_2s", max_lag_seconds=2, authorized_scopes=("composite_sales",)),
            ObserverSpec("O2_ops_10s", max_lag_seconds=10, authorized_scopes=("composite_sales", "ops")),
            ObserverSpec(
                "O3_exec_30s", max_lag_seconds=30, authorized_scopes=("composite_sales", "ops", "exec")
            ),
            ObserverSpec(
                "O4_batch_90s",
                max_lag_seconds=90,
                authorized_scopes=("composite_sales", "ops", "exec", "archive"),
            ),
        ]
        wm_spec = WatermarkSpec(
            allowed_lateness_seconds=50.0,
            initial_watermark_seconds=0.0,
            base_replica_lag_seconds=1.0,
            packet_scope="composite_sales",
            reject_beyond_watermark=True,
        )

        for trial in range(80):
            group_attrs: Tuple[str, ...] = (
                ("region",) if (trial % 2 == 0) else ("region", "channel")
            )

            # Seed 4 initial rows in (US-EAST, B2B) concentrated in [10.0, 14.0)
            initial_rows: List[Dict[str, Any]] = []
            for sid in range(1, 5):
                amt = _sample_power_law_amount(rng, x_min=10.0, scale=0.8, alpha=2.6, x_max=22.0)
                initial_rows.append(
                    {
                        "sale_id": sid,
                        "customer_id": 1,
                        "customer_zip": "10001",
                        "merchant_id": 101,
                        "region": "US-EAST",
                        "channel": "B2B",
                        "tier": "GOLD",
                        "amount": amt,
                        "audit_nonce": f"init_{sid}",
                    }
                )

            def _make_row(sid_val: int, cid_val: int, mid_val: int, amt_val: float, tag: str) -> Dict[str, Any]:
                cz_val = cust_zip[cid_val]
                reg_val = zip_reg[cz_val]
                chan_val, tier_val = merch_info[mid_val]
                return {
                    "sale_id": sid_val,
                    "customer_id": cid_val,
                    "customer_zip": cz_val,
                    "merchant_id": mid_val,
                    "region": reg_val,
                    "channel": chan_val,
                    "tier": tier_val,
                    "amount": amt_val,
                    "audit_nonce": tag,
                }

            # Construct a 10-step watermarked CDC arrival sequence with out-of-order delayed events
            # that both mutate historical quantile buckets (splits & merges) and shift lag across O1..O4:
            # Step 1 (on-time, t_event=10, t_ingest=11, lag=1s <= 2s -> all 4 observers AuthorizedFresh):
            r10 = _make_row(
                10, 1, 101, _sample_power_law_amount(rng, 10.0, 0.8, 2.6, 15.0), "s10"
            )
            # Step 2 (on-time, t_event=25, t_ingest=26, lag=1s <= 2s -> advances high-water mark to 25):
            r11 = _make_row(
                11, 1, 101, _sample_power_law_amount(rng, 10.0, 0.8, 2.6, 15.0), "s11"
            )
            # Step 3 (OUT-OF-ORDER late INSERT, t_event=19, t_ingest=27 -> lateness=6s, lag=8s in (2s, 10s],
            #         rejects O1_rt_2s, admits O2..O4, and splits dense [0, 16) bucket!):
            r12 = _make_row(
                12, 1, 101, _sample_power_law_amount(rng, 10.0, 0.6, 2.8, 13.5), "s12_late"
            )
            # Step 4 (on-time, t_event=45, t_ingest=46 -> lag=1s <= 2s, recovers O1..O4 to AuthorizedFresh,
            #         advances high-water mark to 45, watermark W=0):
            r13 = _make_row(
                13, 1, 101, _sample_power_law_amount(rng, 10.0, 0.6, 2.8, 13.5), "s13"
            )
            # Step 5 (OUT-OF-ORDER late INSERT, t_event=27, t_ingest=48 -> lateness=18s, lag=21s in (10s, 30s],
            #         rejects O1, O2; admits O3, O4; further refines historical dyadic bucket!):
            r14 = _make_row(
                14, 1, 101, _sample_power_law_amount(rng, 10.0, 0.5, 2.9, 12.5), "s14_late"
            )
            # Step 6 (OUT-OF-ORDER late UPDATE on sale_id=10, t_event=30, t_ingest=72 -> lateness=15s,
            #         ingestion lag=42s in (30s, 90s], rejects O1, O2, O3; admits only O4_batch_90s!):
            r10_upd = _make_row(
                10, 1, 101, _sample_power_law_amount(rng, 18.0, 1.2, 2.4, 28.0), "s10_upd_late"
            )
            # Step 7..9 (OUT-OF-ORDER & on-time DELETEs draining the split [0, 16) sub-buckets so they merge):
            # Step 7 (late DELETE on sale_id=1, t_event=35, t_ingest=75 -> lag=40s):
            # Step 8 (late DELETE on sale_id=2, t_event=38, t_ingest=76 -> lag=38s):
            # Step 9 (late DELETE on sale_id=3, t_event=40, t_ingest=77 -> lag=37s):
            # Step 10 (on-time DELETE on sale_id=4, t_event=80, t_ingest=81 -> lag=1s <= 2s, full poset recovery!):
            cochain_events = [
                SalesCochainCdcSpec(
                    op_type="INSERT",
                    sale_id=10,
                    new_amount=float(r10["amount"]),
                    new_row=r10,
                    event_timestamp=10.0,
                    ingestion_timestamp=11.0,
                ),
                SalesCochainCdcSpec(
                    op_type="INSERT",
                    sale_id=11,
                    new_amount=float(r11["amount"]),
                    new_row=r11,
                    event_timestamp=25.0,
                    ingestion_timestamp=26.0,
                ),
                SalesCochainCdcSpec(
                    op_type="INSERT",
                    sale_id=12,
                    new_amount=float(r12["amount"]),
                    new_row=r12,
                    event_timestamp=19.0,
                    ingestion_timestamp=27.0,
                ),
                SalesCochainCdcSpec(
                    op_type="INSERT",
                    sale_id=13,
                    new_amount=float(r13["amount"]),
                    new_row=r13,
                    event_timestamp=45.0,
                    ingestion_timestamp=46.0,
                ),
                SalesCochainCdcSpec(
                    op_type="INSERT",
                    sale_id=14,
                    new_amount=float(r14["amount"]),
                    new_row=r14,
                    event_timestamp=27.0,
                    ingestion_timestamp=48.0,
                ),
                SalesCochainCdcSpec(
                    op_type="UPDATE",
                    sale_id=10,
                    old_amount=float(r10["amount"]),
                    new_amount=float(r10_upd["amount"]),
                    old_row=r10,
                    new_row=r10_upd,
                    event_timestamp=30.0,
                    ingestion_timestamp=72.0,
                ),
                SalesCochainCdcSpec(
                    op_type="DELETE",
                    sale_id=1,
                    old_amount=float(initial_rows[0]["amount"]),
                    old_row=dict(initial_rows[0]),
                    event_timestamp=35.0,
                    ingestion_timestamp=75.0,
                ),
                SalesCochainCdcSpec(
                    op_type="DELETE",
                    sale_id=2,
                    old_amount=float(initial_rows[1]["amount"]),
                    old_row=dict(initial_rows[1]),
                    event_timestamp=38.0,
                    ingestion_timestamp=76.0,
                ),
                SalesCochainCdcSpec(
                    op_type="DELETE",
                    sale_id=3,
                    old_amount=float(initial_rows[2]["amount"]),
                    old_row=dict(initial_rows[2]),
                    event_timestamp=40.0,
                    ingestion_timestamp=77.0,
                ),
                SalesCochainCdcSpec(
                    op_type="DELETE",
                    sale_id=11,
                    old_amount=float(r11["amount"]),
                    old_row=r11,
                    event_timestamp=41.0,
                    ingestion_timestamp=78.0,
                ),
                SalesCochainCdcSpec(
                    op_type="DELETE",
                    sale_id=12,
                    old_amount=float(r12["amount"]),
                    old_row=r12,
                    event_timestamp=42.0,
                    ingestion_timestamp=79.0,
                ),
                SalesCochainCdcSpec(
                    op_type="DELETE",
                    sale_id=4,
                    old_amount=float(initial_rows[3]["amount"]),
                    old_row=dict(initial_rows[3]),
                    event_timestamp=80.0,
                    ingestion_timestamp=81.0,
                ),
            ]

            h1_target = (
                "sale_id",
                "customer_id",
                "customer_zip",
                "merchant_id",
                "region",
                "channel",
                "tier",
                "amount",
            )
            h2_target = ("sale_id", "region", "channel", "tier", "amount")
            hops = [
                CodaMurHopSpec(
                    hop_id="hop1_drop_nonce",
                    source_heading=heading,
                    target_heading=h1_target,
                    group_attribute=group_attrs[0],
                    group_attributes=group_attrs,
                    value_attribute="amount",
                    loss_ledger=build_sealed_loss_ledger(["audit_nonce"], initial_rows, "sale_id"),
                    target_verifier={"verifier_id": "v_wm_1", "executed": True, "outcome": "verified"},
                ),
                CodaMurHopSpec(
                    hop_id="hop2_drop_entities",
                    source_heading=h1_target,
                    target_heading=h2_target,
                    group_attribute=group_attrs[0],
                    group_attributes=group_attrs,
                    value_attribute="amount",
                    loss_ledger=build_sealed_loss_ledger(
                        ["customer_id", "customer_zip", "merchant_id"], initial_rows, "sale_id"
                    ),
                    target_verifier={"verifier_id": "v_wm_2", "executed": True, "outcome": "verified"},
                ),
            ]

            wm_receipt = evaluate_watermarked_cdc_stream_with_observer_poset(
                schema=schema,
                initial_rows=initial_rows,
                cochain_cdc_events=cochain_events,
                watermark_spec=wm_spec,
                observer_poset=observer_poset,
                transport_hops=hops,
                use_cochain=True,
                track_quantiles=True,
                quantile_tolerance=25.0,
                pk_attribute="sale_id",
                group_attributes=group_attrs,
                dynamic_buckets=True,
                bucket_width=16.0,
                split_threshold=4,
                merge_threshold=2,
                min_bucket_width=0.5,
            )

            self.assertTrue(wm_receipt.certified, f"Trial {trial} failed: {wm_receipt.reason}")
            self.assertFalse(wm_receipt.authorized)
            self.assertFalse(wm_receipt.certified_implies_authorized)
            self.assertEqual(wm_receipt.authority_effect, "None")
            self.assertEqual(wm_receipt.events_submitted, 12)
            self.assertEqual(wm_receipt.events_applied, 12)
            self.assertEqual(wm_receipt.out_of_order_events_applied, 8)
            self.assertEqual(wm_receipt.late_events_rejected_or_quarantined, 0)
            self.assertGreaterEqual(wm_receipt.historical_bucket_mutations_on_late_events, 3)
            self.assertGreaterEqual(wm_receipt.total_bucket_splits, 2)
            self.assertGreaterEqual(wm_receipt.total_bucket_merges, 1)
            self.assertGreaterEqual(wm_receipt.poset_threshold_shifts, 4)
            self.assertTrue(wm_receipt.lag_anti_monotonicity_verified)
            self.assertTrue(wm_receipt.all_step_posets_monotonic)
            self.assertTrue(wm_receipt.converges_to_event_time_order)
            self.assertAlmostEqual(wm_receipt.final_watermark_timestamp, 30.0, places=6)
            self.assertAlmostEqual(wm_receipt.max_event_timestamp, 80.0, places=6)

            # Verify exact observer poset transitions at the delayed steps:
            # Step 1 (lag=1s): all 4 observers admitted
            self.assertEqual(
                wm_receipt.step_receipts[0].admitted_observers,
                ("O1_rt_2s", "O2_ops_10s", "O3_exec_30s", "O4_batch_90s"),
            )
            # Step 3 (late arrival, lag=8s): O1 rejected, O2..O4 admitted
            self.assertTrue(wm_receipt.step_receipts[2].is_out_of_order)
            self.assertEqual(
                wm_receipt.step_receipts[2].admitted_observers,
                ("O2_ops_10s", "O3_exec_30s", "O4_batch_90s"),
            )
            self.assertEqual(wm_receipt.step_receipts[2].rejected_observers, ("O1_rt_2s",))
            # Step 4 (on-time catchup, lag=1s): all 4 observers admitted again
            self.assertEqual(
                wm_receipt.step_receipts[3].admitted_observers,
                ("O1_rt_2s", "O2_ops_10s", "O3_exec_30s", "O4_batch_90s"),
            )
            # Step 5 (late arrival, lag=21s): O1, O2 rejected; O3, O4 admitted
            self.assertTrue(wm_receipt.step_receipts[4].is_out_of_order)
            self.assertEqual(
                wm_receipt.step_receipts[4].admitted_observers,
                ("O3_exec_30s", "O4_batch_90s"),
            )
            # Step 6 (late arrival, lag=42s): O1, O2, O3 rejected; only O4 admitted
            self.assertTrue(wm_receipt.step_receipts[5].is_out_of_order)
            self.assertEqual(
                wm_receipt.step_receipts[5].admitted_observers,
                ("O4_batch_90s",),
            )
            # Step 12 (on-time catchup, lag=1s): all 4 observers admitted again
            self.assertEqual(
                wm_receipt.step_receipts[11].admitted_observers,
                ("O1_rt_2s", "O2_ops_10s", "O3_exec_30s", "O4_batch_90s"),
            )
            assert wm_receipt.coda_mur_receipt is not None
            self.assertTrue(wm_receipt.coda_mur_receipt.commutation_verified)

    def test_out_of_order_insert_permutation_dyadic_bucket_path_invariance_60_trials(self) -> None:
        """Verifies across 60 randomized trials that any watermarked out-of-order arrival
        permutation of skewed power-law INSERT events produces the exact same dyadic bucket
        intervals, counts, medians, extrema, and group totals as canonical event-time order.
        """
        rng = random.Random(31415926)
        _, schema = _build_sales_cochain_schema()

        observer_poset = [
            ObserverSpec("O1_3s", max_lag_seconds=3, authorized_scopes=("regional_sales",)),
            ObserverSpec("O2_15s", max_lag_seconds=15, authorized_scopes=("regional_sales", "ops")),
            ObserverSpec(
                "O3_60s", max_lag_seconds=60, authorized_scopes=("regional_sales", "ops", "archive")
            ),
        ]
        wm_spec = WatermarkSpec(
            allowed_lateness_seconds=60.0,
            initial_watermark_seconds=0.0,
            base_replica_lag_seconds=1.0,
            packet_scope="regional_sales",
            reject_beyond_watermark=True,
        )

        for trial in range(60):
            initial_rows = [
                {
                    "sale_id": 1,
                    "customer_id": 1,
                    "customer_zip": "10001",
                    "region": "US-EAST",
                    "amount": 10.5,
                    "audit_nonce": "n_1",
                }
            ]

            # Generate 14 skewed power-law INSERT events at event times t = 10, 12, ..., 36
            canonical_events: List[SalesCochainCdcSpec] = []
            for idx in range(14):
                sid = 10 + idx
                t_ev = 10.0 + 2.0 * idx
                amt = _sample_power_law_amount(rng, x_min=10.0, scale=1.0, alpha=2.7, x_max=80.0)
                row = {
                    "sale_id": sid,
                    "customer_id": 1,
                    "customer_zip": "10001",
                    "region": "US-EAST",
                    "amount": amt,
                    "audit_nonce": f"n_{sid}",
                }
                canonical_events.append(
                    SalesCochainCdcSpec(
                        op_type="INSERT",
                        sale_id=sid,
                        new_region="US-EAST",
                        new_amount=amt,
                        new_row=row,
                        event_timestamp=t_ev,
                        ingestion_timestamp=t_ev + 1.0,
                    )
                )

            # Permute arrival order and assign monotonically increasing ingestion timestamps >= event_timestamp
            perm_indices = list(range(14))
            while True:
                rng.shuffle(perm_indices)
                if perm_indices != list(range(14)):
                    break

            permuted_events: List[SalesCochainCdcSpec] = []
            curr_ingest = 12.0
            for p_i in perm_indices:
                base_ev = canonical_events[p_i]
                assert base_ev.event_timestamp is not None
                curr_ingest = max(curr_ingest + rng.choice([1.0, 2.5, 4.0]), float(base_ev.event_timestamp) + 1.0)
                permuted_events.append(
                    SalesCochainCdcSpec(
                        op_type=base_ev.op_type,
                        sale_id=base_ev.sale_id,
                        new_region=base_ev.new_region,
                        new_amount=base_ev.new_amount,
                        new_row=base_ev.new_row,
                        event_timestamp=base_ev.event_timestamp,
                        ingestion_timestamp=curr_ingest,
                    )
                )

            res_canon = evaluate_watermarked_cdc_stream_with_observer_poset(
                schema=schema,
                initial_rows=initial_rows,
                cochain_cdc_events=canonical_events,
                watermark_spec=wm_spec,
                observer_poset=observer_poset,
                dynamic_buckets=True,
                bucket_width=16.0,
                split_threshold=4,
                merge_threshold=2,
                min_bucket_width=0.5,
            )
            res_perm = evaluate_watermarked_cdc_stream_with_observer_poset(
                schema=schema,
                initial_rows=initial_rows,
                cochain_cdc_events=permuted_events,
                watermark_spec=wm_spec,
                observer_poset=observer_poset,
                dynamic_buckets=True,
                bucket_width=16.0,
                split_threshold=4,
                merge_threshold=2,
                min_bucket_width=0.5,
            )

            self.assertTrue(res_canon.certified)
            self.assertTrue(res_perm.certified, f"Trial {trial}: permuted stream failed: {res_perm.reason}")
            self.assertGreaterEqual(res_perm.out_of_order_events_applied, 1)
            self.assertGreaterEqual(res_perm.historical_bucket_mutations_on_late_events, 1)
            self.assertTrue(res_perm.converges_to_event_time_order)
            self.assertTrue(res_perm.lag_anti_monotonicity_verified)

            assert res_canon.final_cochain_receipt is not None
            assert res_perm.final_cochain_receipt is not None
            self.assertEqual(
                res_canon.final_cochain_receipt.active_bucket_counts,
                res_perm.final_cochain_receipt.active_bucket_counts,
            )
            self.assertAlmostEqual(
                float(res_canon.final_cochain_receipt.cached_medians["US-EAST"]),
                float(res_perm.final_cochain_receipt.cached_medians["US-EAST"]),
                places=9,
            )
            self.assertAlmostEqual(
                float(res_canon.final_cochain_receipt.true_medians["US-EAST"]),
                float(res_perm.final_cochain_receipt.true_medians["US-EAST"]),
                places=9,
            )

    def test_watermarked_late_event_and_causal_anomaly_refusal_matrix(self) -> None:
        """Verifies fail-closed terminal routing across watermark and causal anomalies:
        1. Late event falling below advancing watermark with reject_beyond_watermark=True -> LateEventExceedsWatermark (Invalidate).
        2. Late event falling below advancing watermark with reject_beyond_watermark=False -> QuarantinedLateEvent (Quarantine).
        3. Negative event-to-ingestion lag (t_ingest < t_event) -> NegativeEventLagViolation (ConservativeInvalidate).
        4. Non-monotonic physical ingestion clock (t_ingest(k) < t_ingest(k-1)) -> OutOfOrderIngestionClock (Invalidate).
        5. Out-of-order causal key violation (DELETE before INSERT, or duplicate INSERT) -> CausalKeyViolation (Invalidate).
        6. Missing event_timestamp or ingestion_timestamp -> ConservativeInvalidate.
        7. Invalid WatermarkSpec parameters -> Refuse.
        """
        _, schema = _build_sales_cochain_schema()
        initial_rows = [
            {
                "sale_id": 1,
                "customer_id": 1,
                "customer_zip": "10001",
                "region": "US-EAST",
                "amount": 25.0,
                "audit_nonce": "n_1",
            }
        ]
        observer_poset = [
            ObserverSpec("O1_2s", max_lag_seconds=2, authorized_scopes=("regional_sales",)),
            ObserverSpec("O2_20s", max_lag_seconds=20, authorized_scopes=("regional_sales", "ops")),
        ]
        wm_strict = WatermarkSpec(
            allowed_lateness_seconds=10.0,
            initial_watermark_seconds=0.0,
            base_replica_lag_seconds=1.0,
            packet_scope="regional_sales",
            reject_beyond_watermark=True,
        )

        r2 = {
            "sale_id": 2,
            "customer_id": 1,
            "customer_zip": "10001",
            "region": "US-EAST",
            "amount": 35.0,
            "audit_nonce": "n_2",
        }
        r3 = {
            "sale_id": 3,
            "customer_id": 1,
            "customer_zip": "10001",
            "region": "US-EAST",
            "amount": 45.0,
            "audit_nonce": "n_3",
        }

        # Case 1: Event at t_event=30 advances watermark to W = 30 - 10 = 20;
        #         subsequent late event at t_event=15 < 20 -> LateEventExceedsWatermark (Invalidate)
        events_beyond_wm = [
            SalesCochainCdcSpec(
                op_type="INSERT",
                sale_id=2,
                new_region="US-EAST",
                new_amount=35.0,
                new_row=r2,
                event_timestamp=30.0,
                ingestion_timestamp=31.0,
            ),
            SalesCochainCdcSpec(
                op_type="INSERT",
                sale_id=3,
                new_region="US-EAST",
                new_amount=45.0,
                new_row=r3,
                event_timestamp=15.0,
                ingestion_timestamp=32.0,
            ),
        ]
        res_beyond_strict = evaluate_watermarked_cdc_stream_with_observer_poset(
            schema=schema,
            initial_rows=initial_rows,
            cochain_cdc_events=events_beyond_wm,
            watermark_spec=wm_strict,
            observer_poset=observer_poset,
        )
        self.assertFalse(res_beyond_strict.certified)
        self.assertEqual(res_beyond_strict.terminal_route, "LateEventExceedsWatermark")
        self.assertEqual(res_beyond_strict.canonical_terminal, "Invalidate")
        self.assertEqual(res_beyond_strict.late_events_rejected_or_quarantined, 1)

        # Case 2: Same beyond-watermark event with reject_beyond_watermark=False -> Quarantine
        wm_quarantine = WatermarkSpec(
            allowed_lateness_seconds=10.0,
            initial_watermark_seconds=0.0,
            base_replica_lag_seconds=1.0,
            packet_scope="regional_sales",
            reject_beyond_watermark=False,
        )
        res_beyond_q = evaluate_watermarked_cdc_stream_with_observer_poset(
            schema=schema,
            initial_rows=initial_rows,
            cochain_cdc_events=events_beyond_wm,
            watermark_spec=wm_quarantine,
            observer_poset=observer_poset,
        )
        self.assertTrue(res_beyond_q.certified)
        self.assertEqual(res_beyond_q.terminal_route, "WatermarkedQuarantine")
        self.assertEqual(res_beyond_q.canonical_terminal, "Quarantine")
        self.assertEqual(res_beyond_q.events_submitted, 2)
        self.assertEqual(res_beyond_q.events_applied, 1)
        self.assertEqual(res_beyond_q.late_events_rejected_or_quarantined, 1)
        self.assertEqual(res_beyond_q.step_receipts[1].cochain_step_terminal, "QuarantinedLateEvent")

        # Case 3: Negative event-to-ingestion lag (t_ingest=8.0 < t_event=12.0) -> NegativeEventLagViolation
        res_neg_lag = evaluate_watermarked_cdc_stream_with_observer_poset(
            schema=schema,
            initial_rows=initial_rows,
            cochain_cdc_events=[
                SalesCochainCdcSpec(
                    op_type="INSERT",
                    sale_id=2,
                    new_region="US-EAST",
                    new_amount=35.0,
                    new_row=r2,
                    event_timestamp=12.0,
                    ingestion_timestamp=8.0,
                )
            ],
            watermark_spec=wm_strict,
            observer_poset=observer_poset,
        )
        self.assertFalse(res_neg_lag.certified)
        self.assertEqual(res_neg_lag.terminal_route, "NegativeEventLagViolation")
        self.assertEqual(res_neg_lag.canonical_terminal, "ConservativeInvalidate")

        # Case 4: Non-monotonic physical ingestion clock (t_ingest=20.0 followed by t_ingest=18.0)
        res_bad_clock = evaluate_watermarked_cdc_stream_with_observer_poset(
            schema=schema,
            initial_rows=initial_rows,
            cochain_cdc_events=[
                SalesCochainCdcSpec(
                    op_type="INSERT",
                    sale_id=2,
                    new_region="US-EAST",
                    new_amount=35.0,
                    new_row=r2,
                    event_timestamp=15.0,
                    ingestion_timestamp=20.0,
                ),
                SalesCochainCdcSpec(
                    op_type="INSERT",
                    sale_id=3,
                    new_region="US-EAST",
                    new_amount=45.0,
                    new_row=r3,
                    event_timestamp=16.0,
                    ingestion_timestamp=18.0,
                ),
            ],
            watermark_spec=wm_strict,
            observer_poset=observer_poset,
        )
        self.assertFalse(res_bad_clock.certified)
        self.assertEqual(res_bad_clock.terminal_route, "OutOfOrderIngestionClock")
        self.assertEqual(res_bad_clock.canonical_terminal, "Invalidate")

        # Case 5: Out-of-order causal key violation (DELETE for sale_id=99 before INSERT)
        res_causal_del = evaluate_watermarked_cdc_stream_with_observer_poset(
            schema=schema,
            initial_rows=initial_rows,
            cochain_cdc_events=[
                SalesCochainCdcSpec(
                    op_type="DELETE",
                    sale_id=99,
                    old_region="US-EAST",
                    old_amount=35.0,
                    event_timestamp=10.0,
                    ingestion_timestamp=11.0,
                )
            ],
            watermark_spec=wm_strict,
            observer_poset=observer_poset,
        )
        self.assertFalse(res_causal_del.certified)
        self.assertEqual(res_causal_del.terminal_route, "CausalKeyViolation")
        self.assertEqual(res_causal_del.canonical_terminal, "Invalidate")

        # Case 6: Missing event_timestamp or ingestion_timestamp -> ConservativeInvalidate
        res_missing_ts = evaluate_watermarked_cdc_stream_with_observer_poset(
            schema=schema,
            initial_rows=initial_rows,
            cochain_cdc_events=[
                SalesCochainCdcSpec(
                    op_type="INSERT",
                    sale_id=2,
                    new_region="US-EAST",
                    new_amount=35.0,
                    new_row=r2,
                    event_timestamp=None,
                    ingestion_timestamp=11.0,
                )
            ],
            watermark_spec=wm_strict,
            observer_poset=observer_poset,
        )
        self.assertFalse(res_missing_ts.certified)
        self.assertEqual(res_missing_ts.terminal_route, "ConservativeInvalidate")

        # Case 7: Invalid WatermarkSpec (negative allowed_lateness_seconds) -> Refuse
        res_bad_wm = evaluate_watermarked_cdc_stream_with_observer_poset(
            schema=schema,
            initial_rows=initial_rows,
            cochain_cdc_events=[],
            watermark_spec=WatermarkSpec(allowed_lateness_seconds=-5.0),
            observer_poset=observer_poset,
        )
        self.assertFalse(res_bad_wm.certified)
        self.assertEqual(res_bad_wm.terminal_route, "Refuse")
        self.assertEqual(res_bad_wm.canonical_terminal, "Refuse")


if __name__ == "__main__":
    unittest.main()
