"""Subsumption Lattice & Dead-Check Elimination Pass (NF-IR Layer 2).

Encodes the machine-checkable refinement partial order (NF_A <= NF_B, read
"NF_A refines / subsumes NF_B under shared scope and determinants") across:
  1. Classical Relational Hierarchy:
     nf.classical.6nf <= nf.classical.5nf <= nf.classical.4nf <= nf.classical.bcnf
     <= nf.classical.3nf <= nf.classical.2nf <= nf.classical.1nf <= nf.classical.0nf
  2. Genesis / WDP Derivation Hierarchy:
     nf.derivation.apnf <= nf.wdp.wdnf <= nf.derivation.pdnf
  3. Representation & Transport Hierarchy:
     nf.derivation.sernf <= nf.coda.mur.transport:TransportOk
     <= nf.coda.mur.transport:DegradedTransportWithLoss
     (and nf.derivation.sernf <= nf.coda.mur.transport)
  4. Kernel Determinant / Dependent Inclusion (for NFKernelSpec from Layer 1):
     In functional_dependency mode over a shared carrier and key_field:
       K_1 <= K_2  iff  collapse(K_1) subseteq collapse(K_2)
                   and  protected(K_2) subseteq protected(K_1)
                   and  subsumes_contract(K_1.contract_id, K_2.contract_id)

Provides `run_kernel_pipeline_with_dce` to eliminate redundant downstream checks
subsumed by already-admitted upstream passes while preserving exact terminal routing
and failure refusal semantics.

AuthorityEffect: None.
certified_implies_authorized: false.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from normal_forms.ir_kernel import (
    KernelEvaluationReceipt,
    NFKernelSpec,
    evaluate_nf_kernel,
)


@dataclass(frozen=True)
class SubsumptionEdge:
    """Directed refinement edge stronger_id <= weaker_id in the NF-IR subsumption poset."""

    stronger_id: str
    weaker_id: str
    family: str
    condition: str


@dataclass(frozen=True)
class ElidedCheckRecord:
    """Audit record for a downstream kernel check elided via subsumption."""

    elided_index: int
    elided_contract_id: str
    subsumed_by_index: int
    subsumed_by_contract_id: str
    reason: str


@dataclass(frozen=True)
class SubsumptionOptimizationReceipt:
    """Receipt emitted by run_kernel_pipeline_with_dce."""

    input_pass_count: int
    executed_pass_count: int
    elided_pass_count: int
    elided_records: Tuple[ElidedCheckRecord, ...]
    executed_receipts: Tuple[KernelEvaluationReceipt, ...]
    final_terminal: str
    admitted: bool
    certified: bool
    authorized: bool = False
    authority_effect: str = "None"
    certified_implies_authorized: bool = False


CANONICAL_SUBSUMPTION_EDGES: Tuple[SubsumptionEdge, ...] = (
    # Classical relational hierarchy under shared schema & dependency cover
    SubsumptionEdge(
        stronger_id="nf.classical.6nf",
        weaker_id="nf.classical.5nf",
        family="classical",
        condition="Shared relvar heading and join/key dependency cover",
    ),
    SubsumptionEdge(
        stronger_id="nf.classical.5nf",
        weaker_id="nf.classical.4nf",
        family="classical",
        condition="Shared relvar heading; every MVD is an implied JD",
    ),
    SubsumptionEdge(
        stronger_id="nf.classical.4nf",
        weaker_id="nf.classical.bcnf",
        family="classical",
        condition="Shared relvar heading; every FD is a single-valued MVD",
    ),
    SubsumptionEdge(
        stronger_id="nf.classical.bcnf",
        weaker_id="nf.classical.3nf",
        family="classical",
        condition="Shared relvar heading and functional dependency cover",
    ),
    SubsumptionEdge(
        stronger_id="nf.classical.3nf",
        weaker_id="nf.classical.2nf",
        family="classical",
        condition="Shared relvar heading and candidate key set",
    ),
    SubsumptionEdge(
        stronger_id="nf.classical.2nf",
        weaker_id="nf.classical.1nf",
        family="classical",
        condition="Shared relvar heading with atomic attribute domains",
    ),
    SubsumptionEdge(
        stronger_id="nf.classical.1nf",
        weaker_id="nf.classical.0nf",
        family="classical",
        condition="Every 1NF relation is a valid 0NF relation",
    ),
    # Genesis / WDP derivation hierarchy under shared carrier & distinction relation
    SubsumptionEdge(
        stronger_id="nf.derivation.apnf",
        weaker_id="nf.wdp.wdnf",
        family="derivation_wdp",
        condition="Constructive apartness (irreflexive, symmetric, cotransitive) on |X| >= 2 implies witnessed irreflexive cut",
    ),
    SubsumptionEdge(
        stronger_id="nf.wdp.wdnf",
        weaker_id="nf.derivation.pdnf",
        family="derivation_wdp",
        condition="WDP Level 00 admitted cut satisfies PDNF witnessed irreflexive difference",
    ),
    SubsumptionEdge(
        stronger_id="nf.derivation.pdnf",
        weaker_id="nf.derivation.obnf",
        family="derivation_wdp",
        condition="Shared carrier and protected determinant law",
    ),
    # Representation & CODA_MUR transport hierarchy
    SubsumptionEdge(
        stronger_id="nf.derivation.sernf",
        weaker_id="nf.coda.mur.transport:TransportOk",
        family="representation_transport",
        condition="Split extension-retraction (r_N o u_N = id) implies lossless representation transport",
    ),
    SubsumptionEdge(
        stronger_id="nf.coda.mur.transport:TransportOk",
        weaker_id="nf.coda.mur.transport:DegradedTransportWithLoss",
        family="representation_transport",
        condition="Lossless transport (zero erased fields) trivially satisfies loss-ledgered transport",
    ),
    SubsumptionEdge(
        stronger_id="nf.derivation.sernf",
        weaker_id="nf.coda.mur.transport",
        family="representation_transport",
        condition="Split extension-retraction satisfies CODA_MUR representation transport",
    ),
)


def _build_reachability_map(
    edges: Sequence[SubsumptionEdge],
) -> Dict[str, Set[str]]:
    """Computes the reflexive-transitive closure of the subsumption edge relation."""
    adj: Dict[str, Set[str]] = {}
    nodes: Set[str] = set()
    for e in edges:
        nodes.add(e.stronger_id)
        nodes.add(e.weaker_id)
        adj.setdefault(e.stronger_id, set()).add(e.weaker_id)
        adj.setdefault(e.weaker_id, set())

    closure: Dict[str, Set[str]] = {}
    for start in nodes:
        visited: Set[str] = {start}
        stack: List[str] = [start]
        while stack:
            curr = stack.pop()
            for nxt in adj.get(curr, ()):
                if nxt not in visited:
                    visited.add(nxt)
                    stack.append(nxt)
        closure[start] = visited
    return closure


def verify_subsumption_poset_laws(
    edges: Optional[Sequence[SubsumptionEdge]] = None,
) -> Tuple[bool, List[str]]:
    """Verifies reflexivity, antisymmetry (acyclicity), and transitivity of the subsumption poset."""
    active_edges = tuple(edges) if edges is not None else CANONICAL_SUBSUMPTION_EDGES
    violations: List[str] = []

    # Check direct self-loops if any edge has stronger_id == weaker_id
    for e in active_edges:
        if e.stronger_id == e.weaker_id:
            violations.append(
                f"Explicit self-loop edge not permitted: {e.stronger_id} <= {e.weaker_id}"
            )

    closure = _build_reachability_map(active_edges)

    # 1. Reflexivity: every node reaches itself
    for node, reach in closure.items():
        if node not in reach:
            violations.append(f"Reflexivity failed for node '{node}'")

    # 2. Antisymmetry: if A <= B and B <= A then A == B
    all_nodes = sorted(closure.keys())
    for i, a in enumerate(all_nodes):
        for b in all_nodes[i + 1 :]:
            if b in closure.get(a, set()) and a in closure.get(b, set()):
                violations.append(
                    f"Antisymmetry violation (cycle detected): '{a}' <= '{b}' and '{b}' <= '{a}'"
                )

    # 3. Transitivity: if A <= B and B <= C then A <= C in closure
    for a in all_nodes:
        for b in list(closure.get(a, set())):
            for c in list(closure.get(b, set())):
                if c not in closure.get(a, set()):
                    violations.append(
                        f"Transitivity violation: '{a}' <= '{b}' and '{b}' <= '{c}', but '{c}' not in reach('{a}')"
                    )

    return len(violations) == 0, violations


def subsumes_contract(
    stronger_id: str,
    weaker_id: str,
    edges: Optional[Sequence[SubsumptionEdge]] = None,
) -> bool:
    """Returns True iff stronger_id <= weaker_id in the reflexive-transitive subsumption poset."""
    if stronger_id == weaker_id:
        return True
    active_edges = tuple(edges) if edges is not None else CANONICAL_SUBSUMPTION_EDGES
    closure = _build_reachability_map(active_edges)
    return weaker_id in closure.get(stronger_id, set())


def subsumes_kernel_spec(
    stronger: NFKernelSpec,
    weaker: NFKernelSpec,
    edges: Optional[Sequence[SubsumptionEdge]] = None,
) -> Tuple[bool, str]:
    """Determines whether an admitted `stronger` NFKernelSpec logically subsumes `weaker`.

    Soundness requirements:
      1. Shared key_field and law_mode.
      2. Support floor, irreflexivity, and protected-law declaration flags on `stronger`
         must be at least as strict as on `weaker`.
      3. Contract IDs must satisfy subsumes_contract(stronger.contract_id, weaker.contract_id).
      4. Mode-specific structural refinement:
         - In "functional_dependency" mode:
             collapse(stronger) subseteq collapse(weaker)
             and protected(weaker) subseteq protected(stronger)
             and collapse(weaker) subseteq (collapse(stronger) union protected(stronger) union distinction(stronger))
           Why: if r_1[X_2] == r_2[X_2] and X_1 subseteq X_2, then r_1[X_1] == r_2[X_1],
           so stronger's FD X_1 -> Y_1 forces r_1[Y_1] == r_2[Y_1], which forces r_1[Y_2] == r_2[Y_2]
           for any Y_2 subseteq Y_1.
         - In "representation_transport" mode:
             distinction(stronger) == distinction(weaker)
             and collapse(stronger) == collapse(weaker)
             and protected(stronger) == protected(weaker)
             and require_loss_ledger_on_admissible_collision matches.
    """
    if stronger.key_field != weaker.key_field:
        return False, f"Key field mismatch: {stronger.key_field} != {weaker.key_field}"

    if stronger.law_mode != weaker.law_mode:
        return False, f"Law mode mismatch: {stronger.law_mode} != {weaker.law_mode}"

    if weaker.require_support_floor and not stronger.require_support_floor:
        return False, "Weaker spec requires support floor |X| >= 2, but stronger spec does not."

    if weaker.require_irreflexivity_declaration and not stronger.require_irreflexivity_declaration:
        return False, "Weaker spec requires irreflexivity declaration, but stronger spec does not."

    if weaker.require_protected_law_declaration and (
        not stronger.require_protected_law_declaration or not weaker.protected_law_fields
    ):
        return False, "Weaker spec requires protected law declaration that is absent."

    if not subsumes_contract(stronger.contract_id, weaker.contract_id, edges=edges):
        return (
            False,
            f"Contract '{stronger.contract_id}' does not subsume '{weaker.contract_id}'.",
        )

    if stronger.law_mode == "functional_dependency":
        s_col = set(stronger.collapse_fields)
        w_col = set(weaker.collapse_fields)
        s_prot = set(stronger.protected_law_fields)
        w_prot = set(weaker.protected_law_fields)
        s_known = s_col | s_prot

        if not s_col.issubset(w_col):
            return (
                False,
                f"Determinant {stronger.collapse_fields} is not a subset of {weaker.collapse_fields}.",
            )
        if not w_prot.issubset(s_prot):
            return (
                False,
                f"Dependent {weaker.protected_law_fields} is not a subset of {stronger.protected_law_fields}.",
            )
        # Ensure weaker's collapse fields were already verified to exist on every row by stronger
        if not w_col.issubset(s_known):
            return (
                False,
                f"Weaker determinant {weaker.collapse_fields} references attributes outside stronger checked set {sorted(s_known)}.",
            )
        return (
            True,
            (
                f"{stronger.contract_id}({list(stronger.collapse_fields)}->{list(stronger.protected_law_fields)}) "
                f"subsumes {weaker.contract_id}({list(weaker.collapse_fields)}->{list(weaker.protected_law_fields)})."
            ),
        )

    if stronger.law_mode == "representation_transport":
        if (
            stronger.distinction_fields == weaker.distinction_fields
            and stronger.collapse_fields == weaker.collapse_fields
            and stronger.protected_law_fields == weaker.protected_law_fields
            and stronger.require_loss_ledger_on_admissible_collision
            == weaker.require_loss_ledger_on_admissible_collision
        ):
            return (
                True,
                f"{stronger.contract_id} subsumes identical transport spec {weaker.contract_id}.",
            )
        return False, "Representation transport specs differ on source, target, or protected fields."

    return False, f"Unsupported law_mode for subsumption: {stronger.law_mode}"


def run_kernel_pipeline_with_dce(
    specs: Sequence[NFKernelSpec],
    carrier_rows: Sequence[Mapping[str, Any]],
    enable_dce: bool = True,
    edges: Optional[Sequence[SubsumptionEdge]] = None,
) -> SubsumptionOptimizationReceipt:
    """Executes a sequence of NFKernelSpec passes with optional dead-check elimination (DCE).

    When enable_dce=True, any pass specs[j] that is subsumed by an earlier admitted pass
    specs[i] (i < j) is skipped without re-evaluating carrier_rows, and recorded in
    elided_records. Stops fail-closed on the first pass where admitted == False.
    """
    if not specs:
        return SubsumptionOptimizationReceipt(
            input_pass_count=0,
            executed_pass_count=0,
            elided_pass_count=0,
            elided_records=(),
            executed_receipts=(),
            final_terminal="Preserve",
            admitted=True,
            certified=True,
        )

    admitted_passes: List[Tuple[int, NFKernelSpec, KernelEvaluationReceipt]] = []
    executed_receipts: List[KernelEvaluationReceipt] = []
    elided_records: List[ElidedCheckRecord] = []

    for idx, spec in enumerate(specs):
        if enable_dce:
            subsuming_hit: Optional[Tuple[int, NFKernelSpec, str]] = None
            for prev_idx, prev_spec, _ in admitted_passes:
                ok_sub, reason_sub = subsumes_kernel_spec(
                    prev_spec,
                    spec,
                    edges=edges,
                )
                if ok_sub:
                    subsuming_hit = (prev_idx, prev_spec, reason_sub)
                    break

            if subsuming_hit is not None:
                p_idx, p_spec, p_reason = subsuming_hit
                elided_records.append(
                    ElidedCheckRecord(
                        elided_index=idx,
                        elided_contract_id=spec.contract_id,
                        subsumed_by_index=p_idx,
                        subsumed_by_contract_id=p_spec.contract_id,
                        reason=p_reason,
                    )
                )
                continue

        receipt = evaluate_nf_kernel(spec, carrier_rows)
        executed_receipts.append(receipt)
        if not receipt.admitted:
            return SubsumptionOptimizationReceipt(
                input_pass_count=len(specs),
                executed_pass_count=len(executed_receipts),
                elided_pass_count=len(elided_records),
                elided_records=tuple(elided_records),
                executed_receipts=tuple(executed_receipts),
                final_terminal=receipt.canonical_terminal,
                admitted=False,
                certified=False,
            )

        admitted_passes.append((idx, spec, receipt))

    # Determine final terminal across admitted passes (Quarantine takes precedence over Preserve)
    final_term = "Preserve"
    for r in executed_receipts:
        if r.canonical_terminal == "Quarantine":
            final_term = "Quarantine"
            break

    return SubsumptionOptimizationReceipt(
        input_pass_count=len(specs),
        executed_pass_count=len(executed_receipts),
        elided_pass_count=len(elided_records),
        elided_records=tuple(elided_records),
        executed_receipts=tuple(executed_receipts),
        final_terminal=final_term,
        admitted=True,
        certified=True,
    )
