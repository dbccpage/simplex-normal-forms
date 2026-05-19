# General Theory of Observers and Distinguishability: Domain Extensions and Observer Contracts

Status: Archived source / Domain extension.

> Absorbed observer/domain-extension copy from
> `omega_engine/research/in_work/simplex_cosmos_papers/SMPLX_009_Simplex Databases/normal_form_contracts/relnf.md`.
>
> Non-normative appendix: current definitions are controlled by `book/00_preface.md` through `book/08_open_problems.md`, `glossary/`, `spec/`, and `contracts/`. This file is retained for provenance and domain-extension vocabulary. If it conflicts with the protected-NF rule or quarantine policy, the cleaned taxonomy wins.

This document maps the underlying mathematical substrate of observers, distinguishability, and coordinates. To prevent taxonomy inflation, these are classified as **Observer Contracts** and **Domain Extensions** rather than database normal forms.

---

## 1. Thesis and Master Questions

> **Classical normal forms prevent structural anomalies in stored relations. Simplex normal forms prevent authority anomalies in data that moves, transforms, replicates, summarizes, delegates, or becomes evidence for action.**

Under this architecture, difference is primitive; sameness is observer-relative certified zero-difference. The common spine across databases, distributed systems, networks, and physics is built on these master questions:

1. **What is distinguishable?** What measurements separate two states?
2. **What counts as same?** What equivalence relation identifies them?
3. **What survives comparison?** What survives transport between observers?
4. **What fails to glue?** Can local observer sections form a global section?
5. **What can be repaired?** Can the defect be resolved by allowed corrections?
6. **What residual remains?** What remains after repair and comparison?
7. **What authority is earned?** What finite terminal certificate is earned?

---

## 2. Observer Contracts

Observer contracts define the interface through which representation changes and observations are compared.

### 2.1 Observer Distinguishability Contract (ODC)

Formerly called ODNF; this contract models the base questions of state separation and transport:

* **Distinguishable:** Separated by observable cochain defects $\omega \in C^1$.
* **Same:** Equivalence under repairs $d_0\alpha$.
* **Comparison:** Preservation under transport map $\chi$.
* **Gluing:** Existence of a global section on the observer sheaf.

**Finite Obstruction Realization:**
* $C^0$: Allowed repairs or gauge transformations.
* $C^1$: Observer defects or distinguishability gaps.
* $C^2$: Gluing failures or contextuality failures.
* **Quotient Space:** $Q^1 = C^1 / \operatorname{im}(d_0)$.
* **Obstruction Class:** $[\omega] \in Q^1$.

### 2.2 Observer Information Contract (OIC)

Formerly called SINF; this contract governs signal transmission over noisy boundaries:

* **Alphabet:** Declared message domain.
* **Channel:** Noisy transport characteristics.
* **Distinguishability:** Bounded by mutual information and error probability.
* **Residual:** Unresolved entropy recorded in a loss ledger.

**Terminal Routes:**
* `Decodable`: Signal successfully reconstructed.
* `Ambiguous`: Multiple valid decodings exist.
* `CapacityExceeded`: Channel capability bounds violated.
* `Quarantine`: Isolate packet to prevent erroneous interpretation.
* `Decompose`: Split composite message into independently decodable parts.
* `Refuse`: Decline representation due to excessive noise.

---

## 3. Domain Extensions

Domain extensions apply the observer stack to specific physical or network contexts. They are quarantined from the core database papers.

### 3.1 Bell Contextuality Contract (BCC)

Formerly called BCNF_qm in source notes; the cleaned registry uses BellCNF to avoid confusion with Boyce-Codd Normal Form. This extension models the failure of classical observer-gluing on local measurement sections:

$$\text{local hidden sameness} \neq \text{quantum observational sameness}$$

* **Local Sections:** Outcome distributions per measurement context.
* **Global Candidate:** Joint hidden variable assignment.
* **Gluing Failure:** Bell inequality violation indicating a contextual obstruction.

**Terminal Routes:**
* `ClassicalGlue`: Local contexts merge into a single global section.
* `QuantumSurvivor`: Nonlocal residual verified under quantum assumptions.
* `BellViolation`: Incompatible local margins.
* `Quarantine`: Isolate contextuality failures.

### 3.2 Spacetime Observer Contracts

Formerly called SRNF and its sub-forms; these govern systems operating over relativistic intervals (e.g., GPS timing, satellite cache replicas, orbital links):

* **Timelike Interval:** Causal order survives all reference frames.
* **Lightlike Interval:** Signal propagation limit boundary.
* **Spacelike Interval:** Order is frame-relative; consensus is required for total sequencing.

#### A. Reference Frame Contract
* **Declarations:** Observer frame, clock basis, coordinate system, synchronization protocol.
* **Validation:** No timestamp accepted without a declared clock source and conversion witness.
* **Terminals:** `FrameAccepted`, `DriftExceeded`, `FrameMismatch`, `OrderingUnknown`, `Quarantine`.

#### B. Light-Cone Causality Contract
* **Declarations:** Event location, propagation model, signal speed limit.
* **Validation:** Claimed cause must lie in the past light cone.
* **Terminals:** `CausallyAdmissible`, `SpacelikeConcurrent`, `CausalViolation`, `ConsensusRequired`, `Refuse`.

#### C. Orbital Placement Contract
* **Declarations:** Spacecraft ID, ephemeris epoch, contact windows, handoff policy.
* **Validation:** Telemetry and replica states mapped to ephemeris contact timelines.
* **Terminals:** `InContact`, `OutOfContact`, `EphemerisStale`, `HandoffPending`, `LocationUnknown`.

#### D. Clock-Synchronization Contract
* **Declarations:** Clock type, sync source, drift bounds, monotonicity rule.
* **Validation:** Clock bounds must be verified; resets must be logged.
* **Terminals:** `TimeCertified`, `TimeIntervalOnly`, `DriftExceeded`, `ClockReset`, `Quarantine`.

### 3.3 Lieb-Robinson Locality Contract

This extension captures the finite operational content of locality bounds: a local event cannot be treated as globally available without either a declared propagation cone or an explicit outside-cone residual ledger.

* **Declarations:** Finite locality graph, graph metric, local dependency radius, velocity bound, decay/error bound, event support, observation window.
* **Validation:** Claimed affected support lies inside the locality cone, or the outside-cone effect is terminalized with a residual bound.
* **Terminals:** `WithinLocalityCone`, `ExponentiallySuppressed`, `OutsideConeResidual`, `LocalityBoundExceeded`, `RefuseInstantInfluence`.

Database reading: invalidation, replication, and agent-memory effects are not omnipresent. Authority spreads only through declared dependency paths.

### 3.4 Horizon Emission Contract

This extension captures Hawking-radiation-shaped boundary accounting without claiming a physics result. It applies whenever data crosses a boundary after which the interior state is inaccessible: redaction, eviction, compaction, tombstoning, lossy summaries, or exterior-only telemetry.

* **Declarations:** Horizon boundary, interior/exterior partition, crossing rule, emission channel, coarse-graining map, conservation/loss ledger, recoverability class.
* **Validation:** Exterior packets authorize only what the emission channel preserves; interior claims require a lift witness or terminalize as inaccessible.
* **Terminals:** `ExteriorEmissionCertified`, `LossLedgerRequired`, `InteriorInaccessible`, `RecoverabilityUnknown`, `ConservationViolation`, `RefuseUnledgeredHorizon`.

Database reading: a compacted aggregate, redacted row, or emitted summary is not authority for erased microstate unless the finite lift is certified.

---

## 4. Clean Stack Alignment (Observer Authority Stack)

The Observer Authority Stack (OAS) coordinates the active checks from raw defects to final authorization:

| Layer | Question | Output |
|---|---|---|
| **GTFOC** | What defect remains after repair? | Obstruction class $[\omega] \in Q^1$ |
| **GTFDA** | Did evidence descend to a terminal? | Terminal authority / refusal |
| **GTMUR** | Did representation change preserve authority? | Transport certificate / loss ledger |
| **GTOR** | Can partial views be compared? | Comparison envelope / no-glue |
| **GTTC** | Do finite shadows authorize continuum claims? | Finite shadow authority |
| **GTTA** | What residual remains after all closure attempts? | Typed residual terminal |
| **GTLA** | Were all obligations conserved? | Layered authority classification |
