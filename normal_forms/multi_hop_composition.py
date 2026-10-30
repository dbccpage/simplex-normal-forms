"""Multi-hop composition pipeline chaining relational synthesis (3NF/BCNF),
streaming BQNF delta repair (additive SPJA, non-invertible MIN/MAX priority-queue
cochains, and dynamic-bucket epsilon-BQNF quantile sketches over single or
multi-column composite grouping keys), CODA_MUR representation transport,
and observer-relative freshness posets (nf.epistemic.freshness) across
randomized schema mutations.

Pipeline topologies:
  1. 3-Stage Additive Pipeline (`run_multi_hop_pipeline`):
     Stage 1 (At Rest: 3NF / BCNF synthesis & lossless join reconstruction)
         --> Stage 2 (In Motion: BQNF incremental CDC coboundary repair)
         --> Stage 3 (In Representation: CODA_MUR functorial transport & sealed loss ledgers)

  2. 4-Stage Extended Cochain + Poset Pipeline (`run_extended_multi_hop_pipeline`):
     Stage 1 (At Rest: 3NF / BCNF synthesis & lossless join reconstruction)
         --> Stage 2b (In Motion: Non-invertible MIN/MAX priority-queue cochains
                       + dynamic-bucket epsilon-BQNF quantile sketches in SQLite)
         --> Stage 3 (In Representation: CODA_MUR functorial transport & sealed loss ledgers)
         --> Stage 4 (In Observation: nf.epistemic.freshness observer poset chain)

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
from normal_forms.evaluator import NormalFormsEvaluator
from normal_forms.observer_freshness_example import (
    ObserverSpec,
    evaluate_freshness,
    verify_observer_lattice_monotonicity,
)
from normal_forms.reconciliation_example import verify_loss_ledger_integrity

CODA_MUR_TRIGGER_ID = "coda_mur.unmapped_field_drop"


def encode_composite_group_key(
    row: Mapping[str, Any],
    group_attributes: Sequence[str],
) -> str:
    """Canonical string encoding for single-column or multi-column composite grouping keys."""
    if not group_attributes:
        raise ValueError("group_attributes must be non-empty")
    return "|".join(str(row[attr]) for attr in group_attributes)


def decode_composite_group_key(
    encoded_key: str,
    group_attributes: Sequence[str],
) -> Dict[str, str]:
    """Inverse decoding from a canonical composite group key into attribute-value pairs."""
    parts = encoded_key.split("|")
    if len(parts) != len(group_attributes):
        raise ValueError(
            f"Composite key '{encoded_key}' has {len(parts)} parts, expected {len(group_attributes)} for {group_attributes}"
        )
    return dict(zip(group_attributes, parts))


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
class SalesCochainCdcSpec:
    """Specification of a streaming CDC event for the SQLite extrema/quantile cochain engine."""

    op_type: str
    sale_id: int
    old_region: Optional[str] = None
    new_region: Optional[str] = None
    old_amount: Optional[float] = None
    new_amount: Optional[float] = None
    old_row: Optional[Dict[str, Any]] = None
    new_row: Optional[Dict[str, Any]] = None
    event_timestamp: Optional[float] = None
    ingestion_timestamp: Optional[float] = None


@dataclass(frozen=True)
class WatermarkSpec:
    """Event-time watermark policy for out-of-order late-arriving CDC streams."""

    allowed_lateness_seconds: float
    initial_watermark_seconds: float = 0.0
    base_replica_lag_seconds: float = 0.0
    packet_scope: str = "regional_sales"
    reject_beyond_watermark: bool = True


@dataclass(frozen=True)
class WatermarkedStepReceipt:
    """Per-step receipt coupling late-arriving CDC cochain repair with observer poset freshness shifts."""

    step_index: int
    sale_id: int
    op_type: str
    event_timestamp: float
    ingestion_timestamp: float
    max_event_timestamp: float
    watermark_timestamp: float
    is_out_of_order: bool
    event_lateness_seconds: float
    effective_replica_lag_seconds: float
    within_watermark: bool
    cochain_step_terminal: str
    bucket_splits_at_step: int
    bucket_merges_at_step: int
    active_bucket_counts: Dict[str, int]
    cached_medians: Dict[str, Any]
    true_medians: Dict[str, Any]
    observer_poset_terminal: str
    admitted_observers: Tuple[str, ...]
    rejected_observers: Tuple[str, ...]
    poset_monotonicity_preserved: bool


@dataclass(frozen=True)
class WatermarkedStreamReceipt:
    """Receipt emitted by evaluate_watermarked_cdc_stream_with_observer_poset."""

    terminal_route: str
    canonical_terminal: str
    events_submitted: int
    events_applied: int
    out_of_order_events_applied: int
    late_events_rejected_or_quarantined: int
    historical_bucket_mutations_on_late_events: int
    total_bucket_splits: int
    total_bucket_merges: int
    final_watermark_timestamp: float
    max_event_timestamp: float
    max_observed_replica_lag_seconds: float
    poset_threshold_shifts: int
    lag_anti_monotonicity_verified: bool
    all_step_posets_monotonic: bool
    converges_to_event_time_order: bool
    step_receipts: Tuple[WatermarkedStepReceipt, ...]
    final_cochain_receipt: Optional[CochainExtremaQuantileStageReceipt]
    final_observer_poset_receipt: Optional[ObserverPosetStageReceipt]
    coda_mur_receipt: Optional[CodaMurTransportStageReceipt] = None
    certified: bool = False
    authorized: bool = False
    certified_implies_authorized: bool = False
    authority_effect: str = "None"
    reason: Optional[str] = None


@dataclass(frozen=True)
class CochainExtremaQuantileStageReceipt:
    """Receipt emitted by Hop 2b (Non-invertible MIN/MAX priority-queue cochain & epsilon-BQNF quantile sketch)."""

    terminal_route: str
    canonical_terminal: str
    step_terminals: Tuple[str, ...]
    events_processed: int
    verified_consistent: bool
    commutes_with_3nf_rejoin: bool
    quantile_accuracy_verified: bool
    cached_state: Dict[str, Dict[str, Any]]
    cached_extrema: Dict[str, Dict[str, Any]]
    cached_medians: Dict[str, Any]
    true_medians: Dict[str, Any]
    extrema_repairs: int
    fallback_recomputations: int
    quantile_repairs: int
    quantile_fallback_recomputations: int
    certified: bool
    group_attributes: Tuple[str, ...] = ("region",)
    dynamic_buckets_enabled: bool = False
    bucket_splits_executed: int = 0
    bucket_merges_executed: int = 0
    quantile_invariants_verified: bool = True
    active_bucket_counts: Dict[str, int] = field(default_factory=dict)
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
    group_attributes: Optional[Tuple[str, ...]] = None
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
class ObserverPosetStageReceipt:
    """Receipt emitted by Hop 4 (Observer-relative freshness poset evaluation nf.epistemic.freshness)."""

    terminal_route: str
    canonical_terminal: str
    poset_chain_valid: bool
    monotonicity_preserved: bool
    observer_decisions: Tuple[Dict[str, Any], ...]
    admitted_observers: Tuple[str, ...]
    rejected_observers: Tuple[str, ...]
    certified: bool
    authorized: bool = False
    certified_implies_authorized: bool = False
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


@dataclass(frozen=True)
class ExtendedMultiHopCompositionReceipt:
    """End-to-end 4-stage receipt across 3NF/BCNF, Extrema+Quantile Cochains, CODA_MUR, and Observer Poset."""

    stage1_relational: RelationalSynthesisStageReceipt
    stage2_cochain: Optional[CochainExtremaQuantileStageReceipt]
    stage3_coda_mur: Optional[CodaMurTransportStageReceipt]
    stage4_observer_poset: Optional[ObserverPosetStageReceipt]
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
    force_string_key: bool = False,
) -> Dict[Any, float]:
    groups = boundary.groups if boundary.groups else ("customer_id",)
    val_attr = "amount" if "amount" in boundary.attributes else (boundary.attributes[-1] if boundary.attributes else "amount")
    pred_str = boundary.predicates[0] if boundary.predicates else ""
    totals: Dict[Any, float] = {}
    for row in rows:
        if BqnfValidator._parse_predicate(pred_str, dict(row)):
            if len(groups) > 1 or force_string_key:
                g_val: Any = encode_composite_group_key(row, groups)
            else:
                g_val = row.get(groups[0])
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


def evaluate_stage2b_cochain_extrema_quantiles(
    schema: RelationalSchema,
    nf3_components: Sequence[Sequence[str]],
    initial_rows: Sequence[Mapping[str, Any]],
    cochain_cdc_events: Sequence[SalesCochainCdcSpec],
    use_cochain: bool = True,
    track_quantiles: bool = True,
    quantile_tolerance: float = 15.0,
    pk_attribute: str = "sale_id",
    group_attributes: Sequence[str] = ("region",),
    dynamic_buckets: bool = False,
    bucket_width: float = 10.0,
    split_threshold: int = 8,
    merge_threshold: int = 3,
    min_bucket_width: float = 0.625,
) -> Tuple[CochainExtremaQuantileStageReceipt, List[Dict[str, Any]]]:
    """Hop 2b: Evaluates non-invertible MIN/MAX priority-queue cochains and epsilon-BQNF quantile
    sketches (with optional dynamic dyadic bucket splitting/merging and multi-column composite
    grouping keys) in SQLite over a 3NF/BCNF-normalized relation.
    """
    current_rows = [dict(r) for r in initial_rows]
    grp_tuple = tuple(group_attributes)

    # Validate group_attributes and dynamic bucket configuration (fail closed)
    if not grp_tuple or any(g not in schema.attributes for g in grp_tuple):
        return (
            CochainExtremaQuantileStageReceipt(
                terminal_route="Refuse",
                canonical_terminal="Refuse",
                step_terminals=("Refuse",),
                events_processed=0,
                verified_consistent=False,
                commutes_with_3nf_rejoin=False,
                quantile_accuracy_verified=False,
                cached_state={},
                cached_extrema={},
                cached_medians={},
                true_medians={},
                extrema_repairs=0,
                fallback_recomputations=0,
                quantile_repairs=0,
                quantile_fallback_recomputations=0,
                certified=False,
                group_attributes=grp_tuple,
                dynamic_buckets_enabled=dynamic_buckets,
                quantile_invariants_verified=False,
                reason=f"Invalid or undeclared group_attributes: {grp_tuple}",
            ),
            current_rows,
        )

    if dynamic_buckets and (
        bucket_width <= 0.0
        or min_bucket_width <= 0.0
        or min_bucket_width > bucket_width + 1e-12
        or split_threshold < 2
        or merge_threshold < 0
        or merge_threshold >= split_threshold
    ):
        return (
            CochainExtremaQuantileStageReceipt(
                terminal_route="Refuse",
                canonical_terminal="Refuse",
                step_terminals=("Refuse",),
                events_processed=0,
                verified_consistent=False,
                commutes_with_3nf_rejoin=False,
                quantile_accuracy_verified=False,
                cached_state={},
                cached_extrema={},
                cached_medians={},
                true_medians={},
                extrema_repairs=0,
                fallback_recomputations=0,
                quantile_repairs=0,
                quantile_fallback_recomputations=0,
                certified=False,
                group_attributes=grp_tuple,
                dynamic_buckets_enabled=dynamic_buckets,
                quantile_invariants_verified=False,
                reason=(
                    f"Invalid dynamic bucket configuration: bucket_width={bucket_width}, "
                    f"min_bucket_width={min_bucket_width}, split_threshold={split_threshold}, "
                    f"merge_threshold={merge_threshold}"
                ),
            ),
            current_rows,
        )

    total_splits = 0
    total_merges = 0

    with NormalFormsEvaluator(in_memory=True) as evaluator:
        # 1. Seed baseline rows from the 3NF-rejoined initial instance
        for row in current_rows:
            if pk_attribute not in row or "amount" not in row or any(g not in row for g in grp_tuple):
                return (
                    CochainExtremaQuantileStageReceipt(
                        terminal_route="Refuse",
                        canonical_terminal="Refuse",
                        step_terminals=("Refuse",),
                        events_processed=0,
                        verified_consistent=False,
                        commutes_with_3nf_rejoin=False,
                        quantile_accuracy_verified=False,
                        cached_state={},
                        cached_extrema={},
                        cached_medians={},
                        true_medians={},
                        extrema_repairs=0,
                        fallback_recomputations=0,
                        quantile_repairs=0,
                        quantile_fallback_recomputations=0,
                        certified=False,
                        group_attributes=grp_tuple,
                        dynamic_buckets_enabled=dynamic_buckets,
                        quantile_invariants_verified=False,
                        reason=f"Initial row missing required cochain attributes ({pk_attribute}, {grp_tuple}, amount)",
                    ),
                    current_rows,
                )
            g_key = encode_composite_group_key(row, grp_tuple)
            reb_info = evaluator.apply_sales_cdc(
                op_type="INSERT",
                sale_id=int(row[pk_attribute]),
                new_region=g_key,
                new_amount=float(row["amount"]),
                maintain_cochain=use_cochain,
                dynamic_buckets=dynamic_buckets,
                bucket_width=bucket_width,
                split_threshold=split_threshold,
                merge_threshold=merge_threshold,
                min_bucket_width=min_bucket_width,
            )
            total_splits += int(reb_info.get("splits_executed", 0))
            total_merges += int(reb_info.get("merges_executed", 0))

        # Materialize the initial cache state before streaming CDC deltas
        init_audit = evaluator.process_bqnf_incremental_repair(
            use_cochain=use_cochain,
            track_quantiles=track_quantiles,
            quantile_tolerance=quantile_tolerance,
        )

        total_events_processed = 0
        total_extrema_repairs = 0
        total_fallback_recomputations = 0
        total_quantile_repairs = 0
        total_quantile_fallback_recomputations = 0
        step_terminals: List[str] = []
        all_steps_consistent = bool(init_audit["verified_consistent"])
        last_audit = init_audit

        # 2. Stream CDC events and repair incrementally per event
        for ev in cochain_cdc_events:
            old_g_key: Optional[str] = ev.old_region
            new_g_key: Optional[str] = ev.new_region
            if ev.old_row is not None and all(g in ev.old_row for g in grp_tuple):
                old_g_key = encode_composite_group_key(ev.old_row, grp_tuple)
            elif old_g_key is None and ev.op_type in ("DELETE", "UPDATE"):
                matched = next((r for r in current_rows if int(r[pk_attribute]) == ev.sale_id), None)
                if matched is not None and all(g in matched for g in grp_tuple):
                    old_g_key = encode_composite_group_key(matched, grp_tuple)
            if ev.new_row is not None and all(g in ev.new_row for g in grp_tuple):
                new_g_key = encode_composite_group_key(ev.new_row, grp_tuple)

            # Update relational instance rows and verify declared FDs
            if ev.op_type == "INSERT":
                if new_g_key is None or ev.new_amount is None or ev.new_row is None:
                    return (
                        CochainExtremaQuantileStageReceipt(
                            terminal_route="Invalidate",
                            canonical_terminal="Invalidate",
                            step_terminals=tuple(step_terminals + ["Invalidate"]),
                            events_processed=total_events_processed,
                            verified_consistent=False,
                            commutes_with_3nf_rejoin=False,
                            quantile_accuracy_verified=False,
                            cached_state={},
                            cached_extrema={},
                            cached_medians={},
                            true_medians={},
                            extrema_repairs=total_extrema_repairs,
                            fallback_recomputations=total_fallback_recomputations,
                            quantile_repairs=total_quantile_repairs,
                            quantile_fallback_recomputations=total_quantile_fallback_recomputations,
                            certified=False,
                            group_attributes=grp_tuple,
                            dynamic_buckets_enabled=dynamic_buckets,
                            bucket_splits_executed=total_splits,
                            bucket_merges_executed=total_merges,
                            reason="INSERT CDC event missing new group key, new_amount, or new_row payload",
                        ),
                        current_rows,
                    )
                candidate_rows = [r for r in current_rows if int(r[pk_attribute]) != ev.sale_id]
                candidate_rows.append(dict(ev.new_row))
            elif ev.op_type == "DELETE":
                if old_g_key is None or ev.old_amount is None:
                    return (
                        CochainExtremaQuantileStageReceipt(
                            terminal_route="Invalidate",
                            canonical_terminal="Invalidate",
                            step_terminals=tuple(step_terminals + ["Invalidate"]),
                            events_processed=total_events_processed,
                            verified_consistent=False,
                            commutes_with_3nf_rejoin=False,
                            quantile_accuracy_verified=False,
                            cached_state={},
                            cached_extrema={},
                            cached_medians={},
                            true_medians={},
                            extrema_repairs=total_extrema_repairs,
                            fallback_recomputations=total_fallback_recomputations,
                            quantile_repairs=total_quantile_repairs,
                            quantile_fallback_recomputations=total_quantile_fallback_recomputations,
                            certified=False,
                            group_attributes=grp_tuple,
                            dynamic_buckets_enabled=dynamic_buckets,
                            bucket_splits_executed=total_splits,
                            bucket_merges_executed=total_merges,
                            reason="DELETE CDC event missing old group key or old_amount",
                        ),
                        current_rows,
                    )
                candidate_rows = [r for r in current_rows if int(r[pk_attribute]) != ev.sale_id]
            elif ev.op_type == "UPDATE":
                if (
                    old_g_key is None
                    or ev.old_amount is None
                    or new_g_key is None
                    or ev.new_amount is None
                    or ev.new_row is None
                ):
                    return (
                        CochainExtremaQuantileStageReceipt(
                            terminal_route="Invalidate",
                            canonical_terminal="Invalidate",
                            step_terminals=tuple(step_terminals + ["Invalidate"]),
                            events_processed=total_events_processed,
                            verified_consistent=False,
                            commutes_with_3nf_rejoin=False,
                            quantile_accuracy_verified=False,
                            cached_state={},
                            cached_extrema={},
                            cached_medians={},
                            true_medians={},
                            extrema_repairs=total_extrema_repairs,
                            fallback_recomputations=total_fallback_recomputations,
                            quantile_repairs=total_quantile_repairs,
                            quantile_fallback_recomputations=total_quantile_fallback_recomputations,
                            certified=False,
                            group_attributes=grp_tuple,
                            dynamic_buckets_enabled=dynamic_buckets,
                            bucket_splits_executed=total_splits,
                            bucket_merges_executed=total_merges,
                            reason="UPDATE CDC event missing old/new group key, amount, or new_row payload",
                        ),
                        current_rows,
                    )
                candidate_rows = []
                for r in current_rows:
                    if int(r[pk_attribute]) == ev.sale_id:
                        candidate_rows.append(dict(ev.new_row))
                    else:
                        candidate_rows.append(dict(r))
            else:
                return (
                    CochainExtremaQuantileStageReceipt(
                        terminal_route="Unsupported",
                        canonical_terminal="Unsupported",
                        step_terminals=tuple(step_terminals + ["Unsupported"]),
                        events_processed=total_events_processed,
                        verified_consistent=False,
                        commutes_with_3nf_rejoin=False,
                        quantile_accuracy_verified=False,
                        cached_state={},
                        cached_extrema={},
                        cached_medians={},
                        true_medians={},
                        extrema_repairs=total_extrema_repairs,
                        fallback_recomputations=total_fallback_recomputations,
                        quantile_repairs=total_quantile_repairs,
                        quantile_fallback_recomputations=total_quantile_fallback_recomputations,
                        certified=False,
                        group_attributes=grp_tuple,
                        dynamic_buckets_enabled=dynamic_buckets,
                        bucket_splits_executed=total_splits,
                        bucket_merges_executed=total_merges,
                        reason=f"Unsupported CDC op_type '{ev.op_type}'",
                    ),
                    current_rows,
                )

            # Check FD preservation across normalized subschemas
            fd_ok, fd_err = check_instance_satisfies_fds(candidate_rows, schema.dependencies)
            if not fd_ok:
                return (
                    CochainExtremaQuantileStageReceipt(
                        terminal_route="ClosureFailure",
                        canonical_terminal="ClosureFailure",
                        step_terminals=tuple(step_terminals + ["ClosureFailure"]),
                        events_processed=total_events_processed,
                        verified_consistent=False,
                        commutes_with_3nf_rejoin=False,
                        quantile_accuracy_verified=False,
                        cached_state={},
                        cached_extrema={},
                        cached_medians={},
                        true_medians={},
                        extrema_repairs=total_extrema_repairs,
                        fallback_recomputations=total_fallback_recomputations,
                        quantile_repairs=total_quantile_repairs,
                        quantile_fallback_recomputations=total_quantile_fallback_recomputations,
                        certified=False,
                        group_attributes=grp_tuple,
                        dynamic_buckets_enabled=dynamic_buckets,
                        bucket_splits_executed=total_splits,
                        bucket_merges_executed=total_merges,
                        reason=f"CDC mutation violated declared FD in 3NF relvars: {fd_err}",
                    ),
                    current_rows,
                )

            current_rows = candidate_rows
            reb_step = evaluator.apply_sales_cdc(
                op_type=ev.op_type,
                sale_id=ev.sale_id,
                old_region=old_g_key,
                new_region=new_g_key,
                old_amount=ev.old_amount,
                new_amount=ev.new_amount,
                maintain_cochain=use_cochain,
                dynamic_buckets=dynamic_buckets,
                bucket_width=bucket_width,
                split_threshold=split_threshold,
                merge_threshold=merge_threshold,
                min_bucket_width=min_bucket_width,
            )
            total_splits += int(reb_step.get("splits_executed", 0))
            total_merges += int(reb_step.get("merges_executed", 0))

            step_audit = evaluator.process_bqnf_incremental_repair(
                use_cochain=use_cochain,
                track_quantiles=track_quantiles,
                quantile_tolerance=quantile_tolerance,
            )
            total_events_processed += int(step_audit["events_processed"])
            total_extrema_repairs += int(step_audit["extrema_repairs"])
            total_fallback_recomputations += int(step_audit["fallback_recomputations"])
            total_quantile_repairs += int(step_audit["quantile_repairs"])
            total_quantile_fallback_recomputations += int(step_audit["quantile_fallback_recomputations"])
            step_terminals.append(str(step_audit["terminal"]))
            all_steps_consistent = all_steps_consistent and bool(step_audit["verified_consistent"])
            last_audit = step_audit

        # 3. Verify commutation with 3NF projection-join, quantile sketch invariants, and true median error bounds
        rejoin_ok, rejoined_rows, _ = project_and_rejoin(current_rows, schema.attributes, nf3_components)
        by_region: Dict[str, List[float]] = {}
        for r in rejoined_rows:
            reg = encode_composite_group_key(r, grp_tuple)
            by_region.setdefault(reg, []).append(float(r["amount"]))

        cached_state = {
            reg: (
                {"total": float(v[0]), "count": int(v[1])}
                if isinstance(v, (tuple, list))
                else {"total": float(v.get("total", 0.0)), "count": int(v.get("count", 0))}
            )
            for reg, v in last_audit["cached_state"].items()
        }
        cached_extrema = {
            reg: (
                {"min": v[0], "max": v[1]}
                if isinstance(v, (tuple, list))
                else {"min": v.get("min"), "max": v.get("max")}
            )
            for reg, v in last_audit["cached_extrema"].items()
        }
        cached_medians = dict(last_audit["cached_medians"])

        all_regs = set(cached_state.keys()) | set(by_region.keys())
        commutes_3nf = rejoin_ok and all_steps_consistent
        for reg in all_regs:
            vals = by_region.get(reg, [])
            c_state = cached_state.get(reg, {"total": 0.0, "count": 0})
            c_ext = cached_extrema.get(reg, {"min": None, "max": None})
            if not vals:
                if c_state["count"] != 0 or c_ext["min"] is not None or c_ext["max"] is not None:
                    commutes_3nf = False
            else:
                if c_state["count"] != len(vals):
                    commutes_3nf = False
                if abs(float(c_state["total"]) - sum(vals)) > 1e-9:
                    commutes_3nf = False
                if c_ext["min"] is None or abs(float(c_ext["min"]) - min(vals)) > 1e-9:
                    commutes_3nf = False
                if c_ext["max"] is None or abs(float(c_ext["max"]) - max(vals)) > 1e-9:
                    commutes_3nf = False

        true_medians: Dict[str, Any] = {}
        quantile_ok = True
        for reg in sorted(by_region.keys()):
            t_med = evaluator.compute_true_median(reg)
            true_medians[reg] = t_med
            c_med = cached_medians.get(reg)
            if t_med is not None:
                if c_med is None or abs(float(c_med) - float(t_med)) > quantile_tolerance + 1e-9:
                    quantile_ok = False

        if use_cochain:
            q_inv_ok, _ = evaluator.verify_quantile_cochain_invariants()
        else:
            q_inv_ok = True

        active_bucket_counts: Dict[str, int] = {}
        cur = evaluator.conn.cursor()
        cur.execute(
            "SELECT region, COUNT(*) AS b_cnt FROM region_quantile_cochain WHERE count > 0 GROUP BY region;"
        )
        for b_row in cur.fetchall():
            active_bucket_counts[str(b_row["region"])] = int(b_row["b_cnt"])

    if not commutes_3nf or not quantile_ok or not q_inv_ok:
        final_route = "ClosureFailure"
        canon_route = "ClosureFailure"
        is_cert = False
    elif "Recompute" in step_terminals:
        final_route = "Recompute"
        canon_route = "Recompute"
        is_cert = True
    elif "Repair" in step_terminals or total_events_processed > 0:
        final_route = "Repair"
        canon_route = "Repair"
        is_cert = True
    else:
        final_route = "Preserve"
        canon_route = "Preserve"
        is_cert = True

    return (
        CochainExtremaQuantileStageReceipt(
            terminal_route=final_route,
            canonical_terminal=canon_route,
            step_terminals=tuple(step_terminals),
            events_processed=total_events_processed,
            verified_consistent=all_steps_consistent,
            commutes_with_3nf_rejoin=commutes_3nf,
            quantile_accuracy_verified=quantile_ok,
            cached_state=cached_state,
            cached_extrema=cached_extrema,
            cached_medians=cached_medians,
            true_medians=true_medians,
            extrema_repairs=total_extrema_repairs,
            fallback_recomputations=total_fallback_recomputations,
            quantile_repairs=total_quantile_repairs,
            quantile_fallback_recomputations=total_quantile_fallback_recomputations,
            certified=is_cert,
            group_attributes=grp_tuple,
            dynamic_buckets_enabled=dynamic_buckets,
            bucket_splits_executed=total_splits,
            bucket_merges_executed=total_merges,
            quantile_invariants_verified=q_inv_ok,
            active_bucket_counts=active_bucket_counts,
            authorized=False,
            reason=None if is_cert else "Cochain extrema/quantile state diverged from 3NF projection-join",
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

    use_str_keys = any(isinstance(k, str) and "|" in k for k in bqnf_initial_totals) or any(
        isinstance(k, str) and "|" in k for k in bqnf_updated_totals
    )

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
        hop_group_attrs = hop.group_attributes if hop.group_attributes is not None else (hop.group_attribute,)
        required_for_commutation = set(hop_group_attrs) | {hop.value_attribute}
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
            groups=tuple(hop_group_attrs),
            aggregates=(f"SUM({hop.value_attribute})",),
        )
        f_init_totals = _compute_boundary_group_totals(
            curr_init_rows, hop_boundary, force_string_key=use_str_keys
        )
        # Apply delta (bqnf_updated - bqnf_initial) on target representation
        all_g = set(f_init_totals.keys()) | set(bqnf_initial_totals.keys()) | set(bqnf_updated_totals.keys())
        d_target_after_f: Dict[Any, float] = {}
        for g in all_g:
            delta_g = bqnf_updated_totals.get(g, 0.0) - bqnf_initial_totals.get(g, 0.0)
            val = f_init_totals.get(g, 0.0) + delta_g + hop.injected_target_tamper_delta
            if abs(val) > 1e-12:
                d_target_after_f[g] = val

        # Path B: Apply D_source first, then transport via F_bar_j (F_bar_j o D_source)
        f_bar_after_d_source = _compute_boundary_group_totals(
            curr_upd_rows, hop_boundary, force_string_key=use_str_keys
        )

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


def evaluate_stage4_observer_freshness_poset(
    packet: Mapping[str, Any],
    observer_poset: Sequence[ObserverSpec],
) -> ObserverPosetStageReceipt:
    """Hop 4: Evaluates observer-relative freshness (nf.epistemic.freshness) across a poset chain
    O_1 <= O_2 <= ... <= O_m, verifying poset ordering, upward monotonicity, and fail-closed gates.
    """
    if not observer_poset:
        return ObserverPosetStageReceipt(
            terminal_route="Refuse",
            canonical_terminal="Refuse",
            poset_chain_valid=False,
            monotonicity_preserved=False,
            observer_decisions=(),
            admitted_observers=(),
            rejected_observers=(),
            certified=False,
            reason="Empty observer poset chain declared",
        )

    # 1. Verify that O_1 <= O_2 <= ... <= O_m forms a valid stringency poset chain
    for idx in range(len(observer_poset) - 1):
        curr_obs = observer_poset[idx]
        next_obs = observer_poset[idx + 1]
        if not curr_obs.is_more_stringent_than(next_obs):
            return ObserverPosetStageReceipt(
                terminal_route="PosetOrderViolation",
                canonical_terminal="Refuse",
                poset_chain_valid=False,
                monotonicity_preserved=False,
                observer_decisions=(),
                admitted_observers=(),
                rejected_observers=(),
                certified=False,
                reason=(
                    f"Observer poset chain violated O_{idx} <= O_{idx + 1}: "
                    f"{curr_obs.observer_id} (lag={curr_obs.max_lag_seconds}, scopes={curr_obs.authorized_scopes}) "
                    f"is not more stringent than {next_obs.observer_id} "
                    f"(lag={next_obs.max_lag_seconds}, scopes={next_obs.authorized_scopes})"
                ),
            )

    obs_dicts = [
        {
            "observer_id": obs.observer_id,
            "max_lag_seconds": obs.max_lag_seconds,
            "authorized_scopes": list(obs.authorized_scopes),
        }
        for obs in observer_poset
    ]
    packet_dict = dict(packet)
    decisions = evaluate_freshness({"packet": packet_dict, "observers": obs_dicts})
    mono_ok, mono_violations = verify_observer_lattice_monotonicity(obs_dicts, packet_dict)

    admitted = tuple(d["observer_id"] for d in decisions if d.get("terminal_route") == "AuthorizedFresh")
    rejected = tuple(d["observer_id"] for d in decisions if d.get("terminal_route") != "AuthorizedFresh")
    routes = [d.get("terminal_route") for d in decisions]

    if not mono_ok:
        return ObserverPosetStageReceipt(
            terminal_route="MonotonicityViolation",
            canonical_terminal="Refuse",
            poset_chain_valid=True,
            monotonicity_preserved=False,
            observer_decisions=tuple(decisions),
            admitted_observers=admitted,
            rejected_observers=rejected,
            certified=False,
            reason="; ".join(mono_violations),
        )

    if any(r == "Refuse" for r in routes):
        first_refuse = next(d for d in decisions if d.get("terminal_route") == "Refuse")
        return ObserverPosetStageReceipt(
            terminal_route="Refuse",
            canonical_terminal="Refuse",
            poset_chain_valid=True,
            monotonicity_preserved=mono_ok,
            observer_decisions=tuple(decisions),
            admitted_observers=admitted,
            rejected_observers=rejected,
            certified=False,
            reason=str(first_refuse.get("reason")),
        )

    if any(r == "ConservativeInvalidate" for r in routes):
        first_ci = next(d for d in decisions if d.get("terminal_route") == "ConservativeInvalidate")
        return ObserverPosetStageReceipt(
            terminal_route="ConservativeInvalidate",
            canonical_terminal="ConservativeInvalidate",
            poset_chain_valid=True,
            monotonicity_preserved=mono_ok,
            observer_decisions=tuple(decisions),
            admitted_observers=admitted,
            rejected_observers=rejected,
            certified=False,
            reason=str(first_ci.get("reason")),
        )

    if len(admitted) == len(observer_poset):
        return ObserverPosetStageReceipt(
            terminal_route="AuthorizedFresh",
            canonical_terminal="Preserve",
            poset_chain_valid=True,
            monotonicity_preserved=True,
            observer_decisions=tuple(decisions),
            admitted_observers=admitted,
            rejected_observers=rejected,
            certified=True,
            authorized=False,
            certified_implies_authorized=False,
            authority_effect="None",
            reason=None,
        )

    if len(admitted) > 0:
        return ObserverPosetStageReceipt(
            terminal_route="PartialPosetAdmissibility",
            canonical_terminal="Preserve",
            poset_chain_valid=True,
            monotonicity_preserved=True,
            observer_decisions=tuple(decisions),
            admitted_observers=admitted,
            rejected_observers=rejected,
            certified=True,
            authorized=False,
            certified_implies_authorized=False,
            authority_effect="None",
            reason=None,
        )

    return ObserverPosetStageReceipt(
        terminal_route="RefreshRequired",
        canonical_terminal="Invalidate",
        poset_chain_valid=True,
        monotonicity_preserved=True,
        observer_decisions=tuple(decisions),
        admitted_observers=admitted,
        rejected_observers=rejected,
        certified=False,
        authorized=False,
        certified_implies_authorized=False,
        authority_effect="None",
        reason="Packet replica lag exceeded max_lag_seconds for every observer in the poset chain",
    )


def run_multi_hop_pipeline(
    schema: RelationalSchema,
    initial_rows: Sequence[Mapping[str, Any]],
    boundary: BqnfBoundary,
    cdc_events: Sequence[BqnfCdcEvent],
    transport_hops: Sequence[CodaMurHopSpec],
    pk_attribute: str = "order_id",
) -> MultiHopCompositionReceipt:
    """Executes the 3-stage composition pipeline:
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


def run_extended_multi_hop_pipeline(
    schema: RelationalSchema,
    initial_rows: Sequence[Mapping[str, Any]],
    cochain_cdc_events: Sequence[SalesCochainCdcSpec],
    transport_hops: Sequence[CodaMurHopSpec],
    observer_poset: Sequence[ObserverSpec],
    freshness_packet: Mapping[str, Any],
    use_cochain: bool = True,
    track_quantiles: bool = True,
    quantile_tolerance: float = 15.0,
    pk_attribute: str = "sale_id",
    group_attributes: Sequence[str] = ("region",),
    dynamic_buckets: bool = False,
    bucket_width: float = 10.0,
    split_threshold: int = 8,
    merge_threshold: int = 3,
    min_bucket_width: float = 0.625,
) -> ExtendedMultiHopCompositionReceipt:
    """Executes the 4-stage composition pipeline:
    Stage 1 (3NF/BCNF synthesis)
      -> Stage 2b (Non-invertible MIN/MAX priority-queue cochain & dynamic-bucket epsilon-BQNF quantile sketch)
      -> Stage 3 (CODA_MUR representation transport)
      -> Stage 4 (nf.epistemic.freshness observer-relative freshness poset chain).
    """
    # Stage 1: Relational synthesis & lossless join check
    s1_receipt, rejoined_initial = evaluate_stage1_relational_synthesis(schema, initial_rows)
    if not s1_receipt.certified:
        return ExtendedMultiHopCompositionReceipt(
            stage1_relational=s1_receipt,
            stage2_cochain=None,
            stage3_coda_mur=None,
            stage4_observer_poset=None,
            overall_terminal=s1_receipt.canonical_terminal,
            end_to_end_commutes=False,
            certified=False,
        )

    # Stage 2b: Cochain extrema (MIN/MAX) + epsilon-BQNF quantile sketches in SQLite
    s2b_receipt, rejoined_updated = evaluate_stage2b_cochain_extrema_quantiles(
        schema=schema,
        nf3_components=s1_receipt.nf3_components,
        initial_rows=rejoined_initial,
        cochain_cdc_events=cochain_cdc_events,
        use_cochain=use_cochain,
        track_quantiles=track_quantiles,
        quantile_tolerance=quantile_tolerance,
        pk_attribute=pk_attribute,
        group_attributes=group_attributes,
        dynamic_buckets=dynamic_buckets,
        bucket_width=bucket_width,
        split_threshold=split_threshold,
        merge_threshold=merge_threshold,
        min_bucket_width=min_bucket_width,
    )
    if not s2b_receipt.certified:
        return ExtendedMultiHopCompositionReceipt(
            stage1_relational=s1_receipt,
            stage2_cochain=s2b_receipt,
            stage3_coda_mur=None,
            stage4_observer_poset=None,
            overall_terminal=s2b_receipt.canonical_terminal,
            end_to_end_commutes=False,
            certified=False,
        )

    # Compute initial regional/composite group totals for Stage 3 descent check
    init_totals: Dict[Any, float] = {}
    for r in rejoined_initial:
        g_key = encode_composite_group_key(r, group_attributes)
        init_totals[g_key] = init_totals.get(g_key, 0.0) + float(r.get("amount", 0.0))

    upd_totals = {
        reg: float(state["total"])
        for reg, state in s2b_receipt.cached_state.items()
        if int(state.get("count", 0)) > 0 and abs(float(state["total"])) > 1e-12
    }

    # Stage 3: Multi-hop CODA_MUR representation transport
    s3_receipt = evaluate_stage3_coda_mur_chain(
        initial_rows=rejoined_initial,
        updated_rows=rejoined_updated,
        bqnf_initial_totals=init_totals,
        bqnf_updated_totals=upd_totals,
        hops=transport_hops,
    )
    if not s3_receipt.certified:
        return ExtendedMultiHopCompositionReceipt(
            stage1_relational=s1_receipt,
            stage2_cochain=s2b_receipt,
            stage3_coda_mur=s3_receipt,
            stage4_observer_poset=None,
            overall_terminal=s3_receipt.canonical_terminal,
            end_to_end_commutes=False,
            certified=False,
        )

    # Stage 4: Observer-relative freshness poset evaluation (nf.epistemic.freshness)
    s4_receipt = evaluate_stage4_observer_freshness_poset(
        packet=freshness_packet,
        observer_poset=observer_poset,
    )
    if not s4_receipt.certified:
        return ExtendedMultiHopCompositionReceipt(
            stage1_relational=s1_receipt,
            stage2_cochain=s2b_receipt,
            stage3_coda_mur=s3_receipt,
            stage4_observer_poset=s4_receipt,
            overall_terminal=s4_receipt.canonical_terminal,
            end_to_end_commutes=False,
            certified=False,
        )

    if s3_receipt.canonical_terminal == "Quarantine":
        overall = "Quarantine"
    elif s2b_receipt.canonical_terminal == "Recompute":
        overall = "Recompute"
    elif s2b_receipt.canonical_terminal == "Repair":
        overall = "Repair"
    else:
        overall = "Preserve"

    return ExtendedMultiHopCompositionReceipt(
        stage1_relational=s1_receipt,
        stage2_cochain=s2b_receipt,
        stage3_coda_mur=s3_receipt,
        stage4_observer_poset=s4_receipt,
        overall_terminal=overall,
        end_to_end_commutes=True,
        certified=True,
        authorized=False,
        certified_implies_authorized=False,
        authority_effect="None",
    )


def _snapshot_quantile_cochain(
    evaluator: NormalFormsEvaluator,
) -> Dict[str, List[Tuple[float, float, int]]]:
    """Snapshots active (lower_bound, upper_bound, count) quantile buckets per region."""
    cur = evaluator.conn.cursor()
    cur.execute(
        """
        SELECT region, lower_bound, upper_bound, count
        FROM region_quantile_cochain
        WHERE count > 0
        ORDER BY region ASC, lower_bound ASC, bucket_id ASC;
        """
    )
    snap: Dict[str, List[Tuple[float, float, int]]] = {}
    for row in cur.fetchall():
        snap.setdefault(str(row["region"]), []).append(
            (round(float(row["lower_bound"]), 9), round(float(row["upper_bound"]), 9), int(row["count"]))
        )
    return snap


def evaluate_watermarked_cdc_stream_with_observer_poset(
    schema: RelationalSchema,
    initial_rows: Sequence[Mapping[str, Any]],
    cochain_cdc_events: Sequence[SalesCochainCdcSpec],
    watermark_spec: WatermarkSpec,
    observer_poset: Sequence[ObserverSpec],
    transport_hops: Optional[Sequence[CodaMurHopSpec]] = None,
    use_cochain: bool = True,
    track_quantiles: bool = True,
    quantile_tolerance: float = 15.0,
    pk_attribute: str = "sale_id",
    group_attributes: Sequence[str] = ("region",),
    dynamic_buckets: bool = True,
    bucket_width: float = 10.0,
    split_threshold: int = 8,
    merge_threshold: int = 3,
    min_bucket_width: float = 0.625,
) -> WatermarkedStreamReceipt:
    """Evaluates an out-of-order late-arriving watermarked CDC stream where delayed events
    simultaneously mutate historical quantile buckets in region_quantile_cochain and shift
    observer-relative freshness lag across poset SLA thresholds.
    """
    grp_tuple = tuple(group_attributes)

    # 1. Validate WatermarkSpec parameters (fail closed)
    if (
        watermark_spec.allowed_lateness_seconds < 0.0
        or watermark_spec.initial_watermark_seconds < 0.0
        or watermark_spec.base_replica_lag_seconds < 0.0
        or not isinstance(watermark_spec.packet_scope, str)
        or not watermark_spec.packet_scope.strip()
    ):
        return WatermarkedStreamReceipt(
            terminal_route="Refuse",
            canonical_terminal="Refuse",
            events_submitted=len(cochain_cdc_events),
            events_applied=0,
            out_of_order_events_applied=0,
            late_events_rejected_or_quarantined=0,
            historical_bucket_mutations_on_late_events=0,
            total_bucket_splits=0,
            total_bucket_merges=0,
            final_watermark_timestamp=0.0,
            max_event_timestamp=0.0,
            max_observed_replica_lag_seconds=0.0,
            poset_threshold_shifts=0,
            lag_anti_monotonicity_verified=False,
            all_step_posets_monotonic=False,
            converges_to_event_time_order=False,
            step_receipts=(),
            final_cochain_receipt=None,
            final_observer_poset_receipt=None,
            certified=False,
            reason="Invalid WatermarkSpec parameters (negative lateness/watermark/lag or empty packet_scope)",
        )

    # 2. Validate group_attributes and Stage 1 (3NF/BCNF) relational synthesis
    if not grp_tuple or any(g not in schema.attributes for g in grp_tuple):
        return WatermarkedStreamReceipt(
            terminal_route="Refuse",
            canonical_terminal="Refuse",
            events_submitted=len(cochain_cdc_events),
            events_applied=0,
            out_of_order_events_applied=0,
            late_events_rejected_or_quarantined=0,
            historical_bucket_mutations_on_late_events=0,
            total_bucket_splits=0,
            total_bucket_merges=0,
            final_watermark_timestamp=watermark_spec.initial_watermark_seconds,
            max_event_timestamp=watermark_spec.initial_watermark_seconds,
            max_observed_replica_lag_seconds=0.0,
            poset_threshold_shifts=0,
            lag_anti_monotonicity_verified=False,
            all_step_posets_monotonic=False,
            converges_to_event_time_order=False,
            step_receipts=(),
            final_cochain_receipt=None,
            final_observer_poset_receipt=None,
            certified=False,
            reason=f"Invalid or undeclared group_attributes: {grp_tuple}",
        )

    s1_receipt, rejoined_initial = evaluate_stage1_relational_synthesis(schema, initial_rows)
    if not s1_receipt.certified:
        return WatermarkedStreamReceipt(
            terminal_route=s1_receipt.terminal_route,
            canonical_terminal=s1_receipt.canonical_terminal,
            events_submitted=len(cochain_cdc_events),
            events_applied=0,
            out_of_order_events_applied=0,
            late_events_rejected_or_quarantined=0,
            historical_bucket_mutations_on_late_events=0,
            total_bucket_splits=0,
            total_bucket_merges=0,
            final_watermark_timestamp=watermark_spec.initial_watermark_seconds,
            max_event_timestamp=watermark_spec.initial_watermark_seconds,
            max_observed_replica_lag_seconds=0.0,
            poset_threshold_shifts=0,
            lag_anti_monotonicity_verified=False,
            all_step_posets_monotonic=False,
            converges_to_event_time_order=False,
            step_receipts=(),
            final_cochain_receipt=None,
            final_observer_poset_receipt=None,
            certified=False,
            reason=s1_receipt.reason,
        )

    # 3. Validate observer poset chain baseline
    init_poset_check = evaluate_stage4_observer_freshness_poset(
        packet={
            "value_ref": "watermark_stream:init",
            "packet_scope": watermark_spec.packet_scope,
            "replica_lag_seconds": watermark_spec.base_replica_lag_seconds,
        },
        observer_poset=observer_poset,
    )
    if not init_poset_check.poset_chain_valid or init_poset_check.canonical_terminal in (
        "Refuse",
        "ConservativeInvalidate",
    ):
        return WatermarkedStreamReceipt(
            terminal_route=init_poset_check.terminal_route,
            canonical_terminal=init_poset_check.canonical_terminal,
            events_submitted=len(cochain_cdc_events),
            events_applied=0,
            out_of_order_events_applied=0,
            late_events_rejected_or_quarantined=0,
            historical_bucket_mutations_on_late_events=0,
            total_bucket_splits=0,
            total_bucket_merges=0,
            final_watermark_timestamp=watermark_spec.initial_watermark_seconds,
            max_event_timestamp=watermark_spec.initial_watermark_seconds,
            max_observed_replica_lag_seconds=watermark_spec.base_replica_lag_seconds,
            poset_threshold_shifts=0,
            lag_anti_monotonicity_verified=False,
            all_step_posets_monotonic=False,
            converges_to_event_time_order=False,
            step_receipts=(),
            final_cochain_receipt=None,
            final_observer_poset_receipt=init_poset_check,
            certified=False,
            reason=init_poset_check.reason,
        )

    current_rows = [dict(r) for r in rejoined_initial]
    applied_events: List[SalesCochainCdcSpec] = []
    step_receipts: List[WatermarkedStepReceipt] = []

    max_event_ts = float(watermark_spec.initial_watermark_seconds)
    watermark_ts = float(watermark_spec.initial_watermark_seconds)
    prev_ingest_ts: Optional[float] = None
    prev_admitted: Optional[Tuple[str, ...]] = None

    total_splits = 0
    total_merges = 0
    out_of_order_applied = 0
    late_rejected_or_quarantined = 0
    historical_bucket_mutations = 0
    poset_shifts = 0
    max_observed_lag = float(watermark_spec.base_replica_lag_seconds)
    all_posets_monotonic = True
    last_s4_receipt: ObserverPosetStageReceipt = init_poset_check

    with NormalFormsEvaluator(in_memory=True) as evaluator:
        # Seed initial rows
        for row in current_rows:
            g_key = encode_composite_group_key(row, grp_tuple)
            reb_init = evaluator.apply_sales_cdc(
                op_type="INSERT",
                sale_id=int(row[pk_attribute]),
                new_region=g_key,
                new_amount=float(row["amount"]),
                maintain_cochain=use_cochain,
                dynamic_buckets=dynamic_buckets,
                bucket_width=bucket_width,
                split_threshold=split_threshold,
                merge_threshold=merge_threshold,
                min_bucket_width=min_bucket_width,
            )
            total_splits += int(reb_init.get("splits_executed", 0))
            total_merges += int(reb_init.get("merges_executed", 0))

        evaluator.process_bqnf_incremental_repair(
            use_cochain=use_cochain,
            track_quantiles=track_quantiles,
            quantile_tolerance=quantile_tolerance,
        )

        # Process arriving watermarked CDC events in physical ingestion order
        for idx, ev in enumerate(cochain_cdc_events, start=1):
            if (
                ev.event_timestamp is None
                or ev.ingestion_timestamp is None
                or not isinstance(ev.event_timestamp, (int, float))
                or not isinstance(ev.ingestion_timestamp, (int, float))
                or float(ev.event_timestamp) < 0.0
                or float(ev.ingestion_timestamp) < 0.0
            ):
                return WatermarkedStreamReceipt(
                    terminal_route="ConservativeInvalidate",
                    canonical_terminal="ConservativeInvalidate",
                    events_submitted=len(cochain_cdc_events),
                    events_applied=len(applied_events),
                    out_of_order_events_applied=out_of_order_applied,
                    late_events_rejected_or_quarantined=late_rejected_or_quarantined,
                    historical_bucket_mutations_on_late_events=historical_bucket_mutations,
                    total_bucket_splits=total_splits,
                    total_bucket_merges=total_merges,
                    final_watermark_timestamp=watermark_ts,
                    max_event_timestamp=max_event_ts,
                    max_observed_replica_lag_seconds=max_observed_lag,
                    poset_threshold_shifts=poset_shifts,
                    lag_anti_monotonicity_verified=False,
                    all_step_posets_monotonic=False,
                    converges_to_event_time_order=False,
                    step_receipts=tuple(step_receipts),
                    final_cochain_receipt=None,
                    final_observer_poset_receipt=last_s4_receipt,
                    certified=False,
                    reason=f"Step {idx}: missing or negative event_timestamp or ingestion_timestamp",
                )

            t_event = float(ev.event_timestamp)
            t_ingest = float(ev.ingestion_timestamp)

            # Check physical arrival clock monotonicity
            if prev_ingest_ts is not None and t_ingest < prev_ingest_ts - 1e-9:
                return WatermarkedStreamReceipt(
                    terminal_route="OutOfOrderIngestionClock",
                    canonical_terminal="Invalidate",
                    events_submitted=len(cochain_cdc_events),
                    events_applied=len(applied_events),
                    out_of_order_events_applied=out_of_order_applied,
                    late_events_rejected_or_quarantined=late_rejected_or_quarantined,
                    historical_bucket_mutations_on_late_events=historical_bucket_mutations,
                    total_bucket_splits=total_splits,
                    total_bucket_merges=total_merges,
                    final_watermark_timestamp=watermark_ts,
                    max_event_timestamp=max_event_ts,
                    max_observed_replica_lag_seconds=max_observed_lag,
                    poset_threshold_shifts=poset_shifts,
                    lag_anti_monotonicity_verified=False,
                    all_step_posets_monotonic=False,
                    converges_to_event_time_order=False,
                    step_receipts=tuple(step_receipts),
                    final_cochain_receipt=None,
                    final_observer_poset_receipt=last_s4_receipt,
                    certified=False,
                    reason=(
                        f"Step {idx}: non-monotonic physical ingestion timestamp "
                        f"({t_ingest} < previous {prev_ingest_ts})"
                    ),
                )
            prev_ingest_ts = t_ingest

            # Check causal non-retroactivity: ingestion cannot precede occurrence
            if t_ingest < t_event - 1e-9:
                return WatermarkedStreamReceipt(
                    terminal_route="NegativeEventLagViolation",
                    canonical_terminal="ConservativeInvalidate",
                    events_submitted=len(cochain_cdc_events),
                    events_applied=len(applied_events),
                    out_of_order_events_applied=out_of_order_applied,
                    late_events_rejected_or_quarantined=late_rejected_or_quarantined,
                    historical_bucket_mutations_on_late_events=historical_bucket_mutations,
                    total_bucket_splits=total_splits,
                    total_bucket_merges=total_merges,
                    final_watermark_timestamp=watermark_ts,
                    max_event_timestamp=max_event_ts,
                    max_observed_replica_lag_seconds=max_observed_lag,
                    poset_threshold_shifts=poset_shifts,
                    lag_anti_monotonicity_verified=False,
                    all_step_posets_monotonic=False,
                    converges_to_event_time_order=False,
                    step_receipts=tuple(step_receipts),
                    final_cochain_receipt=None,
                    final_observer_poset_receipt=last_s4_receipt,
                    certified=False,
                    reason=(
                        f"Step {idx}: ingestion_timestamp ({t_ingest}) precedes "
                        f"event_timestamp ({t_event})"
                    ),
                )

            is_ooo = (idx > 1) and (t_event < max_event_ts - 1e-9)
            event_lateness = max(0.0, max_event_ts - t_event) if idx > 1 else 0.0
            max_event_ts = max(max_event_ts, t_event)
            watermark_ts = max(
                watermark_ts,
                max_event_ts - float(watermark_spec.allowed_lateness_seconds),
            )
            within_wm = t_event >= (watermark_ts - 1e-9)

            effective_lag = max(
                float(watermark_spec.base_replica_lag_seconds),
                t_ingest - t_event,
                event_lateness,
            )
            max_observed_lag = max(max_observed_lag, effective_lag)

            s4_step = evaluate_stage4_observer_freshness_poset(
                packet={
                    "value_ref": f"watermark_stream:step_{idx}:sale_{ev.sale_id}",
                    "packet_scope": watermark_spec.packet_scope,
                    "replica_lag_seconds": effective_lag,
                },
                observer_poset=observer_poset,
            )
            last_s4_receipt = s4_step
            all_posets_monotonic = all_posets_monotonic and s4_step.monotonicity_preserved
            if prev_admitted is not None and s4_step.admitted_observers != prev_admitted:
                poset_shifts += 1
            prev_admitted = s4_step.admitted_observers

            if not within_wm:
                late_rejected_or_quarantined += 1
                if watermark_spec.reject_beyond_watermark:
                    return WatermarkedStreamReceipt(
                        terminal_route="LateEventExceedsWatermark",
                        canonical_terminal="Invalidate",
                        events_submitted=len(cochain_cdc_events),
                        events_applied=len(applied_events),
                        out_of_order_events_applied=out_of_order_applied,
                        late_events_rejected_or_quarantined=late_rejected_or_quarantined,
                        historical_bucket_mutations_on_late_events=historical_bucket_mutations,
                        total_bucket_splits=total_splits,
                        total_bucket_merges=total_merges,
                        final_watermark_timestamp=watermark_ts,
                        max_event_timestamp=max_event_ts,
                        max_observed_replica_lag_seconds=max_observed_lag,
                        poset_threshold_shifts=poset_shifts,
                        lag_anti_monotonicity_verified=False,
                        all_step_posets_monotonic=all_posets_monotonic,
                        converges_to_event_time_order=False,
                        step_receipts=tuple(step_receipts),
                        final_cochain_receipt=None,
                        final_observer_poset_receipt=s4_step,
                        certified=False,
                        reason=(
                            f"Step {idx}: late event (t_event={t_event}) fell below advancing "
                            f"watermark (W={watermark_ts}, allowed_lateness={watermark_spec.allowed_lateness_seconds})"
                        ),
                    )
                # Quarantine beyond-watermark event without mutating sealed cochain state
                cur_q = evaluator.conn.cursor()
                cur_q.execute(
                    "SELECT region, COUNT(*) AS b_cnt FROM region_quantile_cochain WHERE count > 0 GROUP BY region;"
                )
                q_counts = {str(r["region"]): int(r["b_cnt"]) for r in cur_q.fetchall()}
                step_receipts.append(
                    WatermarkedStepReceipt(
                        step_index=idx,
                        sale_id=ev.sale_id,
                        op_type=ev.op_type,
                        event_timestamp=t_event,
                        ingestion_timestamp=t_ingest,
                        max_event_timestamp=max_event_ts,
                        watermark_timestamp=watermark_ts,
                        is_out_of_order=is_ooo,
                        event_lateness_seconds=event_lateness,
                        effective_replica_lag_seconds=effective_lag,
                        within_watermark=False,
                        cochain_step_terminal="QuarantinedLateEvent",
                        bucket_splits_at_step=0,
                        bucket_merges_at_step=0,
                        active_bucket_counts=q_counts,
                        cached_medians={},
                        true_medians={},
                        observer_poset_terminal=s4_step.terminal_route,
                        admitted_observers=s4_step.admitted_observers,
                        rejected_observers=s4_step.rejected_observers,
                        poset_monotonicity_preserved=s4_step.monotonicity_preserved,
                    )
                )
                continue

            # Validate causal key life-cycle invariants on current_rows
            active_keys = {int(r[pk_attribute]) for r in current_rows}
            if ev.op_type == "INSERT" and ev.sale_id in active_keys:
                return WatermarkedStreamReceipt(
                    terminal_route="CausalKeyViolation",
                    canonical_terminal="Invalidate",
                    events_submitted=len(cochain_cdc_events),
                    events_applied=len(applied_events),
                    out_of_order_events_applied=out_of_order_applied,
                    late_events_rejected_or_quarantined=late_rejected_or_quarantined,
                    historical_bucket_mutations_on_late_events=historical_bucket_mutations,
                    total_bucket_splits=total_splits,
                    total_bucket_merges=total_merges,
                    final_watermark_timestamp=watermark_ts,
                    max_event_timestamp=max_event_ts,
                    max_observed_replica_lag_seconds=max_observed_lag,
                    poset_threshold_shifts=poset_shifts,
                    lag_anti_monotonicity_verified=False,
                    all_step_posets_monotonic=all_posets_monotonic,
                    converges_to_event_time_order=False,
                    step_receipts=tuple(step_receipts),
                    final_cochain_receipt=None,
                    final_observer_poset_receipt=s4_step,
                    certified=False,
                    reason=f"Step {idx}: duplicate INSERT for already-active {pk_attribute}={ev.sale_id}",
                )
            if ev.op_type in ("DELETE", "UPDATE") and ev.sale_id not in active_keys:
                return WatermarkedStreamReceipt(
                    terminal_route="CausalKeyViolation",
                    canonical_terminal="Invalidate",
                    events_submitted=len(cochain_cdc_events),
                    events_applied=len(applied_events),
                    out_of_order_events_applied=out_of_order_applied,
                    late_events_rejected_or_quarantined=late_rejected_or_quarantined,
                    historical_bucket_mutations_on_late_events=historical_bucket_mutations,
                    total_bucket_splits=total_splits,
                    total_bucket_merges=total_merges,
                    final_watermark_timestamp=watermark_ts,
                    max_event_timestamp=max_event_ts,
                    max_observed_replica_lag_seconds=max_observed_lag,
                    poset_threshold_shifts=poset_shifts,
                    lag_anti_monotonicity_verified=False,
                    all_step_posets_monotonic=all_posets_monotonic,
                    converges_to_event_time_order=False,
                    step_receipts=tuple(step_receipts),
                    final_cochain_receipt=None,
                    final_observer_poset_receipt=s4_step,
                    certified=False,
                    reason=(
                        f"Step {idx}: out-of-order {ev.op_type} arrived before INSERT "
                        f"for {pk_attribute}={ev.sale_id}"
                    ),
                )

            # Resolve composite group keys and update current_rows
            old_g_key: Optional[str] = ev.old_region
            new_g_key: Optional[str] = ev.new_region
            if ev.old_row is not None and all(g in ev.old_row for g in grp_tuple):
                old_g_key = encode_composite_group_key(ev.old_row, grp_tuple)
            elif old_g_key is None and ev.op_type in ("DELETE", "UPDATE"):
                matched = next((r for r in current_rows if int(r[pk_attribute]) == ev.sale_id), None)
                if matched is not None and all(g in matched for g in grp_tuple):
                    old_g_key = encode_composite_group_key(matched, grp_tuple)
            if ev.new_row is not None and all(g in ev.new_row for g in grp_tuple):
                new_g_key = encode_composite_group_key(ev.new_row, grp_tuple)

            if ev.op_type == "INSERT":
                if new_g_key is None or ev.new_amount is None or ev.new_row is None:
                    return WatermarkedStreamReceipt(
                        terminal_route="Invalidate",
                        canonical_terminal="Invalidate",
                        events_submitted=len(cochain_cdc_events),
                        events_applied=len(applied_events),
                        out_of_order_events_applied=out_of_order_applied,
                        late_events_rejected_or_quarantined=late_rejected_or_quarantined,
                        historical_bucket_mutations_on_late_events=historical_bucket_mutations,
                        total_bucket_splits=total_splits,
                        total_bucket_merges=total_merges,
                        final_watermark_timestamp=watermark_ts,
                        max_event_timestamp=max_event_ts,
                        max_observed_replica_lag_seconds=max_observed_lag,
                        poset_threshold_shifts=poset_shifts,
                        lag_anti_monotonicity_verified=False,
                        all_step_posets_monotonic=all_posets_monotonic,
                        converges_to_event_time_order=False,
                        step_receipts=tuple(step_receipts),
                        final_cochain_receipt=None,
                        final_observer_poset_receipt=s4_step,
                        certified=False,
                        reason=f"Step {idx}: INSERT missing new_g_key, new_amount, or new_row",
                    )
                candidate_rows = [dict(r) for r in current_rows] + [dict(ev.new_row)]
            elif ev.op_type == "DELETE":
                if old_g_key is None or ev.old_amount is None:
                    return WatermarkedStreamReceipt(
                        terminal_route="Invalidate",
                        canonical_terminal="Invalidate",
                        events_submitted=len(cochain_cdc_events),
                        events_applied=len(applied_events),
                        out_of_order_events_applied=out_of_order_applied,
                        late_events_rejected_or_quarantined=late_rejected_or_quarantined,
                        historical_bucket_mutations_on_late_events=historical_bucket_mutations,
                        total_bucket_splits=total_splits,
                        total_bucket_merges=total_merges,
                        final_watermark_timestamp=watermark_ts,
                        max_event_timestamp=max_event_ts,
                        max_observed_replica_lag_seconds=max_observed_lag,
                        poset_threshold_shifts=poset_shifts,
                        lag_anti_monotonicity_verified=False,
                        all_step_posets_monotonic=all_posets_monotonic,
                        converges_to_event_time_order=False,
                        step_receipts=tuple(step_receipts),
                        final_cochain_receipt=None,
                        final_observer_poset_receipt=s4_step,
                        certified=False,
                        reason=f"Step {idx}: DELETE missing old_g_key or old_amount",
                    )
                candidate_rows = [dict(r) for r in current_rows if int(r[pk_attribute]) != ev.sale_id]
            elif ev.op_type == "UPDATE":
                if (
                    old_g_key is None
                    or ev.old_amount is None
                    or new_g_key is None
                    or ev.new_amount is None
                    or ev.new_row is None
                ):
                    return WatermarkedStreamReceipt(
                        terminal_route="Invalidate",
                        canonical_terminal="Invalidate",
                        events_submitted=len(cochain_cdc_events),
                        events_applied=len(applied_events),
                        out_of_order_events_applied=out_of_order_applied,
                        late_events_rejected_or_quarantined=late_rejected_or_quarantined,
                        historical_bucket_mutations_on_late_events=historical_bucket_mutations,
                        total_bucket_splits=total_splits,
                        total_bucket_merges=total_merges,
                        final_watermark_timestamp=watermark_ts,
                        max_event_timestamp=max_event_ts,
                        max_observed_replica_lag_seconds=max_observed_lag,
                        poset_threshold_shifts=poset_shifts,
                        lag_anti_monotonicity_verified=False,
                        all_step_posets_monotonic=all_posets_monotonic,
                        converges_to_event_time_order=False,
                        step_receipts=tuple(step_receipts),
                        final_cochain_receipt=None,
                        final_observer_poset_receipt=s4_step,
                        certified=False,
                        reason=f"Step {idx}: UPDATE missing old/new group key, amount, or new_row",
                    )
                candidate_rows = [
                    dict(ev.new_row) if int(r[pk_attribute]) == ev.sale_id else dict(r)
                    for r in current_rows
                ]
            else:
                return WatermarkedStreamReceipt(
                    terminal_route="Unsupported",
                    canonical_terminal="Unsupported",
                    events_submitted=len(cochain_cdc_events),
                    events_applied=len(applied_events),
                    out_of_order_events_applied=out_of_order_applied,
                    late_events_rejected_or_quarantined=late_rejected_or_quarantined,
                    historical_bucket_mutations_on_late_events=historical_bucket_mutations,
                    total_bucket_splits=total_splits,
                    total_bucket_merges=total_merges,
                    final_watermark_timestamp=watermark_ts,
                    max_event_timestamp=max_event_ts,
                    max_observed_replica_lag_seconds=max_observed_lag,
                    poset_threshold_shifts=poset_shifts,
                    lag_anti_monotonicity_verified=False,
                    all_step_posets_monotonic=all_posets_monotonic,
                    converges_to_event_time_order=False,
                    step_receipts=tuple(step_receipts),
                    final_cochain_receipt=None,
                    final_observer_poset_receipt=s4_step,
                    certified=False,
                    reason=f"Step {idx}: unsupported CDC op_type '{ev.op_type}'",
                )

            fd_ok, fd_err = check_instance_satisfies_fds(candidate_rows, schema.dependencies)
            if not fd_ok:
                return WatermarkedStreamReceipt(
                    terminal_route="ClosureFailure",
                    canonical_terminal="ClosureFailure",
                    events_submitted=len(cochain_cdc_events),
                    events_applied=len(applied_events),
                    out_of_order_events_applied=out_of_order_applied,
                    late_events_rejected_or_quarantined=late_rejected_or_quarantined,
                    historical_bucket_mutations_on_late_events=historical_bucket_mutations,
                    total_bucket_splits=total_splits,
                    total_bucket_merges=total_merges,
                    final_watermark_timestamp=watermark_ts,
                    max_event_timestamp=max_event_ts,
                    max_observed_replica_lag_seconds=max_observed_lag,
                    poset_threshold_shifts=poset_shifts,
                    lag_anti_monotonicity_verified=False,
                    all_step_posets_monotonic=all_posets_monotonic,
                    converges_to_event_time_order=False,
                    step_receipts=tuple(step_receipts),
                    final_cochain_receipt=None,
                    final_observer_poset_receipt=s4_step,
                    certified=False,
                    reason=f"Step {idx}: FD violation on out-of-order CDC mutation: {fd_err}",
                )

            pre_snap = _snapshot_quantile_cochain(evaluator)
            current_rows = candidate_rows
            applied_events.append(ev)
            if is_ooo:
                out_of_order_applied += 1

            reb_step = evaluator.apply_sales_cdc(
                op_type=ev.op_type,
                sale_id=ev.sale_id,
                old_region=old_g_key,
                new_region=new_g_key,
                old_amount=ev.old_amount,
                new_amount=ev.new_amount,
                maintain_cochain=use_cochain,
                dynamic_buckets=dynamic_buckets,
                bucket_width=bucket_width,
                split_threshold=split_threshold,
                merge_threshold=merge_threshold,
                min_bucket_width=min_bucket_width,
            )
            step_splits = int(reb_step.get("splits_executed", 0))
            step_merges = int(reb_step.get("merges_executed", 0))
            total_splits += step_splits
            total_merges += step_merges

            step_audit = evaluator.process_bqnf_incremental_repair(
                use_cochain=use_cochain,
                track_quantiles=track_quantiles,
                quantile_tolerance=quantile_tolerance,
            )
            post_snap = _snapshot_quantile_cochain(evaluator)
            if is_ooo and post_snap != pre_snap:
                historical_bucket_mutations += 1

            if use_cochain:
                q_ok, q_errs = evaluator.verify_quantile_cochain_invariants()
                if not q_ok:
                    return WatermarkedStreamReceipt(
                        terminal_route="ClosureFailure",
                        canonical_terminal="ClosureFailure",
                        events_submitted=len(cochain_cdc_events),
                        events_applied=len(applied_events),
                        out_of_order_events_applied=out_of_order_applied,
                        late_events_rejected_or_quarantined=late_rejected_or_quarantined,
                        historical_bucket_mutations_on_late_events=historical_bucket_mutations,
                        total_bucket_splits=total_splits,
                        total_bucket_merges=total_merges,
                        final_watermark_timestamp=watermark_ts,
                        max_event_timestamp=max_event_ts,
                        max_observed_replica_lag_seconds=max_observed_lag,
                        poset_threshold_shifts=poset_shifts,
                        lag_anti_monotonicity_verified=False,
                        all_step_posets_monotonic=all_posets_monotonic,
                        converges_to_event_time_order=False,
                        step_receipts=tuple(step_receipts),
                        final_cochain_receipt=None,
                        final_observer_poset_receipt=s4_step,
                        certified=False,
                        reason=f"Step {idx}: quantile cochain invariant violation: {q_errs}",
                    )

            step_true_medians: Dict[str, Any] = {}
            for reg_k in sorted(post_snap.keys()):
                step_true_medians[reg_k] = evaluator.compute_true_median(reg_k)
            step_bucket_counts = {reg_k: len(b_list) for reg_k, b_list in post_snap.items()}

            step_receipts.append(
                WatermarkedStepReceipt(
                    step_index=idx,
                    sale_id=ev.sale_id,
                    op_type=ev.op_type,
                    event_timestamp=t_event,
                    ingestion_timestamp=t_ingest,
                    max_event_timestamp=max_event_ts,
                    watermark_timestamp=watermark_ts,
                    is_out_of_order=is_ooo,
                    event_lateness_seconds=event_lateness,
                    effective_replica_lag_seconds=effective_lag,
                    within_watermark=True,
                    cochain_step_terminal=str(step_audit["terminal"]),
                    bucket_splits_at_step=step_splits,
                    bucket_merges_at_step=step_merges,
                    active_bucket_counts=step_bucket_counts,
                    cached_medians=dict(step_audit["cached_medians"]),
                    true_medians=step_true_medians,
                    observer_poset_terminal=s4_step.terminal_route,
                    admitted_observers=s4_step.admitted_observers,
                    rejected_observers=s4_step.rejected_observers,
                    poset_monotonicity_preserved=s4_step.monotonicity_preserved,
                )
            )

    # 4. Evaluate final Stage 2b receipt on the applied stream
    final_s2b, rejoined_updated = evaluate_stage2b_cochain_extrema_quantiles(
        schema=schema,
        nf3_components=s1_receipt.nf3_components,
        initial_rows=rejoined_initial,
        cochain_cdc_events=applied_events,
        use_cochain=use_cochain,
        track_quantiles=track_quantiles,
        quantile_tolerance=quantile_tolerance,
        pk_attribute=pk_attribute,
        group_attributes=grp_tuple,
        dynamic_buckets=dynamic_buckets,
        bucket_width=bucket_width,
        split_threshold=split_threshold,
        merge_threshold=merge_threshold,
        min_bucket_width=min_bucket_width,
    )

    # 5. Verify lag-shift anti-monotonicity across all steps:
    #    lag_i <= lag_j ==> set(admitted_j) <= set(admitted_i)
    lag_anti_mono_ok = True
    obs_ids = tuple(obs.observer_id for obs in observer_poset)
    for sr in step_receipts:
        # Also verify admitted_observers is an exact upward-closed suffix of observer_poset
        adm_len = len(sr.admitted_observers)
        expected_suffix = obs_ids[len(obs_ids) - adm_len :] if adm_len > 0 else ()
        if sr.admitted_observers != expected_suffix:
            lag_anti_mono_ok = False
            break
    if lag_anti_mono_ok:
        for i in range(len(step_receipts)):
            for j in range(len(step_receipts)):
                if (
                    step_receipts[i].effective_replica_lag_seconds
                    <= step_receipts[j].effective_replica_lag_seconds + 1e-9
                ):
                    if not set(step_receipts[j].admitted_observers).issubset(
                        set(step_receipts[i].admitted_observers)
                    ):
                        lag_anti_mono_ok = False
                        break

    # 6. Verify convergence to canonical event-time ordered execution
    indexed_applied = list(enumerate(applied_events))
    event_time_sorted = [
        ev for _, ev in sorted(indexed_applied, key=lambda pair: (float(pair[1].event_timestamp or 0.0), pair[0]))
    ]
    et_s2b, _ = evaluate_stage2b_cochain_extrema_quantiles(
        schema=schema,
        nf3_components=s1_receipt.nf3_components,
        initial_rows=rejoined_initial,
        cochain_cdc_events=event_time_sorted,
        use_cochain=use_cochain,
        track_quantiles=track_quantiles,
        quantile_tolerance=quantile_tolerance,
        pk_attribute=pk_attribute,
        group_attributes=grp_tuple,
        dynamic_buckets=dynamic_buckets,
        bucket_width=bucket_width,
        split_threshold=split_threshold,
        merge_threshold=merge_threshold,
        min_bucket_width=min_bucket_width,
    )
    converges_et = bool(final_s2b.certified and et_s2b.certified)
    if converges_et:
        if set(final_s2b.cached_state.keys()) != set(et_s2b.cached_state.keys()):
            converges_et = False
        else:
            for g_k in final_s2b.cached_state:
                s_ooo = final_s2b.cached_state[g_k]
                s_et = et_s2b.cached_state[g_k]
                if int(s_ooo["count"]) != int(s_et["count"]) or abs(float(s_ooo["total"]) - float(s_et["total"])) > 1e-7:
                    converges_et = False
                e_ooo = final_s2b.cached_extrema[g_k]
                e_et = et_s2b.cached_extrema[g_k]
                if (e_ooo["min"] is None) != (e_et["min"] is None) or (e_ooo["max"] is None) != (e_et["max"] is None):
                    converges_et = False
                elif e_ooo["min"] is not None and (
                    abs(float(e_ooo["min"]) - float(e_et["min"])) > 1e-7
                    or abs(float(e_ooo["max"]) - float(e_et["max"])) > 1e-7
                ):
                    converges_et = False
                tm_ooo = final_s2b.true_medians.get(g_k)
                tm_et = et_s2b.true_medians.get(g_k)
                if (tm_ooo is None) != (tm_et is None):
                    converges_et = False
                elif tm_ooo is not None and abs(float(tm_ooo) - float(tm_et)) > 1e-7:
                    converges_et = False

    # 7. Optional Stage 3 CODA_MUR representation transport check
    s3_receipt: Optional[CodaMurTransportStageReceipt] = None
    if transport_hops is not None:
        init_totals: Dict[Any, float] = {}
        for r in rejoined_initial:
            g_k = encode_composite_group_key(r, grp_tuple)
            init_totals[g_k] = init_totals.get(g_k, 0.0) + float(r.get("amount", 0.0))
        upd_totals = {
            reg: float(st["total"])
            for reg, st in final_s2b.cached_state.items()
            if int(st.get("count", 0)) > 0 and abs(float(st["total"])) > 1e-12
        }
        s3_receipt = evaluate_stage3_coda_mur_chain(
            initial_rows=rejoined_initial,
            updated_rows=rejoined_updated,
            bqnf_initial_totals=init_totals,
            bqnf_updated_totals=upd_totals,
            hops=transport_hops,
        )
        if not s3_receipt.certified:
            return WatermarkedStreamReceipt(
                terminal_route=s3_receipt.local_route,
                canonical_terminal=s3_receipt.canonical_terminal,
                events_submitted=len(cochain_cdc_events),
                events_applied=len(applied_events),
                out_of_order_events_applied=out_of_order_applied,
                late_events_rejected_or_quarantined=late_rejected_or_quarantined,
                historical_bucket_mutations_on_late_events=historical_bucket_mutations,
                total_bucket_splits=total_splits,
                total_bucket_merges=total_merges,
                final_watermark_timestamp=watermark_ts,
                max_event_timestamp=max_event_ts,
                max_observed_replica_lag_seconds=max_observed_lag,
                poset_threshold_shifts=poset_shifts,
                lag_anti_monotonicity_verified=lag_anti_mono_ok,
                all_step_posets_monotonic=all_posets_monotonic,
                converges_to_event_time_order=converges_et,
                step_receipts=tuple(step_receipts),
                final_cochain_receipt=final_s2b,
                final_observer_poset_receipt=last_s4_receipt,
                coda_mur_receipt=s3_receipt,
                certified=False,
                reason=s3_receipt.reason,
            )

    is_certified = bool(
        final_s2b.certified
        and lag_anti_mono_ok
        and all_posets_monotonic
        and converges_et
        and (s3_receipt is None or s3_receipt.certified)
    )
    if not is_certified:
        term_route = "ClosureFailure"
        canon_term = "ClosureFailure"
    elif late_rejected_or_quarantined > 0 or (
        s3_receipt is not None and s3_receipt.canonical_terminal == "Quarantine"
    ):
        term_route = "WatermarkedQuarantine" if late_rejected_or_quarantined > 0 else final_s2b.terminal_route
        canon_term = "Quarantine"
    elif final_s2b.canonical_terminal == "Recompute":
        term_route = "Recompute"
        canon_term = "Recompute"
    else:
        term_route = "Repair"
        canon_term = "Repair"

    return WatermarkedStreamReceipt(
        terminal_route=term_route,
        canonical_terminal=canon_term,
        events_submitted=len(cochain_cdc_events),
        events_applied=len(applied_events),
        out_of_order_events_applied=out_of_order_applied,
        late_events_rejected_or_quarantined=late_rejected_or_quarantined,
        historical_bucket_mutations_on_late_events=historical_bucket_mutations,
        total_bucket_splits=total_splits,
        total_bucket_merges=total_merges,
        final_watermark_timestamp=watermark_ts,
        max_event_timestamp=max_event_ts,
        max_observed_replica_lag_seconds=max_observed_lag,
        poset_threshold_shifts=poset_shifts,
        lag_anti_monotonicity_verified=lag_anti_mono_ok,
        all_step_posets_monotonic=all_posets_monotonic,
        converges_to_event_time_order=converges_et,
        step_receipts=tuple(step_receipts),
        final_cochain_receipt=final_s2b,
        final_observer_poset_receipt=last_s4_receipt,
        coda_mur_receipt=s3_receipt,
        certified=is_certified,
        authorized=False,
        certified_implies_authorized=False,
        authority_effect="None",
        reason=None if is_certified else "Watermarked stream failed convergence or monotonicity checks",
    )


def main() -> None:
    """Demo 05: Multi-hop composition across 3NF/BCNF, BQNF cochains, CODA_MUR, and Observer Posets."""
    from dataclasses import asdict

    heading = ("sale_id", "customer_id", "customer_zip", "region", "channel", "amount", "audit_nonce")
    schema = RelationalSchema(
        attributes=frozenset(heading),
        dependencies=frozenset(
            [
                FunctionalDependency(
                    frozenset(["sale_id"]),
                    frozenset(["customer_id", "channel", "amount", "audit_nonce"]),
                ),
                FunctionalDependency.from_str("customer_id", "customer_zip"),
                FunctionalDependency.from_str("customer_zip", "region"),
            ]
        ),
        attribute_domains={a: "scalar" for a in heading},
    )
    initial_rows = [
        {
            "sale_id": 1,
            "customer_id": 10,
            "customer_zip": "10001",
            "region": "US-EAST",
            "channel": "B2B",
            "amount": 11.2,
            "audit_nonce": "n_1",
        },
        {
            "sale_id": 2,
            "customer_id": 10,
            "customer_zip": "10001",
            "region": "US-EAST",
            "channel": "B2B",
            "amount": 11.8,
            "audit_nonce": "n_2",
        },
        {
            "sale_id": 3,
            "customer_id": 10,
            "customer_zip": "10001",
            "region": "US-EAST",
            "channel": "B2B",
            "amount": 95.0,
            "audit_nonce": "n_3",
        },
    ]
    cochain_events = [
        # Destructive deletion of current MAX (95.0) resolved by priority-queue cochain in O(log K)
        SalesCochainCdcSpec(
            op_type="DELETE",
            sale_id=3,
            old_amount=95.0,
            old_row=dict(initial_rows[2]),
        ),
        # Insertion of a new sale (12.4) in composite group (US-EAST, B2B) triggering dynamic dyadic bucket split
        SalesCochainCdcSpec(
            op_type="INSERT",
            sale_id=4,
            new_amount=12.4,
            new_row={
                "sale_id": 4,
                "customer_id": 10,
                "customer_zip": "10001",
                "region": "US-EAST",
                "channel": "B2B",
                "amount": 12.4,
                "audit_nonce": "n_4",
            },
        ),
    ]
    h1_target = ("sale_id", "customer_id", "customer_zip", "region", "channel", "amount")
    h2_target = ("sale_id", "region", "channel", "amount")
    hops = [
        CodaMurHopSpec(
            hop_id="hop1_strip_audit_nonce",
            source_heading=heading,
            target_heading=h1_target,
            group_attribute="region",
            group_attributes=("region", "channel"),
            value_attribute="amount",
            loss_ledger=build_sealed_loss_ledger(["audit_nonce"], initial_rows, "sale_id"),
            target_verifier={"verifier_id": "verifier_hop1", "executed": True, "outcome": "verified"},
        ),
        CodaMurHopSpec(
            hop_id="hop2_strip_customer_pii",
            source_heading=h1_target,
            target_heading=h2_target,
            group_attribute="region",
            group_attributes=("region", "channel"),
            value_attribute="amount",
            loss_ledger=build_sealed_loss_ledger(["customer_id", "customer_zip"], initial_rows, "sale_id"),
            target_verifier={"verifier_id": "verifier_hop2", "executed": True, "outcome": "verified"},
        ),
    ]
    observer_poset = [
        ObserverSpec("obs_rt_1s", max_lag_seconds=1, authorized_scopes=("regional_sales",)),
        ObserverSpec("obs_dash_5s", max_lag_seconds=5, authorized_scopes=("regional_sales", "exec_summary")),
        ObserverSpec("obs_batch_60s", max_lag_seconds=60, authorized_scopes=("regional_sales", "exec_summary", "archive")),
    ]
    freshness_packet = {
        "value_ref": "region_sales_cache:US-EAST|B2B",
        "packet_scope": "regional_sales",
        "replica_lag_seconds": 3,
    }
    ext_receipt = run_extended_multi_hop_pipeline(
        schema=schema,
        initial_rows=initial_rows,
        cochain_cdc_events=cochain_events,
        transport_hops=hops,
        observer_poset=observer_poset,
        freshness_packet=freshness_packet,
        use_cochain=True,
        track_quantiles=True,
        quantile_tolerance=15.0,
        pk_attribute="sale_id",
        group_attributes=("region", "channel"),
        dynamic_buckets=True,
        bucket_width=10.0,
        split_threshold=2,
        merge_threshold=1,
        min_bucket_width=1.25,
    )
    print("================================================================================")
    print("DEMO 05: Extended 4-Hop Composition (Composite Keys + Dynamic Quantile Buckets)")
    print("================================================================================")
    print(json.dumps(asdict(ext_receipt), indent=2))


if __name__ == "__main__":
    main()
