# Location Normal Form (`LNF`)

> **Contract ID:** `nf.epistemic.location` | **Family:** `epistemic` | **Index Status:** `draft` | **AuthorityEffect:** `None`

**[⬅ Back to Wiki Home](Home)** | **[View SVG Diagram](images/nf.epistemic.location.svg)**

---

## 1. Executive Summary & Metadata

Location Normal Form (LNF) enforces structural normalization and explicit defect routing in the epistemic regime.

| Property | Value |
| :--- | :--- |
| **Canonical ID** | `nf.epistemic.location` |
| **Short Name** | `LNF` |
| **Full Name** | Location Normal Form |
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

![Location Normal Form (LNF) Diagram](images/nf.epistemic.location.svg)

---

## 3. Concrete Worked Example & Mechanism

### Visual Transition Summary

| Stage | Carrier / Operator | Concrete State / Invariant |
| :--- | :--- | :--- |
| **1. Before / Candidate Input** | `Input Carrier (LNF Candidate)` | Anomaly risk: ghost locality |
| **2. Normalization / Gate** | `LNF Verification Gate` | `logical identity maps to...` (`certified_implies_authorized: false`) |
| **3. After / Certified Output** | `Certified LNF Output` | Invariant: ['logical_identity', ; 'physical_placement', ; 'replica_set', 'storage_tier'] |

---

## 4. The Four-Pillar Quadrilateral & Non-Claims

Every contract in `simplex-normal-forms` is evaluated against the **Four-Pillar Quadrilateral** defined in `contracts/_golden_nfs/standard.yaml`:

| Pillar | Requirement | Contract Specification for `nf.epistemic.location` |
| :--- | :--- | :--- |
| **Pillar I: Excludes Anomaly** | Name and eliminate a specific class of data or state defects. | ghost locality |
| **Pillar II: Preserves Invariant** | State the structural invariant and protected skeleton preserved across transitions. | **Invariant:** logical identity maps to declared physical placement and movement policy<br>**Protected Skeleton:** ['logical_identity', 'physical_placement', 'replica_set', 'storage_tier'] |
| **Pillar III: Lossless Reconstruction** | State the non-loss reconstruction operator (join, direct sum, pullback, or replay). | Lossless reconstruction under declared projection, direct sum, or pullback operators. |
| **Pillar IV: Syntactic Decidability** | State how conformance is decided from declared constraints without unbudgeted scans. | Decidable from declared schema and witness metadata within bounded evaluation budgets. |

### Explicit Non-Claims (`certified_implies_authorized: false`)

- does not support data is correct only where it lives

---

## 5. Operational Verification & Terminal Routing

### 5.1 Required Declarations

- logical_identity
- physical_locations
- replica_set
- storage_tier
- relocation_policy
- encryption_domain

### 5.2 Required Evidence

- placement_witness per location
- epoch or timestamp on placement claim

### 5.3 Validation Criteria

| Criterion ID | Name | Condition |
| :--- | :--- | :--- |
| `criterion` | Check | every logical object has at least one declared location witness |
| `criterion` | Check | placement claims include timestamp or epoch |
| `criterion` | Check | relocation does not erase lineage |
| `criterion` | Check | unknown placement terminalizes |

### 5.4 Terminal Route Map

Every evaluation terminates in a declared local route mapped to a canonical terminal in `standard.yaml`:

| Local Terminal Route | Canonical Terminal |
| :--- | :--- |
| `Located` | `Preserve` |
| `Relocating` | `Repair` |
| `LocationUnknown` | `BudgetUnknown` |
| `ReplicaDivergence` | `Escalate` |
| `Refuse` | `Refuse` |

### 5.5 Declared Failure Modes

- **symptom**: user told data is in table X but copy lives in cache WAL vector store, **diagnosis**: ghost locality, **terminal**: LocationUnknown

---

## 6. Epistemic Claim Hygiene Quadrant

In accordance with the repository's epistemic claim discipline:

1. **What it supports:**
   - Supports syntactic and operational checking of `nf.epistemic.location` (`LNF`) against its declared schema, boundary constraints, and witness obligations in this model.
   - Supports deterministic terminal routing (`Located, Relocating, LocationUnknown, ReplicaDivergence`) when required declarations or invariants fail.
2. **What it does not support:**
   - Does not confer operational authority (`AuthorityEffect: None`, `certified_implies_authorized: false`).
   - Does not claim semantic truth of undeclared external processes or unverified upstream inputs beyond the declaredprotected skeleton.
3. **The narrowest defensible claim:**
   - Within the declared substrate `in_motion`, this contract enforces that `ghost locality` is either excluded under `logical identity maps to declared physical placement and movement policy` or routed to an explicit refusal/recovery terminal.
4. **The next test needed:**
   - Property-based falsification and mutation testing across boundary edge cases and composed multi-step pipelines for `nf.epistemic.location`.

---

## 7. Canonical YAML Contract (`contracts/nf.epistemic.location.yaml`)

<details>
<summary><strong>Click to expand full canonical YAML contract (contracts/nf.epistemic.location.yaml)</strong></summary>

```yaml
schema_version: smplx.nf.contract.v0
contract_kind: normal_form_contract
identity:
  id: nf.epistemic.location
  name: Location Normal Form
  short_name: LNF
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
  data_posture: in_motion
  mathematical_posture: operational
purpose:
  excludes_anomaly: ghost locality
  preserves_invariant: logical identity maps to declared physical placement and movement
    policy
  protected_skeleton:
  - logical_identity
  - physical_placement
  - replica_set
  - storage_tier
  erased_structure: []
  non_claims:
  - does not support data is correct only where it lives
declarations_required:
- logical_identity
- physical_locations
- replica_set
- storage_tier
- relocation_policy
- encryption_domain
evidence_required:
- placement_witness per location
- epoch or timestamp on placement claim
validation_criteria:
- every logical object has at least one declared location witness
- placement claims include timestamp or epoch
- relocation does not erase lineage
- unknown placement terminalizes
proof_obligations: []
terminal_routes:
- Located
- Relocating
- LocationUnknown
- ReplicaDivergence
- Refuse
certification:
  certificate_required: true
  certificate_kind: placement_certificate
  obstruction_class_required: false
  loss_ledger_required: conditional
  verifier_required: true
authorization:
  authorized_by: null
  certified_implies_authorized: false
failure_modes:
- symptom: user told data is in table X but copy lives in cache WAL vector store
  diagnosis: ghost locality
  terminal: LocationUnknown
references:
- ../1_normal_forms.md
terminal_route_map:
  Located: Preserve
  Relocating: Repair
  LocationUnknown: BudgetUnknown
  ReplicaDivergence: Escalate
  Refuse: Refuse
definition:
  source: coda_all_universe/mssn_sn_tower/definitions.md
  formal_statement: ghost locality. logical identity maps to declared physical placement
    and movement policy
  quadrilateral:
    qualifies_as_true_normal_form: false
    qualification_gap: reconstruction_is_not_a_relational_project_join
    anomaly_exclusion: ghost locality
    lossless_join:
      status: declared_reconstruction
      statement: logical identity maps to declared physical placement and movement
        policy
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
