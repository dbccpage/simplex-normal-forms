# Certified Normal Forms, Representation Transport, and Finite Authority for Simplex Databases

Status: Archived source / Domain extension.

> Absorbed full atlas copy from
> `omega_engine/research/in_work/simplex_cosmos_papers/SMPLX_009_Simplex Databases/crap/1_normal_forms.md`.
> The source folder was integrated into the root scaffold and removed.
>
> Non-normative archive: current definitions are controlled by `book/00_preface.md` through `book/08_open_problems.md`, `glossary/`, `spec/`, and `contracts/`. If this appendix conflicts with the cleaned taxonomy, the cleaned taxonomy wins.

**Status:** working atlas (survey + pointers; not a single publishable theorem paper)  
**Scope:** shape normal forms (data at rest), BQNF and motion forms (data in motion), certificate/evidence forms, authority transport, epistemic normal forms (distributed claims)  
**Base ontology:** `0_relvar_relation_table_and_boundary_relvar.md` — what is normalized, repaired, transported, authorized.

**Machine contracts:** `normal_form_contracts/` — typed YAML per NF; **canonical substrate** = finite obstruction cochain complex (`C0→C1→Q1`); graphs/matrices/presheaves are optional `carrier_realization` / `geometry_module` only.

**Companion papers:** `000_SmplCache Simplex In-Memory Database and CDC.md`, `000_Quotient Normal Form and Boundary-Certified Databases.md`

**Planned trilogy split (editorial):**

| Paper | Working title | Primary content from this atlas |
|---|---|---|
| A | `1a_bqnf_incremental_repair.md` — Boundary-Quotient Normal Form for Incremental Database Repair | §3 BQNF, terminal routes, running example, minimal category theory |
| B | `1b_gtmur_representation_transport.md` — Certified Representation Transport for Database Systems | §4 certificates, loss ledgers, GTMUR transport, **Compilation NF (CpNF)** |
| C | Finite Authority and Shadow Semantics | GTTC, cofinal towers, authority descent (philosophical layer) |

## Abstract

Classical database normal forms discipline **data at rest**: they decompose relations so dependency anomalies do not appear as accidental redundancy. Simplex database architectures discipline **data in motion, representation, and observation**: they decide whether a CDC event, cache update, query rewrite, representation change, or epistemic observation preserves declared authority, requires a loss ledger, or must terminalize via named routes (such as repair, invalidation, quarantine, or decomposition).

The primary operational components are **Boundary-Quotient Normal Form (BQNF)** for incremental repairs on data in motion, **Gauge Normal Form (GNF)** for representation changes, and the **GTMUR** transport verifier.

---

## 0. Thesis

> **Classical normal forms prevent structural anomalies in stored relations. Simplex normal forms prevent authority anomalies in data that moves, transforms, replicates, summarizes, delegates, or becomes evidence for action.**

Rather than expanding normal forms indefinitely, this framework organizes database and observer actions into **four post-Codd data states** and a cross-cutting metadata layer:

### 1. Data at Rest (Codd Territory)
Normalizes static representation shapes to prevent static dependency and logical anomalies:
- Relational schemas, dependencies, keys, constraints, and stored relations (1NF–6NF, DKNF).
- Selection-projection-join (SPJ/SPJA) canonical query shapes.
- Safe tuple/domain relational calculus ranges.

### 2. Data in Motion (BQNF Territory)
Normalizes runtime transitions, cache updates, and incremental modifications:
- Change Data Capture (CDC) events and streams.
- View and cache repair programs.
- Boundary fingerprints ($\partial Q$) and delta execution.
- Typed terminal routes (`Repair`, `Invalidate`, `Quarantine`, `Decompose`).

### 3. Data in Representation (GTMUR/Gauge Territory)
Normalizes representation shifts, compilations, and structural translations:
- Query rewrites and schema migrations.
- **Gauge Normal Form (GNF)**: The certified condition that representation freedom (e.g., JSON ↔ Protobuf, view ↔ materialized cache, record ↔ embedding) has not changed authority-relevant content.
- Loss ledgers tracking erased attributes, precision, or layout.
- Descent witnesses ($\chi_F$) for GTMUR transport.

### 4. Data under Observation (Epistemic Territory)
Normalizes bounded claims about facts in distributed, cached, or agent-mediated systems:
- Visibility, freshness, and temporal bounds.
- Causal frontiers, divergence budgets, and replication epochs.
- Uncertainty scales and source provenance.
- Authority status gates (available, valid, certified, authorized, actionable).

### Cross-Cutting Layer: Data on Data
The audit and governance substrate verifying the four data states:
- Metadata catalogs and policy rules.
- Transition certificates and loss ledgers.
- Trace logs and verifier execution records.

---

## 1. Classification Categories

To prevent taxonomy bloat, database structures and contracts are organized into distinct categories rather than treating every invariant as a new normal form:

- **Normal Forms:** Decidable representation shapes excluding a declared anomaly (e.g., 1NF/3NF for shape, BQNF for change, GNF for gauge).
- **Certified Forms:** Normal forms combined with a certificate, an obstruction class, and a terminal route (certified $\not\Rightarrow$ authorized).
- **Authority Contracts:** Verifier and policy specifications that evaluate credentials, lineage, and permission (e.g., GTMUR transport contract, GTLA verifier).
- **Observer Contracts:** Visibility and coordinate envelopes (e.g., comparison envelopes $\Omega_{\mathfrak O}$).
- **Ledger Forms:** Structured accounts of lost representation, precision, or attributes (e.g., loss ledger).
- **Domain Extensions:** Extensible modules quarantined from the core database papers (e.g., relativistic coordinate frames, noisy channel boundaries, horizon boundaries, locality cones).

The concrete atlas begins below; distributed claim forms are collected in §7.

---

## 2. Shape Normal Forms

Shape normal forms enforce constraints on static schema design or algebraic query representations.

### 2.1 Classical Relational Normal Forms

Classical relational normal forms are static dependency disciplines. Under the Simplex databases framework, classical anomalies are treated as labeled quotient obstruction slices:

\[
\boxed{
\text{Declared dependency violation}
\Rightarrow
[q_{\mathrm{dep}}]\neq 0
\text{ in a labeled quotient slice}.
}
\]

| Normal Form | Preserves / Enforces | Obstruction Slice |
|---|---|---|
| 1NF | atomic values in relations | hidden nested structure, untyped repeated groups |
| 2NF | no partial dependency of non-key facts on part of a candidate key | partial-key dependency |
| 3NF | no transitive dependency from keys to non-key facts | transitive dependency |
| BCNF | every nontrivial determinant is a superkey | non-superkey determinant |
| EKNF | elementary key dependencies are disciplined tightly | elementary-key anomaly |
| 4NF | nontrivial multivalued dependencies have superkey determinants | multivalued dependency |
| ETNF | join dependencies implied by elementary keys are disciplined | tuple-generating redundancy |
| 5NF / PJNF | nontrivial join dependencies are key-implied | join-dependency anomaly |
| DKNF | all constraints follow from domains and keys | non-domain/key constraint leakage |
| 6NF | relations decomposed into irreducible facts | over-fragmentation or reconstruction burden |

### 2.2 SPJ and SPJA Shape Forms

Selection-projection-join (and aggregation) forms normalize query and view representations:

\[
\text{SPJ Form:} \quad Q \equiv \pi_A(\sigma_\varphi(R_1\Join\cdots\Join R_n))
\]
\[
\text{SPJA Form:} \quad Q \equiv \gamma_{G;\,a_1,\dots,a_k}\pi_A(\sigma_\varphi(R_1\Join\cdots\Join R_n))
\]

SPJA form forces aggregate evidence to be explicit, making incremental repair sound relative to declared sufficient statistics:

| Aggregate | Repair Evidence Required |
|---|---|
| `SUM` | old value, new value, group key, predicate entry/exit |
| `COUNT` | old row membership, new row membership, group key |
| `AVG` | `SUM` and `COUNT` sufficient statistics |
| `MIN` / `MAX` | auxiliary extremum state or conservative invalidation |
| percentile / median | order-statistic state or refusal/lift |

### 2.3 Safe Relational Calculus Forms

Relational calculus shapes support safety under the declared assumptions by enforcing that logical formulas range exclusively over finite, replayable database carriers:
- **Safe Tuple Relational Calculus (STRC):** Form: $\{t \mid \varphi(t)\}$, where $\varphi$ is range-restricted. Unsafe formulas are not authority-bearing because they may range over infinite or undeclared domains.
- **Domain Relational Calculus (DRC):** Form: $\{(x_1,\dots,x_n) \mid \varphi(x_1,\dots,x_n)\}$, isolating domain variables for precise attribute masking and loss ledger accounting.
- **Prenex / Guarded Normal Form:** Form: $Q_1x_1\cdots Q_nx_n.\; G(x_1,\dots,x_n)\wedge\psi$, where the guard $G$ is a finite relation preventing the smuggling of continuum assumptions.

### 2.4 Datalog / Fixpoint Normal Form

Exposes recursive query structures as least fixpoints over a finite lattice:

\[
\boxed{
\operatorname{lfp}(T_P)
}
\]

Non-monotone recursion requires stratification or refusal:

| Recursion Type | Normal Form |
|---|---|
| positive recursion | least fixpoint |
| negation | stratified fixpoint |
| aggregation in recursion | monotone aggregate or refusal |
| nonterminating recursion | budget terminal |

---

## 3. Change Normal Forms

Change normal forms discipline data in motion, tracking how incremental updates affect relational representations.

> **Paper A (canonical):** `1a_bqnf_incremental_repair.md` — standalone BQNF paper for incremental repair, CDC, and materialized views. The subsections below are a short atlas index; prefer Paper A for publication draft.

### 3.0 Running example: `Orders` and `paid_revenue_by_customer`

Carry one schema through the rest of this section:

```text
Orders(order_id, customer_id, amount, status)
```

**Shape at rest (3NF sketch).** Facts about customers belong in `Customers(customer_id, …)`; order amounts and status stay on `Orders`. A transitive dependency `order_id → customer_id → customer_name` is removed by decomposition — classical NF excludes the anomaly from the stored shape.

**View in motion (SPJA).** Materialized aggregate:

```text
paid_revenue_by_customer(customer_id) :=
  SELECT customer_id, SUM(amount) AS revenue
  FROM Orders
  WHERE status = 'paid'
  GROUP BY customer_id
```

**Boundary fingerprint** $\partial Q$:

```text
relations:   [Orders]
attributes:  [customer_id, amount, status]
predicates:  [status = 'paid']
groups:      [customer_id]
aggregates:  [SUM(amount)]
```

**CDC event** $e$: `UPDATE Orders SET amount = 120, status = 'paid' WHERE order_id = 42`  
(old: `amount=100`, `status='pending'`, `customer_id=7`).

| Step | Question | This event |
|---|---|---|
| 1. Boundary | Does $e$ intersect $\partial Q$? | Yes — `amount`, `status` |
| 2. Delta | Is $\Delta Q(e)$ computable from CDC evidence? | Yes — predicate entry (`pending`→`paid`), group key 7, old/new amount |
| 3. Quotient class | Is the defect exact or residual? | Exact repair: increment `revenue` for customer 7 by $+20$ |
| 4. Repair image | Witness $\alpha$ with $\omega = d_0\alpha$? | Local aggregate update (SUM lane) |
| 5. Terminal route | If not exact, which route? | `Repair(α)` — not `Invalidate` / `Escalate` |

If the CDC stream omitted `status` before/after, the same boundary intersection would hold but clause (2) would fail → terminal route `Invalidate` (missing evidence), not silent repair. That is the systems point BQNF is trying to capture.

### 3.1 Boundary-Quotient Normal Form (BQNF)

Boundary-Quotient Normal Form is the unified certified normal form for runtime database updates. It integrates boundary declarations, delta programs, and quotient classification to verify whether an update represents a sound repair or an obstruction.

#### Quotient obstruction (operational reading)

Fix a **layer** (one materialized view, cache entry, or observer). Declare:

- **0-cells** $C^0$: admissible repair potentials (e.g., group-key deltas, predicate entry/exit adjustments, sufficient-statistic updates).
- **1-cells** $C^1$: **defects** $\omega$ — finite packets describing how a write event disagrees with the current certified state relative to $\partial Q$.
- **Boundary operator** $d_0: C^0 \to C^1$: maps a repair potential $\alpha$ to its induced defect $d_0\alpha$.

Two defects are **equivalent for repair** when they differ by an admissible repair:

\[
\omega_1 \sim \omega_2 \;\Leftrightarrow\; \omega_1 - \omega_2 \in \operatorname{im}(d_0).
\]

The **quotient obstruction space** is the space of defect classes:

\[
Q^1 = C^1 / \operatorname{im}(d_0),
\qquad
[\omega] = 0 \;\Leftrightarrow\; \omega = d_0\alpha \text{ for some admissible } \alpha.
\]

Operationally: $[\omega]=0$ means “incremental repair preserves declared query semantics under $\partial Q$”; $[\omega]\neq 0$ means “residual obstruction — escalate, lift auxiliary state, or invalidate.” The cochain condition $d_1\omega=0$ (when used) separates **closed residuals** from **closure failure**; see the terminal table below.

> **Theorem-shaped (Boundary exactness criterion).**  
> *Let $Q$ be a view with declared boundary $\partial Q$ and admissible repair potentials $C^0$. If a write event $e$ induces $\omega(e)\in C^1$ and there exists computable evidence yielding a witness $\alpha$ such that $\omega(e)=d_0\alpha$, then incremental repair along $\alpha$ preserves the semantics of $Q$ on the declared SPJA fragment (SUM/COUNT/AVG lanes under sufficient statistics; MIN/MAX only with declared auxiliary state or conservative invalidation).*  
> 
> *Proof obligation:* fix explicit $C^0,C^1,d_0$ for the workload fragment and show $\alpha$ updates sufficient statistics iff the view homomorphism commutes with the CDC-evidence monoid. Deferred to Paper A; SmplCache instantiates the SUM/COUNT/AVG case.

An update event $\omega$ in $C^1$ satisfies BQNF under five strict subclauses:

1. **Boundary Declared:** The query/view shape must declare its boundary fingerprint:
    \[
    \partial Q = (\text{relations},\text{attributes},\text{predicates},\text{groups},\text{aggregates},\text{policies}).
    \]
2. **Delta Computable:** The write event must admit a computable delta program:
    \[
    \Delta Q(e) = Q(S+\Delta_e) - Q(S).
    \]
3. **Quotient Class Computable:** The event defect $\omega(e)$ must map to a computable class $[\omega(e)]$ in the quotient obstruction space $Q^1 = C^1 / \operatorname{im}(d_0)$.
4. **Repair Image Declared:** A sound repair is possible if and only if $[\omega(e)] = 0$ (implying the change is an exact boundary $\omega = d_0\alpha$, resulting in a repair action $\alpha$).
5. **Terminal Route Declared:** If $[\omega(e)] \neq 0$, the system must execute a declared terminal route:

| BQNF Classification | Condition | Terminal Route |
|---|---|---|
| **Exact Repair** | $\omega = d_0\alpha$ | `Repair(α)` |
| **Closed Residual** | $d_1\omega = 0, \ [\omega]\neq0$ | `Residual` / `Escalate` |
| **Closure Failure** | $d_1\omega \neq 0$ | `ClosureFailure` |
| **Unknown Obstruction**| missing evidence | `Invalidate` / `BudgetUnknown` |

Other terminal routes include: `Serialize`, `Recompute`, `Lift`, `Unsupported`, `ConservativeInvalidate`, `Quarantine` (isolate the packet because neither repair nor authorization is safe), and `Decompose` (split a compound packet into separately certifiable subpackets).

---

## 4. Evidence and Certificate Forms

These structures normalize proof and audit artifacts rather than active relations.

> **Paper B (canonical):** `1b_gtmur_representation_transport.md` — GTMUR transport, loss ledgers, comparison envelopes, verifier architecture. The subsections below are a short atlas index.

### 4.1 CDC Evidence Form

Defines the canonical, structured representation of raw database write events:
```text
write event
-> old row
-> new row
-> changed attributes
-> predicate membership before/after
-> group key before/after
-> policy context
```

### 4.2 Certificate Form

Certifies that a representation change, query rewrite, or repair step is authority-preserving. Every certificate must match this canonical packet shape:

```json
{
  "certificate_id": "cert_xyz123",
  "source_regime": "sql_query_or_schema",
  "target_regime": "boundary_repair_packet",
  "morphism_kind": "project|refine|rewrite|approx",
  "preserved_skeleton": ["attributes", "keys"],
  "erased_distinctions": ["phases", "indices"],
  "loss_ledger_ref": "ledger_abc789",
  "obstruction_class": "[omega]",
  "terminal_route": "Repair|Invalidate|Lift|Escalate"
}
```

### 4.3 Loss Ledger Form

Documents lost resolution, forgotten attributes, or structural approximations during a representation change, preventing silent authority degradation.

### 4.4 Provenance Form

Normalizes the tracking of query tuples mapped to algebraic semirings ($t \mapsto p_t \in K$) to verify data lineage and policy adherence.

---

## 5. Authority Contracts

Authority contracts are not normal forms. They are active verification rules that govern whether normal forms can claim active authority.

### 5.1 GTMUR Transport Contract

Governs representation changes ($F: A \to A_{\mathrm{nf}}$). Authority transport is supported if and only if the system declares a descent-compatibility certificate $\chi_F$ and a loss ledger:

\[
\boxed{
\chi_F: D_{A_{\mathrm{nf}}} F \Rightarrow \bar{F} D_A
}
\]

#### GTMUR Failure Terminals
- `TransportViolation`: No $\chi_F$ exists for the normalizing map.
- `SilentMutation`: A protected structural skeleton was altered without a ledger.
- `LossLedgerMissing`: Lossy normalization was executed without an accounting ledger.
- `TargetTerminalBypass`: The normalized object bypassed its target verifier.
- `AuthorityLaundering`: A representationally normal form is mistaken for an authorized form.

### 5.2 Comparison envelope ($\Omega_{\mathfrak O}$)

Enables different candidate normal forms or plan decompositions to be combined or compared via pullback, pushout, or limit constructions (formal details: Paper B §5):

\[
N_1(A) \xleftarrow{p_1} C(A) \xrightarrow{p_2} N_2(A)
\]

- **Pullback Policy-Data Envelope:** Pulls back data representations with policy domains.
- **Pushout Migration Envelope:** Merges schemas under declared identifications.
- **Weak Terminal Comparison Envelope:** Evaluates candidate repairs against a single terminal criterion.
- **Failure terminals:** `NoComparisonEnvelope`, `NonComposableCertificate`, and `CompletionWithoutDescent`.

### 5.3 Finite-shadow authority criterion (GTTC)

Governs continuous or evolving systems by asserting that a continuous object is authority-bearing if and only if there exists a cofinal, coherent tower of authorized finite shadows:

\[
\exists \Lambda_0 \subseteq \Lambda \text{ cofinal}: \forall \lambda \in \Lambda_0, \mathsf{Auth}*{\Omega*{\mathfrak O}}(A_\lambda) \downarrow \text{ and } \chi_{\lambda\mu} \downarrow.
\]

- **GTTC Failure Terminals:** `NoFiniteShadow`, `NoCofinalAuthorizedShadow`, `ShadowIncoherence`, `ApproximationLedgerMissing`, and `LimitMembershipNotAuthority`.

### 5.4 Terminal authority verifier (GTLA)

The outermost verification engine that evaluates the entire pipeline's descent to finite, authorized packets. It is the judge of normal forms, not a member of the normal-form atlas (Paper C):

\[
\Pi^\sharp = \tau^\sharp \circ_K \operatorname{FOC}^\sharp \circ_K D^\sharp \circ_K \rho^\sharp \circ_K \mathcal{R}^\sharp
\]

---

## 6. Motion Accounting Contracts (Archived Draft)

These forms cover data that is moving but not fully accounted for by BQNF's single-boundary repair question. They are **draft finite contracts**, not physics claims. Each one must bind to a finite carrier, emit a terminal route, and state explicit non-claims before promotion.

| Contract | Minimum Declaration | Anomaly Excluded | Carrier |
|---|---|---|---|
| **Flow Control Contract (FCC)** | ordering key, offset, watermark, capacity, backpressure, drop and replay policy | **silent motion loss** — stream loss, lag, duplicate, reorder, or overflow presented as exact delivery | `ordered_stream` |
| **Light-Cone Causality Contract (LCCC)** | event location/time, clock basis, propagation medium, max speed, path/latency bound | **impossible causal order** — event B claims dependence on A before A could reach B | `finite_metric_graph` |
| **Clock-Synchronization Contract (CSC)** | clock id/type, sync source, drift/offset bounds, monotonicity, reset policy | **exact global time fiction** — wall-clock timestamps used as total order without uncertainty | `finite_metric_graph` |
| **Locality-Bound Propagation Contract (LBPC)** | finite locality graph, metric, interaction radius, velocity/decay bound, event support, observation window | **instant influence** — local event treated as globally available without cone or residual ledger | `finite_metric_graph` |
| **Horizon Emission Contract (HEC)** | horizon boundary, interior/exterior partition, emission channel, coarse graining, conservation/loss ledger | **unledgered horizon crossing** — exterior emitted summary treated as interior authority | `boundary_channel` |

### 6.1 Flow Control Contract (FCC)

A stream lane satisfies the **Flow Control Contract** iff each moving record can be replayed or refused through:

```text
event_identity, ordering_key, offset, watermark_rule, capacity_budget,
backpressure_policy, drop_policy, replay_window, duplicate_handling_rule
```

FCNF is the motion discipline for queues, CDC logs, compaction lanes, and retry buffers. It complements BQNF: FCNF proves the event lane did not silently lose or reorder evidence; BQNF proves what a surviving event may do to an observer boundary.

### 6.2 Light-Cone Causality Contract (LCCC)

A distributed event claim satisfies **LCCC** iff a claimed causal edge is admissible under declared propagation bounds:

```text
event_location, event_time, reference_frame_or_clock_basis,
propagation_medium, max_signal_speed, path_model, latency_bound
```

If two writes are outside each other's declared cone, the system may terminalize as `SpacelikeConcurrent` or require `ConsensusRequired`; it may not silently impose a total order.

### 6.3 Clock-Synchronization Contract (CSC)

A timestamp claim satisfies **CSC** iff it carries clock authority and uncertainty:

```text
clock_id, clock_type, sync_source, drift_bound, offset_bound,
monotonicity_rule, reset_policy, total_order_authority_rule
```

The contract excludes treating a timestamp scalar as exact global time. When uncertainty intervals overlap, total ordering requires a clock-bound proof or consensus certificate.

### 6.4 Locality-Bound Propagation Contract (LBPC)

LBPC imports the operational shape of a Lieb-Robinson-style finite locality bound into data systems: a local perturbation may affect distant observers only inside a declared locality cone, or outside it with an explicit residual/suppression ledger.

```text
finite_locality_graph, graph_metric, local_interaction_or_dependency_radius,
velocity_bound, decay_bound_or_epsilon, event_support, observation_window
```

This is useful for dependency graphs, distributed invalidation, lattice shadows, network neighborhoods, and bounded-effect agent tools. It does **not** prove a physical theorem for undeclared systems.

### 6.5 Horizon Emission Contract (HEC)

HEC accounts for data crossing a boundary after which the original interior state is inaccessible to an exterior observer: redaction, eviction, compaction, lossy summarization, tombstoning, or a Hawking-radiation-style emission channel.

```text
horizon_boundary, interior_region, exterior_observer, crossing_rule,
emission_channel, coarse_graining_map, conservation_ledger,
recoverability_class, refusal_rule_for_interior_claims
```

The finite rule is simple: exterior packets can authorize only what the emission channel and loss/conservation ledger support. Row-level or microstate claims across the horizon require a lift witness or must terminalize as `InteriorInaccessible`, `RecoverabilityUnknown`, or `RefuseUnledgeredHorizon`.

---

## 7. Epistemic Verification and Distributed Claims

Classical Codd-style database theory assumed a single coherent store: *the database contains facts.* Distributed, cached, and agent-mediated systems require a different default:

\[
\boxed{
\text{The system contains bounded, authorized \textbf{claims} about facts.}
}
\]

Rather than treating every metadata boundary as a new normal form, we organize checking disciplines into the four post-Codd data states and define a minimal basis of ten core anomalies.

### Core Anomaly and Form Mapping

| Data State | Checking Discipline | Minimum Declaration | Anomaly Excluded |
|---|---|---|---|
| **Data at Rest** | Shape NFs (1NF–3NF) | Functional dependencies, candidate keys | **redundancy anomalies** |
| **Data in Motion** | **Boundary-Quotient NF (BQNF)** | boundary, delta, quotient class, repair image, terminal route | **unsound repair** |
| | Flow Control NF (FCNF) | ordering key, offset, watermark, capacity, drop/replay policy | **silent motion loss** — queue or CDC lane hides loss, lag, duplicate, reorder, or overflow |
| | Locality/Causality contracts (LCCC, LBPC) | finite metric graph, event support, propagation/time bounds | **instant influence** — local event treated as globally available without finite cone or residual ledger |
| | Horizon Emission Contract (HEC) | horizon boundary, emission channel, loss/conservation ledger | **unledgered horizon crossing** — exterior summary promoted to interior authority |
| **Data in Representation** | **Gauge Normal Form (GNF)** | source/target format, authority skeleton, conversion witness | **gauge drift** — representations differ in authority content |
| | GTMUR Transport | descent witness $\chi_F$, loss ledger | **schema drift** & **residual privacy** — silent loss/leak of structure |
| **Data under Observation** | Location NF (LNF) | logical ID, physical placement, movement policy | **ghost locality** — logical location differs from active copies |
| | Replica NF (RNF) / FNF | origin, epoch, causal frontier, freshness SLA | **staleness fraud** — serving stale state without lag declaration |
| | Orchestration NF (ONF) | initiator, tool, input/output, delegation, rollback | **delegation overreach** — actions beyond delegation boundary |
| | Context NF (CNF) | typed prompt, retrieval, tool, and policy layers | **context smuggling** — prompt injection via merged contexts |
| | Provenance NF (PvNF) / ANF | source facts, model/tool calls, seeds, signatures | **authority laundering** — unverified claims promoted as facts |
| | Observer NF (ODNF) | measurements, equivalence relations, transport | **observer leak** — cross-observer information exposure |
| **Data on Data** | Certificate Form | certificate ID, source/target, preserved skeleton | **orphan certificate** — certificate exists without verifier check |
| | Verifier Record | verifier ID, replay logs, signatures | **verifier void** — certificates logged but never replay-checked |

> **A certificate table without a verifier is just another table.**

If a certificate exists (proving *certification*), but no active verifier replay checks it (yielding *authorization*), the system is in a **verifier void**.

(See §7.9 — gates are **not** implied by one another.)

### 7.1 Location Normal Form (LNF)

A datum is in **Location Normal Form** iff every authoritative reference declares:

```text
logical_id, physical_placement, replica_set, storage_tier, relocation_policy
```

**Use:** federated query routing, cache pinning, tiered storage, vector/GPU offload. **Certification:** placement certificate when data moves (GTMUR transport + LNF ledger entry).

### 7.2 Replica Normal Form (RNF)

A copy is in **Replica Normal Form** iff it carries:

```text
origin, epoch, causal_frontier, divergence_budget, reconciliation_rule
```

**Use:** multi-region SQL, CRDTs, read replicas, event sourcing. **Terminal routes:** `Repair`, `Serialize`, `Recompute`, `Escalate` when frontier or budget is exceeded (aligns with BQNF §3.1).

### 7.3 State Normal Form (StNF)

A record is in **State Normal Form** iff its state is not a bare scalar but a packet:

```text
(value, version, causal_context, confidence, freshness, authority)
```

**Composition with BQNF:** BQNF certifies *how* a write updates a layer; StNF certifies *what* consumers read at rest between writes. A BQNF `Repair(α)` should update the StNF packet in lockstep (version bump, freshness, authority bit).

**Example (Orders):** not `revenue = 42000` but:

```json
{
  "value": 42000,
  "version": "mv_paid_revenue_v17",
  "causal_context": "cdc_evt_42",
  "confidence": 1.0,
  "freshness": { "read_at": "2026-05-19T12:00:00Z", "source": "smplcache_primary" },
  "authority": "certified_not_authorized"
}
```

### 7.4 Orchestration Normal Form (ONF)

An agent or workflow step is in **Orchestration Normal Form** iff each action declares:

```text
initiator, tool, input_state, output_state, delegated_authority, rollback_path, terminal_route
```

**Use:** LLM tool loops, ETL DAGs, human-in-the-loop approval. **Analogy:** ONF is BQNF for *agent actions* — same terminal discipline (`Repair`/`Refuse`/`Escalate`), different boundary (tools and policies, not SQL aggregates).

### 7.5 Context Normal Form (CNF)

Agent memory is in **Context Normal Form** iff prompts, retrieved context, tool results, and policy constraints occupy **typed layers** with explicit merge rules — never a single undifferentiated string.

```text
user_intent_layer
retrieval_layer (cite source_id per chunk)
tool_output_layer
policy_layer (non-user-visible; hash or seal)
```

**Loss ledger:** when layers are collapsed for token budget, ledger records what was erased (Paper B).

### 7.6 Provenance Normal Form (PvNF)

A generated answer or derived data product is in **Provenance Normal Form** iff it declares:

```text
source_facts, transformations, model_or_tool_calls, uncertainty, non_replayable_steps
```

Extends §4.4 Provenance Form (semiring packets) to **model outputs** and **irreversible steps** (sampling, external API, human judgment). Terminal `Refuse` when provenance cannot be reconstructed.

### 7.7 Freshness Normal Form (FNF)

A query result is in **Freshness Normal Form** iff it carries:

```text
read_timestamp, replica_lag, cache_age, invalidation_status, freshness_sla
```

**Composition:** pairs with BQNF `Invalidate` / `Preserve` — FNF exposes *why* a read is stale; BQNF decides *whether* repair is possible.

### 7.8 Stripe Normal Form (SnNF)

**Stripe** here means **shard/stripe layout** (erasure coding, parity), not payment processing. Data is in **Stripe Normal Form** iff every logical object has a reconstructable map of:

```text
shards, erasure_fragments, parity_layout, encryption_domains, failure_groups
```

**Use:** object storage, distributed filesystems, columnar shards. Excludes claiming durability without stating survived failure modes.

### 7.9 Authority Normal Form (ANF)

A system object satisfies **Authority Normal Form** iff consumers can distinguish five gates:

| Gate | Meaning |
|---|---|
| `available` | bits reachable (RPC success, row returned) |
| `valid` | satisfies schema, types, local constraints |
| `certified` | normal form + certificate + obstruction/terminal declared |
| `authorized` | policy/verifier accepts trust lineage |
| `actionable` | permitted to drive side effects (write, spend, notify) |

Extends §0 hierarchy explicitly for distributed readers:

Each gate is a **separate check**. In particular: `available` does not imply `valid`; `certified` does not imply `authorized` (§0). The classical hierarchy Form ⊂ NF ⊂ Certified ⊂ Authorized applies to **representation shapes**, not to RPC reachability.

**Terminal:** `AuthorityLaundering` (Paper B) when a lower gate is mistaken for a higher one.

### 7.10 Epistemic Normal Form (ENF) — master packet

A distributed AI/data system is in **Epistemic Normal Form** when every outward claim about data can be reduced to a master packet:

```text
what_is_known
by_whom
as_of_when
under_which_authority
with_what_uncertainty
terminal_route_if_challenged
```

ENF is the **composition target** of LNF–SnNF: subordinate normal forms supply fields; ENF forbids omitting any dimension. Challenge routes reuse BQNF/GTMUR terminals (`Escalate`, `Invalidate`, `Refuse`, `Recompute`).

> **Thesis (epistemic replacement for Codd default).**  
> Modern systems should be judged not only on whether dependencies are decomposed, but on whether they can truthfully answer: *where is it, what version is it, who may rely on it, what uncertainty remains, and what happens if challenged?*  
> 
> **Paper program (future):** operational checklists and certificates per epistemic NF, analogous to Paper A (BQNF) and Paper B (GTMUR).

### 7.11 Mapping epistemic NFs to the existing stack

| Epistemic NF | Nearest existing artifact |
|---|---|
| StNF, FNF | BQNF repair + CDC evidence (Paper A) |
| PvNF | Provenance form (§4.4), certificates (Paper B) |
| ANF, ENF | Form ⊂ NF ⊂ Certified ⊂ Authorized (§0); GTLA verifier (§5.4) |
| ONF, CNF | Orchestration certificates (future); GTMUR loss ledger for collapsed context |
| LNF, RNF, SnNF | Replication/metadata catalogs; Stripe layout manifests |

---

## 8. Synthesis

- **Shape Normal Forms** exclude static dependency and range anomalies in data at rest.
- **Boundary-Quotient Normal Form (BQNF)** certifies whether runtime data in motion represents a sound repair or an obstruction.
- **Evidence and Certificate Forms** standardize audit trails, provenance, and the structural skeletons preserved during transitions.
- **Authority Contracts** govern the active transport, comparison, and finite shadowing of representation states, ensuring authority descent remains bounded and checked.
- **Epistemic Normal Forms** (§7) specify what a distributed system must declare so it does not pretend to omniscient global state — composing locality, version, freshness, provenance, and authority into bounded claims.
