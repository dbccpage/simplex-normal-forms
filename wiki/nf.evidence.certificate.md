# Certificate Form (`CertF`)

> **Contract ID:** `nf.evidence.certificate` | **Family:** `evidence` | **Index Status:** `draft` | **AuthorityEffect:** `None`

**[⬅ Back to Wiki Home](Home)** | **[View SVG Diagram](images/nf.evidence.certificate.svg)**

---

## 1. Executive Summary & Metadata

Certificate Form (CertF) enforces structural normalization and explicit defect routing in the evidence regime.

| Property | Value |
| :--- | :--- |
| **Canonical ID** | `nf.evidence.certificate` |
| **Short Name** | `CertF` |
| **Full Name** | Certificate Form |
| **Family** | `evidence` (Cryptographic Receipts, Dual Witnesses, Loss Ledgers, CDC Logs & Schema Totality) |
| **Qualification** | Extended Form Contract (Normal Form Contract) |
| **Data / Math Posture** | at_rest |
| **Index Status** | `draft` |
| **Theory Status** | `proposed` |
| **Verification Status** | `absent` |
| **Contract Version** | `v0` |
| **Governance Fence** | `AuthorityEffect: None` (`certified_implies_authorized: false`) |

---

## 2. Visual Architecture & Normalization Diagram

![Certificate Form (CertF) Diagram](images/nf.evidence.certificate.svg)

---

## 3. Concrete Worked Example & Mechanism

### Visual Transition Summary

| Stage | Carrier / Operator | Concrete State / Invariant |
| :--- | :--- | :--- |
| **1. Before / Candidate Input** | `Input Carrier (CertF Candidate)` | Anomaly risk: uncertified ; representation transport |
| **2. Normalization / Gate** | `CertF Verification Gate` | `every transition carries ...` (`certified_implies_authorized: false`) |
| **3. After / Certified Output** | `Certified CertF Output` | Invariant: ['certificate_id', ; 'source_regime', 'target_regime', ; 'morphism_kind', 'verifier_id',... |

---

## 4. The Four-Pillar Quadrilateral & Non-Claims

Every contract in `simplex-normal-forms` is evaluated against the **Four-Pillar Quadrilateral** defined in `contracts/_golden_nfs/standard.yaml`:

| Pillar | Requirement | Contract Specification for `nf.evidence.certificate` |
| :--- | :--- | :--- |
| **Pillar I: Excludes Anomaly** | Name and eliminate a specific class of data or state defects. | uncertified representation transport |
| **Pillar II: Preserves Invariant** | State the structural invariant and protected skeleton preserved across transitions. | **Invariant:** every transition carries a canonical certificate specifying ID, regimes, morphism kind, preserved skeleton, and verifier outcome<br>**Protected Skeleton:** ['certificate_id', 'source_regime', 'target_regime', 'morphism_kind', 'verifier_id', 'verifier_outcome'] |
| **Pillar III: Lossless Reconstruction** | State the non-loss reconstruction operator (join, direct sum, pullback, or replay). | Lossless reconstruction under declared projection, direct sum, or pullback operators. |
| **Pillar IV: Syntactic Decidability** | State how conformance is decided from declared constraints without unbudgeted scans. | Decidable from declared schema and witness metadata within bounded evaluation budgets. |

### Explicit Non-Claims (`certified_implies_authorized: false`)

- does not ensure that the target representation preserves all non-skeletal properties

---

## 5. Operational Verification & Terminal Routing

### 5.1 Required Declarations

- certificate_id
- source_regime
- target_regime
- morphism_kind

### 5.2 Required Evidence

- preserved_skeleton
- erased_distinctions
- verifier_id
- verifier_outcome

### 5.3 Validation Criteria

| Criterion ID | Name | Condition |
| :--- | :--- | :--- |
| `criterion` | Check | certificate ID must be globally unique |
| `criterion` | Check | verifier outcome must be pending, accepted, or rejected |
| `criterion` | Check | loss ledger reference is mandatory if erased distinctions are non-empty |

### 5.4 Terminal Route Map

Every evaluation terminates in a declared local route mapped to a canonical terminal in `standard.yaml`:

| Local Terminal Route | Canonical Terminal |
| :--- | :--- |
| `CertificateAccepted` | `Escalate` |
| `CertificatePending` | `Escalate` |
| `CertificateRejected` | `Escalate` |
| `Refuse` | `Refuse` |

### 5.5 Declared Failure Modes

- **symptom**: view compiled without a certificate or with missing preserved skeleton fields, **diagnosis**: uncertified representation transport, **terminal**: CertificateRejected

---

## 6. Epistemic Claim Hygiene Quadrant

In accordance with the repository's epistemic claim discipline:

1. **What it supports:**
   - Supports syntactic and operational checking of `nf.evidence.certificate` (`CertF`) against its declared schema, boundary constraints, and witness obligations in this model.
   - Supports deterministic terminal routing (`CertificateAccepted, CertificatePending, CertificateRejected, Refuse`) when required declarations or invariants fail.
2. **What it does not support:**
   - Does not confer operational authority (`AuthorityEffect: None`, `certified_implies_authorized: false`).
   - Does not claim semantic truth of undeclared external processes or unverified upstream inputs beyond the declaredprotected skeleton.
3. **The narrowest defensible claim:**
   - Within the declared substrate `at_rest`, this contract enforces that `uncertified representation transport` is either excluded under `every transition carries a canonical certificate specifying ID, regimes, morphism kind, preserved skeleton, and verifier outcome` or routed to an explicit refusal/recovery terminal.
4. **The next test needed:**
   - Property-based falsification and mutation testing across boundary edge cases and composed multi-step pipelines for `nf.evidence.certificate`.

---

## 7. Canonical YAML Contract (`contracts/nf.evidence.certificate.yaml`)

<details>
<summary><strong>Click to expand full canonical YAML contract (contracts/nf.evidence.certificate.yaml)</strong></summary>

```yaml
schema_version: smplx.nf.contract.v0
contract_kind: normal_form_contract
identity:
  id: nf.evidence.certificate
  name: Certificate Form
  short_name: CertF
  version: v0
  status: draft
  family: evidence
  theory_status: proposed
  contract_status: draft
  verification_status: absent
classification:
  hierarchy_level: form
  subject_kind:
  - certificate_packet
  data_posture: at_rest
  mathematical_posture: operational
purpose:
  excludes_anomaly: uncertified representation transport
  preserves_invariant: every transition carries a canonical certificate specifying
    ID, regimes, morphism kind, preserved skeleton, and verifier outcome
  protected_skeleton:
  - certificate_id
  - source_regime
  - target_regime
  - morphism_kind
  - verifier_id
  - verifier_outcome
  erased_structure: []
  non_claims:
  - does not ensure that the target representation preserves all non-skeletal properties
declarations_required:
- certificate_id
- source_regime
- target_regime
- morphism_kind
evidence_required:
- preserved_skeleton
- erased_distinctions
- verifier_id
- verifier_outcome
validation_criteria:
- certificate ID must be globally unique
- verifier outcome must be pending, accepted, or rejected
- loss ledger reference is mandatory if erased distinctions are non-empty
proof_obligations: []
terminal_routes:
- CertificateAccepted
- CertificatePending
- CertificateRejected
- Refuse
certification:
  certificate_required: true
  certificate_kind: meta_certificate
  obstruction_class_required: false
  loss_ledger_required: false
  verifier_required: true
authorization:
  authorized_by: null
  certified_implies_authorized: false
failure_modes:
- symptom: view compiled without a certificate or with missing preserved skeleton
    fields
  diagnosis: uncertified representation transport
  terminal: CertificateRejected
references:
- ../1_normal_forms.md
- ../nf.coda.mur.transport.yaml
terminal_route_map:
  CertificateAccepted: Escalate
  CertificatePending: Escalate
  CertificateRejected: Escalate
  Refuse: Refuse
definition:
  source: coda_all_universe/mssn_sn_tower/definitions.md
  formal_statement: uncertified representation transport. every transition carries
    a canonical certificate specifying ID, regimes, morphism kind, preserved skeleton,
    and verifier outcome
  quadrilateral:
    qualifies_as_true_normal_form: false
    qualification_gap: reconstruction_is_not_a_relational_project_join
    anomaly_exclusion: uncertified representation transport
    lossless_join:
      status: declared_reconstruction
      statement: every transition carries a canonical certificate specifying ID, regimes,
        morphism kind, preserved skeleton, and verifier outcome
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
