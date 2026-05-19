# Certified Representation Transport for Database Systems

> Absorbed canonical paper copy from
> `omega_engine/research/in_work/simplex_cosmos_papers/SMPLX_009_Simplex Databases/crap/1b_gtmur_representation_transport.md`.
> The source folder was integrated into the root scaffold and removed.

**Author:** Jeremy H. Carroll  
**Date:** May 2026  
**Series:** SMPLX-009 Paper B (certificates, loss ledgers, GTMUR)  
**Status:** draft — standalone extract from the Simplex Databases atlas

**Companion documents:**

| Document | Role |
|---|---|
| `1a_bqnf_incremental_repair.md` | Paper A — runtime repair (BQNF), CDC terminals |
| `1_normal_forms.md` | Full taxonomy atlas |
| `0_relvar_relation_table_and_boundary_relvar.md` | **base ontology** — relvar regimes, observer boundaries; `RepairCertificate` DDL |
| `normal_form_contracts/contracts/contract.transport.gtmur.yaml` | **Contract** — GTMUR / transport obligations |
| `normal_form_contracts/contracts/contract.compilation.cpnf.yaml` | **Contract** — compilation chain obligations |
| `2_sql_server_certified_normal_forms_attempts.md`, `3_postgresql_certified_normal_forms_attempts.md` | Engine-level certificate tables |
| `1c_*` (planned) | Finite-shadow authority (GTTC), cofinal towers |

---

## Abstract

Paper A (BQNF) certifies whether a **write event** can repair an observer layer. Paper B certifies whether a **representation change** — query rewrite, schema normalization, cache shape compilation, federated view mapping, or approximate rollup — may claim the same authority as its source.

The mechanism is **certified representation transport (GTMUR)**: every admissible map $F : A \to A_{\mathrm{nf}}$ must ship (1) a **certificate** naming preserved and erased structure, (2) a **loss ledger** when distinctions are destroyed, and (3) a **descent witness** $\chi_F$ checked by a verifier.

The publishable systems abstraction is not the category notation but its operational meaning:

\[
\boxed{
\text{Updates commute with representation change, up to declared loss.}
}
\]

Equivalently: $D_{A_{\mathrm{nf}}} F$ matches $\bar{F} D_A$ on the certified fragment (§3.3). **Certified** means the packet is well-formed and the witness checks; **authorized** means a policy engine accepts trust lineage. Confusing the two is `AuthorityLaundering`.

> *A certificate table without a verifier is just another table.*

This paper defines packet schemas, verifier duties, ledger obligations, and morphism kinds; walks SQL → SPJA → boundary shape; and records failure pathologies modern lineage tooling does not prevent.

---

## 1. Introduction

> **Ontology:** GTMUR transports between **relvar regimes** (source $A$, target $A_{\mathrm{nf}}$); unifying invariant: *no silent authority degradation* — `0_relvar_relation_table_and_boundary_relvar.md` Part VI.

### 1.1 Two motion problems

| Problem | Question | Paper |
|---|---|---|
| **Incremental repair** | Given state $S$ and write $e$, can layer $Q$ update locally? | A (BQNF) |
| **Representation transport** | Given regimes $A$ and $A_{\mathrm{nf}}$, does rewrite $F$ preserve declared authority? | B (GTMUR) |

BQNF produces **repair certificates** (one morphism kind). GTMUR governs the wider class: projections, refinements, rewrites, approximations, and migrations.

### 1.2 Three-layer architecture

| Layer | Question | Mechanism |
|---|---|---|
| **BQNF** (Paper A) | Can a **runtime change** be repaired? | boundary, delta, quotient, repair image, terminal |
| **GTMUR** (Paper B) | Can a **representation** still claim authority after transformation? | certificate, loss ledger, $\chi_F$, verifier |
| **GTTC** (Paper C) | Can an **approximation / infinite-resolution** object be authorized? | cofinal finite shadows |

### 1.3 Hierarchy (validity vs permission)

\[
\boxed{
\text{Form} \subset \text{Normal Form} \subset \text{Certified Normal Form} \subset \text{Authorized Normal Form}
}
\]

| Stage | Meaning |
|---|---|
| **Form** | Recognizable syntax (SQL text, JSON packet, view definition) |
| **Normal form** | Decidable shape excluding a declared anomaly class |
| **Certified normal form** | Normal form + obstruction class + **certificate** + terminal route |
| **Authorized normal form** | Certified form accepted by an **authority verifier** (policy, federation, lineage) |

> **Invariant:** A row in a certificate table does not imply authorization.  
> *A certificate table without a verifier is just another table.*

### 1.4 Reader contract

| Construct | Status in this paper |
|---|---|
| Certificate JSON schema, loss ledger rows, CDC evidence shape | **Operational** — implementable in SQL + application verifiers |
| GTMUR transport contract, failure terminals | **Operational semantics** — required fields and verifier checks |
| Comparison envelope (pullback / pushout policies) | **Design patterns** — names composition rules; full limits deferred |
| GTTC cofinal towers, GTLA pipeline | **Deferred to Paper C** — pointer only |

---

## 2. Canonical evidence and certificate forms

These are **not** normal forms. They normalize **audit artifacts** so verifiers can parse proofs uniformly.

### 2.1 CDC evidence form (input to Paper A)

Shared with BQNF; listed here because transport often **compiles** CDC handlers when a shape is promoted to certified form.

```text
write event
  -> old row
  -> new row
  -> changed attributes
  -> predicate membership before/after
  -> group key before/after
  -> policy context
```

See Paper A §5.2 for aggregate-lane requirements.

### 2.2 Certificate form (canonical packet)

Every representation change or certified repair step should emit:

```json
{
  "certificate_id": "cert_xyz123",
  "source_regime": "sql_query_or_schema",
  "target_regime": "spja_canonical | boundary_shape | policy_envelope",
  "morphism_kind": "project | refine | rewrite | approx | repair",
  "preserved_skeleton": ["relations", "keys", "attributes", "predicates", "groups"],
  "erased_distinctions": ["phases", "unused_join_columns", "precision"],
  "loss_ledger_ref": "ledger_abc789 | null",
  "obstruction_class": "[omega] | [0]",
  "terminal_route": "TransportOk | Repair | Invalidate | Lift | Escalate | Refuse",
  "descent_witness_ref": "chi_cert_xyz123 | null",
  "verifier_id": "gtmur_v1",
  "verifier_outcome": "pending | accepted | rejected"
}
```

**Required fields for GTMUR transport** (morphism_kind ≠ `repair`):

* `preserved_skeleton` — what downstream verifiers may treat as authoritative
* `erased_distinctions` — what was removed (may be empty only for lossless $F$)
* `loss_ledger_ref` — mandatory if `erased_distinctions` is non-empty
* `descent_witness_ref` — mandatory unless verifier embeds witness inline

**Repair certificates** (Paper A) are the special case `morphism_kind = repair` with `target_regime = boundary_shape` and BQNF terminal routes.

### 2.3 Loss ledger form

A loss ledger is an append-only accounting of **destroyed distinctions**:

```json
{
  "ledger_id": "ledger_abc789",
  "entries": [
    {
      "kind": "attribute_drop",
      "source": "Orders.ship_date",
      "reason": "not in boundary_shape",
      "authority_effect": "non_authoritative_for_repair"
    },
    {
      "kind": "precision_loss",
      "source": "numeric(18,4) -> numeric(18,2)",
      "reason": "cache_storage_policy",
      "authority_effect": "rounded_display_only"
    },
    {
      "kind": "approximation",
      "source": "exact_percentile -> t_digest_sketch",
      "reason": "sketch_rollout",
      "authority_effect": "epsilon_bound_declared",
      "bound": "0.01"
    }
  ],
  "composed_at": "2026-05-19T12:00:00Z",
  "parent_ledger_ref": null
}
```

**Rule:** If $F$ is not injective on the declared authority skeleton, the ledger must say what was lost and how downstream layers must behave (e.g., display-only, recompute-only, invalidate-on-use).

### 2.4 Provenance form (lineage)

For policies that require tuple lineage, provenance maps each output tuple to a semiring element $p_t \in K$ (counts, trust weights, probabilities):

\[
t \mapsto p_t \in K
\]

The database stores packets; the verifier interprets them. Provenance is orthogonal to GTMUR but often **composed** with transport: a rewrite certificate should reference whether provenance weights are preserved, rescaled, or dropped (ledger entry `kind: provenance_rescale`).

---

## 3. GTMUR representation transport contract

**GTMUR** (Graph of Transport for Module Updates and Representations) names the contract; implementations may use any verifier name.

### 3.1 Objects and morphisms (operational)

* **Object $A$:** a source regime — e.g. ad-hoc SQL text, legacy wide table, federated foreign table, analyst notebook query.
* **Object $A_{\mathrm{nf}}$:** a target regime in a declared normal form — SPJA canonical, BQNF boundary shape, 3NF decomposition, policy-masked view.
* **Morphism $F : A \to A_{\mathrm{nf}}$:** a documented transformation (compiler pass, migration script, cache warmer).

### 3.2 Transport succeeds iff

1. **Certificate emitted** matching §2.2.
2. **Loss ledger present** iff structure is erased (§2.3).
3. **Descent witness $\chi_F$** available to the verifier — operationally: a machine-checkable justification that **updates on $A_{\mathrm{nf}}$** correspond to admissible updates on $A$ modulo the ledger.

Design equation (vocabulary, not a proved natural isomorphism in this draft):

\[
\boxed{
\chi_F:\ D_{A_{\mathrm{nf}}}\,F \Rightarrow \bar{F}\,D_A
}
\]

**Operational reading:** Let $D_A$ be the **declared update action** on the source (CDC rules, triggers, application writes). Let $D_{A_{\mathrm{nf}}}$ be the update action on the target. Transport is valid when pushing an update through $F$ after applying $D_{A_{\mathrm{nf}}}$ matches applying $D_A$ first then transporting, **up to ledger-identified identifications**.

When no $\chi_F$ exists → terminal `TransportViolation`.

### 3.3 The commuting-updates principle (publishable core)

Modern pipelines constantly perform **compilation-like** moves:

* schema rewrite and denormalization,
* cache and materialized-view projection,
* vector embedding and summarization,
* stream-to-table materialization,
* agent context compilation.

Almost none formally track: what was preserved, what was erased, which updates remain valid, and what authority survived. The modern anomaly class is **semantic drift through compilation layers**.

GTMUR’s contract compresses that into one question:

> After map $F : A \to A_{\mathrm{nf}}$, do declared updates on the target correspond to admissible updates on the source, modulo ledgered loss?

If yes, $\chi_F$ is accepted. If no → `TransportViolation`, `SilentMutation`, or `LossLedgerMissing`. Authority requires **executable descent checks**, not metadata annotations alone.

### 3.4 Compilation Normal Form (CpNF)

Paper B implicitly defines **Compilation Normal Form**: a representation is in CpNF iff:

1. every transformation $F$ is declared (`morphism_kind`, certificate),
2. every erased distinction has a **loss ledger** entry,
3. every update path has a **transport witness** $\chi_F$ (or explicit refusal),
4. every authority claim passes a **verifier** (not merely a catalog row).

**Anomaly excluded:** *semantic drift through compilation layers* — SQL becomes cache, cache becomes embeddings, embeddings become agent context, context drives writes, and nobody knows where authority degraded.

CpNF is the compile-time sibling of BQNF: BQNF governs **events on a fixed shape**; CpNF governs **how the shape was obtained**. A system can satisfy BQNF per write while violating CpNF if the shape was produced by unledgered approximation.

### 3.5 GTMUR failure terminals

| Terminal | Meaning |
|---|---|
| `TransportViolation` | No descent witness; $F$ must not be used for authoritative sync |
| `SilentMutation` | Protected skeleton changed without certificate/ledger |
| `LossLedgerMissing` | Erasure without ledger |
| `TargetTerminalBypass` | Target layer skipped BQNF or local verifier |
| `AuthorityLaundering` | Certified or normal form mistaken for authorized form |
| `NonComposableCertificate` | Chain $F \circ G$ lacks composed ledger/witness |
| `Refuse` | Policy engine rejects lineage |

### 3.6 Certified vs authorized (again)

| Check | Who |
|---|---|
| Schema of certificate, obstruction class, terminal enum | GTMUR / BQNF verifier |
| Role may read column `salary` | Policy / RBAC |
| Federated source trusted | Lineage / governance |
| Sketch within ε for SLA | SLO / GTTC shadows (Paper C) |

---

## 4. Running example: SQL → SPJA → boundary shape

Continue the Paper A schema; add a **compilation chain** common in production.

### 4.1 Source regime $A$ (analyst SQL)

```sql
-- Regime A: ad-hoc SQL (not yet certified)
SELECT c.customer_id,
       c.display_name,
       SUM(o.amount) AS revenue,
       AVG(o.amount) AS avg_ticket
FROM Orders o
JOIN Customers c ON c.customer_id = o.customer_id
WHERE o.status = 'paid'
GROUP BY c.customer_id, c.display_name;
```

### 4.2 Target regime $A_{\mathrm{nf}}$ (boundary shape for SmplCache)

Paper A shape (SPJA + boundary fingerprint):

```text
paid_revenue_by_customer(customer_id) :=
  SELECT customer_id, SUM(amount) AS revenue
  FROM Orders
  WHERE status = 'paid'
  GROUP BY customer_id
```

**Morphism $F_1$:** `rewrite` — fold join away using FD `customer_id → display_name` stored only in `Customers`.

| Field | Value |
|---|---|
| `preserved_skeleton` | `[Orders.customer_id, Orders.amount, Orders.status, SUM(amount)]` |
| `erased_distinctions` | `[display_name, AVG(amount), Customers relation from active boundary]` |
| `loss_ledger_ref` | `ledger_join_fold_001` |

**Ledger excerpt:**

```json
{
  "ledger_id": "ledger_join_fold_001",
  "entries": [
    {
      "kind": "attribute_drop",
      "source": "display_name",
      "reason": "not in boundary_shape; lookup via Customers for display",
      "authority_effect": "non_authoritative_in_cache"
    },
    {
      "kind": "aggregate_drop",
      "source": "AVG(amount)",
      "reason": "target shape exposes SUM only",
      "authority_effect": "must_not_answer_avg_from_cache"
    }
  ]
}
```

**Descent witness $\chi_{F_1}$ (operational):**  
CDC updates to `Orders.amount`, `Orders.status`, `Orders.customer_id` drive BQNF repair on `paid_revenue_by_customer`. Updates to `Customers.display_name` **do not** intersect $\partial Q$ → `Preserve` on the cache (display must be refreshed from `Customers` or a separate layer).

Without the ledger, a user could treat cache rows as authoritative for `display_name` — **silent authority degradation**.

### 4.3 Approximation transport $F_2$ (optional)

Replace exact revenue with a rolled-up sketch for a dashboard:

| Field | Value |
|---|---|
| `morphism_kind` | `approx` |
| `erased_distinctions` | `[exact SUM]` |
| `loss_ledger_ref` | `ledger_sketch_002` |
| `terminal_route` | `TransportOk` with `authority_effect: epsilon_bound_declared` |

Paper C (GTTC) addresses when such approximations may be **authorized** via cofinal finite shadows; Paper B only requires the ledger to exist.

### 4.4 Composed certificate chain

```text
A  --F1-->  SPJA_canonical  --F2-->  boundary_shape  --BQNF-->  repair_packets
```

**Composition rule:** `loss_ledger_ref` of the composition must list all entries from child ledgers (or point to `parent_ledger_ref`). Verifier checks **non-composability** → `NonComposableCertificate`.

---

## 5. Comparison envelope $\Omega_{\mathfrak O}$ (merging candidate representations)

When two normalizations or repair plans exist — e.g. two materialized view definitions for the same workload — systems need a **comparison envelope** rather than silent winner-takes-all.

**Naming.** In the SMPLX-009 database papers, this layer is called the **comparison envelope** with symbol $\Omega_{\mathfrak O}$. The older research acronym **GTOR** (*General Theory of Omniversal Representation*) is retired here to reduce acronym load; the underlying theory corpus remains in `omega_engine/research/in_work/general_theory_of_finite_obstruction/.3_gtor/`.

### 5.1 Span pattern

\[
N_1(A) \xleftarrow{p_1} C(A) \xrightarrow{p_2} N_2(A)
\]

* $N_1, N_2$ — candidate normal forms (two views, two cache shapes, two federated wrappers).
* $C(A)$ — **comparison cone**: pairs of states that map consistently to both sides (policy-aligned pullback, migration identification, or shared key space).

### 5.2 Envelope kinds (operational)

| Envelope | Use |
|---|---|
| **Pullback (policy–data)** | Align a data representation with a policy domain before comparing permissions |
| **Pushout (migration)** | Merge schemas under declared identifications; dual certificates from each leg |
| **Weak terminal comparison** | Score candidate repairs against one obstruction criterion; pick `Repair` only if both agree on $[\omega]$ |

### 5.3 Failure terminals

| Terminal | Meaning |
|---|---|
| `NoComparisonEnvelope` | No shared $C(A)$ declared |
| `NonComposableCertificate` | Certificates on legs do not glue to a composite |
| `CompletionWithoutDescent` | Limit object built without $\chi$ for transport |

Full categorical limits are **not** assumed in this draft; envelopes are **policies** with checklists, analogous to BQNF’s five clauses.

---

## 6. Theorems and proof obligations

### 6.1 Lossless transport

> **Theorem (Lossless transport).**  
> If `erased_distinctions` is empty and $\chi_F$ is accepted by the verifier, then for all admissible updates $u$ on $A_{\mathrm{nf}}$, the induced update on $A$ is unique up to isomorphism and preserves all declared query answers on the shared SPJA fragment.

**Proof obligation:** Exhibit $F$ as a bijection on carriers for the fragment; show $D_{A_{\mathrm{nf}}} F = F D_A$ on generators.

### 6.2 Lossy transport

> **Theorem (Lossy transport accounting).**  
> If `erased_distinctions` is non-empty and `loss_ledger_ref` is present, then any consumer of $A_{\mathrm{nf}}$ must not answer queries that depend on erased fields unless it escalates to a regime listed in the ledger’s `authority_effect` or recomputes from source.

**Proof obligation:** Map each ledger `kind` to a static analysis rule on query shapes (column reference, aggregate type).

### 6.3 Certificate composition

> **Theorem (Composed descent).**  
> For $F: A \to B$ and $G: B \to C$ with accepted $\chi_F$, $\chi_G$, the composite $G \circ F$ is accepted iff the composed loss ledger is well-formed and obstruction classes multiply as declared.

**Proof obligation:** Define composition on certificates and verify associativity on a finite test suite.

### 6.4 Bridge to BQNF

> **Lemma (Repair as transport).**  
> A BQNF `Repair(α)` decision is a morphism `repair : boundary_shape → boundary_shape` with `morphism_kind = repair`, `obstruction_class = [0]`, and CDC evidence embedded in the certificate.

Paper A proves **when** repair is sound; Paper B proves **how** repair certificates compose with compile-time transports.

---

## 7. Verifier architecture

### 7.1 Pipeline

```text
Source regime A
  -> normalize (optional NF pass)
  -> emit certificate + ledger
  -> verify chi_F (static + spot checks)
  -> if repair path: delegate to BQNF verifier
  -> policy engine (authorization)
  -> Authorized | Refuse
```

### 7.2 SQL persistence (pattern)

Engines do not natively store GTMUR objects; use certificate tables + application verifiers (see `3_postgresql_certified_normal_forms_attempts.md` §11):

```sql
CREATE TABLE transport_certificate (
    certificate_id       bigserial PRIMARY KEY,
    source_regime        text NOT NULL,
    target_regime        text NOT NULL,
    morphism_kind        text NOT NULL,
    preserved_skeleton   jsonb NOT NULL,
    erased_distinctions  jsonb NOT NULL DEFAULT '[]',
    loss_ledger_ref      text,
    obstruction_class    text NOT NULL,
    terminal_route       text NOT NULL,
    descent_witness      jsonb,
    verifier_outcome     text NOT NULL DEFAULT 'pending',
    created_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE loss_ledger (
    ledger_id    text PRIMARY KEY,
    entries      jsonb NOT NULL,
    composed_at  timestamptz NOT NULL DEFAULT now(),
    parent_ledger_ref text
);
```

**Repair certificates** (Paper A) may live in the same table with `morphism_kind = 'repair'` or a dedicated `repair_certificate` table — one verifier family, two morphisms.

### 7.3 SmplCache mapping

| GTMUR artifact | SmplCache / SimplexStor |
|---|---|
| `target_regime = boundary_shape` | `QueryShape` fingerprint |
| `morphism_kind = repair` | CDC `Decision` + JSON certificate |
| `descent_witness` | Evidence + obstruction evaluation (Paper A §7) |
| `AuthorityLaundering` guard | Do not treat `PRESERVE`/`REPAIR` as policy approval |

---

## 8. Related contexts

| Context | Transport example |
|---|---|
| **View migration** | $F$ rewrites view SQL; ledger records dropped columns |
| **CQRS projection** | Event schema → read model; ledger for denormalized fields |
| **Federation** | Foreign table → local cache shape; lineage in provenance |
| **Column masking** | `refine` morphism; ledger records masked attributes |
| **Approximate MV** | `approx` + GTTC shadows (Paper C) |
| **Zero-trust pipeline** | Certificate without authorization until policy sign-off |

### 8.1 Certificate schema as epistemic transport (AI bridge)

The same packet shape governs database compilation and **epistemic transport** in agent systems. Mapping is illustrative — not a claim that SQL equals LLM cognition:

| DB / systems meaning | AI-era reading |
|---|---|
| `erased_distinctions` (dropped column) | forgotten or summarized context |
| `morphism_kind: approx` | summarization / sketch / embedding |
| `morphism_kind: rewrite` | prompt or context compilation |
| `refine` + policy mask | safety filter / redaction |
| provenance rescale (ledger) | retrieval reweighting |
| `AuthorityLaundering` | hallucinated confidence — output sounds valid without recoverable basis |
| `TransportViolation` | agent acts on stale or non-composable retrieval |
| BQNF `Invalidate` | tool memory must refresh |

Orchestration and Context normal forms (atlas §7.4–7.5) extend this bridge; Paper B supplies the **certificate apparatus** they share with GTMUR.

---

## 9. Failure pathology (what GTMUR prevents)

| Production failure | Symptom | GTMUR / CpNF diagnosis | Terminal |
|---|---|---|---|
| Stale cache after partial CDC | wrong aggregate, “worked” in logs | Paper A: missing evidence → invalidate; Paper B: shape compiled without $\chi_F$ | `Invalidate` + audit compile chain |
| Approximate dashboard used for billing | sketch displayed as invoice truth | approximation without ledger + policy | `AuthorityLaundering` |
| Denormalized projection drops constraints | silent semantic narrowing | skeleton changed, no ledger | `SilentMutation` |
| Vector embedding treated as source of truth | RAG answer overrides SQL | `approx` without `loss_ledger_ref`; embedding not in `preserved_skeleton` | `LossLedgerMissing` / `TransportViolation` |
| AI agent on stale retrieval | action on outdated tool output | non-composable context compile | `TransportViolation` / `NonComposableCertificate` |
| Schema migration loses semantics | prod ≠ staging behavior | migration without composed certificates | `NonComposableCertificate` |
| Lineage catalog with no enforcement | metadata exists, bugs persist | certificate table without verifier | *not a GTMUR object* — fix verifier |

**Prevented pattern:** “we have lineage” without **executable** descent — the dominant failure mode of governance and metadata products.

**Implementation priority:** minimal verifier accepting/rejecting composed chains (SQL → SPJA → boundary shape); generate real `transport_certificate` and `loss_ledger` rows; negative tests for `SilentMutation` and `LossLedgerMissing`; then benchmark authority-preserving compile vs ad-hoc ETL.

---

## 10. What Paper C adds (pointer only)

**GTTC (finite-shadow authority)** governs when infinite-resolution or continuous objects (streams, exact percentiles, real-time limits) may be treated as authoritative only through **cofinal towers** of finite approximations, each with its own certificate chain.

Paper B supplies the **ledger and certificate apparatus** those shadows consume. Paper C supplies the **limit and authorization** story.

---

## 11. Conclusion

Representation transport is the second half of “data in motion”:

* **BQNF** — certify local repair of a fixed shape.  
* **GTMUR / CpNF** — certify that the shape was obtained without smuggling authority; updates commute with $F$ up to ledgered loss.

**Do not expand the ontology faster than the executable substrate.** The operational kernel is: SPJA shapes, CDC evidence, repair and transport certificates, loss ledgers, verifier terminals. Publish that first.

Paper B is complete when a reference verifier:

1. accepts a composed chain SQL → SPJA → boundary shape with valid $\chi_F$;
2. rejects `SilentMutation`, `LossLedgerMissing`, and `NonComposableCertificate` on negative tests;
3. emits certificates consumers can audit without trusting cache heuristics.

---

## 12. References (in-repo)

* `1a_bqnf_incremental_repair.md` — Paper A  
* `1_normal_forms.md` — atlas §4–5  
* `0_relvar_relation_table_and_boundary_relvar.md` — `RepairCertificate` DDL  
* `000_SmplCache Simplex In-Memory Database and CDC.md` — repair certificates  
