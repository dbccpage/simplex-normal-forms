"""Primitive WDP / OBNF Witness Micro-Kernel (NF-IR Layer 1).

Unifies normal-form evaluation around the Genesis / Witnessed Difference Programme
(nf.wdp.wdnf, nf.derivation.pdnf, nf.derivation.obnf) primitive triple:

    K = (Carrier X, Collapse/Projection Map F: X -> Y, Protected Law L)

Every normal-form check lowered to NFKernelSpec evaluates:
  1. Level 00 Admitted Cut (WDNF / PDNF):
     - Support floor |X| >= 2 (when require_support_floor=True),
     - Irreflexivity ¬(x Δ x),
     - Constructive witness presence w(x, y) >= 1 with witness multiplicity normalized to
       boolean presence.
  2. Obstruction Relativization (OBNF):
     - Evaluates collisions under F: X -> Y relative to the declared Protected Law L,
     - Extracts a deterministic minimal 2-element counterexample pair
       (ConstructiveWitnessPair) whenever L is violated,
     - Routes admissible collisions to Preserve or Quarantine (with a SHA-256 Merkle-sealed
       LossLedger) and obstructed collisions to Reject / Refuse.

AuthorityEffect: None.
certified_implies_authorized: false.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from normal_forms.domain.relational import FunctionalDependency
from normal_forms.multi_hop_composition import build_sealed_loss_ledger
from normal_forms.reconciliation_example import verify_loss_ledger_integrity


@dataclass(frozen=True)
class ConstructiveWitnessPair:
    """Minimal 2-element constructive witness for a distinction, collision, or violation."""

    left_id: str
    right_id: str
    witness_kind: str
    feature: str
    left_value: Any
    right_value: Any
    collapsed_image: Any = None


@dataclass(frozen=True)
class NFKernelSpec:
    """Declarative specification for the (Carrier, CollapseMap, ProtectedLaw) micro-kernel."""

    contract_id: str
    key_field: str
    distinction_fields: Tuple[str, ...]
    collapse_fields: Tuple[str, ...]
    protected_law_fields: Tuple[str, ...]
    law_mode: str = "functional_dependency"
    require_support_floor: bool = True
    require_loss_ledger_on_admissible_collision: bool = False
    require_irreflexivity_declaration: bool = True
    require_protected_law_declaration: bool = True


@dataclass(frozen=True)
class KernelEvaluationReceipt:
    """Deterministic receipt emitted by evaluate_nf_kernel."""

    contract_id: str
    carrier_size: int
    admitted_cut_ok: bool
    distinction_witnesses: Tuple[ConstructiveWitnessPair, ...]
    admissible_collisions: Tuple[ConstructiveWitnessPair, ...]
    obstructed_collisions: Tuple[ConstructiveWitnessPair, ...]
    minimal_counterexample: Optional[ConstructiveWitnessPair]
    loss_ledger: Optional[Dict[str, Any]]
    local_terminal: str
    canonical_terminal: str
    admitted: bool
    certified: bool
    authorized: bool = False
    authority_effect: str = "None"
    certified_implies_authorized: bool = False
    reason: str = ""


def _row_id(row: Mapping[str, Any], key_field: str, fallback_idx: int) -> str:
    if key_field in row and row[key_field] is not None:
        return str(row[key_field])
    return f"row_{fallback_idx}"


def evaluate_nf_kernel(
    spec: NFKernelSpec,
    carrier_rows: Sequence[Mapping[str, Any]],
    asserted_pairs: Optional[Sequence[Tuple[str, str]]] = None,
    irreflexivity_declared: bool = True,
) -> KernelEvaluationReceipt:
    """Evaluates an NFKernelSpec on a finite carrier of rows and extracts minimal witnesses."""
    n = len(carrier_rows)
    row_ids = [_row_id(r, spec.key_field, i) for i, r in enumerate(carrier_rows)]
    by_id: Dict[str, Mapping[str, Any]] = {
        rid: r for rid, r in zip(row_ids, carrier_rows)
    }

    # 1. Support floor check (|X| >= 2 when required)
    if spec.require_support_floor and n < 2:
        only_id = row_ids[0] if row_ids else "<empty_carrier>"
        cx = ConstructiveWitnessPair(
            left_id=only_id,
            right_id=only_id,
            witness_kind="subsingleton_carrier",
            feature=spec.key_field,
            left_value=only_id,
            right_value=None,
            collapsed_image=None,
        )
        return KernelEvaluationReceipt(
            contract_id=spec.contract_id,
            carrier_size=n,
            admitted_cut_ok=False,
            distinction_witnesses=(),
            admissible_collisions=(),
            obstructed_collisions=(cx,),
            minimal_counterexample=cx,
            loss_ledger=None,
            local_terminal="SubsingletonCollapseRefusal",
            canonical_terminal="Refuse",
            admitted=False,
            certified=False,
            reason=f"Support floor failed: carrier has {n} element(s); kernel requires |X| >= 2.",
        )

    # 2. Irreflexivity declaration check
    if spec.require_irreflexivity_declaration and not irreflexivity_declared:
        first_id = row_ids[0] if row_ids else "<undeclared>"
        cx = ConstructiveWitnessPair(
            left_id=first_id,
            right_id=first_id,
            witness_kind="undeclared_irreflexivity",
            feature=spec.key_field,
            left_value=first_id,
            right_value=first_id,
            collapsed_image=None,
        )
        return KernelEvaluationReceipt(
            contract_id=spec.contract_id,
            carrier_size=n,
            admitted_cut_ok=False,
            distinction_witnesses=(),
            admissible_collisions=(),
            obstructed_collisions=(cx,),
            minimal_counterexample=cx,
            loss_ledger=None,
            local_terminal="RequireIrreflexivityDeclaration",
            canonical_terminal="Refuse",
            admitted=False,
            certified=False,
            reason="Irreflexivity law must be declared before asserting distinctions.",
        )

    # 3. Level 00 WDNF / PDNF distinction evaluation & witness multiplicity erasure
    if asserted_pairs is not None:
        candidate_pairs = list(asserted_pairs)
    else:
        candidate_pairs = [
            (row_ids[i], row_ids[j]) for i in range(n) for j in range(i + 1, n)
        ]

    distinction_witnesses: List[ConstructiveWitnessPair] = []
    seen_normalized_pairs: set[Tuple[str, str]] = set()

    for left_id, right_id in candidate_pairs:
        if left_id == right_id:
            cx = ConstructiveWitnessPair(
                left_id=left_id,
                right_id=right_id,
                witness_kind="self_difference",
                feature=spec.key_field,
                left_value=left_id,
                right_value=right_id,
                collapsed_image=None,
            )
            return KernelEvaluationReceipt(
                contract_id=spec.contract_id,
                carrier_size=n,
                admitted_cut_ok=False,
                distinction_witnesses=tuple(distinction_witnesses),
                admissible_collisions=(),
                obstructed_collisions=(cx,),
                minimal_counterexample=cx,
                loss_ledger=None,
                local_terminal="IrreflexivityViolation",
                canonical_terminal="Reject",
                admitted=False,
                certified=False,
                reason=f"Term '{left_id}' asserted distinct from itself; violates irreflexivity.",
            )

        left_row = by_id.get(left_id, {})
        right_row = by_id.get(right_id, {})
        differing_feat: Optional[str] = None
        for feat in spec.distinction_fields:
            if feat in left_row and feat in right_row and left_row[feat] != right_row[feat]:
                differing_feat = feat
                break

        if differing_feat is None:
            if asserted_pairs is not None:
                probe_feat = (
                    spec.distinction_fields[0]
                    if spec.distinction_fields
                    else spec.key_field
                )
                cx = ConstructiveWitnessPair(
                    left_id=left_id,
                    right_id=right_id,
                    witness_kind="ghost_distinction",
                    feature=probe_feat,
                    left_value=left_row.get(probe_feat),
                    right_value=right_row.get(probe_feat),
                    collapsed_image=None,
                )
                return KernelEvaluationReceipt(
                    contract_id=spec.contract_id,
                    carrier_size=n,
                    admitted_cut_ok=False,
                    distinction_witnesses=tuple(distinction_witnesses),
                    admissible_collisions=(),
                    obstructed_collisions=(cx,),
                    minimal_counterexample=cx,
                    loss_ledger=None,
                    local_terminal="GhostDistinctionViolation",
                    canonical_terminal="Reject",
                    admitted=False,
                    certified=False,
                    reason=(
                        f"Asserted distinction ({left_id}, {right_id}) has zero witnessing "
                        f"differences across {spec.distinction_fields}."
                    ),
                )
            continue

        norm_pair = (min(left_id, right_id), max(left_id, right_id))
        if norm_pair not in seen_normalized_pairs:
            seen_normalized_pairs.add(norm_pair)
            distinction_witnesses.append(
                ConstructiveWitnessPair(
                    left_id=left_id,
                    right_id=right_id,
                    witness_kind="distinction",
                    feature=differing_feat,
                    left_value=left_row.get(differing_feat),
                    right_value=right_row.get(differing_feat),
                    collapsed_image=None,
                )
            )

    # 4. Protected law declaration check (OBNF)
    if spec.require_protected_law_declaration and not spec.protected_law_fields:
        first_id = row_ids[0] if row_ids else "<unrelativized>"
        cx = ConstructiveWitnessPair(
            left_id=first_id,
            right_id=first_id,
            witness_kind="unrelativized_obstruction",
            feature="<missing_protected_law>",
            left_value=None,
            right_value=None,
            collapsed_image=None,
        )
        return KernelEvaluationReceipt(
            contract_id=spec.contract_id,
            carrier_size=n,
            admitted_cut_ok=True,
            distinction_witnesses=tuple(distinction_witnesses),
            admissible_collisions=(),
            obstructed_collisions=(cx,),
            minimal_counterexample=cx,
            loss_ledger=None,
            local_terminal="RequireProtectedLawDeclaration",
            canonical_terminal="Refuse",
            admitted=False,
            certified=False,
            reason="OBNF requires an explicit protected_law_fields declaration to relativize collisions.",
        )

    # 5. Evaluate OBNF Collapse Map & Protected Law by mode
    admissible_collisions: List[ConstructiveWitnessPair] = []
    obstructed_collisions: List[ConstructiveWitnessPair] = []

    if spec.law_mode == "representation_transport":
        # Check if any protected field was dropped from collapse_fields (target_fields)
        dropped_protected = [
            pf for pf in spec.protected_law_fields if pf not in spec.collapse_fields
        ]
        if dropped_protected:
            bad_pf = dropped_protected[0]
            first_id = row_ids[0] if row_ids else "<row_0>"
            second_id = row_ids[1] if len(row_ids) > 1 else first_id
            cx = ConstructiveWitnessPair(
                left_id=first_id,
                right_id=second_id,
                witness_kind="obstructed_collision",
                feature=bad_pf,
                left_value=carrier_rows[0].get(bad_pf) if carrier_rows else None,
                right_value=None,
                collapsed_image="<dropped_protected_field>",
            )
            return KernelEvaluationReceipt(
                contract_id=spec.contract_id,
                carrier_size=n,
                admitted_cut_ok=True,
                distinction_witnesses=tuple(distinction_witnesses),
                admissible_collisions=(),
                obstructed_collisions=(cx,),
                minimal_counterexample=cx,
                loss_ledger=None,
                local_terminal="TransportViolation",
                canonical_terminal="Reject",
                admitted=False,
                certified=False,
                reason=f"Protected field '{bad_pf}' was dropped from target projection {spec.collapse_fields}.",
            )

        # Check for missing/null protected fields or duplicate protected keys across rows
        seen_prot_sig: Dict[Tuple[Any, ...], Tuple[str, Mapping[str, Any]]] = {}
        for idx, (rid, row) in enumerate(zip(row_ids, carrier_rows)):
            for pf in spec.protected_law_fields:
                if pf not in row or row[pf] is None:
                    cx = ConstructiveWitnessPair(
                        left_id=rid,
                        right_id=rid,
                        witness_kind="obstructed_collision",
                        feature=pf,
                        left_value=row.get(pf),
                        right_value=None,
                        collapsed_image="<null_protected_field>",
                    )
                    return KernelEvaluationReceipt(
                        contract_id=spec.contract_id,
                        carrier_size=n,
                        admitted_cut_ok=True,
                        distinction_witnesses=tuple(distinction_witnesses),
                        admissible_collisions=(),
                        obstructed_collisions=(cx,),
                        minimal_counterexample=cx,
                        loss_ledger=None,
                        local_terminal="TransportViolation",
                        canonical_terminal="Reject",
                        admitted=False,
                        certified=False,
                        reason=f"Row '{rid}' is missing or has null protected field '{pf}'.",
                    )
            prot_sig = tuple(row[pf] for pf in spec.protected_law_fields)
            if prot_sig in seen_prot_sig:
                prev_id, prev_row = seen_prot_sig[prot_sig]
                if prev_id != rid:
                    cx = ConstructiveWitnessPair(
                        left_id=prev_id,
                        right_id=rid,
                        witness_kind="obstructed_collision",
                        feature=spec.protected_law_fields[0],
                        left_value=prev_row.get(spec.protected_law_fields[0]),
                        right_value=row.get(spec.protected_law_fields[0]),
                        collapsed_image=prot_sig,
                    )
                    obstructed_collisions.append(cx)
            else:
                seen_prot_sig[prot_sig] = (rid, row)

        if obstructed_collisions:
            first_cx = obstructed_collisions[0]
            return KernelEvaluationReceipt(
                contract_id=spec.contract_id,
                carrier_size=n,
                admitted_cut_ok=True,
                distinction_witnesses=tuple(distinction_witnesses),
                admissible_collisions=(),
                obstructed_collisions=tuple(obstructed_collisions),
                minimal_counterexample=first_cx,
                loss_ledger=None,
                local_terminal="TransportViolation",
                canonical_terminal="Reject",
                admitted=False,
                certified=False,
                reason=(
                    f"Protected determinant collision between '{first_cx.left_id}' and "
                    f"'{first_cx.right_id}' on {spec.protected_law_fields}."
                ),
            )

        erased_attrs = tuple(
            sorted(set(spec.distinction_fields) - set(spec.collapse_fields))
        )
        non_prot_targets = tuple(
            f for f in spec.collapse_fields if f not in spec.protected_law_fields
        )
        if non_prot_targets:
            seen_nk: Dict[Tuple[Any, ...], str] = {}
            for rid, row in zip(row_ids, carrier_rows):
                nk_sig = tuple(row.get(f) for f in non_prot_targets)
                if nk_sig in seen_nk and seen_nk[nk_sig] != rid:
                    admissible_collisions.append(
                        ConstructiveWitnessPair(
                            left_id=seen_nk[nk_sig],
                            right_id=rid,
                            witness_kind="admissible_collision",
                            feature=non_prot_targets[0],
                            left_value=row.get(non_prot_targets[0]),
                            right_value=row.get(non_prot_targets[0]),
                            collapsed_image=nk_sig,
                        )
                    )
                else:
                    seen_nk[nk_sig] = rid

        if erased_attrs:
            first_erased = erased_attrs[0]
            if not admissible_collisions and n >= 2:
                admissible_collisions.append(
                    ConstructiveWitnessPair(
                        left_id=row_ids[0],
                        right_id=row_ids[1],
                        witness_kind="admissible_collision",
                        feature=first_erased,
                        left_value=carrier_rows[0].get(first_erased),
                        right_value=carrier_rows[1].get(first_erased),
                        collapsed_image="<erased_attribute_quotient>",
                    )
                )
            if spec.require_loss_ledger_on_admissible_collision:
                ledger = build_sealed_loss_ledger(
                    erased_attributes=erased_attrs,
                    source_rows=carrier_rows,
                    key_attribute=spec.key_field,
                )
                ok_seal, _ = verify_loss_ledger_integrity(ledger)
                return KernelEvaluationReceipt(
                    contract_id=spec.contract_id,
                    carrier_size=n,
                    admitted_cut_ok=True,
                    distinction_witnesses=tuple(distinction_witnesses),
                    admissible_collisions=tuple(admissible_collisions),
                    obstructed_collisions=(),
                    minimal_counterexample=None,
                    loss_ledger=ledger,
                    local_terminal="DegradedTransportWithLoss" if ok_seal else "TransportViolation",
                    canonical_terminal="Quarantine" if ok_seal else "Reject",
                    admitted=ok_seal,
                    certified=ok_seal,
                    reason=(
                        f"Lossy quotient projection certified with sealed LossLedger "
                        f"over erased attributes {list(erased_attrs)}."
                    ),
                )

        return KernelEvaluationReceipt(
            contract_id=spec.contract_id,
            carrier_size=n,
            admitted_cut_ok=True,
            distinction_witnesses=tuple(distinction_witnesses),
            admissible_collisions=tuple(admissible_collisions),
            obstructed_collisions=(),
            minimal_counterexample=None,
            loss_ledger=None,
            local_terminal="TransportOk" if spec.contract_id == "nf.coda.mur.transport" else "AcceptAdmissibleCollision",
            canonical_terminal="Preserve",
            admitted=True,
            certified=True,
            reason="Projection preserves all protected determinants with zero unsealed attribute loss.",
        )

    # Default law_mode == "functional_dependency" (or general OBNF collision check):
    # First check that every row contains all collapse_fields and protected_law_fields
    required_cols = tuple(dict.fromkeys(spec.collapse_fields + spec.protected_law_fields))
    for rid, row in zip(row_ids, carrier_rows):
        for col in required_cols:
            if col not in row:
                cx = ConstructiveWitnessPair(
                    left_id=rid,
                    right_id=rid,
                    witness_kind="obstructed_collision",
                    feature=col,
                    left_value=None,
                    right_value=None,
                    collapsed_image="<missing_attribute>",
                )
                return KernelEvaluationReceipt(
                    contract_id=spec.contract_id,
                    carrier_size=n,
                    admitted_cut_ok=True,
                    distinction_witnesses=tuple(distinction_witnesses),
                    admissible_collisions=(),
                    obstructed_collisions=(cx,),
                    minimal_counterexample=cx,
                    loss_ledger=None,
                    local_terminal="PromoteToObstruction",
                    canonical_terminal="Reject",
                    admitted=False,
                    certified=False,
                    reason=f"Row '{rid}' is missing attribute '{col}' required by kernel law.",
                )

    for i in range(n):
        r_i = carrier_rows[i]
        id_i = row_ids[i]
        img_i = tuple(r_i[c] for c in spec.collapse_fields)
        for j in range(i + 1, n):
            r_j = carrier_rows[j]
            id_j = row_ids[j]
            img_j = tuple(r_j[c] for c in spec.collapse_fields)
            if img_i != img_j:
                continue

            # Collision under F: img_i == img_j. Check protected law L:
            violating_feat: Optional[str] = None
            for pf in spec.protected_law_fields:
                if r_i[pf] != r_j[pf]:
                    violating_feat = pf
                    break

            if violating_feat is not None:
                obstructed_collisions.append(
                    ConstructiveWitnessPair(
                        left_id=id_i,
                        right_id=id_j,
                        witness_kind="obstructed_collision",
                        feature=violating_feat,
                        left_value=r_i[violating_feat],
                        right_value=r_j[violating_feat],
                        collapsed_image=img_i,
                    )
                )
            else:
                # Protected law survives collision on (id_i, id_j)
                diff_feat = spec.distinction_fields[0] if spec.distinction_fields else spec.key_field
                for df in spec.distinction_fields:
                    if r_i.get(df) != r_j.get(df):
                        diff_feat = df
                        break
                admissible_collisions.append(
                    ConstructiveWitnessPair(
                        left_id=id_i,
                        right_id=id_j,
                        witness_kind="admissible_collision",
                        feature=diff_feat,
                        left_value=r_i.get(diff_feat),
                        right_value=r_j.get(diff_feat),
                        collapsed_image=img_i,
                    )
                )

    if obstructed_collisions:
        first_cx = obstructed_collisions[0]
        return KernelEvaluationReceipt(
            contract_id=spec.contract_id,
            carrier_size=n,
            admitted_cut_ok=True,
            distinction_witnesses=tuple(distinction_witnesses),
            admissible_collisions=tuple(admissible_collisions),
            obstructed_collisions=tuple(obstructed_collisions),
            minimal_counterexample=first_cx,
            loss_ledger=None,
            local_terminal="PromoteToObstruction",
            canonical_terminal="Reject",
            admitted=False,
            certified=False,
            reason=(
                f"Collision on {spec.collapse_fields}={first_cx.collapsed_image} between "
                f"'{first_cx.left_id}' and '{first_cx.right_id}' violates protected field "
                f"'{first_cx.feature}': {first_cx.left_value!r} != {first_cx.right_value!r}."
            ),
        )

    return KernelEvaluationReceipt(
        contract_id=spec.contract_id,
        carrier_size=n,
        admitted_cut_ok=True,
        distinction_witnesses=tuple(distinction_witnesses),
        admissible_collisions=tuple(admissible_collisions),
        obstructed_collisions=(),
        minimal_counterexample=None,
        loss_ledger=None,
        local_terminal="AcceptAdmissibleCollision" if admissible_collisions else "AdmittedCut",
        canonical_terminal="Preserve",
        admitted=True,
        certified=True,
        reason="All carrier collisions preserve the declared protected law.",
    )


def lower_fd_to_kernel_spec(
    fd: FunctionalDependency,
    key_field: str,
    heading: Sequence[str],
    contract_id: str = "nf.classical.bcnf",
    require_support_floor: bool = False,
) -> NFKernelSpec:
    """Lowers a classical FunctionalDependency X -> Y into an NFKernelSpec.

    Under WDP/OBNF, X -> Y states that when the projection F_X onto determinant X
    collides two tuples (F_X(r_1) == F_X(r_2)), the protected law on dependent Y
    must hold (r_1[Y] == r_2[Y]).
    """
    det_tuple = tuple(sorted(fd.determinant))
    dep_tuple = tuple(sorted(fd.dependent))
    return NFKernelSpec(
        contract_id=contract_id,
        key_field=key_field,
        distinction_fields=tuple(heading),
        collapse_fields=det_tuple,
        protected_law_fields=dep_tuple,
        law_mode="functional_dependency",
        require_support_floor=require_support_floor,
        require_loss_ledger_on_admissible_collision=False,
    )


def evaluate_fds_via_kernel(
    rows: Sequence[Mapping[str, Any]],
    dependencies: Iterable[FunctionalDependency],
    key_field: str,
    heading: Sequence[str],
    contract_id: str = "nf.classical.bcnf",
) -> KernelEvaluationReceipt:
    """Evaluates a family of functional dependencies via lowered NFKernelSpecs."""
    fd_list = list(dependencies)
    if not fd_list:
        spec = NFKernelSpec(
            contract_id=contract_id,
            key_field=key_field,
            distinction_fields=tuple(heading),
            collapse_fields=(key_field,),
            protected_law_fields=tuple(heading),
            law_mode="functional_dependency",
            require_support_floor=False,
        )
        return evaluate_nf_kernel(spec, rows)

    last_receipt: Optional[KernelEvaluationReceipt] = None
    for fd in fd_list:
        spec = lower_fd_to_kernel_spec(
            fd=fd,
            key_field=key_field,
            heading=heading,
            contract_id=contract_id,
            require_support_floor=False,
        )
        receipt = evaluate_nf_kernel(spec, rows)
        if not receipt.admitted:
            return receipt
        last_receipt = receipt

    assert last_receipt is not None
    return last_receipt


def lower_coda_mur_to_kernel_spec(
    source_fields: Sequence[str],
    target_fields: Sequence[str],
    key_field: str,
    protected_fields: Sequence[str],
    contract_id: str = "nf.coda.mur.transport",
    require_support_floor: bool = False,
) -> NFKernelSpec:
    """Lowers a CODA_MUR representation projection into an NFKernelSpec."""
    src_tuple = tuple(source_fields)
    tgt_tuple = tuple(target_fields)
    prot_tuple = tuple(protected_fields)
    erased = set(src_tuple) - set(tgt_tuple)
    return NFKernelSpec(
        contract_id=contract_id,
        key_field=key_field,
        distinction_fields=src_tuple,
        collapse_fields=tgt_tuple,
        protected_law_fields=prot_tuple,
        law_mode="representation_transport",
        require_support_floor=require_support_floor,
        require_loss_ledger_on_admissible_collision=bool(erased),
    )
