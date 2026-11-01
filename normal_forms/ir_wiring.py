"""Operadic Pipeline Wiring Compiler (NF-IR Layer 3).

Composes NFKernelSpec passes into sequential (`seq_passes`), parallel (`par_passes`),
and authority-guarded (`guard_pass`) multi-hop DAGs over the canonical terminal
severity join semilattice:

    Preserve (0) < Repair (1) < Quarantine (2)
        < Recompute (3) < Invalidate (4) < Reject (5) < Refuse (6)

Key invariants:
  1. Associativity of sequential wiring:
       eval(seq(seq(A, B), C)) == eval(seq(A, seq(B, C))) == eval(seq(A, B, C))
  2. Fail-closed short-circuiting in `seq_passes` on the first blocking terminal
     (Recompute, Invalidate, Reject, Refuse), integrated with Layer 2 dead-check
     elimination (`subsumes_kernel_spec`).
  3. Commutativity of terminal severity join and counterexample / loss-chain
     merging in `par_passes`.
  4. Cryptographic SHA-256 Merkle loss-chain accumulation across multi-hop
     `CODA_MUR` lossy projections (`MerkleLossChainEntry`, `loss_chain_head_digest`).
  5. Strict separation of certification from authorization (`AuthorityEffect: None`,
     `certified_implies_authorized: false`): `leaf_pass`, `seq_passes`, and
     `par_passes` always emit `authorized=False`; only `guard_pass` with an
     independent `policy_verifier` (`verifier_identity != producer_identity` and
     `outcome == "authorized"`) sets `authorized=True`.

AuthorityEffect: None.
certified_implies_authorized: false.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from normal_forms.ir_kernel import (
    ConstructiveWitnessPair,
    KernelEvaluationReceipt,
    NFKernelSpec,
    evaluate_nf_kernel,
)
from normal_forms.ir_subsumption import (
    ElidedCheckRecord,
    subsumes_kernel_spec,
)

TERMINAL_SEVERITY_RANK: Dict[str, int] = {
    "Preserve": 0,
    "Repair": 1,
    "Quarantine": 2,
    "Recompute": 3,
    "Invalidate": 4,
    "Reject": 5,
    "Refuse": 6,
}

ADMITTED_TERMINALS = frozenset({"Preserve", "Repair", "Quarantine"})


def join_canonical_terminals(terminals: Sequence[str]) -> str:
    """Computes the least upper bound (join) in the canonical terminal severity semilattice."""
    if not terminals:
        return "Preserve"
    best = "Preserve"
    best_rank = -1
    for t in terminals:
        rank = TERMINAL_SEVERITY_RANK.get(t, 6)
        if rank > best_rank:
            best_rank = rank
            best = t
    return best


def is_admitted_terminal(terminal: str) -> bool:
    """Returns True iff the canonical terminal is in the admitted sub-semilattice."""
    return terminal in ADMITTED_TERMINALS


@dataclass(frozen=True)
class NFWiringNode:
    """AST node for an operadic normal-form wiring DAG."""

    kind: str  # "leaf", "seq", "par", "guard"
    spec: Optional[NFKernelSpec] = None
    children: Tuple["NFWiringNode", ...] = ()
    enable_dce: bool = True
    policy_verifier: Any = None
    producer_identity: str = "nf_wiring_producer"


@dataclass(frozen=True)
class MerkleLossChainEntry:
    """One hop in a cumulative SHA-256 Merkle chain of CODA_MUR LossLedgers."""

    step_index: int
    contract_id: str
    erased_attributes: Tuple[str, ...]
    ledger_digest: str
    cumulative_chain_digest: str


@dataclass(frozen=True)
class WiringEvaluationReceipt:
    """Receipt emitted by evaluate_wiring_dag."""

    node_kind: str
    executed_specs_count: int
    elided_specs_count: int
    leaf_receipts: Tuple[KernelEvaluationReceipt, ...]
    elided_records: Tuple[ElidedCheckRecord, ...]
    loss_chain: Tuple[MerkleLossChainEntry, ...]
    loss_chain_head_digest: Optional[str]
    counterexamples: Tuple[ConstructiveWitnessPair, ...]
    canonical_terminal: str
    admitted: bool
    certified: bool
    authorized: bool = False
    authorization_status: str = "certified_not_authorized"
    authority_effect: str = "None"
    certified_implies_authorized: bool = False
    reason: str = ""


def leaf_pass(spec: NFKernelSpec) -> NFWiringNode:
    """Wraps a single NFKernelSpec as an atomic wiring node."""
    return NFWiringNode(kind="leaf", spec=spec)


def seq_passes(*nodes: NFWiringNode, enable_dce: bool = True) -> NFWiringNode:
    """Composes wiring nodes sequentially with fail-closed short-circuiting and optional DCE."""
    return NFWiringNode(kind="seq", children=tuple(nodes), enable_dce=enable_dce)


def par_passes(*nodes: NFWiringNode) -> NFWiringNode:
    """Composes wiring nodes in parallel fan-out / fan-in over the terminal severity semilattice."""
    return NFWiringNode(kind="par", children=tuple(nodes), enable_dce=False)


def guard_pass(
    node: NFWiringNode,
    policy_verifier: Any,
    producer_identity: str = "nf_wiring_producer",
) -> NFWiringNode:
    """Wraps a wiring DAG in an epistemic authority firewall gate."""
    return NFWiringNode(
        kind="guard",
        children=(node,),
        policy_verifier=policy_verifier,
        producer_identity=producer_identity,
    )


def _advance_merkle_chain(
    prev_head: Optional[str],
    step_index: int,
    contract_id: str,
    erased_attributes: Sequence[str],
    ledger_digest: str,
) -> MerkleLossChainEntry:
    genesis_prefix = prev_head if prev_head is not None else ("0" * 64)
    erased_tuple = tuple(sorted(erased_attributes))
    payload = f"{genesis_prefix}:{contract_id}:{','.join(erased_tuple)}:{ledger_digest}"
    cumulative = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return MerkleLossChainEntry(
        step_index=step_index,
        contract_id=contract_id,
        erased_attributes=erased_tuple,
        ledger_digest=ledger_digest,
        cumulative_chain_digest=cumulative,
    )


def _witness_sort_key(w: ConstructiveWitnessPair) -> Tuple[str, str, str, str, str, str]:
    return (
        w.left_id,
        w.right_id,
        w.witness_kind,
        w.feature,
        repr(w.left_value),
        repr(w.right_value),
    )


@dataclass
class _SeqState:
    """Mutable accumulator threaded across sequential wiring passes to preserve strict associativity."""

    admitted_specs: List[Tuple[int, NFKernelSpec]] = field(default_factory=list)
    leaf_receipts: List[KernelEvaluationReceipt] = field(default_factory=list)
    elided_records: List[ElidedCheckRecord] = field(default_factory=list)
    loss_chain: List[MerkleLossChainEntry] = field(default_factory=list)
    counterexamples: List[ConstructiveWitnessPair] = field(default_factory=list)
    terminals: List[str] = field(default_factory=list)
    step_counter: int = 0
    halted: bool = False
    halt_reason: str = ""

    @property
    def head_digest(self) -> Optional[str]:
        return self.loss_chain[-1].cumulative_chain_digest if self.loss_chain else None


def _eval_into_seq_state(
    node: NFWiringNode,
    carrier_rows: Sequence[Mapping[str, Any]],
    state: _SeqState,
    active_dce: bool,
) -> None:
    if state.halted:
        return

    if node.kind == "leaf":
        assert node.spec is not None
        spec = node.spec
        curr_idx = state.step_counter
        state.step_counter += 1

        if active_dce:
            for prev_idx, prev_spec in state.admitted_specs:
                ok_sub, reason_sub = subsumes_kernel_spec(prev_spec, spec)
                if ok_sub:
                    state.elided_records.append(
                        ElidedCheckRecord(
                            elided_index=curr_idx,
                            elided_contract_id=spec.contract_id,
                            subsumed_by_index=prev_idx,
                            subsumed_by_contract_id=prev_spec.contract_id,
                            reason=reason_sub,
                        )
                    )
                    return

        receipt = evaluate_nf_kernel(spec, carrier_rows)
        state.leaf_receipts.append(receipt)
        state.terminals.append(receipt.canonical_terminal)

        if receipt.loss_ledger is not None and receipt.loss_ledger.get("merkle_digest"):
            entry = _advance_merkle_chain(
                prev_head=state.head_digest,
                step_index=len(state.loss_chain),
                contract_id=spec.contract_id,
                erased_attributes=receipt.loss_ledger.get("erased_attributes", ()),
                ledger_digest=str(receipt.loss_ledger["merkle_digest"]),
            )
            state.loss_chain.append(entry)

        if not receipt.admitted:
            if receipt.minimal_counterexample is not None:
                state.counterexamples.append(receipt.minimal_counterexample)
            state.halted = True
            state.halt_reason = receipt.reason
            return

        state.admitted_specs.append((curr_idx, spec))
        return

    if node.kind == "seq":
        child_dce = active_dce and node.enable_dce
        for child in node.children:
            _eval_into_seq_state(child, carrier_rows, state, child_dce)
            if state.halted:
                return
        return

    # For "par" or "guard" inside a sequential chain, evaluate standalone and fold into state
    sub_receipt = evaluate_wiring_dag(node, carrier_rows)
    state.step_counter += sub_receipt.executed_specs_count + sub_receipt.elided_specs_count
    state.leaf_receipts.extend(sub_receipt.leaf_receipts)
    state.elided_records.extend(sub_receipt.elided_records)
    state.terminals.append(sub_receipt.canonical_terminal)

    for l_entry in sub_receipt.loss_chain:
        chained = _advance_merkle_chain(
            prev_head=state.head_digest,
            step_index=len(state.loss_chain),
            contract_id=l_entry.contract_id,
            erased_attributes=l_entry.erased_attributes,
            ledger_digest=l_entry.ledger_digest,
        )
        state.loss_chain.append(chained)

    if not sub_receipt.admitted:
        state.counterexamples.extend(sub_receipt.counterexamples)
        state.halted = True
        state.halt_reason = sub_receipt.reason


def evaluate_wiring_dag(
    root: NFWiringNode,
    carrier_rows: Sequence[Mapping[str, Any]],
) -> WiringEvaluationReceipt:
    """Evaluates an operadic NFWiringNode DAG over carrier_rows."""
    if root.kind in ("leaf", "seq"):
        state = _SeqState()
        _eval_into_seq_state(
            node=root,
            carrier_rows=carrier_rows,
            state=state,
            active_dce=(root.enable_dce if root.kind == "seq" else False),
        )
        final_term = join_canonical_terminals(state.terminals)
        admitted = not state.halted and is_admitted_terminal(final_term)
        return WiringEvaluationReceipt(
            node_kind=root.kind,
            executed_specs_count=len(state.leaf_receipts),
            elided_specs_count=len(state.elided_records),
            leaf_receipts=tuple(state.leaf_receipts),
            elided_records=tuple(state.elided_records),
            loss_chain=tuple(state.loss_chain),
            loss_chain_head_digest=state.head_digest,
            counterexamples=tuple(state.counterexamples),
            canonical_terminal=final_term,
            admitted=admitted,
            certified=admitted,
            authorized=False,
            authorization_status="certified_not_authorized" if admitted else "rejected",
            reason=state.halt_reason if state.halted else "Sequential wiring admitted.",
        )

    if root.kind == "par":
        branch_receipts = [evaluate_wiring_dag(c, carrier_rows) for c in root.children]
        all_leafs: List[KernelEvaluationReceipt] = []
        all_elided: List[ElidedCheckRecord] = []
        raw_loss_entries: List[Tuple[str, str, Tuple[str, ...]]] = []
        raw_cxs: List[ConstructiveWitnessPair] = []
        branch_terminals: List[str] = []
        reasons: List[str] = []

        for br in branch_receipts:
            all_leafs.extend(br.leaf_receipts)
            all_elided.extend(br.elided_records)
            branch_terminals.append(br.canonical_terminal)
            raw_cxs.extend(br.counterexamples)
            if not br.admitted and br.reason:
                reasons.append(br.reason)
            for le in br.loss_chain:
                raw_loss_entries.append(
                    (le.ledger_digest, le.contract_id, le.erased_attributes)
                )

        # Canonical sort for commutativity across parallel branches
        raw_loss_entries.sort(key=lambda item: (item[0], item[1], item[2]))
        merged_loss_chain: List[MerkleLossChainEntry] = []
        prev_head: Optional[str] = None
        for idx, (ldig, cid, e_attrs) in enumerate(raw_loss_entries):
            entry = _advance_merkle_chain(
                prev_head=prev_head,
                step_index=idx,
                contract_id=cid,
                erased_attributes=e_attrs,
                ledger_digest=ldig,
            )
            merged_loss_chain.append(entry)
            prev_head = entry.cumulative_chain_digest

        sorted_cxs = tuple(sorted(raw_cxs, key=_witness_sort_key))
        joined_term = join_canonical_terminals(branch_terminals)
        admitted = all(br.admitted for br in branch_receipts) and is_admitted_terminal(
            joined_term
        )
        return WiringEvaluationReceipt(
            node_kind="par",
            executed_specs_count=len(all_leafs),
            elided_specs_count=len(all_elided),
            leaf_receipts=tuple(all_leafs),
            elided_records=tuple(all_elided),
            loss_chain=tuple(merged_loss_chain),
            loss_chain_head_digest=prev_head,
            counterexamples=sorted_cxs,
            canonical_terminal=joined_term,
            admitted=admitted,
            certified=admitted,
            authorized=False,
            authorization_status="certified_not_authorized" if admitted else "rejected",
            reason="; ".join(reasons) if reasons else "Parallel wiring admitted.",
        )

    if root.kind == "guard":
        if not root.children:
            raise ValueError("guard node requires one child NFWiringNode")
        inner = evaluate_wiring_dag(root.children[0], carrier_rows)
        if not inner.admitted or not inner.certified:
            return WiringEvaluationReceipt(
                node_kind="guard",
                executed_specs_count=inner.executed_specs_count,
                elided_specs_count=inner.elided_specs_count,
                leaf_receipts=inner.leaf_receipts,
                elided_records=inner.elided_records,
                loss_chain=inner.loss_chain,
                loss_chain_head_digest=inner.loss_chain_head_digest,
                counterexamples=inner.counterexamples,
                canonical_terminal=inner.canonical_terminal,
                admitted=False,
                certified=False,
                authorized=False,
                authorization_status="rejected_upstream",
                reason=inner.reason,
            )

        pv = root.policy_verifier
        if isinstance(pv, str):
            return WiringEvaluationReceipt(
                node_kind="guard",
                executed_specs_count=inner.executed_specs_count,
                elided_specs_count=inner.elided_specs_count,
                leaf_receipts=inner.leaf_receipts,
                elided_records=inner.elided_records,
                loss_chain=inner.loss_chain,
                loss_chain_head_digest=inner.loss_chain_head_digest,
                counterexamples=inner.counterexamples,
                canonical_terminal="Refuse",
                admitted=False,
                certified=True,
                authorized=False,
                authorization_status="unauthenticated_verifier_string",
                reason="Bare string policy_verifier refused; independent verifier record required.",
            )

        if not isinstance(pv, Mapping):
            return WiringEvaluationReceipt(
                node_kind="guard",
                executed_specs_count=inner.executed_specs_count,
                elided_specs_count=inner.elided_specs_count,
                leaf_receipts=inner.leaf_receipts,
                elided_records=inner.elided_records,
                loss_chain=inner.loss_chain,
                loss_chain_head_digest=inner.loss_chain_head_digest,
                counterexamples=inner.counterexamples,
                canonical_terminal="Refuse",
                admitted=True,
                certified=True,
                authorized=False,
                authorization_status="certified_not_authorized",
                reason="Wiring DAG is certified, but policy_verifier is absent.",
            )

        verifier_id = str(pv.get("verifier_identity", "")).strip()
        outcome = str(pv.get("outcome", "")).strip()

        if not verifier_id or verifier_id == root.producer_identity:
            return WiringEvaluationReceipt(
                node_kind="guard",
                executed_specs_count=inner.executed_specs_count,
                elided_specs_count=inner.elided_specs_count,
                leaf_receipts=inner.leaf_receipts,
                elided_records=inner.elided_records,
                loss_chain=inner.loss_chain,
                loss_chain_head_digest=inner.loss_chain_head_digest,
                counterexamples=inner.counterexamples,
                canonical_terminal="Refuse",
                admitted=False,
                certified=True,
                authorized=False,
                authorization_status="self_authorized_violation",
                reason=(
                    f"Policy verifier identity '{verifier_id}' is missing or matches "
                    f"producer_identity '{root.producer_identity}'."
                ),
            )

        if outcome != "authorized":
            return WiringEvaluationReceipt(
                node_kind="guard",
                executed_specs_count=inner.executed_specs_count,
                elided_specs_count=inner.elided_specs_count,
                leaf_receipts=inner.leaf_receipts,
                elided_records=inner.elided_records,
                loss_chain=inner.loss_chain,
                loss_chain_head_digest=inner.loss_chain_head_digest,
                counterexamples=inner.counterexamples,
                canonical_terminal="Refuse",
                admitted=True,
                certified=True,
                authorized=False,
                authorization_status="certified_not_authorized",
                reason=f"Policy verifier outcome is '{outcome}' (requires 'authorized').",
            )

        return WiringEvaluationReceipt(
            node_kind="guard",
            executed_specs_count=inner.executed_specs_count,
            elided_specs_count=inner.elided_specs_count,
            leaf_receipts=inner.leaf_receipts,
            elided_records=inner.elided_records,
            loss_chain=inner.loss_chain,
            loss_chain_head_digest=inner.loss_chain_head_digest,
            counterexamples=inner.counterexamples,
            canonical_terminal=inner.canonical_terminal,
            admitted=True,
            certified=True,
            authorized=True,
            authorization_status="authorized",
            reason=f"Authorized by independent policy_verifier '{verifier_id}'.",
        )

    raise ValueError(f"Unsupported NFWiringNode kind: {root.kind!r}")
