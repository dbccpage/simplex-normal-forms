# Boundary-Quotient Normal Form for Incremental Database Repair

> Absorbed canonical paper copy from
> `omega_engine/research/in_work/simplex_cosmos_papers/SMPLX_009_Simplex Databases/crap/1a_bqnf_incremental_repair.md`.
> The source folder was integrated into the root scaffold and removed.

**Author:** Jeremy H. Carroll  
**Date:** May 2026  
**Series:** SMPLX-009 Paper A (systems / incremental repair)  
**Status:** draft — standalone extract from the Simplex Databases atlas

**Companion documents:**

| Document | Role |
|---|---|
| `0_relvar_relation_table_and_boundary_relvar.md` | **Base ontology** — relvar, boundary relvar, observer relvar |
| `normal_form_contracts/contracts/nf.change.bqnf.yaml` | **Contract** — checkable BQNF obligations |
| `1_normal_forms.md` | Full taxonomy atlas (shape forms, certificates, authority pointers) |
| `paper_0_quotient_normal_form_boundary_certified_databases` | Product wedge summary |
| `000_SmplCache Simplex In-Memory Database and CDC.md` | Reference implementation |
| `1b_gtmur_representation_transport.md` | Paper B — representation transport (GTMUR) |
| `1c_*` (planned) | Paper C — finite-shadow authority (GTTC) |

---

## Abstract

Classical database normal forms discipline **data at rest**: they decompose relations so dependency anomalies do not appear as accidental redundancy. They do not decide whether a CDC event can incrementally repair a materialized view, preserve a cache entry, or must force invalidation.

**Boundary-Quotient Normal Form (BQNF)** disciplines **data in motion**. For each observer layer (materialized view, cache shape, incremental aggregate), BQNF requires five declared artifacts: a boundary fingerprint, a computable delta program, a quotient obstruction class, a repair image, and a terminal route. Repair is permitted only when the write defect lies in the repair image (quotient class zero); otherwise the system must follow a typed terminal (`Repair`, `Invalidate`, `Escalate`, `ClosureFailure`, …) — never silent success.

This paper states BQNF operationally, walks a single running example end-to-end, and maps the framework onto CDC pipelines, materialized views, and cache repair (SmplCache). Category-theoretic vocabulary is minimized; proof obligations are stated explicitly where full formalization is deferred.

---

## 1. Introduction

> **Ontology:** BQNF certifies transitions on a **boundary relvar** $\mathcal B = (H,\Sigma,C^0\xrightarrow{d_0}C^1,Q^1,\mathsf{Term})$ — see `0_relvar_relation_table_and_boundary_relvar.md` Part VII.

### 1.1 The gap classical normal forms do not close

Third normal form answers: *How should I store facts so updates do not create dependency anomalies?*

It does not answer:

* Does this `UPDATE` require recomputing my materialized aggregate?
* Can I apply a local delta to `SUM(amount)` given only partial CDC columns?
* When two concurrent writes hit the same boundary, must I serialize?
* Is my cache still authoritative, or must I invalidate?

Those are **runtime repair** questions. They depend on the triple

\[
(\mathsf{schema},\ \mathsf{workload},\ \mathsf{CDC\ stream}),
\]

not on schema alone.

### 1.2 Design principle

\[
\boxed{\text{A database should not guess what a write breaks. It should compute the obstruction.}}
\]

BQNF is the checklist that makes this principle auditable: every decision is either a certified repair or a declared terminal.

### 1.3 Relation to classical normal forms (one paragraph)

Classical violations (partial key, transitive dependency, join dependency, …) can be encoded as **labeled obstruction slices** once dependency-specific matrices are fixed. This paper does not develop that bridge; it is conservative and one-way in the atlas. Paper A focuses on **incremental SPJA views** under CDC evidence.

### 1.4 Professional bar (implementation invariant)

Any system claiming BQNF compliance must enforce:

1. **No silent under-invalidation** — if the boundary is hit and repair is not certified, do not serve stale results as fresh.
2. **No repair claim without evidence** — $\omega = d_0\alpha$ only when CDC supplies the witnesses the aggregate lane requires.
3. **No unsupported feature quietly accepted** — return `Unsupported` or `ConservativeInvalidate`, not heuristic success.

### 1.5 Classical vs distributed era (why BQNF now)

| Classical DB era | Distributed / AI era |
|---|---|
| redundancy anomaly | **epistemic anomaly** (stale, approximate, or unlocatable truth) |
| dependency preservation | **authority preservation** |
| tuple consistency | **observer consistency** (per layer $L$) |
| schema decomposition | **state decomposition** (version, freshness, provenance packets) |
| normal form | **certifiable operational boundary** ($\partial Q$) |
| transaction commit | **terminalized repair decision** (`Repair` / `Invalidate` / …) |

Codd assumed centralized authority, bounded state, and a singular store. Modern systems have diverging replicas, competing caches, vector shadows, and agent-mediated writes. BQNF does not solve all of that; it solves the **finite-evidence incremental repair** wedge. Broader epistemic normal forms are indexed in `1_normal_forms.md` §7.

---

## 2. Boundary-Quotient Normal Form (BQNF)

A **layer** $L$ is one certified observer: a materialized view row-set, cache entry, streaming aggregate pane, or CQRS read model slice.

An update **write event** $e$ (from CDC, logical replication, or application log) induces a **defect** $\omega(e)$ relative to a declared query shape $Q$.

$e$ satisfies **BQNF** for layer $L$ when all five subclauses hold.

### 2.1 Five subclauses

| # | Subclause | Requirement |
|---|---|---|
| 1 | **Boundary declared** | Fingerprint $\partial Q$ is fixed before runtime |
| 2 | **Delta computable** | $\Delta Q(e) = Q(S+\Delta_e) - Q(S)$ is computable from admissible evidence |
| 3 | **Quotient class computable** | $\omega(e)$ maps to class $[\omega(e)] \in Q^1$ |
| 4 | **Repair image declared** | Exact repair iff $[\omega(e)] = 0$ (equivalently $\omega(e) = d_0\alpha$ for admissible $\alpha$) |
| 5 | **Terminal route declared** | If $[\omega(e)] \neq 0$ or evidence is missing, execute a named terminal |

**Boundary fingerprint:**

\[
\partial Q = (\text{relations},\ \text{attributes},\ \text{predicates},\ \text{groups},\ \text{aggregates},\ \text{policies}).
\]

**Delta program:**

\[
\Delta Q(e) = Q(S+\Delta_e) - Q(S).
\]

Clause (1) is cheap: disjoint column change → `Preserve` (no boundary intersection). Clauses (2)–(5) are where systems fail today (silent stale cache, guessed invalidation).

### 2.2 Quotient obstruction (operational)

Per layer, fix finite-dimensional data structures (not a general category):

* $C^0$ — **repair potentials** $\alpha$: finite packets describing admissible local updates (group-key delta, predicate entry/exit, sufficient-statistic bump).
* $C^1$ — **defects** $\omega$: how event $e$ disagrees with the current certified state relative to $\partial Q$.
* $d_0: C^0 \to C^1$ — maps potential $\alpha$ to induced defect $d_0\alpha$.

**Equivalence:** $\omega_1 \sim \omega_2$ iff $\omega_1 - \omega_2 \in \operatorname{im}(d_0)$.

**Quotient space:**

\[
Q^1 = C^1 / \operatorname{im}(d_0),
\qquad
[\omega] = 0 \;\Leftrightarrow\; \omega = d_0\alpha \text{ for some admissible } \alpha.
\]

**Reading:** $[\omega]=0$ → incremental repair preserves $Q$ under the declared SPJA fragment. $[\omega]\neq 0$ → residual obstruction; choose `Escalate`, `Lift`, `Recompute`, or `Invalidate`.

**Optional closure bit:** when a secondary check $d_1$ is declared, $d_1\omega = 0$ with $[\omega]\neq 0$ marks a **closed residual** (obstruction visible but not exact); $d_1\omega \neq 0$ marks **closure failure**. Many production pipelines omit $d_1$ and collapse to the four-row table in §4.

### 2.3 Certified vs authorized

BQNF produces a **certified** decision (valid class, evidence, terminal). **Authorization** (policy, federation, trust lineage) is a separate gate — see the atlas §0 and planned Paper B (`1b_*`). Do not treat a BQNF certificate as permission to bypass policy.

---

## 3. Running example: `Orders` and `paid_revenue_by_customer`

### 3.1 Schema and view

```text
Orders(order_id, customer_id, amount, status)

paid_revenue_by_customer(customer_id) :=
  SELECT customer_id, SUM(amount) AS revenue
  FROM Orders
  WHERE status = 'paid'
  GROUP BY customer_id
```

**Boundary** $\partial Q$:

```text
relations:   [Orders]
attributes:  [customer_id, amount, status]
predicates:  [status = 'paid']
groups:      [customer_id]
aggregates:  [SUM(amount)]
```

### 3.2 Event A — certified repair

**CDC:** `UPDATE Orders SET amount = 120, status = 'paid' WHERE order_id = 42`  
**Before:** `(amount=100, status='pending', customer_id=7)`  
**After:** `(amount=120, status='paid', customer_id=7)`

| BQNF step | Result |
|---|---|
| 1. Boundary | Intersects (`amount`, `status`) |
| 2. Delta | Predicate entry `pending→paid`; group key `7`; amount delta `+20` on paid lane |
| 3. Quotient | Class zero: defect equals $d_0\alpha$ for SUM lane |
| 4. Repair | $\alpha$ = increment `revenue` for customer `7` by `20` |
| 5. Terminal | `Repair(α)` |

**Certificate sketch:**

```json
{
  "shape": "paid_revenue_by_customer",
  "event_id": "evt_42",
  "relation": "Orders",
  "decision_kind": "repair",
  "reason_code": "predicate_entry_and_amount_delta",
  "required_evidence": ["amount", "customer_id", "status"],
  "available_evidence": ["amount", "customer_id", "status"],
  "repair_program": "paid_sum_by_group_key",
  "obstruction_class": "[0]",
  "terminal_route": "Repair"
}
```

### 3.3 Event B — same boundary, missing evidence

Same `UPDATE`, but CDC delivers only `(order_id, amount)` — no `status` before/after.

| BQNF step | Result |
|---|---|
| 1. Boundary | Intersects |
| 2. Delta | **Not computable** — cannot certify predicate entry/exit |
| 3–4. Quotient / repair | Not claimed |
| 5. Terminal | `Invalidate` (or `ConservativeInvalidate`) |

**Invariant:** boundary intersection without evidence must not repair. This is the primary failure mode of heuristic caches.

### 3.4 Event C — disjoint boundary

`UPDATE Orders SET ship_date = today WHERE order_id = 99` — `ship_date` not in $\partial Q$.

| BQNF step | Result |
|---|---|
| 1. Boundary | No intersection |
| 5. Terminal | `Preserve` |

### 3.5 Event D — MIN/MAX without auxiliary state

View: `max_paid_amount = MAX(amount) …` with no extremum witness table. A qualifying `UPDATE` may change the global maximum without finite evidence.

| BQNF step | Result |
|---|---|
| 2–4. | No admissible $\alpha$ in declared $C^0$ |
| 5. Terminal | `Unsupported` or `ConservativeInvalidate` |

**Lift path:** add auxiliary `(value, row_id)` per group or refuse repair — BQNF `Lift` terminal documents the engineering obligation.

---

## 4. Terminal routes

### 4.1 Core classification (BQNF table)

| Classification | Condition | Terminal route |
|---|---|---|
| **Exact repair** | $\omega = d_0\alpha$ | `Repair(α)` |
| **Closed residual** | $d_1\omega = 0$, $[\omega]\neq 0$ | `Residual` / `Escalate` |
| **Closure failure** | $d_1\omega \neq 0$ | `ClosureFailure` |
| **Unknown** | missing evidence | `Invalidate` / `BudgetUnknown` |

### 4.2 Extended operational routes

| Route | When to use |
|---|---|
| `Preserve` | no boundary intersection |
| `Repair` | quotient class zero; local delta certified |
| `Invalidate` | intersects boundary; repair not certified |
| `Recompute` | full materialization available; local repair refused |
| `Serialize` | concurrent boundary events do not commute |
| `Lift` | repairable after adding auxiliary state / witness |
| `Unsupported` | shape outside declared SPJA fragment |
| `ConservativeInvalidate` | safe fallback under partial evidence |

Terminals are **typed outcomes** (like checked exceptions): the obstruction is part of the API contract, not an internal log detail.

### 4.3 Terminals as epistemic declarations

BQNF terminals are not mere implementation return codes. Each names what the system **may claim to know** about layer $L$ after event $e$:

| Terminal | Epistemic meaning (observer $L$) |
|---|---|
| `Preserve` | write irrelevant to declared boundary; prior knowledge unchanged |
| `Repair` | knowledge preserved; local update certified |
| `Invalidate` | knowledge lost for $L$; must not present stale state as current |
| `Escalate` / `Residual` | local knowledge insufficient; wider regime required |
| `Serialize` | concurrent writes yield incompatible knowledge; order required |
| `Lift` | current representation cannot express repair; auxiliary state needed |
| `Unsupported` | observer algebra cannot represent change finitely |
| `ClosureFailure` | inconsistency would propagate if repair were claimed |
| `ConservativeInvalidate` | evidence incomplete; safe refusal |

This is the seed of **epistemic boundary normal forms** (atlas §7): the system must not present uncertainty as certainty, stale state as authoritative, or approximate state as exact. BQNF is the **executable** subset grounded in finite CDC evidence and SPJA algebras.

### 4.4 Engineering discipline (scope guard)

BQNF remains tractable only while claims stay tied to:

* finite evidence packets,
* finite aggregate repair programs,
* explicit boundaries $\partial Q$,
* typed terminals.

Generalizing “all cognition is quotient transport” without this substrate loses engineering traction. Papers A–B stay anchored in **replayability, certifiability, and explicit observer boundaries**.

---

## 5. SPJA fragment and aggregate evidence

BQNF is intentionally aligned with **selection–projection–join–aggregate** materialized views.

**SPJ shape:**

\[
Q \equiv \pi_A(\sigma_\varphi(R_1 \Join \cdots \Join R_n))
\]

**SPJA shape:**

\[
Q \equiv \gamma_{G;\,a_1,\dots,a_k}\,\pi_A(\sigma_\varphi(R_1 \Join \cdots \Join R_n))
\]

### 5.1 Evidence required per aggregate lane

| Aggregate | Repair evidence (minimum) |
|---|---|
| `SUM` | old value, new value, group key, predicate before/after |
| `COUNT` | row membership before/after, group key |
| `AVG` | `SUM` and `COUNT` sufficient statistics |
| `MIN` / `MAX` | extremum witness or conservative invalidation |
| percentile / median | order-statistic state or `Unsupported` / `Lift` |

**AVG rule:** never repair AVG from a single column delta without COUNT; maintain $(\sum, cnt)$ or invalidate.

### 5.2 CDC evidence form (canonical packet)

```text
write event
  -> old row
  -> new row
  -> changed attributes
  -> predicate membership before/after
  -> group key before/after
  -> policy context (optional)
```

Clause (2) of BQNF is satisfied iff this packet supports the aggregate lane’s row in §5.1.

---

## 6. Theorems and proof obligations

### 6.1 Boundary exactness (sufficient condition)

> **Theorem (Boundary exactness).**  
> Let $Q$ be a view with declared $\partial Q$ and admissible $C^0,C^1,d_0$ for a fixed SPJA fragment $\mathcal{F}$. If event $e$ induces $\omega(e)\in C^1$ and evidence yields $\alpha$ with $\omega(e)=d_0\alpha$, then applying repair $\alpha$ to the certified state of $Q$ yields the same result as recomputing $Q$ on $S+\Delta_e$ for all operations in $\mathcal{F}$.

**Proof obligation:** For $\mathcal{F}$ = `{SUM, COUNT, AVG}` with sufficient statistics, show $d_0$ is a homomorphism from the CDC-evidence monoid to defect classes and that $\alpha$ updates statistics iff recomputation agrees. SmplCache is the constructive proof for the supported fragment.

### 6.2 Boundary repair soundness (necessary condition)

> **Theorem (Boundary repair soundness).**  
> Given declared $(\mathsf{schema},\mathsf{workload},\mathsf{CDC})$, a local repair patch is sound only if $[\omega(e)]=0$. If $[\omega(e)]\neq 0$ or evidence is incomplete, any silent local patch is unsound; the implementation must execute a declared terminal from §4.

This is the **no silent success** theorem: the operational dual of classical anomaly avoidance.

### 6.3 Classical NF bridge (conservative, optional)

\[
\text{declared dependency violation}
\Rightarrow
\text{nonzero labeled obstruction slice}.
\]

Converse **not** claimed until dependency matrices and $\sim$ are fixed. Omitted here; see atlas §2.1.

---

## 7. Implementation mapping (SmplCache)

SmplCache is the reference BQNF engine for in-memory cache layers.

| BQNF subclause | SmplCache stage |
|---|---|
| 1. Boundary | `QueryShape` fingerprint; disjoint → `PRESERVE` |
| 2. Delta | Theorem 7 evidence check (old/new row, columns) |
| 3–4. Quotient / repair | Obstruction evaluation; SUM/COUNT/AVG lanes |
| 5. Terminal | Typed `Decision` + JSON `Certificate` |

**Pipeline:**

1. Boundary intersection  
2. Evidence certification  
3. Obstruction evaluation  
4. Terminalization  

See `000_SmplCache Simplex In-Memory Database and CDC.md` for certificate examples (`revenue_by_customer_paid`, missing-evidence invalidation).

---

## 8. Related systems contexts

BQNF is intended to apply wherever **incremental maintenance** meets **finite evidence**:

| Context | Layer $L$ | Typical terminal |
|---|---|---|
| Materialized view maintenance | view tuple / delta table | `Repair` / `Recompute` |
| CQRS read model | projection partition | `Repair` / `Invalidate` |
| Stream processing pane | keyed aggregate state | `Repair` / `Serialize` |
| Application cache (SmplCache) | cached query shape | `Repair` / `Invalidate` / `Unsupported` |
| Approximate / sketch view | sketch state | `Lift` or `ConservativeInvalidate` |

The same five-clause checklist applies; only $C^0,C^1,d_0$ change with the aggregate algebra.

---

## 9. Failure pathology (what BQNF prevents)

Machinery is credible only when it names **production failures** readers already suffer. BQNF diagnoses:

| Production failure | Symptom | BQNF diagnosis | Required terminal |
|---|---|---|---|
| Partial CDC | cache “repaired” after update missing `status` before/after | delta not computable (clause 2) | `Invalidate` / `ConservativeInvalidate` |
| Stale aggregate after boundary hit | dashboard revenue wrong post-order update | repair claimed without $\omega = d_0\alpha$ | `Invalidate` (not silent patch) |
| MIN/MAX cache without witness | wrong max after row delete | no admissible $\alpha$ in $C^0$ | `Unsupported` or `Lift` |
| Concurrent group moves | lost updates under parallel CDC | defects do not commute | `Serialize` |
| Over-broad materialized view | any column change invalidates everything | boundary not declared | fix $\partial Q$ (design), then classify |
| “Eventually consistent” read | user billed on lagging replica | timeless truth (no freshness packet) | pair with Freshness NF (atlas §7.7); BQNF on cache layer |

**Prevented failure pattern:** heuristic cache that **always** patches on intersection instead of certifying evidence — the dominant cause of silent under-invalidation. SmplCache’s three rules (§1.4) exist to make that pattern unrepresentable.

**Evaluation target (implementation):** minimal verifier + generated repair certificates; benchmark **repair vs full recompute** on SPJA workloads; publish negative tests where missing evidence forces invalidation.

---

## 10. Conclusion

**Boundary-Quotient Normal Form** turns incremental repair from a heuristic into a five-point audit:

1. Declare what the view depends on ($\partial Q$).  
2. Require evidence for the delta.  
3. Classify the defect modulo admissible repairs ($Q^1$).  
4. Repair only on the image of $d_0$.  
5. Otherwise, terminalize loudly.

Paper B (`1b_gtmur_representation_transport.md`) treats **certified representation transport** (certificates, loss ledgers, GTMUR, Compilation NF). Paper C will treat **finite-shadow authority** (GTTC).

**Completion criteria:** explicit $C^0,C^1,d_0$ for the supported SPJA fragment; discharged boundary-exactness proof; **minimal verifier** emitting repair certificates; negative tests for missing evidence; benchmark repair vs recompute (§9).

---

## 11. References (in-repo)

* `1_normal_forms.md` — full atlas  
* `000_Quotient Normal Form and Boundary-Certified Databases.md` — product wedge  
* `000_SmplCache Simplex In-Memory Database and CDC.md` — implementation  
* `0_relvar_relation_table_and_boundary_relvar.md` — base ontology (read first)  
