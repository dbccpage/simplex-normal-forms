# Gauge Experimental Extension (`XGauge`)

> **Contract ID:** `nf.experimental.gauge` | **Family:** `experimental` | **Index Status:** `draft` | **AuthorityEffect:** `None`

**[⬅ Back to Wiki Home](Home)** | **[View SVG Diagram](images/nf.experimental.gauge.svg)**

---

## 1. Executive Summary & Metadata

Gauge Experimental Extension (XGauge) enforces structural normalization and explicit defect routing in the experimental regime.

| Property | Value |
| :--- | :--- |
| **Canonical ID** | `nf.experimental.gauge` |
| **Short Name** | `XGauge` |
| **Full Name** | Gauge Experimental Extension |
| **Family** | `experimental` (Bounded Quantum-Classical, Contextuality, Quantifier Alternation & Agent-State Contracts) |
| **Qualification** | Extended Form Contract (Normal Form Contract) |
| **Data / Math Posture** | at_rest |
| **Index Status** | `draft` |
| **Theory Status** | `experimental` |
| **Verification Status** | `absent` |
| **Contract Version** | `v1` |
| **Governance Fence** | `AuthorityEffect: None` (`certified_implies_authorized: false`) |

---

## 2. Visual Architecture & Normalization Diagram

![Gauge Experimental Extension (XGauge) Diagram](images/nf.experimental.gauge.svg)

---

## 3. Concrete Worked Example & Mechanism

### Visual Transition Summary

| Stage | Carrier / Operator | Concrete State / Invariant |
| :--- | :--- | :--- |
| **1. Before / Candidate Input** | `Input Carrier (XGauge Candidate)` | Anomaly risk: gauge drift |
| **2. Normalization / Gate** | `XGauge Verification Gate` | `protected_skeleton_must_be_declared_before_transport` (`certified_implies_authorized: false`) |
| **3. After / Certified Output** | `Certified XGauge Output` | Invariant: ['source_regime', ; 'target_regime', ; 'protected_skeleton',... |

---

## 4. The Four-Pillar Quadrilateral & Non-Claims

Every contract in `simplex-normal-forms` is evaluated against the **Four-Pillar Quadrilateral** defined in `contracts/_golden_nfs/standard.yaml`:

| Pillar | Requirement | Contract Specification for `nf.experimental.gauge` |
| :--- | :--- | :--- |
| **Pillar I: Excludes Anomaly** | Name and eliminate a specific class of data or state defects. | gauge drift |
| **Pillar II: Preserves Invariant** | State the structural invariant and protected skeleton preserved across transitions. | **Invariant:** protected_skeleton_must_be_declared_before_transport<br>**Protected Skeleton:** ['source_regime', 'target_regime', 'protected_skeleton', 'allowed_gauge_transformations', 'loss_ledger_policy'] |
| **Pillar III: Lossless Reconstruction** | State the non-loss reconstruction operator (join, direct sum, pullback, or replay). | Lossless reconstruction under declared projection, direct sum, or pullback operators. |
| **Pillar IV: Syntactic Decidability** | State how conformance is decided from declared constraints without unbudgeted scans. | Decidable from declared schema and witness metadata within bounded evaluation budgets. |

### Explicit Non-Claims (`certified_implies_authorized: false`)

- does not make quantum market legal or physical domain claims part of the core taxonomy
- does not promote experimental data regimes to normal forms

---

## 5. Operational Verification & Terminal Routing

### 5.1 Required Declarations

- source_regime
- target_regime
- protected_skeleton
- allowed_gauge_transformations
- loss_ledger_policy

### 5.2 Required Evidence

- transformation_trace
- preserved_skeleton_witness
- loss_ledger_when_distinctions_are_erased

### 5.3 Validation Criteria

| Criterion ID | Name | Condition |
| :--- | :--- | :--- |
| `criterion` | Check | protected_skeleton_must_be_declared_before_transport |
| `criterion` | Check | erased_distinctions_require_loss_ledger |
| `criterion` | Check | experimental_claims_must_remain_quarantined |

### 5.4 Terminal Route Map

Every evaluation terminates in a declared local route mapped to a canonical terminal in `standard.yaml`:

| Local Terminal Route | Canonical Terminal |
| :--- | :--- |
| `Preserve` | `Preserve` |
| `Lift` | `Lift` |
| `Escalate` | `Escalate` |
| `Unsupported` | `Unsupported` |
| `ClosureFailure` | `ClosureFailure` |
| `BudgetUnknown` | `BudgetUnknown` |
| `Quarantine` | `Quarantine` |
| `Refuse` | `Refuse` |

### 5.5 Declared Failure Modes

_All defects route explicitly through the Terminal Route Map above._

---

## 6. Epistemic Claim Hygiene Quadrant

In accordance with the repository's epistemic claim discipline:

1. **What it supports:**
   - Supports syntactic and operational checking of `nf.experimental.gauge` (`XGauge`) against its declared schema, boundary constraints, and witness obligations in this model.
   - Supports deterministic terminal routing (`Preserve, Lift, Escalate, Unsupported`) when required declarations or invariants fail.
2. **What it does not support:**
   - Does not confer operational authority (`AuthorityEffect: None`, `certified_implies_authorized: false`).
   - Does not claim semantic truth of undeclared external processes or unverified upstream inputs beyond the declaredprotected skeleton.
3. **The narrowest defensible claim:**
   - Within the declared substrate `at_rest`, this contract enforces that `gauge drift` is either excluded under `protected_skeleton_must_be_declared_before_transport` or routed to an explicit refusal/recovery terminal.
4. **The next test needed:**
   - Property-based falsification and mutation testing across boundary edge cases and composed multi-step pipelines for `nf.experimental.gauge`.

---

## 7. Canonical YAML Contract (`contracts/nf.experimental.gauge.yaml`)

<details>
<summary><strong>Click to expand full canonical YAML contract (contracts/nf.experimental.gauge.yaml)</strong></summary>

```yaml
schema_version: smplx.nf.contract.v0
contract_kind: normal_form_contract
identity:
  id: nf.experimental.gauge
  name: Gauge Experimental Extension
  short_name: XGauge
  version: v1
  status: draft
  family: experimental
  theory_status: experimental
  contract_status: draft
  verification_status: absent
classification:
  hierarchy_level: normal_form
  subject_kind:
  - data_under_gauge_or_higher_regime
  data_posture: at_rest
  mathematical_posture: operational
purpose:
  excludes_anomaly: gauge drift
  preserves_invariant: protected_skeleton_must_be_declared_before_transport
  protected_skeleton:
  - source_regime
  - target_regime
  - protected_skeleton
  - allowed_gauge_transformations
  - loss_ledger_policy
  erased_structure: []
  non_claims:
  - does not make quantum market legal or physical domain claims part of the core
    taxonomy
  - does not promote experimental data regimes to normal forms
declarations_required:
- source_regime
- target_regime
- protected_skeleton
- allowed_gauge_transformations
- loss_ledger_policy
evidence_required:
- transformation_trace
- preserved_skeleton_witness
- loss_ledger_when_distinctions_are_erased
validation_criteria:
- protected_skeleton_must_be_declared_before_transport
- erased_distinctions_require_loss_ledger
- experimental_claims_must_remain_quarantined
terminal_routes:
- Preserve
- Lift
- Escalate
- Unsupported
- ClosureFailure
- BudgetUnknown
- Quarantine
- Refuse
certification:
  certificate_required: true
  certificate_kind: experimental_gauge_certificate
  obstruction_class_required: false
  loss_ledger_required: false
  verifier_required: false
terminal_route_map:
  Preserve: Preserve
  Lift: Lift
  Escalate: Escalate
  Unsupported: Unsupported
  ClosureFailure: ClosureFailure
  BudgetUnknown: BudgetUnknown
  Quarantine: Quarantine
  Refuse: Refuse
authorization:
  authorized_by: null
  certified_implies_authorized: false
definition:
  source: coda_all_universe/mssn_sn_tower/definitions.md
  formal_statement: gauge drift. protected_skeleton_must_be_declared_before_transport
  quadrilateral:
    qualifies_as_true_normal_form: false
    qualification_gap: reconstruction_is_not_a_relational_project_join
    anomaly_exclusion: gauge drift
    lossless_join:
      status: declared_reconstruction
      statement: protected_skeleton_must_be_declared_before_transport
    dependency_preservation:
      status: declared_with_the_invariant
      statement: The preserved invariant stays on the declared schema. This form does
        not state a functional-dependency projection of a flat relvar decomposition.
    syntactic_decision:
      status: declaration_decidable
      statement: The check reads the declared constraints and validation criteria.
        One unrecorded runtime image is not the decider.
schema_ref: ./normal_form_contract_schema.yaml
```

</details>
