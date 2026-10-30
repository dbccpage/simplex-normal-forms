# Freshness Normal Form (`FNF`)

> **Contract ID:** `nf.epistemic.freshness` | **Family:** `epistemic` | **Index Status:** `draft` | **AuthorityEffect:** `None`

**[⬅ Back to Wiki Home](Home)** | **[View SVG Diagram](images/nf.epistemic.freshness.svg)**

---

## 1. Executive Summary & Metadata

Freshness Normal Form (FNF) enforces structural normalization and explicit defect routing in the epistemic regime.

| Property | Value |
| :--- | :--- |
| **Canonical ID** | `nf.epistemic.freshness` |
| **Short Name** | `FNF` |
| **Full Name** | Freshness Normal Form |
| **Family** | `epistemic` (Observer-Relative Epistemic, Freshness, Context, Provenance & Distinguishability Contracts) |
| **Qualification** | Extended Form Contract (Normal Form Contract) |
| **Data / Math Posture** | in_motion |
| **Index Status** | `draft` |
| **Theory Status** | `proposed` |
| **Verification Status** | `absent` |
| **Contract Version** | `v0` |
| **Governance Fence** | `AuthorityEffect: None` (`certified_implies_authorized: false`) |

---

## 2. Visual Architecture & Normalization Diagram

![Freshness Normal Form (FNF) Diagram](images/nf.epistemic.freshness.svg)

---

## 3. Concrete Worked Example & Mechanism

### Visual Transition Summary

| Stage | Carrier / Operator | Concrete State / Invariant |
| :--- | :--- | :--- |
| **1. Before / Candidate Input** | `Input Carrier (FNF Candidate)` | Anomaly risk: timeless truth |
| **2. Normalization / Gate** | `FNF Verification Gate` | `every read declares tempo...` (`certified_implies_authorized: false`) |
| **3. After / Certified Output** | `Certified FNF Output` | Invariant: ['read_timestamp', ; 'replica_lag', 'cache_age', ; 'invalidation_status',... |

---

## 4. The Four-Pillar Quadrilateral & Non-Claims

Every contract in `simplex-normal-forms` is evaluated against the **Four-Pillar Quadrilateral** defined in `contracts/_golden_nfs/standard.yaml`:

| Pillar | Requirement | Contract Specification for `nf.epistemic.freshness` |
| :--- | :--- | :--- |
| **Pillar I: Excludes Anomaly** | Name and eliminate a specific class of data or state defects. | timeless truth |
| **Pillar II: Preserves Invariant** | State the structural invariant and protected skeleton preserved across transitions. | **Invariant:** every read declares temporal boundary and invalidation status<br>**Protected Skeleton:** ['read_timestamp', 'replica_lag', 'cache_age', 'invalidation_status', 'freshness_sla'] |
| **Pillar III: Lossless Reconstruction** | State the non-loss reconstruction operator (join, direct sum, pullback, or replay). | Lossless reconstruction under declared projection, direct sum, or pullback operators. |
| **Pillar IV: Syntactic Decidability** | State how conformance is decided from declared constraints without unbudgeted scans. | Decidable from declared schema and witness metadata within bounded evaluation budgets. |

### Explicit Non-Claims (`certified_implies_authorized: false`)

- does not replace BQNF repair decision

---

## 5. Operational Verification & Terminal Routing

### 5.1 Required Declarations

- read_timestamp
- replica_lag
- cache_age
- invalidation_status
- freshness_sla

### 5.2 Required Evidence

- clock_source
- lag_metrics from replica or cache layer

### 5.3 Validation Criteria

| Criterion ID | Name | Condition |
| :--- | :--- | :--- |
| `criterion` | Check | query result never served without read_timestamp |
| `criterion` | Check | SLA breach terminalizes or escalates |
| `criterion` | Check | pairs with BQNF Invalidate when cache stale |

### 5.4 Terminal Route Map

Every evaluation terminates in a declared local route mapped to a canonical terminal in `standard.yaml`:

| Local Terminal Route | Canonical Terminal |
| :--- | :--- |
| `Fresh` | `Preserve` |
| `Stale` | `Escalate` |
| `LagExceeded` | `Invalidate` |
| `Invalidate` | `Invalidate` |
| `Refuse` | `Refuse` |

### 5.5 Declared Failure Modes

_All defects route explicitly through the Terminal Route Map above._

---

## 6. Epistemic Claim Hygiene Quadrant

In accordance with the repository's epistemic claim discipline:

1. **What it supports:**
   - Supports syntactic and operational checking of `nf.epistemic.freshness` (`FNF`) against its declared schema, boundary constraints, and witness obligations in this model.
   - Supports deterministic terminal routing (`Fresh, Stale, LagExceeded, Invalidate`) when required declarations or invariants fail.
2. **What it does not support:**
   - Does not confer operational authority (`AuthorityEffect: None`, `certified_implies_authorized: false`).
   - Does not claim semantic truth of undeclared external processes or unverified upstream inputs beyond the declaredprotected skeleton.
3. **The narrowest defensible claim:**
   - Within the declared substrate `in_motion`, this contract enforces that `timeless truth` is either excluded under `every read declares temporal boundary and invalidation status` or routed to an explicit refusal/recovery terminal.
4. **The next test needed:**
   - Property-based falsification and mutation testing across boundary edge cases and composed multi-step pipelines for `nf.epistemic.freshness`.

---

## 7. Canonical YAML Contract (`contracts/nf.epistemic.freshness.yaml`)

<details>
<summary><strong>Click to expand full canonical YAML contract (contracts/nf.epistemic.freshness.yaml)</strong></summary>

```yaml
schema_version: smplx.nf.contract.v0
contract_kind: normal_form_contract
identity:
  id: nf.epistemic.freshness
  name: Freshness Normal Form
  short_name: FNF
  version: v0
  status: draft
  family: epistemic
  theory_status: proposed
  contract_status: draft
  verification_status: absent
classification:
  hierarchy_level: normal_form
  subject_kind:
  - distributed_claim
  - query_shape
  data_posture: in_motion
  mathematical_posture: operational
purpose:
  excludes_anomaly: timeless truth
  preserves_invariant: every read declares temporal boundary and invalidation status
  protected_skeleton:
  - read_timestamp
  - replica_lag
  - cache_age
  - invalidation_status
  - freshness_sla
  erased_structure: []
  non_claims:
  - does not replace BQNF repair decision
declarations_required:
- read_timestamp
- replica_lag
- cache_age
- invalidation_status
- freshness_sla
evidence_required:
- clock_source
- lag_metrics from replica or cache layer
validation_criteria:
- query result never served without read_timestamp
- SLA breach terminalizes or escalates
- pairs with BQNF Invalidate when cache stale
proof_obligations: []
terminal_routes:
- Fresh
- Stale
- LagExceeded
- Invalidate
- Refuse
certification:
  certificate_required: true
  certificate_kind: freshness_packet
  obstruction_class_required: false
  loss_ledger_required: false
  verifier_required: true
authorization:
  authorized_by: null
  certified_implies_authorized: false
references:
- ../1_normal_forms.md
- ../1a_bqnf_incremental_repair.md
terminal_route_map:
  Fresh: Preserve
  Stale: Escalate
  LagExceeded: Invalidate
  Invalidate: Invalidate
  Refuse: Refuse
definition:
  source: coda_all_universe/mssn_sn_tower/definitions.md
  formal_statement: timeless truth. every read declares temporal boundary and invalidation
    status
  quadrilateral:
    qualifies_as_true_normal_form: false
    qualification_gap: reconstruction_is_not_a_relational_project_join
    anomaly_exclusion: timeless truth
    lossless_join:
      status: declared_reconstruction
      statement: every read declares temporal boundary and invalidation status
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
