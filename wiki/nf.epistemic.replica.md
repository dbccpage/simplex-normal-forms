# Replica Normal Form (`RNF`)

> **Contract ID:** `nf.epistemic.replica` | **Family:** `epistemic` | **Index Status:** `draft` | **AuthorityEffect:** `None`

**[⬅ Back to Wiki Home](Home)** | **[View SVG Diagram](images/nf.epistemic.replica.svg)**

---

## 1. Executive Summary & Metadata

Replica Normal Form (RNF) enforces structural normalization and explicit defect routing in the epistemic regime.

| Property | Value |
| :--- | :--- |
| **Canonical ID** | `nf.epistemic.replica` |
| **Short Name** | `RNF` |
| **Full Name** | Replica Normal Form |
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

![Replica Normal Form (RNF) Diagram](images/nf.epistemic.replica.svg)

---

## 3. Concrete Worked Example & Mechanism

### Visual Transition Summary

| Stage | Carrier / Operator | Concrete State / Invariant |
| :--- | :--- | :--- |
| **1. Before / Candidate Input** | `Input Carrier (RNF Candidate)` | Anomaly risk: false sameness |
| **2. Normalization / Gate** | `RNF Verification Gate` | `every copy declares origi...` (`certified_implies_authorized: false`) |
| **3. After / Certified Output** | `Certified RNF Output` | Invariant: ['origin', 'epoch', ; 'causal_frontier', ; 'divergence_budget'] |

---

## 4. The Four-Pillar Quadrilateral & Non-Claims

Every contract in `simplex-normal-forms` is evaluated against the **Four-Pillar Quadrilateral** defined in `contracts/_golden_nfs/standard.yaml`:

| Pillar | Requirement | Contract Specification for `nf.epistemic.replica` |
| :--- | :--- | :--- |
| **Pillar I: Excludes Anomaly** | Name and eliminate a specific class of data or state defects. | false sameness |
| **Pillar II: Preserves Invariant** | State the structural invariant and protected skeleton preserved across transitions. | **Invariant:** every copy declares origin epoch causal frontier divergence budget reconciliation<br>**Protected Skeleton:** ['origin', 'epoch', 'causal_frontier', 'divergence_budget'] |
| **Pillar III: Lossless Reconstruction** | State the non-loss reconstruction operator (join, direct sum, pullback, or replay). | Lossless reconstruction under declared projection, direct sum, or pullback operators. |
| **Pillar IV: Syntactic Decidability** | State how conformance is decided from declared constraints without unbudgeted scans. | Decidable from declared schema and witness metadata within bounded evaluation budgets. |

### Explicit Non-Claims (`certified_implies_authorized: false`)

- eventual consistency is not equivalence without declared budget

---

## 5. Operational Verification & Terminal Routing

### 5.1 Required Declarations

- origin
- epoch
- causal_frontier
- divergence_budget
- reconciliation_rule

### 5.2 Required Evidence

- replica_identity
- frontier_vector or lamport_clock

### 5.3 Validation Criteria

| Criterion ID | Name | Condition |
| :--- | :--- | :--- |
| `criterion` | Check | replicas are not compared without declared frontier |
| `criterion` | Check | merge requires reconciliation_rule terminal when budget exceeded |
| `criterion` | Check | aligns with BQNF Serialize terminal when concurrent defects do not commute |

### 5.4 Terminal Route Map

Every evaluation terminates in a declared local route mapped to a canonical terminal in `standard.yaml`:

| Local Terminal Route | Canonical Terminal |
| :--- | :--- |
| `Reconciled` | `Preserve` |
| `Converging` | `Repair` |
| `DivergenceExceeded` | `Escalate` |
| `Serialize` | `Serialize` |
| `Refuse` | `Refuse` |

### 5.5 Declared Failure Modes

_All defects route explicitly through the Terminal Route Map above._

---

## 6. Epistemic Claim Hygiene Quadrant

In accordance with the repository's epistemic claim discipline:

1. **What it supports:**
   - Supports syntactic and operational checking of `nf.epistemic.replica` (`RNF`) against its declared schema, boundary constraints, and witness obligations in this model.
   - Supports deterministic terminal routing (`Reconciled, Converging, DivergenceExceeded, Serialize`) when required declarations or invariants fail.
2. **What it does not support:**
   - Does not confer operational authority (`AuthorityEffect: None`, `certified_implies_authorized: false`).
   - Does not claim semantic truth of undeclared external processes or unverified upstream inputs beyond the declaredprotected skeleton.
3. **The narrowest defensible claim:**
   - Within the declared substrate `in_motion`, this contract enforces that `false sameness` is either excluded under `every copy declares origin epoch causal frontier divergence budget reconciliation` or routed to an explicit refusal/recovery terminal.
4. **The next test needed:**
   - Property-based falsification and mutation testing across boundary edge cases and composed multi-step pipelines for `nf.epistemic.replica`.

---

## 7. Canonical YAML Contract (`contracts/nf.epistemic.replica.yaml`)

<details>
<summary><strong>Click to expand full canonical YAML contract (contracts/nf.epistemic.replica.yaml)</strong></summary>

```yaml
schema_version: smplx.nf.contract.v0
contract_kind: normal_form_contract
identity:
  id: nf.epistemic.replica
  name: Replica Normal Form
  short_name: RNF
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
  - relvar
  data_posture: in_motion
  mathematical_posture: operational
purpose:
  excludes_anomaly: false sameness
  preserves_invariant: every copy declares origin epoch causal frontier divergence
    budget reconciliation
  protected_skeleton:
  - origin
  - epoch
  - causal_frontier
  - divergence_budget
  erased_structure: []
  non_claims:
  - eventual consistency is not equivalence without declared budget
declarations_required:
- origin
- epoch
- causal_frontier
- divergence_budget
- reconciliation_rule
evidence_required:
- replica_identity
- frontier_vector or lamport_clock
validation_criteria:
- replicas are not compared without declared frontier
- merge requires reconciliation_rule terminal when budget exceeded
- aligns with BQNF Serialize terminal when concurrent defects do not commute
proof_obligations: []
terminal_routes:
- Reconciled
- Converging
- DivergenceExceeded
- Serialize
- Refuse
certification:
  certificate_required: true
  certificate_kind: replica_witness
  obstruction_class_required: false
  loss_ledger_required: false
  verifier_required: true
authorization:
  authorized_by: null
  certified_implies_authorized: false
references:
- ../1_normal_forms.md
terminal_route_map:
  Reconciled: Preserve
  Converging: Repair
  DivergenceExceeded: Escalate
  Serialize: Serialize
  Refuse: Refuse
definition:
  source: coda_all_universe/mssn_sn_tower/definitions.md
  formal_statement: false sameness. every copy declares origin epoch causal frontier
    divergence budget reconciliation
  quadrilateral:
    qualifies_as_true_normal_form: false
    qualification_gap: reconstruction_is_not_a_relational_project_join
    anomaly_exclusion: false sameness
    lossless_join:
      status: declared_reconstruction
      statement: every copy declares origin epoch causal frontier divergence budget
        reconciliation
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
