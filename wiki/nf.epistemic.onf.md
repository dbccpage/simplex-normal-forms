# Orchestration Normal Form (`ONF`)

> **Contract ID:** `nf.epistemic.onf` | **Family:** `epistemic` | **Index Status:** `draft` | **AuthorityEffect:** `None`

**[⬅ Back to Wiki Home](Home)** | **[View SVG Diagram](images/nf.epistemic.onf.svg)**

---

## 1. Executive Summary & Metadata

Orchestration Normal Form (ONF) enforces structural normalization and explicit defect routing in the epistemic regime.

| Property | Value |
| :--- | :--- |
| **Canonical ID** | `nf.epistemic.onf` |
| **Short Name** | `ONF` |
| **Full Name** | Orchestration Normal Form |
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

![Orchestration Normal Form (ONF) Diagram](images/nf.epistemic.onf.svg)

---

## 3. Concrete Worked Example & Mechanism

### Visual Transition Summary

| Stage | Carrier / Operator | Concrete State / Invariant |
| :--- | :--- | :--- |
| **1. Before / Candidate Input** | `Input Carrier (ONF Candidate)` | Anomaly risk: agent laundering |
| **2. Normalization / Gate** | `ONF Verification Gate` | `agent/tool action declare...` (`certified_implies_authorized: false`) |
| **3. After / Certified Output** | `Certified ONF Output` | Invariant: ['initiator', 'tool', ; 'input_state', 'output_state', ; 'delegated_authority'] |

---

## 4. The Four-Pillar Quadrilateral & Non-Claims

Every contract in `simplex-normal-forms` is evaluated against the **Four-Pillar Quadrilateral** defined in `contracts/_golden_nfs/standard.yaml`:

| Pillar | Requirement | Contract Specification for `nf.epistemic.onf` |
| :--- | :--- | :--- |
| **Pillar I: Excludes Anomaly** | Name and eliminate a specific class of data or state defects. | agent laundering |
| **Pillar II: Preserves Invariant** | State the structural invariant and protected skeleton preserved across transitions. | **Invariant:** agent/tool action declares initiator, tool, input/output state, delegated authority, rollback, and terminal route<br>**Protected Skeleton:** ['initiator', 'tool', 'input_state', 'output_state', 'delegated_authority'] |
| **Pillar III: Lossless Reconstruction** | State the non-loss reconstruction operator (join, direct sum, pullback, or replay). | Lossless reconstruction under declared projection, direct sum, or pullback operators. |
| **Pillar IV: Syntactic Decidability** | State how conformance is decided from declared constraints without unbudgeted scans. | Decidable from declared schema and witness metadata within bounded evaluation budgets. |

### Explicit Non-Claims (`certified_implies_authorized: false`)

- does not ensure agent actions are globally optimal or logically correct

---

## 5. Operational Verification & Terminal Routing

### 5.1 Required Declarations

- initiator
- tool
- input_state
- output_state
- delegated_authority
- rollback_path
- terminal_route

### 5.2 Required Evidence

- cryptographic_delegation_seal
- action_epoch
- input_hash
- output_hash

### 5.3 Validation Criteria

| Criterion ID | Name | Condition |
| :--- | :--- | :--- |
| `criterion` | Check | action must have initiator and tool declared |
| `criterion` | Check | delegated authority must be cryptographically sealed |
| `criterion` | Check | rollback path must be declared |
| `criterion` | Check | terminal route must resolve on failure |

### 5.4 Terminal Route Map

Every evaluation terminates in a declared local route mapped to a canonical terminal in `standard.yaml`:

| Local Terminal Route | Canonical Terminal |
| :--- | :--- |
| `ActionSuccess` | `Preserve` |
| `RollbackExecuted` | `Escalate` |
| `AgentLaunderingViolation` | `Refuse` |
| `DelegationExpired` | `Refuse` |
| `ActionRefused` | `Refuse` |
| `Escalate` | `Escalate` |

### 5.5 Declared Failure Modes

- **symptom**: agent action performed without reconstructible authorization or belief state, **diagnosis**: agent laundering, **terminal**: AgentLaunderingViolation

---

## 6. Epistemic Claim Hygiene Quadrant

In accordance with the repository's epistemic claim discipline:

1. **What it supports:**
   - Supports syntactic and operational checking of `nf.epistemic.onf` (`ONF`) against its declared schema, boundary constraints, and witness obligations in this model.
   - Supports deterministic terminal routing (`ActionSuccess, RollbackExecuted, AgentLaunderingViolation, DelegationExpired`) when required declarations or invariants fail.
2. **What it does not support:**
   - Does not confer operational authority (`AuthorityEffect: None`, `certified_implies_authorized: false`).
   - Does not claim semantic truth of undeclared external processes or unverified upstream inputs beyond the declaredprotected skeleton.
3. **The narrowest defensible claim:**
   - Within the declared substrate `in_motion`, this contract enforces that `agent laundering` is either excluded under `agent/tool action declares initiator, tool, input/output state, delegated authority, rollback, and terminal route` or routed to an explicit refusal/recovery terminal.
4. **The next test needed:**
   - Property-based falsification and mutation testing across boundary edge cases and composed multi-step pipelines for `nf.epistemic.onf`.

---

## 7. Canonical YAML Contract (`contracts/nf.epistemic.onf.yaml`)

<details>
<summary><strong>Click to expand full canonical YAML contract (contracts/nf.epistemic.onf.yaml)</strong></summary>

```yaml
schema_version: smplx.nf.contract.v0
contract_kind: normal_form_contract
identity:
  id: nf.epistemic.onf
  name: Orchestration Normal Form
  short_name: ONF
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
  excludes_anomaly: agent laundering
  preserves_invariant: agent/tool action declares initiator, tool, input/output state,
    delegated authority, rollback, and terminal route
  protected_skeleton:
  - initiator
  - tool
  - input_state
  - output_state
  - delegated_authority
  erased_structure: []
  non_claims:
  - does not ensure agent actions are globally optimal or logically correct
declarations_required:
- initiator
- tool
- input_state
- output_state
- delegated_authority
- rollback_path
- terminal_route
evidence_required:
- cryptographic_delegation_seal
- action_epoch
- input_hash
- output_hash
validation_criteria:
- action must have initiator and tool declared
- delegated authority must be cryptographically sealed
- rollback path must be declared
- terminal route must resolve on failure
proof_obligations: []
terminal_routes:
- ActionSuccess
- RollbackExecuted
- AgentLaunderingViolation
- DelegationExpired
- ActionRefused
- Escalate
certification:
  certificate_required: true
  certificate_kind: orchestration_certificate
  obstruction_class_required: false
  loss_ledger_required: true
  verifier_required: true
authorization:
  authorized_by: null
  certified_implies_authorized: false
failure_modes:
- symptom: agent action performed without reconstructible authorization or belief
    state
  diagnosis: agent laundering
  terminal: AgentLaunderingViolation
references:
- ../1_normal_forms.md
terminal_route_map:
  ActionSuccess: Preserve
  RollbackExecuted: Escalate
  AgentLaunderingViolation: Refuse
  DelegationExpired: Refuse
  ActionRefused: Refuse
  Escalate: Escalate
definition:
  source: coda_all_universe/mssn_sn_tower/definitions.md
  formal_statement: agent laundering. agent/tool action declares initiator, tool,
    input/output state, delegated authority, rollback, and terminal route
  quadrilateral:
    qualifies_as_true_normal_form: false
    qualification_gap: reconstruction_is_not_a_relational_project_join
    anomaly_exclusion: agent laundering
    lossless_join:
      status: declared_reconstruction
      statement: agent/tool action declares initiator, tool, input/output state, delegated
        authority, rollback, and terminal route
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
