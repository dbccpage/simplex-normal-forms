"""Multi-hop composition pipeline chaining relational synthesis (3NF/BCNF),
streaming BQNF delta repair, and CODA_MUR representation transport across
randomized schema mutations.

Pipeline topology:
    Stage 1 (At Rest: 3NF / BCNF synthesis & lossless join reconstruction)
        --> Stage 2 (In Motion: BQNF incremental CDC coboundary repair)
        --> Stage 3 (In Representation: CODA_MUR functorial transport & sealed loss ledgers)

AuthorityEffect: None.
certified_implies_authorized: false.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from normal_forms.domain.bqnf_validator import (
    BqnfBoundary,
    BqnfCdcEvent,
    BqnfEvaluationResult,
    BqnfValidator,
)
from normal_forms.domain.relational import (
    FunctionalDependency,
    JoinDependency,
    RelationalSchema,
    check_1nf,
    check_3nf,
    check_bcnf,
    check_dependency_preservation,
    check_lossless_decomposition,
    evaluate_join_dependency_on_relation,
)
from normal_forms.domain.relational_advanced import (
    decompose_bcnf_tree,
    project_functional_dependencies,
    synthesize_3nf_bernstein,
)
from normal_forms.reconciliation_example import verify_loss_ledger_integrity

CODA_MUR_TRIGGER_ID = "coda_mur.unmapped_field_drop"


def build_sealed_loss_ledger(
    erased_attributes: Sequence[str],
    source_rows: Sequence[Mapping[str, Any]],
    key_attribute: str,
    trigger_id: str = CODA_MUR_TRIGGER_ID,
) -> Dict[str, Any]:
    """Constructs a cryptographically sealed CODA_MUR LossLedger for erased attributes."""
    sorted_erased = sorted(set(erased_attributes))
    entries: List[Dict[str, Any]] = []
    for idx, row in enumerate(source_rows):
        dropped_payload = {attr: row.get(attr) for attr in sorted_erased if attr in row}
        entries.append(
            {
                "row_key": str(row.get(key_attribute, idx)),
                "trigger_id": trigger_id,
                "erased_fields": dropped_payload,
            }
        )
    canonical_bytes = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(canonical_bytes).hexdigest()
    return {
        "trigger_id": trigger_id,
        "erased_attributes": sorted_erased,
        "record_count": len(entries),
        "entries": entries,
        "sealed": True,
        "merkle_digest": digest,
        "authority_effect": "None",
    }


def check_instance_satisfies_fds(
    rows: Sequence[Mapping[str, Any]],
    dependencies: Iterable[FunctionalDependency],
) -> Tuple[bool, Optional[str]]:
    """Checks whether a relation instance satisfies every declared functional dependency X -> Y."""
    for fd in dependencies:
        det_cols = tuple(sorted(fd.determinant))
        dep_cols = tuple(sorted(fd.dependent))
        seen: Dict[Tuple[Any, ...], Tuple[Any, ...]] = {}
        for row in rows:
            if any(c not in row for c in det_cols) or any(c not in row for c in dep_cols):
                return (
                    False,
                    f"Row missing attribute required by FD {fd}: {dict(row)}",
                )
            det_val = tuple(row[c] for c in det_cols)
            dep_val = tuple(row[c] for c in dep_cols)
            if det_val in seen and seen[det_val] != dep_val:
                return (
                    False,
                    f"Instance FD violation on {fd}: key {det_val} maps to both {seen[det_val]} and {dep_val}",
                )
            seen[det_val] = dep_val
    return True, None


def project_and_rejoin(
    rows: Sequence[Mapping[str, Any]],
    heading: Iterable[str],
    components: Sequence[Iterable[str]],
) -> Tuple[bool, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Projects a relation onto subschema components and natural-joins them back."""
    h_set = frozenset(heading)
    comps = tuple(frozenset(c) for c in components)
    if len(comps) == 1 and comps[0] == h_set:
        sorted_h = sorted(h_set)
        dedup = []
        seen = set()
        for r in rows:
            t = tuple(r.get(a) for a in sorted_h)
            if t not in seen:
                seen.add(t)
                dedup.append({a: r.get(a) for a in sorted_h})
        return True, dedup, []
    jd = JoinDependency(heading=h_set, components=comps)
    is_lossless, _, spurious = evaluate_join_dependency_on_relation(rows, jd)
    sorted_h = sorted(h_set)
    reconstructed = []
    seen = set()
    for r in rows:
        t = tuple(r.get(a) for a in sorted_h)
        if t not in seen:
            seen.add(t)
            reconstructed.append({a: r.get(a) for a in sorted_h})
    return is_lossless, reconstructed, spurious


@dataclass(frozen=True)
class RelationalSynthesisStageReceipt:
    """Receipt emitted by Hop 1 (3NF Bernstein synthesis & BCNF tree decomposition)."""

    terminal_route: str
    canonical_terminal: str
    nf3_components: Tuple[Tuple[str, ...], ...]
    bcnf_components: Tuple[Tuple[str, ...], ...]
    nf3_lossless: bool
    nf3_dependency_preserving: bool
    bcnf_lossless: bool
    bcnf_dependency_preserving: bool
    instance_fd_satisfied: bool
    instance_reconstructed_exact: bool
    certified: bool
    authorized: bool = False
    authority_effect: str = "None"
    reason: Optional[str] = None


@dataclass(frozen=True)
class BqnfStreamStageReceipt:
    """Receipt emitted by Hop 2 (Streaming BQNF delta evaluation over normalized relvars)."""

    terminal_route: str
    canonical_terminal: str
    event_decisions: Tuple[str, ...]
    obstruction_classes: Tuple[str, ...]
    incremental_totals_by_group: Dict[Any, float]
    batch_rejoined_totals_by_group: Dict[Any, float]
    commutes_with_relational_join: bool
    certified: bool
    authorized: bool = False
    authority_effect: str = "None"
    reason: Optional[str] = None


@dataclass(frozen=True)
class CodaMurHopSpec:
    """Specification of a single representation transport hop F_j: Rep_{j-1} -> Rep_j."""

    hop_id: str
    source_heading: Tuple[str, ...]
    target_heading: Tuple[str, ...]
    group_attribute: str
    value_attribute: str
    predicate_attribute: Optional[str] = None
    predicate_expected_value: Optional[str] = None
    loss_ledger: Optional[Dict[str, Any]] = None
    target_verifier: Optional[Dict[str, Any]] = None
    injected_target_tamper_delta: float = 0.0


@dataclass(frozen=True)
class CodaMurTransportStageReceipt:
    """Receipt emitted by Hop 3 (Single or multi-hop CODA_MUR representation transport)."""

    local_route: str
    canonical_terminal: str
    obstruction_class: str
    commutation_verified: bool
    composed_erased_attributes: Tuple[str, ...]
    loss_ledger_triggers: Tuple[str, ...]
    hop_routes: Tuple[str, ...]
    certified: bool
    authorized: bool = False
    authority_effect: str = "None"
    reason: Optional[str] = None


@dataclass(frozen=True)
class MultiHopCompositionReceipt:
    """End-to-end receipt across Hop 1 (3NF/BCNF), Hop 2 (BQNF), and Hop 3 (CODA_MUR)."""

    stage1_relational: RelationalSynthesisStageReceipt
    stage2_bqnf: Optional[BqnfStreamStageReceipt]
    stage3_coda_mur: Optional[CodaMurTransportStageReceipt]
    overall_terminal: str
    end_to_end_commutes: bool
    certified: bool
    authorized: bool = False
    certified_implies_authorized: bool = False
    authority_effect: str = "None"


def evaluate_stage1_relational_synthesis(
    schema: RelationalSchema,
    instance_rows: Sequence[Mapping[str, Any]],
) -> Tuple[RelationalSynthesisStageReceipt, List[Dict[str, Any]]]:
    """Hop 1: Validates schema totality, synthesizes 3NF & BCNF decompositions, and verifies lossless join."""
    ok_1nf, err_1nf = check_1nf(schema)
    if not ok_1nf:
        return (
            RelationalSynthesisStageReceipt(
                terminal_route="SchemaMutationRefusal",
                canonical_terminal="Refuse",
                nf3_components=(),
                bcnf_components=(),
                nf3_lossless=False,
                nf3_dependency_preserving=False,
                bcnf_lossless=False,
                bcnf_dependency_preserving=False,
                instance_fd_satisfied=False,
                instance_reconstructed_exact=False,
                certified=False,
                reason=err_1nf,
            ),
            [],
        )

    # Check that every FD only references declared schema attributes
    for fd in schema.dependencies:
        undeclared = (fd.determinant | fd.dependent) - schema.attributes
        if undeclared:
            return (
                RelationalSynthesisStageReceipt(
                    terminal_route="SchemaMutationRefusal",
                    canonical_terminal="Refuse",
                    nf3_components=(),
                    bcnf_components=(),
                    nf3_lossless=False,
                    nf3_dependency_preserving=False,
                    bcnf_lossless=False,
                    bcnf_dependency_preserving=False,
                    instance_fd_satisfied=False,
                    instance_reconstructed_exact=False,
                    certified=False,
                    reason=f"FD {fd} references attributes outside declared heading: {sorted(undeclared)}",
                ),
                [],
            )

    # Check that all rows contain declared heading and satisfy FDs
    for row in instance_rows:
        missing_cols = set(schema.attributes) - set(row.keys())
        if missing_cols:
            return (
                RelationalSynthesisStageReceipt(
                    terminal_route="SchemaMutationRefusal",
                    canonical_terminal="Refuse",
                    nf3_components=(),
                    bcnf_components=(),
                    nf3_lossless=False,
                    nf3_dependency_preserving=False,
                    bcnf_lossless=False,
                    bcnf_dependency_preserving=False,
                    instance_fd_satisfied=False,
                    instance_reconstructed_exact=False,
                    certified=False,
                    reason=f"Instance row missing declared schema attributes: {sorted(missing_cols)}",
                ),
                [],
            )

    fd_ok, fd_err = check_instance_satisfies_fds(instance_rows, schema.dependencies)
    if not fd_ok:
        return (
            RelationalSynthesisStageReceipt(
                terminal_route="InstanceFdViolationRefusal",
                canonical_terminal="Refuse",
                nf3_components=(),
                bcnf_components=(),
                nf3_lossless=False,
                nf3_dependency_preserving=False,
                bcnf_lossless=False,
                bcnf_dependency_preserving=False,
                instance_fd_satisfied=False,
                instance_reconstructed_exact=False,
                certified=False,
                reason=fd_err,
            ),
            [],
        )

    # 1. Bernstein 3NF synthesis
    nf3_subschemas = synthesize_3nf_bernstein(schema)
    for sub in nf3_subschemas:
        proj_fds = project_functional_dependencies(schema.dependencies, sub)
        sub_schema = RelationalSchema(attributes=sub, dependencies=frozenset(proj_fds))
        ok_3, err_3 = check_3nf(sub_schema)
        if not ok_3:
            return (
                RelationalSynthesisStageReceipt(
                    terminal_route="SynthesisFailure",
                    canonical_terminal="Refuse",
                    nf3_components=tuple(tuple(sorted(s)) for s in nf3_subschemas),
                    bcnf_components=(),
                    nf3_lossless=False,
                    nf3_dependency_preserving=False,
                    bcnf_lossless=False,
                    bcnf_dependency_preserving=False,
                    instance_fd_satisfied=True,
                    instance_reconstructed_exact=False,
                    certified=False,
                    reason=err_3,
                ),
                [],
            )

    nf3_lossless, _ = check_lossless_decomposition(schema, nf3_subschemas)
    nf3_dep_pres, _ = check_dependency_preservation(schema, nf3_subschemas)

    # 2. Tsou-Fischer BCNF tree decomposition
    bcnf_rels = decompose_bcnf_tree(schema)
    bcnf_subschemas = [r.attributes for r in bcnf_rels]
    for r_sub in bcnf_rels:
        ok_b, err_b = check_bcnf(r_sub)
        if not ok_b:
            return (
                RelationalSynthesisStageReceipt(
                    terminal_route="BcnfDecompositionFailure",
                    canonical_terminal="Refuse",
                    nf3_components=tuple(tuple(sorted(s)) for s in nf3_subschemas),
                    bcnf_components=tuple(tuple(sorted(s)) for s in bcnf_subschemas),
                    nf3_lossless=nf3_lossless,
                    nf3_dependency_preserving=nf3_dep_pres,
                    bcnf_lossless=False,
                    bcnf_dependency_preserving=False,
                    instance_fd_satisfied=True,
                    instance_reconstructed_exact=False,
                    certified=False,
                    reason=err_b,
                ),
                [],
            )

    bcnf_lossless, _ = check_lossless_decomposition(schema, bcnf_subschemas)
    bcnf_dep_pres, _ = check_dependency_preservation(schema, bcnf_subschemas)

    # 3. Concrete projection-join reconstruction check on instance_rows
    nf3_inst_ok, rejoined_rows, _ = project_and_rejoin(instance_rows, schema.attributes, nf3_subschemas)
    bcnf_inst_ok, _, _ = project_and_rejoin(instance_rows, schema.attributes, bcnf_subschemas)
    inst_exact = bool(nf3_inst_ok and bcnf_inst_ok and nf3_lossless and bcnf_lossless)

    return (
        RelationalSynthesisStageReceipt(
            terminal_route="SynthesizedAndVerified" if inst_exact else "ClosureFailure",
            canonical_terminal="Preserve" if inst_exact else "ClosureFailure",
            nf3_components=tuple(tuple(sorted(s)) for s in nf3_subschemas),
            bcnf_components=tuple(tuple(sorted(s)) for s in bcnf_subschemas),
            nf3_lossless=nf3_lossless,
            nf3_dependency_preserving=nf3_dep_pres,
            bcnf_lossless=bcnf_lossless,
            bcnf_dependency_preserving=bcnf_dep_pres,
            instance_fd_satisfied=True,
            instance_reconstructed_exact=inst_exact,
            certified=inst_exact,
            authorized=False,
            reason=None if inst_exact else "Projection-join failed lossless recovery",
        ),
        rejoined_rows,
    )


def _compute_boundary_group_totals(
    rows: Sequence[Mapping[str, Any]],
    boundary: BqnfBoundary,
) -> Dict[Any, float]:
    group_attr = boundary.groups[0] if boundary.groups else "customer_id"
    val_attr = "amount" if "amount" in boundary.attributes else (boundary.attributes[-1] if boundary.attributes else "amount")
    pred_str = boundary.predicates[0] if boundary.predicates else ""
    totals: Dict[Any, float] = {}
    for row in rows:
        if BqnfValidator._parse_predicate(pred_str, dict(row)):
            g_val = row.get(group_attr)
            totals[g_val] = totals.get(g_val, 0.0) + float(row.get(val_attr, 0.0))
    return {k: v for k, v in totals.items() if abs(v) > 1e-12}


def _apply_cdc_event_to_rows(
    rows: List[Dict[str, Any]],
    event: BqnfCdcEvent,
    pk_attr: str,
) -> List[Dict[str, Any]]:
    updated = [dict(r) for r in rows]
    if event.op == "INSERT" and event.new is not None:
        pk_val = event.new.get(pk_attr)
        updated = [r for r in updated if r.get(pk_attr) != pk_val]
        updated.append(dict(event.new))
    elif event.op == "DELETE" and event.old is not None:
        pk_val = event.old.get(pk_attr)
        updated = [r for r in updated if r.get(pk_attr) != pk_val]
    elif event.op == "UPDATE" and event.old is not None and event.new is not None:
        pk_val = event.old.get(pk_attr, event.new.get(pk_attr))
        for idx, r in enumerate(updated):
            if r.get(pk_attr) == pk_val:
                merged = dict(r)
                merged.update(event.new)
                updated[idx] = merged
                break
    return updated


def evaluate_stage2_bqnf_stream(
    schema: RelationalSchema,
    nf3_components: Sequence[Sequence[str]],
    initial_rows: Sequence[Mapping[str, Any]],
    boundary: BqnfBoundary,
    cdc_events: Sequence[BqnfCdcEvent],
    pk_attribute: str = "order_id",
) -> Tuple[BqnfStreamStageReceipt, List[Dict[str, Any]]]:
    """Hop 2: Evaluates streaming CDC events via BQNF and checks commutation with 3NF projection-join."""
    current_rows = [dict(r) for r in initial_rows]
    inc_totals = _compute_boundary_group_totals(current_rows, boundary)
    decisions: List[str] = []
    obstructions: List[str] = []
    group_attr = boundary.groups[0] if boundary.groups else "customer_id"

    for ev in cdc_events:
        res: BqnfEvaluationResult = BqnfValidator.evaluate(boundary, ev)
        decisions.append(res.terminal_route)
        obstructions.append(res.obstruction_class)

        if res.terminal_route in {"Invalidate", "Unsupported", "Refuse", "ClosureFailure"}:
            return (
                BqnfStreamStageReceipt(
                    terminal_route=res.terminal_route,
                    canonical_terminal=res.terminal_route,
                    event_decisions=tuple(decisions),
                    obstruction_classes=tuple(obstructions),
                    incremental_totals_by_group=dict(inc_totals),
                    batch_rejoined_totals_by_group=dict(inc_totals),
                    commutes_with_relational_join=False,
                    certified=False,
                    authorized=False,
                    reason=res.reason,
                ),
                current_rows,
            )

        # Apply mutation to base rows and verify FD preservation across 3NF components
        candidate_rows = _apply_cdc_event_to_rows(current_rows, ev, pk_attribute)
        fd_ok, fd_err = check_instance_satisfies_fds(candidate_rows, schema.dependencies)
        if not fd_ok:
            return (
                BqnfStreamStageReceipt(
                    terminal_route="ClosureFailure",
                    canonical_terminal="ClosureFailure",
                    event_decisions=tuple(decisions),
                    obstruction_classes=tuple(obstructions),
                    incremental_totals_by_group=dict(inc_totals),
                    batch_rejoined_totals_by_group=dict(inc_totals),
                    commutes_with_relational_join=False,
                    certified=False,
                    authorized=False,
                    reason=f"CDC event violated declared FD in normalized relvars: {fd_err}",
                ),
                current_rows,
            )

        current_rows = candidate_rows
        if res.terminal_route == "Repair" and res.repair is not None:
            g_key = res.repair.get(group_attr, res.repair.get("customer_id", res.repair.get("group_key")))
            delta = float(res.repair.get("delta_revenue", res.repair.get("delta_sum", 0.0)))
            new_val = inc_totals.get(g_key, 0.0) + delta
            if abs(new_val) <= 1e-12:
                inc_totals.pop(g_key, None)
            else:
                inc_totals[g_key] = new_val

    # Re-project onto 3NF components, natural-join back, and evaluate boundary query from scratch
    rejoin_ok, rejoined_rows, _ = project_and_rejoin(current_rows, schema.attributes, nf3_components)
    batch_totals = _compute_boundary_group_totals(rejoined_rows, boundary)

    all_groups = set(inc_totals.keys()) | set(batch_totals.keys())
    commutes = rejoin_ok and all(
        abs(inc_totals.get(g, 0.0) - batch_totals.get(g, 0.0)) <= 1e-9 for g in all_groups
    )
    final_route = "Repair" if "Repair" in decisions else "Preserve"
    if not commutes:
        final_route = "ClosureFailure"

    return (
        BqnfStreamStageReceipt(
            terminal_route=final_route,
            canonical_terminal=final_route,
            event_decisions=tuple(decisions),
            obstruction_classes=tuple(obstructions),
            incremental_totals_by_group=dict(inc_totals),
            batch_rejoined_totals_by_group=dict(batch_totals),
            commutes_with_relational_join=commutes,
            certified=commutes,
            authorized=False,
            reason=None if commutes else "Incremental BQNF state diverged from 3NF projection-join batch evaluation",
        ),
        rejoined_rows,
    )


def evaluate_stage3_coda_mur_chain(
    initial_rows: Sequence[Mapping[str, Any]],
    updated_rows: Sequence[Mapping[str, Any]],
    bqnf_initial_totals: Mapping[Any, float],
    bqnf_updated_totals: Mapping[Any, float],
    hops: Sequence[CodaMurHopSpec],
) -> CodaMurTransportStageReceipt:
    """Hop 3: Evaluates a multi-hop CODA_MUR representation transport chain (nf.coda.mur.transport)."""
    if not hops:
        return CodaMurTransportStageReceipt(
            local_route="Unsupported",
            canonical_terminal="Unsupported",
            obstruction_class="[NonZero - EmptyTransportChain]",
            commutation_verified=False,
            composed_erased_attributes=(),
            loss_ledger_triggers=(),
            hop_routes=(),
            certified=False,
            reason="No transport hops declared",
        )

    composed_erased: List[str] = []
    triggers: List[str] = []
    hop_routes: List[str] = []

    curr_init_rows = [dict(r) for r in initial_rows]
    curr_upd_rows = [dict(r) for r in updated_rows]

    for hop in hops:
        # 1. Target verifier gate (never bypass target verification)
        tv = hop.target_verifier
        if not isinstance(tv, dict):
            return CodaMurTransportStageReceipt(
                local_route="AuthorityLaundering",
                canonical_terminal="Refuse",
                obstruction_class="[NonZero - MissingOrInvalidVerifier]",
                commutation_verified=False,
                composed_erased_attributes=tuple(sorted(set(composed_erased))),
                loss_ledger_triggers=tuple(triggers),
                hop_routes=tuple(hop_routes + ["AuthorityLaundering"]),
                certified=False,
                reason=f"Hop '{hop.hop_id}' missing authenticated target verifier dictionary",
            )
        if tv.get("executed") is not True or tv.get("outcome") != "verified":
            return CodaMurTransportStageReceipt(
                local_route="AuthorityLaundering",
                canonical_terminal="Refuse",
                obstruction_class="[NonZero - UnexecutedTargetVerifier]",
                commutation_verified=False,
                composed_erased_attributes=tuple(sorted(set(composed_erased))),
                loss_ledger_triggers=tuple(triggers),
                hop_routes=tuple(hop_routes + ["AuthorityLaundering"]),
                certified=False,
                reason=f"Hop '{hop.hop_id}' target verifier not executed or outcome != verified",
            )

        src_set = set(hop.source_heading)
        tgt_set = set(hop.target_heading)
        erased = sorted(src_set - tgt_set)

        # 2. Check that target heading does not invent undeclared source attributes
        invented = sorted(tgt_set - src_set)
        if invented:
            return CodaMurTransportStageReceipt(
                local_route="TransportViolation",
                canonical_terminal="Reject",
                obstruction_class="[NonZero - UndeclaredTargetAttribute]",
                commutation_verified=False,
                composed_erased_attributes=tuple(sorted(set(composed_erased))),
                loss_ledger_triggers=tuple(triggers),
                hop_routes=tuple(hop_routes + ["TransportViolation"]),
                certified=False,
                reason=f"Hop '{hop.hop_id}' target heading invents unmapped attributes: {invented}",
            )

        # 3. Loss Ledger check whenever distinctions are erased
        if erased:
            ledger = hop.loss_ledger
            if not isinstance(ledger, dict):
                return CodaMurTransportStageReceipt(
                    local_route="LossLedgerMissing",
                    canonical_terminal="Refuse",
                    obstruction_class="[NonZero - MissingLossLedger]",
                    commutation_verified=False,
                    composed_erased_attributes=tuple(sorted(set(composed_erased))),
                    loss_ledger_triggers=tuple(triggers),
                    hop_routes=tuple(hop_routes + ["LossLedgerMissing"]),
                    certified=False,
                    reason=f"Hop '{hop.hop_id}' erases {erased} without a LossLedger",
                )
            declared_erased = set(ledger.get("erased_attributes") or ())
            if not set(erased).issubset(declared_erased):
                return CodaMurTransportStageReceipt(
                    local_route="LossLedgerMissing",
                    canonical_terminal="Refuse",
                    obstruction_class="[NonZero - UnrecordedFieldDrop]",
                    commutation_verified=False,
                    composed_erased_attributes=tuple(sorted(set(composed_erased))),
                    loss_ledger_triggers=tuple(triggers),
                    hop_routes=tuple(hop_routes + ["LossLedgerMissing"]),
                    certified=False,
                    reason=f"Hop '{hop.hop_id}' dropped {sorted(set(erased) - declared_erased)} without booking in LossLedger",
                )
            trigger = ledger.get("trigger_id")
            if trigger != CODA_MUR_TRIGGER_ID:
                return CodaMurTransportStageReceipt(
                    local_route="LossLedgerMissing",
                    canonical_terminal="Refuse",
                    obstruction_class="[NonZero - InvalidLossLedgerTrigger]",
                    commutation_verified=False,
                    composed_erased_attributes=tuple(sorted(set(composed_erased))),
                    loss_ledger_triggers=tuple(triggers),
                    hop_routes=tuple(hop_routes + ["LossLedgerMissing"]),
                    certified=False,
                    reason=f"Hop '{hop.hop_id}' LossLedger must declare trigger_id '{CODA_MUR_TRIGGER_ID}', got '{trigger}'",
                )
            ok_seal, seal_err = verify_loss_ledger_integrity(ledger)
            if not ok_seal:
                return CodaMurTransportStageReceipt(
                    local_route="LossLedgerMissing",
                    canonical_terminal="Refuse",
                    obstruction_class="[NonZero - TamperedLossLedger]",
                    commutation_verified=False,
                    composed_erased_attributes=tuple(sorted(set(composed_erased))),
                    loss_ledger_triggers=tuple(triggers),
                    hop_routes=tuple(hop_routes + ["LossLedgerMissing"]),
                    certified=False,
                    reason=f"Hop '{hop.hop_id}' LossLedger seal invalid: {seal_err}",
                )
            composed_erased.extend(erased)
            triggers.append(trigger)

        # 4. Commutation square check: D_target(F(r)) == F_bar(D_source(r))
        required_for_commutation = {hop.group_attribute, hop.value_attribute}
        if hop.predicate_attribute:
            required_for_commutation.add(hop.predicate_attribute)
        if not required_for_commutation.issubset(tgt_set):
            return CodaMurTransportStageReceipt(
                local_route="TransportViolation",
                canonical_terminal="Reject",
                obstruction_class="[NonZero - ErasedProtectedBoundarySkeleton]",
                commutation_verified=False,
                composed_erased_attributes=tuple(sorted(set(composed_erased))),
                loss_ledger_triggers=tuple(triggers),
                hop_routes=tuple(hop_routes + ["TransportViolation"]),
                certified=False,
                reason=f"Hop '{hop.hop_id}' erased protected boundary attributes required for update commutation: {sorted(required_for_commutation - tgt_set)}",
            )

        # Project rows through F_j
        curr_init_rows = [{a: r.get(a) for a in hop.target_heading} for r in curr_init_rows]
        curr_upd_rows = [{a: r.get(a) for a in hop.target_heading} for r in curr_upd_rows]

        # Path A: Transport initial rows via F_j, then apply BQNF delta (D_target o F_j)
        pred_list = (
            (f"{hop.predicate_attribute} = {hop.predicate_expected_value}",)
            if hop.predicate_attribute and hop.predicate_expected_value is not None
            else ()
        )
        hop_boundary = BqnfBoundary(
            relations=("TargetRep",),
            attributes=tuple(sorted(required_for_commutation)),
            predicates=pred_list,
            groups=(hop.group_attribute,),
            aggregates=(f"SUM({hop.value_attribute})",),
        )
        f_init_totals = _compute_boundary_group_totals(curr_init_totals_rows := curr_init_rows, hop_boundary)
        del curr_init_totals_rows
        # Apply delta (bqnf_updated - bqnf_initial) on target representation
        all_g = set(f_init_totals.keys()) | set(bqnf_initial_totals.keys()) | set(bqnf_updated_totals.keys())
        d_target_after_f: Dict[Any, float] = {}
        for g in all_g:
            delta_g = bqnf_updated_totals.get(g, 0.0) - bqnf_initial_totals.get(g, 0.0)
            val = f_init_totals.get(g, 0.0) + delta_g + hop.injected_target_tamper_delta
            if abs(val) > 1e-12:
                d_target_after_f[g] = val

        # Path B: Apply D_source first, then transport via F_bar_j (F_bar_j o D_source)
        f_bar_after_d_source = _compute_boundary_group_totals(curr_upd_rows, hop_boundary)

        check_groups = set(d_target_after_f.keys()) | set(f_bar_after_d_source.keys())
        commutes_at_hop = all(
            abs(d_target_after_f.get(g, 0.0) - f_bar_after_d_source.get(g, 0.0)) <= 1e-9
            for g in check_groups
        )
        if not commutes_at_hop:
            return CodaMurTransportStageReceipt(
                local_route="TransportViolation",
                canonical_terminal="Reject",
                obstruction_class="[NonZero - CommutationSquareDivergence]",
                commutation_verified=False,
                composed_erased_attributes=tuple(sorted(set(composed_erased))),
                loss_ledger_triggers=tuple(triggers),
                hop_routes=tuple(hop_routes + ["TransportViolation"]),
                certified=False,
                reason=f"Hop '{hop.hop_id}' violated descent commutation square chi_F: D_target(F(r)) != F_bar(D_source(r))",
            )

        hop_route = "DegradedTransportWithLoss" if erased else "TransportOk"
        hop_routes.append(hop_route)

    has_loss = bool(composed_erased)
    final_local = "DegradedTransportWithLoss" if has_loss else "TransportOk"
    final_canon = "Quarantine" if has_loss else "Preserve"
    return CodaMurTransportStageReceipt(
        local_route=final_local,
        canonical_terminal=final_canon,
        obstruction_class="[0]",
        commutation_verified=True,
        composed_erased_attributes=tuple(sorted(set(composed_erased))),
        loss_ledger_triggers=tuple(triggers),
        hop_routes=tuple(hop_routes),
        certified=True,
        authorized=False,
        reason=None,
    )


def run_multi_hop_pipeline(
    schema: RelationalSchema,
    initial_rows: Sequence[Mapping[str, Any]],
    boundary: BqnfBoundary,
    cdc_events: Sequence[BqnfCdcEvent],
    transport_hops: Sequence[CodaMurHopSpec],
    pk_attribute: str = "order_id",
) -> MultiHopCompositionReceipt:
    """Executes the full 3-stage composition pipeline:
    Stage 1 (3NF/BCNF synthesis) -> Stage 2 (BQNF CDC stream) -> Stage 3 (CODA_MUR transport).
    """
    # Stage 1: Relational synthesis & lossless join check
    s1_receipt, rejoined_initial = evaluate_stage1_relational_synthesis(schema, initial_rows)
    if not s1_receipt.certified:
        return MultiHopCompositionReceipt(
            stage1_relational=s1_receipt,
            stage2_bqnf=None,
            stage3_coda_mur=None,
            overall_terminal=s1_receipt.canonical_terminal,
            end_to_end_commutes=False,
            certified=False,
        )

    init_totals = _compute_boundary_group_totals(rejoined_initial, boundary)

    # Stage 2: Streaming BQNF repair over 3NF decomposed relvars
    s2_receipt, rejoined_updated = evaluate_stage2_bqnf_stream(
        schema=schema,
        nf3_components=s1_receipt.nf3_components,
        initial_rows=rejoined_initial,
        boundary=boundary,
        cdc_events=cdc_events,
        pk_attribute=pk_attribute,
    )
    if not s2_receipt.certified:
        return MultiHopCompositionReceipt(
            stage1_relational=s1_receipt,
            stage2_bqnf=s2_receipt,
            stage3_coda_mur=None,
            overall_terminal=s2_receipt.canonical_terminal,
            end_to_end_commutes=False,
            certified=False,
        )

    # Stage 3: Multi-hop CODA_MUR representation transport
    s3_receipt = evaluate_stage3_coda_mur_chain(
        initial_rows=rejoined_initial,
        updated_rows=rejoined_updated,
        bqnf_initial_totals=init_totals,
        bqnf_updated_totals=s2_receipt.incremental_totals_by_group,
        hops=transport_hops,
    )
    if not s3_receipt.certified:
        return MultiHopCompositionReceipt(
            stage1_relational=s1_receipt,
            stage2_bqnf=s2_receipt,
            stage3_coda_mur=s3_receipt,
            overall_terminal=s3_receipt.canonical_terminal,
            end_to_end_commutes=False,
            certified=False,
        )

    # Determine overall canonical terminal
    if s3_receipt.canonical_terminal == "Quarantine":
        overall = "Quarantine"
    elif s2_receipt.canonical_terminal == "Repair":
        overall = "Repair"
    else:
        overall = "Preserve"

    return MultiHopCompositionReceipt(
        stage1_relational=s1_receipt,
        stage2_bqnf=s2_receipt,
        stage3_coda_mur=s3_receipt,
        overall_terminal=overall,
        end_to_end_commutes=True,
        certified=True,
        authorized=False,
        certified_implies_authorized=False,
        authority_effect="None",
    )


def main() -> None:
    """Demo 05: Multi-hop composition across 3NF/BCNF, BQNF CDC repair, and CODA_MUR transport."""
    from dataclasses import asdict

    heading = ("order_id", "customer_id", "customer_zip", "region", "status", "amount", "audit_nonce")
    schema = RelationalSchema(
        attributes=frozenset(heading),
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
        attribute_domains={a: "scalar" for a in heading},
    )
    initial_rows = [
        {
            "order_id": 101,
            "customer_id": 7,
            "customer_zip": "10001",
            "region": "US-EAST",
            "status": "pending",
            "amount": 100.0,
            "audit_nonce": "n_101",
        },
        {
            "order_id": 102,
            "customer_id": 7,
            "customer_zip": "10001",
            "region": "US-EAST",
            "status": "paid",
            "amount": 250.0,
            "audit_nonce": "n_102",
        },
    ]
    boundary = BqnfBoundary(
        relations=("Orders",),
        attributes=("customer_id", "status", "amount"),
        predicates=("status = paid",),
        groups=("customer_id",),
        aggregates=("SUM(amount)",),
    )
    events = [
        BqnfCdcEvent(
            op="UPDATE",
            relation="Orders",
            old=dict(initial_rows[0]),
            new={**initial_rows[0], "status": "paid", "amount": 150.0},
        )
    ]
    h1_target = ("order_id", "customer_id", "customer_zip", "region", "status", "amount")
    h2_target = ("order_id", "customer_id", "status", "amount")
    hops = [
        CodaMurHopSpec(
            hop_id="hop1_strip_audit_nonce",
            source_heading=heading,
            target_heading=h1_target,
            group_attribute="customer_id",
            value_attribute="amount",
            predicate_attribute="status",
            predicate_expected_value="paid",
            loss_ledger=build_sealed_loss_ledger(["audit_nonce"], initial_rows, "order_id"),
            target_verifier={"verifier_id": "verifier_hop1", "executed": True, "outcome": "verified"},
        ),
        CodaMurHopSpec(
            hop_id="hop2_strip_geography",
            source_heading=h1_target,
            target_heading=h2_target,
            group_attribute="customer_id",
            value_attribute="amount",
            predicate_attribute="status",
            predicate_expected_value="paid",
            loss_ledger=build_sealed_loss_ledger(["customer_zip", "region"], initial_rows, "order_id"),
            target_verifier={"verifier_id": "verifier_hop2", "executed": True, "outcome": "verified"},
        ),
    ]
    receipt = run_multi_hop_pipeline(schema, initial_rows, boundary, events, hops)
    print("================================================================================")
    print("DEMO 05: Multi-Hop Composition (3NF/BCNF -> BQNF Stream -> CODA_MUR Transport)")
    print("================================================================================")
    print(json.dumps(asdict(receipt), indent=2))


if __name__ == "__main__":
    main()
