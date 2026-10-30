# Observer-Relative Ontology: Relvars, Freshness Posets & Epistemic Normal Forms

**AuthorityEffect:** `None` (`certified_implies_authorized: false`)  
**[⬅ Back to Wiki Home](Home)**

![Observer-Relative Ontology](images/observer.svg)

---

## 1. The Four-Fold Ontological Distinction

A recurring failure mode in data engineering is conflating a physical storage table with a mathematical relation or an observer-facing contract. **Simplex Normal Forms** enforces a strict four-part distinction:

| Concept | Mathematical / Operational Nature | Mutability | Governing Contracts |
| :--- | :--- | :--- | :--- |
| **1. Table** | Physical bag/sequence of byte rows on disk or wire; may contain duplicate rows, NULL markers, or ordering artifacts. | Mutable physical storage | [`nf.classical.0nf`](nf.classical.0nf), [`nf.operational.schema-totality`](nf.operational.schema-totality) |
| **2. Relation** | Immutable mathematical set of tuples $r \subseteq \prod_{A \in H} \operatorname{dom}(A)$ over a typed heading $H$. | Immutable value | [`nf.classical.1nf`](nf.classical.1nf) – [`nf.classical.6nf`](nf.classical.6nf) |
| **3. Relvar** | Named relation variable $R$ whose legal states over time are relations obeying declared schema constraints $\Sigma$. | Mutable variable holding relation values | [`nf.bridge.wir_relvar`](nf.bridge.wir_relvar), [`nf.epistemic.state`](nf.epistemic.state) |
| **4. Boundary-Relvar** | Observer-scoped projection $(\partial Q, O_i, \text{SLA}, \text{Scope})$ equipped with a delta repair law and explicit refusal routes. | Stateful boundary contract | [`nf.change.bqnf`](nf.change.bqnf), [`nf.epistemic.observer`](nf.epistemic.observer), [`nf.epistemic.freshness`](nf.epistemic.freshness) |

---

## 2. Observer-Relative Freshness & Poset Monotonicity ([`nf.epistemic.freshness`](nf.epistemic.freshness))

A read timestamp on a packet is metadata, not authority. Under [`nf.epistemic.freshness`](nf.epistemic.freshness) and [`nf.epistemic.observer`](nf.epistemic.observer) (implemented in `normal_forms/observer_freshness_example.py`), the **same data packet** can be simultaneously valid for one observer and inadmissible for another:

- Each observer $O_i = (\text{id}, \tau_{\max}, S_{\text{auth}})$ declares a maximum tolerable replica lag $\tau_{\max}$ and an explicit set of authorized scopes $S_{\text{auth}}$.
- **Poset Ordering ($O_1 \le O_2$):** Observer $O_1$ is more stringent than $O_2$ iff $\tau_{\max}(O_1) \le \tau_{\max}(O_2)$ and $S_{\text{auth}}(O_1) \subseteq S_{\text{auth}}(O_2)$.
- **Monotonicity Functor Law:** If a stringent observer $O_1$ admits a packet as `AuthorizedFresh` (`Preserve`), then every less stringent observer $O_2 \ge O_1$ on the same poset chain also admits the packet.
- **Fail-Closed Defaults:** Missing `packet_scope` routes to `Refuse`; missing or negative `replica_lag_seconds` routes to `ConservativeInvalidate`.

---

## 3. Epistemic Quotient (`EQNF`) & Observer Distinguishability (`ODNF`)

- **Epistemic Quotient Normal Form ([`nf.coda.eqnf`](nf.coda.eqnf)):** Requires every observation map $f: X \to Y$ to respect the declared epistemic equivalence kernel $\sim_E$ ($x \sim_E x' \implies f(x) = f(x')$), factoring uniquely through $X / {\sim_E}$. Any leak of sub-quotient gauge coordinates routes to `KernelViolationRefusal`.
- **Observer Distinguishability Normal Form ([`nf.epistemic.odnf`](nf.epistemic.odnf)):** Separates zero pseudometric distance $d_O(x, y) = 0$ (indistinguishable to observer $O$) from ontological identity $x = y$, preventing premature quotient collapse when downstream observers carry finer resolution.
- **Authority Normal Form ([`nf.epistemic.authority`](nf.epistemic.authority)) & Terminal Partition ([`nf.ddc.terminal_partition`](nf.ddc.terminal_partition)):** Enforces that every contract evaluation has `AuthorityEffect: None` and `certified_implies_authorized: false`.

---

## 4. Epistemic Claim Hygiene Quadrant

1. **What it supports:**
   - Supports observer-scoped freshness evaluation, poset monotonicity checks, and kernel invariance checks (`EQNF`/`ODNF`) in this model.
2. **What it does not support:**
   - Does not grant execution or access-control privileges in production identity systems (`AuthorityEffect: None`).
3. **The narrowest defensible claim:**
   - Declaring explicit observer SLA budgets and scopes prevents a single global "fresh/stale" bit from misrepresenting multi-observer read requirements.
4. **The next test needed:**
   - Multi-region clock-skew composition tests combining [`nf.relativistic.time_sync`](nf.relativistic.time_sync) with [`nf.epistemic.freshness`](nf.epistemic.freshness).
