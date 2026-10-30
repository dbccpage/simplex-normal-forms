# Rational cochain quotient section (`RATIONAL_QUOTIENT`)

> **Contract ID:** `nf.change.rational_quotient` | **Family:** `change` | **Index Status:** `active` | **AuthorityEffect:** `None`

**[⬅ Back to Wiki Home](Home)** | **[View SVG Diagram](images/nf.change.rational_quotient.svg)**

---

## 1. Executive Summary & Metadata

Rational cochain quotient section (RATIONAL_QUOTIENT) enforces structural normalization and explicit defect routing in the change regime.

| Property | Value |
| :--- | :--- |
| **Canonical ID** | `nf.change.rational_quotient` |
| **Short Name** | `RATIONAL_QUOTIENT` |
| **Full Name** | Rational cochain quotient section |
| **Family** | `change` (Data in Motion & Boundary-Quotient Incremental Maintenance Contracts (BQNF & Cochain Repair)) |
| **Qualification** | Extended Form Contract (Normal Form Contract) |
| **Data / Math Posture** | in_transformation |
| **Index Status** | `active` |
| **Theory Status** | `proposed` |
| **Verification Status** | `executable` |
| **Contract Version** | `v1` |
| **Governance Fence** | `AuthorityEffect: None` (`certified_implies_authorized: false`) |

---

## 2. Visual Architecture & Normalization Diagram

![Rational cochain quotient section (RATIONAL_QUOTIENT) Diagram](images/nf.change.rational_quotient.svg)

---

## 3. Concrete Worked Example & Mechanism

### Visual Transition Summary

| Stage | Carrier / Operator | Concrete State / Invariant |
| :--- | :--- | :--- |
| **1. Before / Candidate Input** | `Input Carrier (RATIONAL_QUOTIENT Candidate)` | Anomaly risk: Different ; representatives of a declared ; equivalence class appearing as... |
| **2. Normalization / Gate** | `RATIONAL_QUOTIENT Verification Gate` | `The declared equivalence...` (`certified_implies_authorized: false`) |
| **3. After / Certified Output** | `Certified RATIONAL_QUOTIENT Output` | Invariant: ; ['fixed_ordered_ambient_carrier', ; 'declared_gauge_action'] |

---

## 4. The Four-Pillar Quadrilateral & Non-Claims

Every contract in `simplex-normal-forms` is evaluated against the **Four-Pillar Quadrilateral** defined in `contracts/_golden_nfs/standard.yaml`:

| Pillar | Requirement | Contract Specification for `nf.change.rational_quotient` |
| :--- | :--- | :--- |
| **Pillar I: Excludes Anomaly** | Name and eliminate a specific class of data or state defects. | Different representatives of a declared equivalence class appearing as distinct normal representatives |
| **Pillar II: Preserves Invariant** | State the structural invariant and protected skeleton preserved across transitions. | **Invariant:** The declared equivalence class<br>**Protected Skeleton:** ['fixed_ordered_ambient_carrier', 'declared_gauge_action'] |
| **Pillar III: Lossless Reconstruction** | State the non-loss reconstruction operator (join, direct sum, pullback, or replay). | Lossless reconstruction under declared projection, direct sum, or pullback operators. |
| **Pillar IV: Syntactic Decidability** | State how conformance is decided from declared constraints without unbudgeted scans. | Decidable from declared schema and witness metadata within bounded evaluation budgets. |

### Explicit Non-Claims (`certified_implies_authorized: false`)

- No polynomial algorithm for arbitrary succinct fermionic Hamiltonians
- No normalization across changes of labels, bases, carrier size, or equivalence relation

---

## 5. Operational Verification & Terminal Routing

### 5.1 Required Declarations

- ordered finite carrier
- exact input
- declared gauge action

### 5.2 Required Evidence

- **exact_gauge_witness**: rational_vector

### 5.3 Validation Criteria

| Criterion ID | Name | Condition |
| :--- | :--- | :--- |
| `criterion` | Check | replay the returned gauge witness exactly |
| `criterion` | Check | check the representative condition |

### 5.4 Terminal Route Map

Every evaluation terminates in a declared local route mapped to a canonical terminal in `standard.yaml`:

| Local Terminal Route | Canonical Terminal |
| :--- | :--- |
| `Normalized` | `Preserve` |
| `Refused` | `Refuse` |

### 5.5 Declared Failure Modes

_All defects route explicitly through the Terminal Route Map above._

---

## 6. Epistemic Claim Hygiene Quadrant

In accordance with the repository's epistemic claim discipline:

1. **What it supports:**
   - Supports syntactic and operational checking of `nf.change.rational_quotient` (`RATIONAL_QUOTIENT`) against its declared schema, boundary constraints, and witness obligations in this model.
   - Supports deterministic terminal routing (`Normalized, Refused`) when required declarations or invariants fail.
2. **What it does not support:**
   - Does not confer operational authority (`AuthorityEffect: None`, `certified_implies_authorized: false`).
   - Does not claim semantic truth of undeclared external processes or unverified upstream inputs beyond the declaredprotected skeleton.
3. **The narrowest defensible claim:**
   - Within the declared substrate `in_transformation`, this contract enforces that `Different representatives of a declared equivalence class appearing as distinct normal representatives` is either excluded under `The declared equivalence class` or routed to an explicit refusal/recovery terminal.
4. **The next test needed:**
   - Property-based falsification and mutation testing across boundary edge cases and composed multi-step pipelines for `nf.change.rational_quotient`.

---

## 7. Canonical YAML Contract (`contracts/nf.change.rational_quotient.yaml`)

<details>
<summary><strong>Click to expand full canonical YAML contract (contracts/nf.change.rational_quotient.yaml)</strong></summary>

```yaml
schema_version: smplx.nf.contract.v1
contract_kind: normal_form_contract
identity:
  version: v1
  status: active
  theory_status: proposed
  contract_status: active
  verification_status: executable
  family: change
  id: nf.change.rational_quotient
  name: Rational cochain quotient section
  short_name: RATIONAL_QUOTIENT
classification:
  hierarchy_level: normal_form
  subject_kind:
  - finite_quotient
  data_posture: in_transformation
  mathematical_posture: formal_algebraic
purpose:
  excludes_anomaly: Different representatives of a declared equivalence class appearing
    as distinct normal representatives
  preserves_invariant: The declared equivalence class
  protected_skeleton:
  - fixed_ordered_ambient_carrier
  - declared_gauge_action
  erased_structure:
  - declared_gauge_redundancy
  non_claims:
  - No polynomial algorithm for arbitrary succinct fermionic Hamiltonians
  - No normalization across changes of labels, bases, carrier size, or equivalence
    relation
declarations_required:
- ordered finite carrier
- exact input
- declared gauge action
evidence_required:
- exact_gauge_witness: rational_vector
validation_criteria:
- replay the returned gauge witness exactly
- check the representative condition
terminal_routes:
- Normalized
- Refused
terminal_route_map:
  Normalized: Preserve
  Refused: Refuse
certification:
  certificate_required: true
  certificate_kind: explicit_gauge_witness
  obstruction_class_required: true
  loss_ledger_required: false
  loss_ledger_trigger_id: null
  verifier_required: true
authorization:
  authorized_by: null
  certified_implies_authorized: false
extensions:
  normalization:
    kind: canonicalizer
    claim_scope: A normal form for the finite rational additive quotient; its L1 norm
      is not generally the quotient distance.
    domain: Q^m with a fixed exact rational matrix d0 and ordered coordinates
    equivalence: c ~ c_prime iff c-c_prime lies in im(d0)
    normalizer: code/bqnf_sign_evaluator.py:BQNFSignEvaluator.normalize_cochain
    representative_condition: All pivot coordinates of RREF(d0 transpose) are zero
    laws:
      soundness: c - N(c) = d0 * returned_gauge
      idempotence: N(N(c)) = N(c)
      completeness: N(c) = N(c_prime) iff c-c_prime lies in im(d0)
      determinism: Fixed coordinate order and the unique RREF row-space basis determine
        N
    evidence:
    - ../docs/normal_form_audit.md
    - ../code/tests/test_normal_form_laws.py
quadrilateral:
  qualifies_as_true_normal_form: false
```

</details>
