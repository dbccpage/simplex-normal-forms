"""AI / RAG / MCP normal-form decorator layer and Witnessed Difference (WDNF/PDNF) pipeline.

Provides executable decorators and stage evaluators for AI retrieval-augmented generation
(RAG) context compression and Model Context Protocol (MCP) tool-call gating:

1. Stage 0 (Level 00 Admitted Cut — ``nf.wdp.wdnf`` / ``nf.derivation.pdnf`` / ``nf.derivation.obnf``):
   - ``evaluate_wdnf_candidate_cut``: Checks that a retrieved candidate carrier satisfies the
     support floor (|X| >= 2), irreflexivity (no self-difference x != x), and constructive
     witness presence (every asserted distinction carries at least one concrete witness while
     witness multiplicity is normalized to boolean presence).
   - ``evaluate_obnf_projection_collision``: Evaluates Obstruction Relativization Normal Form
     (``nf.derivation.obnf``) when a projection map collapses distinct witnessed chunks,
     recording the colliding pair witness and promoting the collision to an obstruction if and
     only if it violates a declared protected determinant law.

2. Stage 1 (In Representation — ``@coda_mur_projection``, ``nf.coda.mur.transport`` & ``nf.representation.tbnf``):
   - Wraps RAG context projection and token-budget truncation functions.
   - Tracks attribute erasure (``coda_mur.unmapped_field_drop``), per-chunk token truncation
     (``coda_mur.context_token_truncation``), and whole-chunk budget eviction in a single
     SHA-256 Merkle-sealed ``LossLedger``.
   - Enforces exact token conservation (``retained_tokens + truncated_tokens == source_tokens``)
     and fails closed (``TransportViolation`` -> ``Reject``) if any protected grounding
     determinant is dropped, nullified, mutated, or collides across distinct keys.

3. Stage 2 (In Observation & Recursion — ``@observer_freshness_gate``, ``nf.epistemic.freshness`` & ``nf.recursion.asrf``):
   - Wraps MCP tool handlers and RAG action synthesizers with four fail-closed gates:
     (a) ``CODA_MUR`` envelope & cryptographic ``LossLedger`` seal verification,
     (b) ``ASRF`` autopoietic self-reference refusal (producer != evaluator, caller_hash !=
         target_content_hash, directed call-graph acyclicity, bounded recursion depth),
     (c) Observer-relative freshness poset evaluation (stringency ordering O_1 <= ... <= O_m,
         explicit packet_scope authorization, SLA lag budget, upward poset monotonicity),
     (d) Epistemic authority firewall (``AuthorityEffect: None``, ``certified_implies_authorized: false``):
         a certified, fresh context envelope stays ``certified_not_authorized`` and cannot
         execute an MCP tool unless an explicit, independent ``policy_verifier`` record
         (with ``verifier_identity != producer_identity`` and ``outcome == "authorized"``)
         is supplied.

AuthorityEffect: None.
certified_implies_authorized: false.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import functools
import hashlib
import json
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from normal_forms.observer_freshness_example import (
    ObserverSpec,
    evaluate_freshness,
    verify_observer_lattice_monotonicity,
)
from normal_forms.reconciliation_example import verify_loss_ledger_integrity
from normal_forms.sn_forms import evaluate_sn_pdnf

CODA_MUR_CONTEXT_TRIGGER_ID = "coda_mur.context_truncation_and_field_drop"


def tokenize_whitespace(text: str) -> List[str]:
    """Deterministic whitespace tokenizer for token-bounded normal form (TBNF) accounting."""
    if not text:
        return []
    return text.split()


def detokenize_whitespace(tokens: Sequence[str]) -> str:
    """Inverse whitespace join over a token sequence."""
    return " ".join(tokens)


@dataclass(frozen=True)
class WitnessedDifference:
    """A constructive witness that element left_id and right_id differ on a declared feature."""

    left_id: str
    right_id: str
    witness_feature: str
    left_value: Any
    right_value: Any
    multiplicity: int = 1


@dataclass(frozen=True)
class WdnfEvaluationReceipt:
    """Receipt for WDP Level 00 Admitted Cut (nf.wdp.wdnf / nf.derivation.pdnf)."""

    contract_id: str
    carrier_ids: Tuple[str, ...]
    carrier_size: int
    witnessed_differences: Tuple[WitnessedDifference, ...]
    normalized_distinction_pairs: Tuple[Tuple[str, str], ...]
    witness_multiplicity_erased: bool
    local_terminal: str
    canonical_terminal: str
    admitted: bool
    certified: bool
    authorized: bool
    reason: str
    offending_pair: Optional[Tuple[str, str]] = None
    authority_effect: str = "None"


@dataclass(frozen=True)
class ObnfCollisionReceipt:
    """Receipt for Obstruction Relativization Normal Form (nf.derivation.obnf) under projection."""

    contract_id: str
    protected_law: Tuple[str, ...]
    colliding_pairs: Tuple[Tuple[str, str], ...]
    violates_protected_law: bool
    local_terminal: str
    canonical_terminal: str
    admitted: bool
    reason: str
    authority_effect: str = "None"


@dataclass(frozen=True)
class CodaMurContextEnvelope:
    """Certified envelope emitted by @coda_mur_projection for RAG context transport."""

    contract_id: str
    source_fields: Tuple[str, ...]
    target_fields: Tuple[str, ...]
    key_field: str
    protected_fields: Tuple[str, ...]
    erased_attributes: Tuple[str, ...]
    max_token_budget: Optional[int]
    source_chunk_count: int
    retained_chunk_count: int
    dropped_chunk_count: int
    source_token_count: int
    retained_token_count: int
    truncated_token_count: int
    token_conservation_commutes: bool
    score_conservation_commutes: bool
    projected_chunks: Tuple[Dict[str, Any], ...]
    loss_ledger: Optional[Dict[str, Any]]
    loss_ledger_verified: bool
    obnf_receipt: ObnfCollisionReceipt
    local_route: str
    canonical_terminal: str
    admitted: bool
    certified: bool
    authorized: bool
    authorization_status: str
    reason: str
    authority_effect: str = "None"
    certified_implies_authorized: bool = False


@dataclass(frozen=True)
class AsrfEvaluationReceipt:
    """Receipt for Autopoietic Self-Reference Refusal Form (nf.recursion.asrf)."""

    contract_id: str
    producer_identity: str
    evaluator_identity: str
    caller_hash: str
    target_content_hash: str
    recursion_depth: int
    max_recursion_depth: int
    cycle_witness: Optional[Tuple[str, ...]]
    local_terminal: str
    canonical_terminal: str
    admitted: bool
    reason: str
    authority_effect: str = "None"


@dataclass(frozen=True)
class McpGateReceipt:
    """Receipt emitted by @observer_freshness_gate over an MCP tool invocation."""

    contract_id: str
    observer_id: str
    packet_scope: Optional[str]
    replica_lag_seconds: Optional[float]
    observer_max_lag_seconds: Optional[float]
    poset_valid_order: bool
    poset_monotonic: bool
    poset_resolutions: Tuple[Dict[str, Any], ...]
    asrf_receipt: AsrfEvaluationReceipt
    loss_ledger_verified: bool
    freshness_route: str
    terminal_route: str
    canonical_terminal: str
    admitted: bool
    certified: bool
    authorized: bool
    authorization_status: str
    tool_executed: bool
    tool_output: Any
    reason: str
    authority_effect: str = "None"
    certified_implies_authorized: bool = False


@dataclass(frozen=True)
class RagMcpPipelineReceipt:
    """End-to-end receipt chaining Stage 0 (WDNF) -> Stage 1 (CODA_MUR) -> Stage 2 (MCP Gate)."""

    wdnf_receipt: WdnfEvaluationReceipt
    context_envelope: Optional[CodaMurContextEnvelope]
    mcp_receipt: Optional[McpGateReceipt]
    pipeline_terminal: str
    certified: bool
    authorized: bool
    tool_executed: bool
    authority_effect: str = "None"
    certified_implies_authorized: bool = False


def evaluate_wdnf_candidate_cut(
    candidates: Sequence[Mapping[str, Any]],
    key_field: str = "chunk_id",
    distinction_fields: Sequence[str] = ("text", "doc_id"),
    asserted_pairs: Optional[Sequence[Tuple[str, str]]] = None,
    witness_Multiplicity_override: Optional[Mapping[Tuple[str, str], int]] = None,
    irreflexivity_declared: bool = True,
    scope_declared: bool = True,
) -> WdnfEvaluationReceipt:
    """Evaluates WDP Level 00 Admitted Cut (nf.wdp.wdnf / nf.derivation.pdnf) on RAG candidates.

    Checks:
      1. Support floor: carrier size |X| >= 2.
      2. Irreflexivity law declared and satisfied: no (x, x) in asserted distinctions.
      3. Constructive witness presence: every asserted distinction (x, y) has >= 1 concrete
         attribute witness where candidate[x][f] != candidate[y][f].
      4. Witness multiplicity erasure: multiple witnesses between (x, y) normalize to a single
         canonical pair in normalized_distinction_pairs.
    """
    carrier_ids = tuple(str(c.get(key_field, f"idx_{i}")) for i, c in enumerate(candidates))
    by_id: Dict[str, Mapping[str, Any]] = {
        str(c.get(key_field, f"idx_{i}")): c for i, c in enumerate(candidates)
    }

    if len(carrier_ids) < 2:
        return WdnfEvaluationReceipt(
            contract_id="nf.wdp.wdnf",
            carrier_ids=carrier_ids,
            carrier_size=len(carrier_ids),
            witnessed_differences=(),
            normalized_distinction_pairs=(),
            witness_multiplicity_erased=True,
            local_terminal="SubsingletonCollapseRefusal",
            canonical_terminal="Refuse",
            admitted=False,
            certified=False,
            authorized=False,
            reason=f"Support floor failed: carrier has {len(carrier_ids)} element(s); WDNF requires |X| >= 2.",
        )

    if asserted_pairs is None:
        inferred_pairs: List[Tuple[str, str]] = []
        for i in range(len(carrier_ids)):
            for j in range(i + 1, len(carrier_ids)):
                inferred_pairs.append((carrier_ids[i], carrier_ids[j]))
        pairs_to_check: Sequence[Tuple[str, str]] = inferred_pairs
    else:
        pairs_to_check = list(asserted_pairs)

    witnesses: List[WitnessedDifference] = []
    witness_map: Dict[Tuple[str, str], int] = {}

    for x_id, y_id in pairs_to_check:
        if x_id == y_id:
            witness_map[(x_id, y_id)] = 0
            continue
        cand_x = by_id.get(x_id, {})
        cand_y = by_id.get(y_id, {})
        matching_features: List[str] = []
        for feat in distinction_fields:
            if feat in cand_x and feat in cand_y and cand_x[feat] != cand_y[feat]:
                matching_features.append(feat)

        if witness_Multiplicity_override is not None and (x_id, y_id) in witness_Multiplicity_override:
            mult = int(witness_Multiplicity_override[(x_id, y_id)])
        else:
            mult = len(matching_features)

        witness_map[(x_id, y_id)] = mult
        if mult > 0:
            first_feat = matching_features[0] if matching_features else distinction_fields[0]
            witnesses.append(
                WitnessedDifference(
                    left_id=x_id,
                    right_id=y_id,
                    witness_feature=first_feat,
                    left_value=cand_x.get(first_feat),
                    right_value=cand_y.get(first_feat),
                    multiplicity=mult,
                )
            )

    pdnf_fixture = {
        "carrier": list(dict.fromkeys(carrier_ids)),
        "irreflexivity_declared": irreflexivity_declared,
        "scope_declared": scope_declared,
        "asserted_relation": list(pairs_to_check),
        "witness_map": witness_map,
    }
    pdnf_res = evaluate_sn_pdnf(pdnf_fixture)
    local_term = pdnf_res["local_terminal"]

    route_map = {
        "AcceptWitnessedIrreflexive": ("AdmittedCut", "Preserve", True),
        "RequireCarrierDeclaration": ("SubsingletonCollapseRefusal", "Refuse", False),
        "RequireIrreflexivityDeclaration": ("RequireIrreflexivityDeclaration", "Refuse", False),
        "RejectSelfDifference": ("IrreflexivityViolation", "Reject", False),
        "RejectUnwitnessedAssertion": ("GhostDistinctionViolation", "Reject", False),
        "Undetermined": ("Undetermined", "Abstain", False),
    }
    wdnf_local, canonical_term, admitted = route_map.get(
        local_term, (local_term, "Refuse", False)
    )

    normalized_pairs = tuple(
        sorted({(min(w.left_id, w.right_id), max(w.left_id, w.right_id)) for w in witnesses})
    )

    return WdnfEvaluationReceipt(
        contract_id="nf.wdp.wdnf",
        carrier_ids=carrier_ids,
        carrier_size=len(dict.fromkeys(carrier_ids)),
        witnessed_differences=tuple(witnesses),
        normalized_distinction_pairs=normalized_pairs,
        witness_multiplicity_erased=True,
        local_terminal=wdnf_local,
        canonical_terminal=canonical_term,
        admitted=admitted,
        certified=admitted,
        authorized=False,
        reason=pdnf_res["reason"],
        offending_pair=pdnf_res.get("offending_pair"),
    )


def evaluate_obnf_projection_collision(
    source_chunks: Sequence[Mapping[str, Any]],
    projected_chunks: Sequence[Mapping[str, Any]],
    key_field: str,
    target_fields: Sequence[str],
    protected_fields: Sequence[str],
) -> ObnfCollisionReceipt:
    """Evaluates Obstruction Relativization Normal Form (nf.derivation.obnf).

    A projection F: Source -> Target may collapse two distinct source chunks into the same
    projected image. Under OBNF:
      - If no protected law is declared, returns RequireProtectedLawDeclaration -> Refuse.
      - If two distinct source chunks collide on their protected_fields signature in Target
        (or if a protected determinant is lost), returns PromoteToObstruction -> Reject.
      - If two source chunks collide only on non-protected attributes while preserving distinct
        protected determinants, returns AcceptAdmissibleCollision -> Preserve.
    """
    protected_tuple = tuple(protected_fields)
    if not protected_tuple:
        return ObnfCollisionReceipt(
            contract_id="nf.derivation.obnf",
            protected_law=(),
            colliding_pairs=(),
            violates_protected_law=True,
            local_terminal="RequireProtectedLawDeclaration",
            canonical_terminal="Refuse",
            admitted=False,
            reason="OBNF requires an explicit protected_fields declaration to relativize collisions.",
        )

    non_key_targets = tuple(f for f in target_fields if f not in protected_tuple)
    colliding_pairs: List[Tuple[str, str]] = []
    violates_protected = False

    # Check protected signature collisions across projected chunks
    seen_protected: Dict[Tuple[Any, ...], str] = {}
    for idx, p_chunk in enumerate(projected_chunks):
        chunk_id = str(p_chunk.get(key_field, f"proj_{idx}"))
        prot_sig = tuple(p_chunk.get(f) for f in protected_tuple)
        if any(p_chunk.get(f) is None for f in protected_tuple):
            violates_protected = True
            colliding_pairs.append((chunk_id, "<null_protected_determinant>"))
            continue
        if prot_sig in seen_protected and seen_protected[prot_sig] != chunk_id:
            violates_protected = True
            colliding_pairs.append((seen_protected[prot_sig], chunk_id))
        else:
            seen_protected[prot_sig] = chunk_id

    # Check non-key quotient collisions (admissible when protected determinants stay distinct)
    if not violates_protected and non_key_targets:
        seen_non_key: Dict[Tuple[Any, ...], str] = {}
        for idx, p_chunk in enumerate(projected_chunks):
            chunk_id = str(p_chunk.get(key_field, f"proj_{idx}"))
            nk_sig = tuple(p_chunk.get(f) for f in non_key_targets)
            if nk_sig in seen_non_key and seen_non_key[nk_sig] != chunk_id:
                colliding_pairs.append((seen_non_key[nk_sig], chunk_id))
            else:
                seen_non_key[nk_sig] = chunk_id

    if violates_protected:
        return ObnfCollisionReceipt(
            contract_id="nf.derivation.obnf",
            protected_law=protected_tuple,
            colliding_pairs=tuple(colliding_pairs),
            violates_protected_law=True,
            local_terminal="PromoteToObstruction",
            canonical_terminal="Reject",
            admitted=False,
            reason=f"Projection collision violates protected determinant law {protected_tuple}: {colliding_pairs}",
        )

    return ObnfCollisionReceipt(
        contract_id="nf.derivation.obnf",
        protected_law=protected_tuple,
        colliding_pairs=tuple(colliding_pairs),
        violates_protected_law=False,
        local_terminal="AcceptAdmissibleCollision",
        canonical_terminal="Preserve",
        admitted=True,
        reason="Protected determinant law survives projection; any non-key collisions are admissible.",
    )


def build_context_loss_ledger(
    erased_attributes: Sequence[str],
    source_chunks: Sequence[Mapping[str, Any]],
    retained_chunks_by_key: Mapping[str, Mapping[str, Any]],
    key_field: str,
    text_field: str = "text",
    trigger_id: str = CODA_MUR_CONTEXT_TRIGGER_ID,
) -> Dict[str, Any]:
    """Constructs a SHA-256 Merkle-sealed LossLedger for RAG attribute erasure and token truncation."""
    sorted_erased = sorted(set(erased_attributes))
    entries: List[Dict[str, Any]] = []

    for idx, src in enumerate(source_chunks):
        row_key = str(src.get(key_field, f"chunk_{idx}"))
        erased_payload = {attr: src.get(attr) for attr in sorted_erased if attr in src}
        src_tokens = tokenize_whitespace(str(src.get(text_field, ""))) if text_field in src else []

        if row_key not in retained_chunks_by_key:
            # Whole chunk dropped due to token budget exhaustion
            dropped_text = detokenize_whitespace(src_tokens)
            dropped_hash = hashlib.sha256(dropped_text.encode("utf-8")).hexdigest()
            erased_payload["__dropped_chunk__"] = True
            erased_payload["__truncated_token_count__"] = len(src_tokens)
            erased_payload["__truncated_text_sha256__"] = dropped_hash
            erased_payload["__truncated_tokens__"] = src_tokens
        else:
            ret = retained_chunks_by_key[row_key]
            ret_tokens = (
                tokenize_whitespace(str(ret.get(text_field, ""))) if text_field in ret else []
            )
            if len(ret_tokens) < len(src_tokens):
                dropped_slice = src_tokens[len(ret_tokens) :]
                dropped_text = detokenize_whitespace(dropped_slice)
                dropped_hash = hashlib.sha256(dropped_text.encode("utf-8")).hexdigest()
                erased_payload["__dropped_chunk__"] = False
                erased_payload["__truncated_token_count__"] = len(dropped_slice)
                erased_payload["__truncated_text_sha256__"] = dropped_hash
                erased_payload["__truncated_tokens__"] = dropped_slice

        entries.append(
            {
                "row_key": row_key,
                "trigger_id": trigger_id,
                "erased_fields": erased_payload,
            }
        )

    ledger_erased_attrs = list(sorted_erased)
    if any(
        "__truncated_token_count__" in e["erased_fields"] for e in entries
    ) and "__context_token_truncation__" not in ledger_erased_attrs:
        ledger_erased_attrs.append("__context_token_truncation__")

    canonical_bytes = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(canonical_bytes).hexdigest()

    return {
        "trigger_id": trigger_id,
        "erased_attributes": ledger_erased_attrs,
        "record_count": len(entries),
        "entries": entries,
        "sealed": True,
        "merkle_digest": digest,
        "authority_effect": "None",
    }


def coda_mur_projection(
    source_fields: Sequence[str],
    target_fields: Sequence[str],
    key_field: str = "chunk_id",
    protected_fields: Sequence[str] = ("chunk_id",),
    score_field: Optional[str] = "relevance_score",
    text_field: str = "text",
    max_token_budget: Optional[int] = None,
    contract_id: str = "nf.coda.mur.transport",
) -> Callable[[Callable[..., Any]], Callable[..., CodaMurContextEnvelope]]:
    """Decorator enforcing CODA_MUR representation transport and TBNF token-budget loss ledgers.

    The wrapped function receives ``(source_chunks, *args, **kwargs)`` and may return either:
      - a sequence of projected/transformed chunk dicts, OR
      - ``None`` (in which case the decorator applies canonical projection onto ``target_fields``).
    After the wrapped function runs, the decorator applies any active ``max_token_budget`` limit,
    checks protected determinant preservation and OBNF collision rules, verifies exact token
    conservation (``retained_token_count + truncated_token_count == source_token_count``), and
    seals a cryptographic SHA-256 ``LossLedger`` whenever attributes or tokens are erased.
    """
    src_tuple = tuple(source_fields)
    tgt_tuple = tuple(target_fields)
    prot_tuple = tuple(protected_fields)

    def decorator(fn: Callable[..., Any]) -> Callable[..., CodaMurContextEnvelope]:
        @functools.wraps(fn)
        def wrapper(
            source_chunks: Sequence[Mapping[str, Any]],
            *args: Any,
            max_token_budget_override: Optional[int] = None,
            tamper_loss_ledger: bool = False,
            omit_loss_ledger: bool = False,
            **kwargs: Any,
        ) -> CodaMurContextEnvelope:
            active_budget = (
                max_token_budget_override
                if max_token_budget_override is not None
                else max_token_budget
            )
            erased_attrs = tuple(sorted(set(src_tuple) - set(tgt_tuple)))

            # Check 1: Protected fields must be retained in target_fields
            missing_protected = [f for f in prot_tuple if f not in tgt_tuple]
            if missing_protected:
                obnf = ObnfCollisionReceipt(
                    contract_id="nf.derivation.obnf",
                    protected_law=prot_tuple,
                    colliding_pairs=(),
                    violates_protected_law=True,
                    local_terminal="PromoteToObstruction",
                    canonical_terminal="Reject",
                    admitted=False,
                    reason=f"Protected fields {missing_protected} dropped from target_fields {tgt_tuple}.",
                )
                return CodaMurContextEnvelope(
                    contract_id=contract_id,
                    source_fields=src_tuple,
                    target_fields=tgt_tuple,
                    key_field=key_field,
                    protected_fields=prot_tuple,
                    erased_attributes=erased_attrs,
                    max_token_budget=active_budget,
                    source_chunk_count=len(source_chunks),
                    retained_chunk_count=0,
                    dropped_chunk_count=len(source_chunks),
                    source_token_count=0,
                    retained_token_count=0,
                    truncated_token_count=0,
                    token_conservation_commutes=False,
                    score_conservation_commutes=False,
                    projected_chunks=(),
                    loss_ledger=None,
                    loss_ledger_verified=False,
                    obnf_receipt=obnf,
                    local_route="TransportViolation",
                    canonical_terminal="Reject",
                    admitted=False,
                    certified=False,
                    authorized=False,
                    authorization_status="rejected",
                    reason=obnf.reason,
                )

            # Execute wrapped projection function
            raw_output = fn(source_chunks, *args, **kwargs)
            if raw_output is None:
                candidate_projected = [
                    {k: chunk[k] for k in tgt_tuple if k in chunk} for chunk in source_chunks
                ]
            else:
                candidate_projected = [dict(c) for c in raw_output]

            # Apply token budget truncation across projected chunks if active_budget is set
            source_by_key: Dict[str, Mapping[str, Any]] = {}
            total_source_tokens = 0
            for idx, s_chunk in enumerate(source_chunks):
                rk = str(s_chunk.get(key_field, f"chunk_{idx}"))
                source_by_key[rk] = s_chunk
                if text_field in s_chunk:
                    total_source_tokens += len(tokenize_whitespace(str(s_chunk.get(text_field, ""))))

            final_projected: List[Dict[str, Any]] = []
            retained_by_key: Dict[str, Dict[str, Any]] = {}
            remaining_budget = active_budget
            total_retained_tokens = 0

            for idx, p_chunk in enumerate(candidate_projected):
                projected_row = {k: p_chunk.get(k) for k in tgt_tuple if k in p_chunk}
                rk = str(projected_row.get(key_field, f"chunk_{idx}"))

                if text_field in projected_row and projected_row[text_field] is not None:
                    tokens = tokenize_whitespace(str(projected_row[text_field]))
                else:
                    tokens = []

                if remaining_budget is not None:
                    if remaining_budget <= 0:
                        # Budget exhausted: drop this chunk from active context window
                        continue
                    if len(tokens) > remaining_budget:
                        tokens = tokens[:remaining_budget]
                        projected_row[text_field] = detokenize_whitespace(tokens)
                    remaining_budget -= len(tokens)

                total_retained_tokens += len(tokens)
                final_projected.append(projected_row)
                retained_by_key[rk] = projected_row

            # Check 2: Verify protected determinants match source_chunks on all retained chunks
            for p_row in final_projected:
                rk = str(p_row.get(key_field, ""))
                src_row = source_by_key.get(rk)
                if src_row is None:
                    obnf = ObnfCollisionReceipt(
                        contract_id="nf.derivation.obnf",
                        protected_law=prot_tuple,
                        colliding_pairs=((rk, "<unmapped_source_key>"),),
                        violates_protected_law=True,
                        local_terminal="PromoteToObstruction",
                        canonical_terminal="Reject",
                        admitted=False,
                        reason=f"Projected chunk key '{rk}' does not trace to any source chunk.",
                    )
                    return CodaMurContextEnvelope(
                        contract_id=contract_id,
                        source_fields=src_tuple,
                        target_fields=tgt_tuple,
                        key_field=key_field,
                        protected_fields=prot_tuple,
                        erased_attributes=erased_attrs,
                        max_token_budget=active_budget,
                        source_chunk_count=len(source_chunks),
                        retained_chunk_count=len(final_projected),
                        dropped_chunk_count=len(source_chunks) - len(final_projected),
                        source_token_count=total_source_tokens,
                        retained_token_count=total_retained_tokens,
                        truncated_token_count=max(0, total_source_tokens - total_retained_tokens),
                        token_conservation_commutes=False,
                        score_conservation_commutes=False,
                        projected_chunks=tuple(final_projected),
                        loss_ledger=None,
                        loss_ledger_verified=False,
                        obnf_receipt=obnf,
                        local_route="TransportViolation",
                        canonical_terminal="Reject",
                        admitted=False,
                        certified=False,
                        authorized=False,
                        authorization_status="rejected",
                        reason=obnf.reason,
                    )
                for pf in prot_tuple:
                    if p_row.get(pf) is None or p_row.get(pf) != src_row.get(pf):
                        obnf = ObnfCollisionReceipt(
                            contract_id="nf.derivation.obnf",
                            protected_law=prot_tuple,
                            colliding_pairs=((rk, pf),),
                            violates_protected_law=True,
                            local_terminal="PromoteToObstruction",
                            canonical_terminal="Reject",
                            admitted=False,
                            reason=f"Protected field '{pf}' on chunk '{rk}' was nullified or mutated during projection.",
                        )
                        return CodaMurContextEnvelope(
                            contract_id=contract_id,
                            source_fields=src_tuple,
                            target_fields=tgt_tuple,
                            key_field=key_field,
                            protected_fields=prot_tuple,
                            erased_attributes=erased_attrs,
                            max_token_budget=active_budget,
                            source_chunk_count=len(source_chunks),
                            retained_chunk_count=len(final_projected),
                            dropped_chunk_count=len(source_chunks) - len(final_projected),
                            source_token_count=total_source_tokens,
                            retained_token_count=total_retained_tokens,
                            truncated_token_count=max(0, total_source_tokens - total_retained_tokens),
                            token_conservation_commutes=False,
                            score_conservation_commutes=False,
                            projected_chunks=tuple(final_projected),
                            loss_ledger=None,
                            loss_ledger_verified=False,
                            obnf_receipt=obnf,
                            local_route="TransportViolation",
                            canonical_terminal="Reject",
                            admitted=False,
                            certified=False,
                            authorized=False,
                            authorization_status="rejected",
                            reason=obnf.reason,
                        )

            obnf_receipt = evaluate_obnf_projection_collision(
                source_chunks=source_chunks,
                projected_chunks=final_projected,
                key_field=key_field,
                target_fields=tgt_tuple,
                protected_fields=prot_tuple,
            )
            if not obnf_receipt.admitted:
                return CodaMurContextEnvelope(
                    contract_id=contract_id,
                    source_fields=src_tuple,
                    target_fields=tgt_tuple,
                    key_field=key_field,
                    protected_fields=prot_tuple,
                    erased_attributes=erased_attrs,
                    max_token_budget=active_budget,
                    source_chunk_count=len(source_chunks),
                    retained_chunk_count=len(final_projected),
                    dropped_chunk_count=len(source_chunks) - len(final_projected),
                    source_token_count=total_source_tokens,
                    retained_token_count=total_retained_tokens,
                    truncated_token_count=max(0, total_source_tokens - total_retained_tokens),
                    token_conservation_commutes=False,
                    score_conservation_commutes=False,
                    projected_chunks=tuple(final_projected),
                    loss_ledger=None,
                    loss_ledger_verified=False,
                    obnf_receipt=obnf_receipt,
                    local_route="TransportViolation",
                    canonical_terminal="Reject",
                    admitted=False,
                    certified=False,
                    authorized=False,
                    authorization_status="rejected",
                    reason=obnf_receipt.reason,
                )

            # Check score conservation on retained chunks
            score_commutes = True
            if score_field and score_field in tgt_tuple:
                for p_row in final_projected:
                    rk = str(p_row.get(key_field, ""))
                    src_row = source_by_key.get(rk, {})
                    if abs(float(p_row.get(score_field, 0.0)) - float(src_row.get(score_field, 0.0))) > 1e-9:
                        score_commutes = False
                        break

            truncated_tokens = total_source_tokens - total_retained_tokens
            dropped_chunks = len(source_chunks) - len(final_projected)
            has_loss = bool(erased_attrs) or (truncated_tokens > 0) or (dropped_chunks > 0)

            if not has_loss:
                return CodaMurContextEnvelope(
                    contract_id=contract_id,
                    source_fields=src_tuple,
                    target_fields=tgt_tuple,
                    key_field=key_field,
                    protected_fields=prot_tuple,
                    erased_attributes=(),
                    max_token_budget=active_budget,
                    source_chunk_count=len(source_chunks),
                    retained_chunk_count=len(final_projected),
                    dropped_chunk_count=0,
                    source_token_count=total_source_tokens,
                    retained_token_count=total_retained_tokens,
                    truncated_token_count=0,
                    token_conservation_commutes=True,
                    score_conservation_commutes=score_commutes,
                    projected_chunks=tuple(final_projected),
                    loss_ledger=None,
                    loss_ledger_verified=True,
                    obnf_receipt=obnf_receipt,
                    local_route="TransportOk",
                    canonical_terminal="Preserve",
                    admitted=score_commutes,
                    certified=score_commutes,
                    authorized=False,
                    authorization_status="certified_not_authorized",
                    reason="Lossless context representation transport with zero erased fields or truncated tokens.",
                )

            if omit_loss_ledger:
                return CodaMurContextEnvelope(
                    contract_id=contract_id,
                    source_fields=src_tuple,
                    target_fields=tgt_tuple,
                    key_field=key_field,
                    protected_fields=prot_tuple,
                    erased_attributes=erased_attrs,
                    max_token_budget=active_budget,
                    source_chunk_count=len(source_chunks),
                    retained_chunk_count=len(final_projected),
                    dropped_chunk_count=dropped_chunks,
                    source_token_count=total_source_tokens,
                    retained_token_count=total_retained_tokens,
                    truncated_token_count=truncated_tokens,
                    token_conservation_commutes=False,
                    score_conservation_commutes=score_commutes,
                    projected_chunks=tuple(final_projected),
                    loss_ledger=None,
                    loss_ledger_verified=False,
                    obnf_receipt=obnf_receipt,
                    local_route="TransportViolation",
                    canonical_terminal="Reject",
                    admitted=False,
                    certified=False,
                    authorized=False,
                    authorization_status="rejected",
                    reason="Lossy context projection or token truncation occurred without a declared LossLedger.",
                )

            loss_ledger = build_context_loss_ledger(
                erased_attributes=erased_attrs,
                source_chunks=source_chunks,
                retained_chunks_by_key=retained_by_key,
                key_field=key_field,
                text_field=text_field,
            )
            if tamper_loss_ledger:
                loss_ledger = dict(loss_ledger)
                loss_ledger["merkle_digest"] = "0" * 64

            ledger_ok, ledger_err = verify_loss_ledger_integrity(loss_ledger)
            ledger_truncated_sum = sum(
                int(e["erased_fields"].get("__truncated_token_count__", 0))
                for e in loss_ledger.get("entries", [])
            )
            token_commutes = (
                total_retained_tokens + ledger_truncated_sum == total_source_tokens
                and truncated_tokens == ledger_truncated_sum
            )

            if not ledger_ok or not token_commutes or not score_commutes:
                return CodaMurContextEnvelope(
                    contract_id=contract_id,
                    source_fields=src_tuple,
                    target_fields=tgt_tuple,
                    key_field=key_field,
                    protected_fields=prot_tuple,
                    erased_attributes=erased_attrs,
                    max_token_budget=active_budget,
                    source_chunk_count=len(source_chunks),
                    retained_chunk_count=len(final_projected),
                    dropped_chunk_count=dropped_chunks,
                    source_token_count=total_source_tokens,
                    retained_token_count=total_retained_tokens,
                    truncated_token_count=truncated_tokens,
                    token_conservation_commutes=token_commutes,
                    score_conservation_commutes=score_commutes,
                    projected_chunks=tuple(final_projected),
                    loss_ledger=loss_ledger,
                    loss_ledger_verified=ledger_ok,
                    obnf_receipt=obnf_receipt,
                    local_route="TransportViolation",
                    canonical_terminal="Reject",
                    admitted=False,
                    certified=False,
                    authorized=False,
                    authorization_status="rejected",
                    reason=ledger_err or "Token or score conservation failed to commute across projection.",
                )

            return CodaMurContextEnvelope(
                contract_id=contract_id,
                source_fields=src_tuple,
                target_fields=tgt_tuple,
                key_field=key_field,
                protected_fields=prot_tuple,
                erased_attributes=tuple(loss_ledger["erased_attributes"]),
                max_token_budget=active_budget,
                source_chunk_count=len(source_chunks),
                retained_chunk_count=len(final_projected),
                dropped_chunk_count=dropped_chunks,
                source_token_count=total_source_tokens,
                retained_token_count=total_retained_tokens,
                truncated_token_count=truncated_tokens,
                token_conservation_commutes=True,
                score_conservation_commutes=True,
                projected_chunks=tuple(final_projected),
                loss_ledger=loss_ledger,
                loss_ledger_verified=True,
                obnf_receipt=obnf_receipt,
                local_route="DegradedTransportWithLoss",
                canonical_terminal="Quarantine",
                admitted=True,
                certified=True,
                authorized=False,
                authorization_status="certified_not_authorized",
                reason=(
                    f"Lossy context transport certified with sealed SHA-256 LossLedger "
                    f"(erased={list(erased_attrs)}, truncated_tokens={truncated_tokens}, "
                    f"dropped_chunks={dropped_chunks})."
                ),
            )

        return wrapper

    return decorator


def _find_directed_cycle(edges: Sequence[Tuple[str, str]]) -> Optional[Tuple[str, ...]]:
    """Detects a directed cycle in call_graph_edges and returns the minimal cycle witness."""
    adj: Dict[str, List[str]] = {}
    nodes: List[str] = []
    for u, v in edges:
        if u not in adj:
            adj[u] = []
            nodes.append(u)
        if v not in adj:
            adj[v] = []
            nodes.append(v)
        adj[u].append(v)

    visited: Dict[str, int] = {}  # 0=unvisited, 1=visiting, 2=done
    parent: Dict[str, str] = {}

    for start in nodes:
        if visited.get(start, 0) != 0:
            continue
        stack: List[Tuple[str, int]] = [(start, 0)]
        visited[start] = 1
        path: List[str] = [start]

        while stack:
            curr, idx = stack[-1]
            neighbors = adj.get(curr, [])
            if idx < len(neighbors):
                stack[-1] = (curr, idx + 1)
                nxt = neighbors[idx]
                state = visited.get(nxt, 0)
                if state == 1:
                    # Found cycle
                    cycle_start_idx = path.index(nxt)
                    return tuple(path[cycle_start_idx:] + [nxt])
                elif state == 0:
                    visited[nxt] = 1
                    parent[nxt] = curr
                    path.append(nxt)
                    stack.append((nxt, 0))
            else:
                visited[curr] = 2
                stack.pop()
                path.pop()

    return None


def evaluate_asrf_guard(
    asrf_context: Optional[Mapping[str, Any]],
) -> AsrfEvaluationReceipt:
    """Evaluates Autopoietic Self-Reference Refusal Form (nf.recursion.asrf)."""
    ctx = dict(asrf_context or {})
    producer = str(ctx.get("producer_identity", "rag_context_producer"))
    evaluator = str(ctx.get("evaluator_identity", "mcp_gate_evaluator"))
    caller_hash = str(ctx.get("caller_hash", "caller_sha256_default"))
    target_hash = str(ctx.get("target_content_hash", "target_sha256_default"))
    depth = int(ctx.get("recursion_depth", 0))
    max_depth = int(ctx.get("max_recursion_depth", 8))
    raw_edges = ctx.get("call_graph_edges", ())
    edges: List[Tuple[str, str]] = [
        (str(e[0]), str(e[1])) for e in raw_edges if isinstance(e, (list, tuple)) and len(e) == 2
    ]

    if not producer or not evaluator or producer == evaluator:
        return AsrfEvaluationReceipt(
            contract_id="nf.recursion.asrf",
            producer_identity=producer,
            evaluator_identity=evaluator,
            caller_hash=caller_hash,
            target_content_hash=target_hash,
            recursion_depth=depth,
            max_recursion_depth=max_depth,
            cycle_witness=(producer, evaluator),
            local_terminal="SelfReferenceRefusal",
            canonical_terminal="Refuse",
            admitted=False,
            reason=f"ASRF violation: producer_identity '{producer}' == evaluator_identity '{evaluator}'.",
        )

    if caller_hash == target_hash:
        return AsrfEvaluationReceipt(
            contract_id="nf.recursion.asrf",
            producer_identity=producer,
            evaluator_identity=evaluator,
            caller_hash=caller_hash,
            target_content_hash=target_hash,
            recursion_depth=depth,
            max_recursion_depth=max_depth,
            cycle_witness=(caller_hash, target_hash),
            local_terminal="SelfReferenceRefusal",
            canonical_terminal="Refuse",
            admitted=False,
            reason=f"ASRF violation: caller_hash '{caller_hash}' equals target_content_hash.",
        )

    cycle = _find_directed_cycle(edges)
    if cycle is not None:
        return AsrfEvaluationReceipt(
            contract_id="nf.recursion.asrf",
            producer_identity=producer,
            evaluator_identity=evaluator,
            caller_hash=caller_hash,
            target_content_hash=target_hash,
            recursion_depth=depth,
            max_recursion_depth=max_depth,
            cycle_witness=cycle,
            local_terminal="CycleDetected",
            canonical_terminal="Refuse",
            admitted=False,
            reason=f"ASRF violation: cyclic evaluation dependency detected: {' -> '.join(cycle)}.",
        )

    if depth < 0 or depth > max_depth:
        return AsrfEvaluationReceipt(
            contract_id="nf.recursion.asrf",
            producer_identity=producer,
            evaluator_identity=evaluator,
            caller_hash=caller_hash,
            target_content_hash=target_hash,
            recursion_depth=depth,
            max_recursion_depth=max_depth,
            cycle_witness=None,
            local_terminal="UnboundedRecursion",
            canonical_terminal="Refuse",
            admitted=False,
            reason=f"ASRF violation: recursion_depth ({depth}) exceeds max_recursion_depth ({max_depth}).",
        )

    return AsrfEvaluationReceipt(
        contract_id="nf.recursion.asrf",
        producer_identity=producer,
        evaluator_identity=evaluator,
        caller_hash=caller_hash,
        target_content_hash=target_hash,
        recursion_depth=depth,
        max_recursion_depth=max_depth,
        cycle_witness=None,
        local_terminal="AcyclicCertified",
        canonical_terminal="Preserve",
        admitted=True,
        reason="Evaluation call graph is acyclic with distinct producer and evaluator identities.",
    )


def _normalize_observer_specs(
    observer_poset: Sequence[ObserverSpec | Mapping[str, Any]],
) -> Tuple[List[ObserverSpec], List[Dict[str, Any]]]:
    specs: List[ObserverSpec] = []
    dicts: List[Dict[str, Any]] = []
    for item in observer_poset:
        if isinstance(item, ObserverSpec):
            specs.append(item)
            dicts.append(
                {
                    "observer_id": item.observer_id,
                    "max_lag_seconds": item.max_lag_seconds,
                    "authorized_scopes": list(item.authorized_scopes),
                }
            )
        else:
            scopes = item.get("authorized_scopes")
            scope_tuple = (
                tuple(str(s) for s in scopes)
                if isinstance(scopes, (list, tuple, set))
                else ()
            )
            max_lag = item.get("max_lag_seconds")
            lag_int = int(max_lag) if isinstance(max_lag, (int, float)) else -1
            specs.append(
                ObserverSpec(
                    observer_id=str(item.get("observer_id", "unknown")),
                    max_lag_seconds=lag_int,
                    authorized_scopes=scope_tuple,
                )
            )
            dicts.append(dict(item))
    return specs, dicts


def observer_freshness_gate(
    observer_poset: Sequence[ObserverSpec | Mapping[str, Any]],
    enforce_asrf: bool = True,
    require_verified_loss_ledger: bool = True,
    contract_id: str = "nf.epistemic.freshness",
) -> Callable[[Callable[..., Any]], Callable[..., McpGateReceipt]]:
    """Decorator enforcing observer-relative freshness, ASRF acyclicity, and MCP authorization firewalls.

    Even when a context envelope is CODA_MUR-certified, ASRF-acyclic, and AuthorizedFresh
    within the observer's SLA budget, ``certified_implies_authorized`` is strictly ``False``:
    the wrapped MCP tool function is NEVER executed unless an independent ``policy_verifier``
    mapping with ``verifier_identity != producer_identity`` and ``outcome == "authorized"``
    is supplied.
    """
    specs, poset_dicts = _normalize_observer_specs(observer_poset)

    def decorator(tool_fn: Callable[..., Any]) -> Callable[..., McpGateReceipt]:
        @functools.wraps(tool_fn)
        def wrapper(
            context_envelope: CodaMurContextEnvelope,
            *,
            observer_id: str,
            packet_metadata: Mapping[str, Any],
            policy_verifier: Any = None,
            asrf_context: Optional[Mapping[str, Any]] = None,
            **tool_kwargs: Any,
        ) -> McpGateReceipt:
            packet_scope = packet_metadata.get("packet_scope")
            lag = packet_metadata.get("replica_lag_seconds")

            # Verify poset chain stringency order O_1 <= O_2 <= ... <= O_m
            valid_order = True
            for i in range(len(specs) - 1):
                if not specs[i].is_more_stringent_than(specs[i + 1]):
                    valid_order = False
                    break

            resolutions = evaluate_freshness(
                {"packet": dict(packet_metadata), "observers": poset_dicts}
            )
            monotonic_ok, _ = verify_observer_lattice_monotonicity(
                poset_dicts, dict(packet_metadata)
            )

            # Find target observer resolution
            obs_resolution: Optional[Dict[str, Any]] = None
            obs_max_lag: Optional[float] = None
            for spec, res in zip(specs, resolutions):
                if res.get("observer_id") == observer_id:
                    obs_resolution = res
                    obs_max_lag = float(spec.max_lag_seconds)
                    break

            # Evaluate ASRF guard
            asrf_receipt = (
                evaluate_asrf_guard(asrf_context)
                if enforce_asrf
                else AsrfEvaluationReceipt(
                    contract_id="nf.recursion.asrf",
                    producer_identity="unchecked",
                    evaluator_identity="unchecked",
                    caller_hash="0",
                    target_content_hash="1",
                    recursion_depth=0,
                    max_recursion_depth=8,
                    cycle_witness=None,
                    local_terminal="AcyclicCertified",
                    canonical_terminal="Preserve",
                    admitted=True,
                    reason="ASRF check disabled.",
                )
            )

            # Gate 1: CODA_MUR envelope & LossLedger seal verification
            if not context_envelope.admitted or not context_envelope.certified:
                return McpGateReceipt(
                    contract_id=contract_id,
                    observer_id=observer_id,
                    packet_scope=packet_scope,
                    replica_lag_seconds=lag,
                    observer_max_lag_seconds=obs_max_lag,
                    poset_valid_order=valid_order,
                    poset_monotonic=monotonic_ok,
                    poset_resolutions=tuple(resolutions),
                    asrf_receipt=asrf_receipt,
                    loss_ledger_verified=context_envelope.loss_ledger_verified,
                    freshness_route=obs_resolution["terminal_route"] if obs_resolution else "Refuse",
                    terminal_route="TransportViolation",
                    canonical_terminal="Reject",
                    admitted=False,
                    certified=False,
                    authorized=False,
                    authorization_status="rejected",
                    tool_executed=False,
                    tool_output=None,
                    reason=f"Upstream CODA_MUR context envelope rejected: {context_envelope.reason}",
                )

            has_loss = (
                bool(context_envelope.erased_attributes)
                or context_envelope.truncated_token_count > 0
                or context_envelope.dropped_chunk_count > 0
                or context_envelope.local_route == "DegradedTransportWithLoss"
            )
            ledger_ok = True
            if require_verified_loss_ledger and has_loss:
                if context_envelope.loss_ledger is None:
                    return McpGateReceipt(
                        contract_id=contract_id,
                        observer_id=observer_id,
                        packet_scope=packet_scope,
                        replica_lag_seconds=lag,
                        observer_max_lag_seconds=obs_max_lag,
                        poset_valid_order=valid_order,
                        poset_monotonic=monotonic_ok,
                        poset_resolutions=tuple(resolutions),
                        asrf_receipt=asrf_receipt,
                        loss_ledger_verified=False,
                        freshness_route=obs_resolution["terminal_route"] if obs_resolution else "Refuse",
                        terminal_route="LossLedgerMissing",
                        canonical_terminal="Refuse",
                        admitted=False,
                        certified=False,
                        authorized=False,
                        authorization_status="rejected",
                        tool_executed=False,
                        tool_output=None,
                        reason="Lossy RAG context envelope is missing its mandatory CODA_MUR LossLedger.",
                    )
                ledger_ok, ledger_err = verify_loss_ledger_integrity(context_envelope.loss_ledger)
                if not ledger_ok:
                    return McpGateReceipt(
                        contract_id=contract_id,
                        observer_id=observer_id,
                        packet_scope=packet_scope,
                        replica_lag_seconds=lag,
                        observer_max_lag_seconds=obs_max_lag,
                        poset_valid_order=valid_order,
                        poset_monotonic=monotonic_ok,
                        poset_resolutions=tuple(resolutions),
                        asrf_receipt=asrf_receipt,
                        loss_ledger_verified=False,
                        freshness_route=obs_resolution["terminal_route"] if obs_resolution else "Refuse",
                        terminal_route="LossLedgerTampered",
                        canonical_terminal="Refuse",
                        admitted=False,
                        certified=False,
                        authorized=False,
                        authorization_status="rejected",
                        tool_executed=False,
                        tool_output=None,
                        reason=f"CODA_MUR LossLedger failed cryptographic integrity verification: {ledger_err}",
                    )

            # Gate 2: ASRF Self-Reference & Call-Graph Acyclicity Gate
            if not asrf_receipt.admitted:
                return McpGateReceipt(
                    contract_id=contract_id,
                    observer_id=observer_id,
                    packet_scope=packet_scope,
                    replica_lag_seconds=lag,
                    observer_max_lag_seconds=obs_max_lag,
                    poset_valid_order=valid_order,
                    poset_monotonic=monotonic_ok,
                    poset_resolutions=tuple(resolutions),
                    asrf_receipt=asrf_receipt,
                    loss_ledger_verified=ledger_ok,
                    freshness_route=obs_resolution["terminal_route"] if obs_resolution else "Refuse",
                    terminal_route=asrf_receipt.local_terminal,
                    canonical_terminal="Refuse",
                    admitted=False,
                    certified=False,
                    authorized=False,
                    authorization_status="refused_self_reference",
                    tool_executed=False,
                    tool_output=None,
                    reason=asrf_receipt.reason,
                )

            # Gate 3: Observer Poset Freshness & Scope Gate
            if not valid_order or not monotonic_ok or obs_resolution is None:
                return McpGateReceipt(
                    contract_id=contract_id,
                    observer_id=observer_id,
                    packet_scope=packet_scope,
                    replica_lag_seconds=lag,
                    observer_max_lag_seconds=obs_max_lag,
                    poset_valid_order=valid_order,
                    poset_monotonic=monotonic_ok,
                    poset_resolutions=tuple(resolutions),
                    asrf_receipt=asrf_receipt,
                    loss_ledger_verified=ledger_ok,
                    freshness_route="Refuse",
                    terminal_route="Refuse",
                    canonical_terminal="Refuse",
                    admitted=False,
                    certified=False,
                    authorized=False,
                    authorization_status="refused_unregistered_observer_or_poset",
                    tool_executed=False,
                    tool_output=None,
                    reason=f"Observer '{observer_id}' is not registered in a valid monotonic observer poset.",
                )

            f_route = obs_resolution["terminal_route"]
            if f_route != "AuthorizedFresh":
                canonical_map = {
                    "RefreshRequired": "Invalidate",
                    "ConservativeInvalidate": "Invalidate",
                    "Refuse": "Refuse",
                }
                return McpGateReceipt(
                    contract_id=contract_id,
                    observer_id=observer_id,
                    packet_scope=packet_scope,
                    replica_lag_seconds=lag,
                    observer_max_lag_seconds=obs_max_lag,
                    poset_valid_order=valid_order,
                    poset_monotonic=monotonic_ok,
                    poset_resolutions=tuple(resolutions),
                    asrf_receipt=asrf_receipt,
                    loss_ledger_verified=ledger_ok,
                    freshness_route=f_route,
                    terminal_route=f_route,
                    canonical_terminal=canonical_map.get(f_route, "Refuse"),
                    admitted=False,
                    certified=False,
                    authorized=False,
                    authorization_status="rejected_by_freshness_or_scope",
                    tool_executed=False,
                    tool_output=None,
                    reason=obs_resolution["reason"],
                )

            # Gate 4: Epistemic Authority Firewall (certified_implies_authorized == False)
            if isinstance(policy_verifier, str):
                return McpGateReceipt(
                    contract_id=contract_id,
                    observer_id=observer_id,
                    packet_scope=packet_scope,
                    replica_lag_seconds=lag,
                    observer_max_lag_seconds=obs_max_lag,
                    poset_valid_order=valid_order,
                    poset_monotonic=monotonic_ok,
                    poset_resolutions=tuple(resolutions),
                    asrf_receipt=asrf_receipt,
                    loss_ledger_verified=ledger_ok,
                    freshness_route=f_route,
                    terminal_route="UnauthenticatedVerifierString",
                    canonical_terminal="Refuse",
                    admitted=False,
                    certified=True,
                    authorized=False,
                    authorization_status="certified_not_authorized",
                    tool_executed=False,
                    tool_output=None,
                    reason=(
                        f"Policy verifier '{policy_verifier}' is a bare string claim; "
                        "authenticated independent verifier record is required."
                    ),
                )

            if not isinstance(policy_verifier, Mapping):
                return McpGateReceipt(
                    contract_id=contract_id,
                    observer_id=observer_id,
                    packet_scope=packet_scope,
                    replica_lag_seconds=lag,
                    observer_max_lag_seconds=obs_max_lag,
                    poset_valid_order=valid_order,
                    poset_monotonic=monotonic_ok,
                    poset_resolutions=tuple(resolutions),
                    asrf_receipt=asrf_receipt,
                    loss_ledger_verified=ledger_ok,
                    freshness_route=f_route,
                    terminal_route="CertifiedNotAuthorized",
                    canonical_terminal="Refuse",
                    admitted=True,
                    certified=True,
                    authorized=False,
                    authorization_status="certified_not_authorized",
                    tool_executed=False,
                    tool_output=None,
                    reason=(
                        "Context envelope is CODA_MUR-certified and AuthorizedFresh, but "
                        "policy_verifier is absent; certification does not imply MCP tool authorization."
                    ),
                )

            verifier_id = str(policy_verifier.get("verifier_identity", "")).strip()
            outcome = str(policy_verifier.get("outcome", "")).strip()

            if not verifier_id or verifier_id == asrf_receipt.producer_identity:
                return McpGateReceipt(
                    contract_id=contract_id,
                    observer_id=observer_id,
                    packet_scope=packet_scope,
                    replica_lag_seconds=lag,
                    observer_max_lag_seconds=obs_max_lag,
                    poset_valid_order=valid_order,
                    poset_monotonic=monotonic_ok,
                    poset_resolutions=tuple(resolutions),
                    asrf_receipt=asrf_receipt,
                    loss_ledger_verified=ledger_ok,
                    freshness_route=f_route,
                    terminal_route="SelfAuthorizedViolation",
                    canonical_terminal="Refuse",
                    admitted=False,
                    certified=True,
                    authorized=False,
                    authorization_status="certified_not_authorized",
                    tool_executed=False,
                    tool_output=None,
                    reason=(
                        f"Policy verifier identity '{verifier_id}' is missing or matches "
                        f"producer_identity '{asrf_receipt.producer_identity}'."
                    ),
                )

            if outcome != "authorized":
                return McpGateReceipt(
                    contract_id=contract_id,
                    observer_id=observer_id,
                    packet_scope=packet_scope,
                    replica_lag_seconds=lag,
                    observer_max_lag_seconds=obs_max_lag,
                    poset_valid_order=valid_order,
                    poset_monotonic=monotonic_ok,
                    poset_resolutions=tuple(resolutions),
                    asrf_receipt=asrf_receipt,
                    loss_ledger_verified=ledger_ok,
                    freshness_route=f_route,
                    terminal_route="CertifiedNotAuthorized",
                    canonical_terminal="Refuse",
                    admitted=True,
                    certified=True,
                    authorized=False,
                    authorization_status="certified_not_authorized",
                    tool_executed=False,
                    tool_output=None,
                    reason=(
                        f"Context envelope is certified, but policy_verifier outcome is '{outcome}' "
                        "(requires 'authorized')."
                    ),
                )

            # All 4 gates + independent policy verifier passed -> execute MCP tool
            output = tool_fn(context_envelope, **tool_kwargs)
            return McpGateReceipt(
                contract_id=contract_id,
                observer_id=observer_id,
                packet_scope=packet_scope,
                replica_lag_seconds=lag,
                observer_max_lag_seconds=obs_max_lag,
                poset_valid_order=valid_order,
                poset_monotonic=monotonic_ok,
                poset_resolutions=tuple(resolutions),
                asrf_receipt=asrf_receipt,
                loss_ledger_verified=ledger_ok,
                freshness_route=f_route,
                terminal_route="AuthorizedFresh",
                canonical_terminal="Preserve",
                admitted=True,
                certified=True,
                authorized=True,
                authorization_status="authorized",
                tool_executed=True,
                tool_output=output,
                reason=(
                    f"All normal-form gates passed and independent policy_verifier '{verifier_id}' "
                    "authorized MCP tool execution."
                ),
            )

        return wrapper

    return decorator


def run_rag_mcp_pipeline(
    candidates: Sequence[Mapping[str, Any]],
    projection_fn: Callable[..., CodaMurContextEnvelope],
    mcp_tool_fn: Callable[..., McpGateReceipt],
    *,
    observer_id: str,
    packet_metadata: Mapping[str, Any],
    policy_verifier: Any = None,
    asrf_context: Optional[Mapping[str, Any]] = None,
    key_field: str = "chunk_id",
    distinction_fields: Sequence[str] = ("text", "doc_id"),
    asserted_pairs: Optional[Sequence[Tuple[str, str]]] = None,
    irreflexivity_declared: bool = True,
    scope_declared: bool = True,
    max_token_budget_override: Optional[int] = None,
    tamper_loss_ledger: bool = False,
    omit_loss_ledger: bool = False,
    **tool_kwargs: Any,
) -> RagMcpPipelineReceipt:
    """Runs the 3-stage AI RAG -> MCP normal-form pipeline:

    Stage 0 (WDNF / PDNF): Candidate distinction cut on retrieved RAG chunks.
    Stage 1 (@coda_mur_projection): Context projection and token-budget loss ledger sealing.
    Stage 2 (@observer_freshness_gate): Observer freshness poset, ASRF guard, and MCP authorization gate.
    """
    wdnf_receipt = evaluate_wdnf_candidate_cut(
        candidates=candidates,
        key_field=key_field,
        distinction_fields=distinction_fields,
        asserted_pairs=asserted_pairs,
        irreflexivity_declared=irreflexivity_declared,
        scope_declared=scope_declared,
    )
    if not wdnf_receipt.admitted:
        return RagMcpPipelineReceipt(
            wdnf_receipt=wdnf_receipt,
            context_envelope=None,
            mcp_receipt=None,
            pipeline_terminal=wdnf_receipt.canonical_terminal,
            certified=False,
            authorized=False,
            tool_executed=False,
        )

    envelope = projection_fn(
        candidates,
        max_token_budget_override=max_token_budget_override,
        tamper_loss_ledger=tamper_loss_ledger,
        omit_loss_ledger=omit_loss_ledger,
    )
    if not envelope.admitted:
        return RagMcpPipelineReceipt(
            wdnf_receipt=wdnf_receipt,
            context_envelope=envelope,
            mcp_receipt=None,
            pipeline_terminal=envelope.canonical_terminal,
            certified=False,
            authorized=False,
            tool_executed=False,
        )

    mcp_receipt = mcp_tool_fn(
        envelope,
        observer_id=observer_id,
        packet_metadata=packet_metadata,
        policy_verifier=policy_verifier,
        asrf_context=asrf_context,
        **tool_kwargs,
    )
    return RagMcpPipelineReceipt(
        wdnf_receipt=wdnf_receipt,
        context_envelope=envelope,
        mcp_receipt=mcp_receipt,
        pipeline_terminal=mcp_receipt.canonical_terminal,
        certified=mcp_receipt.certified,
        authorized=mcp_receipt.authorized,
        tool_executed=mcp_receipt.tool_executed,
    )


def main() -> None:
    """CLI demonstration of the @coda_mur_projection and @observer_freshness_gate RAG/MCP pipeline."""
    print("=" * 80)
    print("DEMO: AI RAG / MCP Pipeline with @coda_mur_projection & @observer_freshness_gate")
    print("=" * 80)

    sample_chunks = [
        {
            "chunk_id": "chk_101",
            "doc_id": "sec_filing_2026_q1",
            "text": "Quarterly revenue reached 420 million dollars with operating margin at 18 percent.",
            "relevance_score": 0.96,
            "raw_embedding_norm": 1.0002,
            "internal_acl_tag": "finance_confidential",
        },
        {
            "chunk_id": "chk_102",
            "doc_id": "sec_filing_2026_q2",
            "text": "Second quarter guidance projects 455 million dollars driven by enterprise subscriptions.",
            "relevance_score": 0.91,
            "raw_embedding_norm": 0.9998,
            "internal_acl_tag": "finance_confidential",
        },
        {
            "chunk_id": "chk_103",
            "doc_id": "risk_register_2026",
            "text": "Supply chain latency in EMEA region remains below five seconds across primary replicas.",
            "relevance_score": 0.84,
            "raw_embedding_norm": 1.0001,
            "internal_acl_tag": "ops_internal",
        },
    ]

    @coda_mur_projection(
        source_fields=(
            "chunk_id",
            "doc_id",
            "text",
            "relevance_score",
            "raw_embedding_norm",
            "internal_acl_tag",
        ),
        target_fields=("chunk_id", "doc_id", "text", "relevance_score"),
        key_field="chunk_id",
        protected_fields=("chunk_id", "doc_id"),
        max_token_budget=18,
    )
    def compress_rag_context(chunks: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "chunk_id": c["chunk_id"],
                "doc_id": c["doc_id"],
                "text": c["text"],
                "relevance_score": c["relevance_score"],
            }
            for c in chunks
        ]

    poset = [
        ObserverSpec("agent_realtime_trading", 5, ("finance_rag",)),
        ObserverSpec("agent_exec_copilot", 30, ("finance_rag", "ops_rag")),
        ObserverSpec("agent_batch_auditor", 300, ("finance_rag", "ops_rag", "archive_rag")),
    ]

    @observer_freshness_gate(observer_poset=poset)
    def execute_mcp_ledger_post(
        envelope: CodaMurContextEnvelope,
        *,
        action: str = "summarize_guidance",
    ) -> Dict[str, Any]:
        return {
            "action": action,
            "retained_chunks": envelope.retained_chunk_count,
            "retained_tokens": envelope.retained_token_count,
            "loss_ledger_digest": (
                envelope.loss_ledger["merkle_digest"] if envelope.loss_ledger else None
            ),
        }

    # Case 1: Certified & Fresh, but NO policy_verifier -> CertifiedNotAuthorized (tool_executed=False)
    res_unauth = run_rag_mcp_pipeline(
        candidates=sample_chunks,
        projection_fn=compress_rag_context,
        mcp_tool_fn=execute_mcp_ledger_post,
        observer_id="agent_exec_copilot",
        packet_metadata={"packet_scope": "finance_rag", "replica_lag_seconds": 12},
        policy_verifier=None,
    )
    print("\n[Case 1: Certified + Fresh, policy_verifier=None]")
    print(f"  WDNF Cut:          {res_unauth.wdnf_receipt.local_terminal} ({res_unauth.wdnf_receipt.canonical_terminal})")
    assert res_unauth.context_envelope is not None
    print(f"  CODA_MUR Route:    {res_unauth.context_envelope.local_route} (tokens: {res_unauth.context_envelope.retained_token_count}/{res_unauth.context_envelope.source_token_count} retained, {res_unauth.context_envelope.truncated_token_count} in LossLedger)")
    assert res_unauth.mcp_receipt is not None
    print(f"  MCP Gate Route:    {res_unauth.mcp_receipt.terminal_route} -> {res_unauth.mcp_receipt.canonical_terminal}")
    print(f"  certified={res_unauth.certified}, authorized={res_unauth.authorized}, tool_executed={res_unauth.tool_executed}")

    # Case 2: Certified + Fresh + Independent policy_verifier -> AuthorizedFresh (tool_executed=True)
    res_auth = run_rag_mcp_pipeline(
        candidates=sample_chunks,
        projection_fn=compress_rag_context,
        mcp_tool_fn=execute_mcp_ledger_post,
        observer_id="agent_exec_copilot",
        packet_metadata={"packet_scope": "finance_rag", "replica_lag_seconds": 12},
        policy_verifier={"verifier_identity": "external_policy_engine_v1", "outcome": "authorized"},
    )
    print("\n[Case 2: Certified + Fresh + Independent policy_verifier]")
    assert res_auth.mcp_receipt is not None
    print(f"  MCP Gate Route:    {res_auth.mcp_receipt.terminal_route} -> {res_auth.mcp_receipt.canonical_terminal}")
    print(f"  certified={res_auth.certified}, authorized={res_auth.authorized}, tool_executed={res_auth.tool_executed}")
    print(f"  Tool Output:       {json.dumps(res_auth.mcp_receipt.tool_output)}")
    print("=" * 80)


if __name__ == "__main__":
    main()
