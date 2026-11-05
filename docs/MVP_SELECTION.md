# Simplex Normal Forms: Minimum Viable Product (MVP) Selection & Architectural Specification

**Document Version:** 1.0.0  
**Target Domain:** `smplxnf.anomalon.com` via Render (`onrender.com`)  
**Repository:** `simplex-normal-forms`  
**Classification:** Systems Architecture & Technical Product Specification  
**Epistemic Standard:** Landau Rigor / Claim Discipline Compliant (No Hype Terminology)  

**Status reconciliation, 2026-11-02:** This specification includes original design
targets, not measured guarantees. The separate `smplxnf-live` service now serves
the canonical domain on Free compute; HTTPS/API smoke checks passed. Full live
browser acceptance remains incomplete. Availability, latency and broad compiler
claims below remain design targets where they exceed the
[current evidence and executable scope](PROJECT_STATUS.md).

---

## 1. Executive Summary: The smplxnf.anomalon.com Vision

### 1.1 Context and Objective
The `simplex-normal-forms` repository implements a rigorous, mathematically grounded suite of 112 normal-form contracts, relational algebra synthesis algorithms, streaming Change Data Capture (CDC) boundary quotient repair engines, an intermediate representation compiler stack (NF-IR), and cryptographic Model Context Protocol (MCP) context projection decorators. 

The objective of this specification is to define, evaluate, and architect the single most valuable Minimum Viable Product (MVP) derived from this codebase. The selected MVP must be deployed as a high-availability, responsive web application at `smplxnf.anomalon.com` hosted on Render (`onrender.com`). It must serve two interrelated goals:
1. Provide an immediate, zero-friction interactive workbench where visitors (engineers, technical leaders, and hiring managers) can observe, test, and manipulate formal normal-form execution within thirty seconds.
2. Enable an external developer to clone the repository, install the package via standard tooling, and import the core normal-form logic into their own database, compiler, or AI workflows in under fifteen minutes to support the author's technical resume.

### 1.2 The Production Vision on Render
The application is deployed as a lightweight Web Service on Render bound to the custom hostname `smplxnf.anomalon.com`. Public provisioning and HTTPS/API verification passed on 2026-11-02; see [current status](PROJECT_STATUS.md) for the remaining browser checks. The original production design below targets a stateless ASGI process model powered by FastAPI and Uvicorn:
- A responsive, high-contrast single-page application (SPA) dashboard styled with modern systems-grade typography and Tailwind CSS.
- Strongly typed REST endpoints exposing relational synthesis, Tableau Chase verification, streaming CDC delta repair, 4-layer NF-IR compilation to SQLite triggers and Python guards, and AI context compression with Merkle LossLedger generation.
- Sub-50 millisecond algorithmic execution latencies for typical schemas and streams, executing purely in-process with zero external database dependencies.

### 1.3 The 30-Second Evaluator Experience
Technical evaluators and engineering managers spend less than one minute assessing candidate portfolio demonstrations. A blank form or an abstract command-line log leads to immediate evaluator bounce. 

To achieve maximum impact, `smplxnf.anomalon.com` adopts a **Pre-Configured Instant Execution** paradigm:
- **0–5 Seconds (Instant Impression):** The visitor arrives at `smplxnf.anomalon.com`. The layout displays a clean, dark-mode terminal-inspired interface with pre-loaded presets ("E-Commerce Order & Fulfillment", "Hospital Patient & Physician Ward", "Zipfian Skewed Stream", "Multi-Pass Compiler Lowering", "RAG Prompt Token Truncation").
- **5–15 Seconds (One-Click Verification):** The visitor clicks **"Execute Synthesis & Verification"**. The engine immediately computes candidate keys, prime attribute partitions, minimal functional dependency covers, Bernstein 3NF subschemas, Tsou-Fischer BCNF decomposition trees, and an interactive step-by-step Tableau Chase matrix displaying symbol substitutions ($a_i$ vs. $b_{i,j}$) and spurious tuple counterexamples.
- **15–30 Seconds (Artifact Inspection & Code Generation):** The visitor switches tabs to inspect the generated PostgreSQL/SQLite DDL triggers, copies the runnable Python decorator code, or navigates to the streaming BQNF and NF-IR Compiler tabs.
- **30+ Seconds (Developer Adoption):** The visitor clicks the **"Clone & Import"** tab, revealing three-line copy-paste code snippets that execute cleanly in any Python environment following `pip install -e .`.

### 1.4 Architectural Selection Summary
Following a structured evaluation of five candidate architectures, this specification selects **Option E: Simplex-NF Studio ("The Normal Form Workbench")**. Simplex-NF Studio designates the **Interactive Relational Schema Normalizer & Bernstein 3NF/BCNF Synthesis Studio** as the flagship landing interface, supported by three synchronized specialized workbenches:
1. *Streaming BQNF Delta Repair Simulator* (Incremental CDC view maintenance and priority-queue extremum cochains).
2. *NF-IR Compiler Explorer* (Multi-pass intermediate representation lowering, poset subsumption dead-check elimination, and SQLite trigger codegen).
3. *AI LossLedger Context Gateway* (Token conservation accounting and SHA-256 Merkle loss ledger receipts for RAG pipelines).

---

## 2. Comprehensive Capability Evaluation of Repository Modules

The `simplex-normal-forms` repository encompasses four primary technical subsystems. Below is a detailed evaluation of their mathematical foundations, implementation architectures, algorithmic complexities, and operational boundaries.

```
+---------------------------------------------------------------------------------------------------+
|                                  simplex-normal-forms Repository                                   |
+---------------------------------------------------------------------------------------------------+
   │
   ├── Module A: Relational Synthesis & Dependency Algebra (Data-at-Rest)
   │     ├── normal_forms/domain/relational.py          (Armstrong closure, keys, 1NF–6NF, Chase)
   │     └── normal_forms/domain/relational_advanced.py (Minimal cover, Bernstein 3NF, BCNF tree, GYO)
   │
   ├── Module B: Streaming BQNF Delta Repair Substrate (Data-in-Motion)
   │     ├── normal_forms/domain/bqnf_validator.py      (Boundary quotient validation, CDC routes)
   │     ├── normal_forms/bqnf_repair.py                (Signed coboundary delta repair)
   │     ├── normal_forms/bqnf_extrema.py               (Priority-queue extremum cochains O(log K))
   │     └── normal_forms/sales_cochain.py              (Dynamic dyadic-bucket epsilon-quantile sketch)
   │
   ├── Module C: 4-Layer NF-IR Compiler Stack (Verification Intermediate Representation)
   │     ├── normal_forms/ir_kernel.py                  (Layer 1: Witness micro-kernel triples)
   │     ├── normal_forms/ir_subsumption.py             (Layer 2: Poset lattice optimization & DCE)
   │     ├── normal_forms/ir_wiring.py                  (Layer 3: Operadic DAG composition & Merkle)
   │     └── normal_forms/ir_lowering.py                (Layer 4: Python guard & SQLite trigger codegen)
   │
   └── Module D: AI Agent Verifiable LossLedger (Representation Transport)
         └── normal_forms/ai/                           (@coda_mur_projection, token conservation law)
```

### 2.1 Module A: Relational Synthesis & Dependency Algebra Engine

#### 2.1.1 Core Entities and Invariants
Located in `normal_forms/domain/relational.py` and `normal_forms/domain/relational_advanced.py`, this engine implements classical relational database theory using immutable Python dataclasses and standard set algebra:
- **`FunctionalDependency`**: An immutable frozen dataclass modeling $X \to Y$. Enforces that determinant $X$ and dependent $Y$ are non-empty `frozenset[str]`. Provides helper `is_trivial()` ($Y \subseteq X$) and string parser `from_str("A,B", "C")`.
- **`compute_attribute_closure(attributes, dependencies)`**: Computes the reflexive-transitive closure $X^+$ under Armstrong's Axioms. Iteratively accumulates attributes determined by dependencies whose determinants are subsets of the current accumulated set.
  - *Termination Invariant:* Monotonic growth over finite attribute set $U$: $X^{(0)} \subseteq X^{(1)} \subseteq \dots \subseteq X^{(k)} = X^{(k+1)} \subseteq U$. Terminates in at most $|F| \cdot |U|$ iterations.
- **`RelationalSchema`**: Encapsulates attribute universe $U$, dependency set $F$, and optional domain mappings.
  - *Candidate Key Derivation:* Explores attribute subsets of increasing cardinality $k \in \{1, \dots, |U|\}$, testing superkey closure ($U \subseteq K^+$) and minimality ($\forall K_i \in \text{keys}, K_i \not\subset K$).
  - *Prime Attribute Partitioning:* Derives the prime attribute set $P = \bigcup_{K \in \text{candidate\_keys}} K$. Attributes in $U \setminus P$ are designated non-prime.

#### 2.1.2 Normal Form Decision Procedures
The engine implements decision procedures across the relational hierarchy:
- **1NF (`check_1nf`)**: Asserts attribute set is non-empty and verifies that no attribute domain contains structured tokens (`array`, `bag`, `json_array`, `nested`, `struct`) or nested enclosure characters (`[]`, `{}`, `<>`).
- **2NF (`check_2nf`)**: Enforces 1NF and confirms that no non-prime attribute is partially dependent on any candidate key. Formally: $\forall K \in \text{Keys}, \forall X \subset K, (X^+ \cap (U \setminus P)) \setminus X = \emptyset$.
- **3NF (`check_3nf`)**: Enforces 2NF and verifies that for every non-trivial functional dependency $X \to A$, either $X$ is a superkey or $A$ is a prime attribute.
- **BCNF (`check_bcnf`)**: Enforces 1NF and verifies that for every non-trivial functional dependency $X \to Y$, $X$ is a superkey ($X^+ = U$).
- **EKNF (`check_eknf`)**: Implements Zaniolo's Elementary Key Normal Form. For every non-trivial $X \to A$, either $X$ is a superkey or $A$ is an elementary key attribute (where no proper subset of any candidate key determines $A$).
- **5NF / PJNF (`check_5nf`)**: Verifies that every non-trivial Join Dependency $\bowtie[R_1, \dots, R_k]$ is logically implied by candidate keys alone.
- **Extended Forms (ETNF, SKNF, RFNF, 6NF, DKNF)**: Implements specialized checks including Essential Tuple Normal Form (ETNF), Superkey Normal Form (SKNF), Redundancy-Free Normal Form (RFNF), and fail-safe screens for 6NF and Domain-Key Normal Form (DKNF).

#### 2.1.3 Synthesis and Decomposition Algorithms
- **Bernstein's 3NF Synthesis (`synthesize_3nf_bernstein`)**:
  1. Computes the minimal (canonical) cover $F_c$ via `compute_minimal_cover`: decomposes right-hand sides to singletons, eliminates extraneous left-hand attributes via closure testing, and eliminates redundant dependencies.
  2. Partitions $F_c$ into equivalence classes possessing identical determinants.
  3. Constructs subschema $R_i = X \cup Y_i$ for each determinant group.
  4. Enforces the lossless join property: tests whether any candidate key of the original relation is a subset of at least one generated subschema. If none exists, appends a relation consisting of an arbitrary candidate key.
  5. Prunes redundant subschemas strictly contained within another subschema.
  - *Outcome:* Yields a decomposition that preserves dependencies and provides a lossless join in 3NF.
- **Tsou-Fischer BCNF Decomposition Tree (`decompose_bcnf_tree`)**:
  - Recursively identifies non-trivial violating dependencies $X \to Y$ where $X^+ \ne U$.
  - Decomposes relation $R$ into $R_1 = X^+$ and $R_2 = R \setminus (X^+ \setminus X)$.
  - Projects dependencies onto subschemas via `project_functional_dependencies`.
  - Recursively decomposes until all leaf nodes satisfy BCNF.
- **Graham-Yu-Ozsoyoglu (GYO) Reduction (`gyo_reduction`)**:
  - Tests hypergraph $\alpha$-acyclicity by iteratively removing non-mineral hyperedges (ears) and isolated nodes, emitting reduction step logs and identifying cyclic cores.

#### 2.1.4 Deterministic Tableau Chase & Spurious Tuple Counterexample Generator
The Chase procedure (`chase_join_dependency`) evaluates whether a decomposition $\bowtie[R_1, \dots, R_k]$ yields a lossless join under functional dependencies $F$:
1. **Tableau Initialization:** Constructs a $k \times |U|$ matrix. For row $i$ corresponding to subschema $R_i$ and column attribute $A_j$, assigns distinguished symbol $a_j$ if $A_j \in R_i$, otherwise assigns non-distinguished symbol $b_{i,j}$.
2. **Deterministic Equivalence Steps:** For each functional dependency $X \to Y$, identifies rows agreeing on all attributes in $X$. Equates their symbols in $Y$:
   - If one symbol is distinguished ($a_j$) and the other is non-distinguished ($b_{i,j}$), replaces all occurrences of $b_{i,j}$ with $a_j$.
   - If both are non-distinguished, replaces the lexicographically larger symbol with the smaller symbol to preserve determinism.
3. **Lossless Join Witness or Spurious Tuple Generation:**
   - If an entire row becomes completely distinguished $(a_1, a_2, \dots, a_n)$, the join is lossless.
   - If a fixed point is reached without producing a distinguished row, the algorithm constructs a concrete spurious tuple witness: an instance where $\pi_{R_1}(r) \bowtie \dots \bowtie \pi_{R_k}(r)$ produces tuples not present in $r$.

#### 2.1.5 Algorithmic Complexity, Strengths, and Boundaries
- **Complexity:** Attribute closure executes in $O(|F| \cdot |U|)$. Minimal cover executes in $O(|F|^2 \cdot |U|)$. Candidate key search evaluates subsets of size $k \in [1, |U|]$, which exhibits worst-case exponential complexity $O(2^{|U|})$ on highly cyclic schemas, though bounded to small $k$ in typical real-world schemas. Tableau Chase fixed-point search terminates within $O(k^2 \cdot |F| \cdot |U|)$ iterations.
- **Strengths:** Pure Python with zero external libraries; deterministic execution; produces constructive counterexamples; verified against standard textbook cases.
- **Boundaries:** Schemas with large numbers of unconstrained attributes ($|U| > 30$) can exhaust key-search combinations if unconstrained.

---

### 2.2 Module B: Streaming BQNF Boundary Quotient Delta Repair Substrate

#### 2.2.1 Boundary Specification & CDC Event Semantics
Located across `normal_forms/domain/bqnf_validator.py`, `normal_forms/bqnf_repair.py`, `normal_forms/bqnf_extrema.py`, and `normal_forms/sales_cochain.py`, this module models incremental view maintenance over streaming Change Data Capture (CDC) events:
- **`BqnfBoundary`**: Defines an active query boundary enclosing target relations, monitored attributes, filter predicates, grouping attributes, and aggregate expressions (`SUM`, `COUNT`, `AVG`, `MIN`, `MAX`, `PERCENTILE_CONT`).
- **`BqnfCdcEvent`**: Represents atomic stream mutations (`INSERT`, `UPDATE`, `DELETE`) with before/after row images (`old`, `new`).

#### 2.2.2 Terminal Route Decisions & Report Insufficiency
Upon ingesting a CDC event, `BqnfValidator.evaluate` classifies the mutation into one of four route decisions:
1. **`Preserve`**: The mutation does not affect any monitored attribute or predicate boundary. Maintained state remains unmodified with $O(0)$ computational work.
2. **`Repair`**: The mutation impacts an additive aggregate or bounded boundary. Computes an exact signed coboundary delta ($\Delta$) applied to the cached state in $O(1)$ time without reading the underlying base table.
3. **`Invalidate`**: The mutation violates structural boundary assumptions, requiring the cached entry to be evicted.
4. **`Unsupported` (Report Insufficiency Screen)**: Triggered when scalar state lacks sufficient auxiliary dimensions to commute repair. For example, evaluating an `AVG(amount)` query without tracking both `SUM` and `COUNT` is classified as `Unsupported` (`[NonZero - LimitOfSubstrate]`), enforcing fail-closed refusal rather than silent mathematical approximation.

#### 2.2.3 Priority-Queue Extrema Cochains under Destructive Deletions
Extremum aggregations (`MIN`, `MAX`) present an established challenge in stream processing:
- **Non-Destructive Operations:** An insertion exceeding the current maximum updates the cached state in $O(1)$. A deletion of a value strictly below the current maximum leaves the state unchanged in $O(1)$.
- **Destructive Deletions:** When the row embodying the current maximum is deleted, standard scalar systems suffer from report insufficiency and must execute an $O(N)$ full table recomputation.
- **The Priority-Queue Cochain Solution (`normal_forms/bqnf_extrema.py`):**
  - Maintains a multiset frequency-indexed priority queue (`region_extremum_cochain`).
  - Upon a destructive deletion, the cochain retracts the deleted element and immediately queries the next active maximum via an index probe (`ORDER BY amount DESC LIMIT 1`).
  - *Time Complexity:* Serviced in $O(\log K)$ index maintenance time, bypassing the $O(N)$ base table scan.

#### 2.2.4 Dynamic Dyadic-Bucket Epsilon-Quantile Sketch Rebalancing
For non-stationary, streaming percentile calculations (e.g., median $q = 0.5$) under Zipfian or Pareto skew:
- **Dyadic Intervals:** Partitions the value range into canonical intervals $[b \cdot W_0, (b+1) \cdot W_0)$.
- **Dynamic Bisection Splitting:** When bucket event counts exceed `split_threshold`, recursively bisects the bucket into left and right dyadic children $[L, \frac{L+H}{2})$ and $[\frac{L+H}{2}, H)$ down to `min_bucket_width`.
- **Bottom-Up Cousin Merging:** When deletions reduce sub-bucket occupancy below `merge_threshold`, coalesces child intervals back into their dyadic parent.
- **Invariant Enforcement:** Formally verifies four structural invariants:
  1. *Mass Conservation:* $\sum \text{bucket.count} = \operatorname{COUNT}(*)$.
  2. *Interval Integrity:* $\forall i, \text{count}_i > 0 \land L_i < H_i$.
  3. *Pairwise Disjointness:* $H_i \le L_{i+1}$.
  4. *Point Membership:* Exact point-in-interval verification.
- **Epsilon Tolerance Gate:** Computes linear interpolation estimate $\hat{q}$ and verifies $|\hat{q} - q_{\text{true}}| \le \epsilon$. If error exceeds $\epsilon$, triggers bounded fallback recomputation.

---

### 2.3 Module C: 4-Layer NF-IR Compiler Stack

The NF-IR subsystem compiles high-level declarative data invariants through four abstraction layers:

```
[Declarative Contract / Schema Specification]
                      │
                      ▼
[Layer 1: Witness Micro-Kernel Triple K = (X, F: X -> Y, L)]  (ir_kernel.py)
                      │
                      ▼
[Layer 2: Monotone Poset Lattice Optimization & DCE]          (ir_subsumption.py)
                      │
                      ▼
[Layer 3: Operadic DAG Wiring & Canonical Terminal Semilattice] (ir_wiring.py)
                      │
                      ▼
[Layer 4: Target Codegen: Python Guards & SQLite Triggers]     (ir_lowering.py)
```

#### 2.3.1 Layer 1: Primitive WDP/OBNF Witness Micro-Kernel (`ir_kernel.py`)
- Unifies normalization around the mathematical triple:
  $$K = (\text{Carrier } X, \text{Collapse Map } F: X \to Y, \text{Protected Law } L)$$
- **Admitted Cut Invariants:**
  - *Support Floor:* When enabled, asserts carrier size $|X| \ge 2$; rejects subsingleton carriers with `SubsingletonCollapseRefusal` $\to$ `Refuse`.
  - *Irreflexivity:* Asserts $\neg(x \Delta x)$; identical elements asserted distinct trigger `IrreflexivityViolation` $\to$ `Reject`.
  - *Constructive Witness Extraction:* When an invariant is violated, constructs a `ConstructiveWitnessPair` recording `left_id`, `right_id`, `witness_kind`, `feature`, `left_value`, `right_value`, and `collapsed_image`.
- **OBNF Relativization:** Distinguishes between *admissible collisions* (where projection $F(x_1) = F(x_2)$ preserves protected law $L(x_1) = L(x_2)$) and *obstructed collisions* (where $L(x_1) \ne L(x_2)$, triggering `Reject`).

#### 2.3.2 Layer 2: Poset Subsumption Lattice & Dead-Check Elimination (`ir_subsumption.py`)
- Defines a machine-checked partial order $(NF, \le)$ across normal form contracts.
- **Axiomatic Poset Laws:** `verify_subsumption_poset_laws` verifies reflexivity, antisymmetry, and transitivity over the transitive closure of the relation graph.
- **Dead-Check Elimination (DCE):** Given an ordered pipeline of checks, if an upstream check $K_1$ is evaluated and admitted, and $K_1 \le K_2$ (meaning $K_1$ structurally subsumes $K_2$), then $K_2$ is safely elided. Records an `ElidedCheckRecord` without evaluating carrier rows.

#### 2.3.3 Layer 3: Operadic Wiring Compiler & Canonical Terminal Severity Join-Semilattice (`ir_wiring.py`)
- **Combinators:** Supports atomic leaf evaluation (`leaf_pass`), sequential composition (`seq_passes`), parallel composition (`par_passes`), and authorization gates (`guard_pass`).
- **Canonical Terminal Severity Join-Semilattice:** Formally orders terminal execution states:
  $$\text{Preserve } (0) < \text{Repair } (1) < \text{Quarantine } (2) < \text{Recompute } (3) < \text{Invalidate } (4) < \text{Reject } (5) < \text{Refuse } (6)$$
  - *Admitted set:* $\{\text{Preserve}, \text{Repair}, \text{Quarantine}\}$.
  - *Blocking set:* $\{\text{Recompute}, \text{Invalidate}, \text{Reject}, \text{Refuse}\}$.
  - *Lattice Join:* Parallel node aggregation computes the least upper bound: $\bigsqcup_i t_i = \max_{\le}(t_i)$.
- **Cumulative Merkle Loss Chain:** Multi-hop projections append an entry with:
  $$\text{chain\_digest} = \text{SHA256}(\text{prev\_digest} \mathbin{\Vert} \text{ledger\_digest})$$
- **Epistemic Authority Firewall:** Enforces `certified_implies_authorized: False`. Atomic and composite wiring passes unconditionally emit `authorized=False`. Only `guard_pass` can emit `authorized=True`, requiring an independent verifier identity distinct from the producer.

#### 2.3.4 Layer 4: Multi-Target Lowering (`ir_lowering.py`)
- **Target A — Python `@nf_kernel_guard`:** Generates decorators that intercept function arguments, evaluate the wiring DAG, and refuse execution if `admitted == False`.
- **Target B — SQLite Trigger & DDL Compiler:** Translates `NFKernelSpec` into standard SQL:
  - Generates `CREATE TABLE <name> (...)` with declared columns.
  - Generates `CREATE TRIGGER trg_before_insert BEFORE INSERT ON <name>` checking non-null determinants and checking collision conditions via `EXISTS (SELECT 1 FROM <table> WHERE <collapse_eq> AND (<protected_neq>))`. Aborts on violation via `RAISE(ABORT, 'NF_VIOLATION:...')`.
  - Generates matching `BEFORE UPDATE` trigger excluding `OLD.rowid`.
- **Target C — Automated Counterexample Fixture Synthesizer:** Algorithmically constructs baseline valid row fixtures and minimal failing counterexamples for each failure category (`subsingleton_carrier`, `self_difference`, `ghost_distinction`, `obstructed_collision`).

---

### 2.4 Module D: AI Agent Verifiable LossLedger & Representation Transport

Located in `normal_forms/ai/`, this module addresses data integrity during context truncation and prompt compression in Retrieval-Augmented Generation (RAG) and Model Context Protocol (MCP) systems:
- **Token Conservation Law:** Formally monitors token budgets during context compression:
  $$\text{source\_tokens} = \text{retained\_tokens} + \text{truncated\_tokens}$$
  If the sum of retained and truncated tokens fails to match the original token count, the operation is marked non-commuting and rejected.
- **Cryptographic SHA-256 Merkle LossLedger:** Generates a structured JSON ledger documenting every erased attribute, truncated token count, and field transformation, sealed by a deterministic SHA-256 Merkle digest.
- **ASRF Cycle Refusal:** Detects self-referential cycles in agent reasoning contexts and refuses evaluation to prevent hallucination amplification loops.

---

### 2.5 Comparative Capability Matrix

| Feature Dimension | Module A: Relational Synthesis | Module B: Streaming BQNF | Module C: 4-Layer NF-IR | Module D: AI LossLedger |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Domain** | Relational Database Systems | Distributed Stream Processing | Compilers & Verification IR | Verifiable AI & RAG Contexts |
| **Data Modality** | Data-at-Rest (Schemas & FDs) | Data-in-Motion (CDC Events) | Declarative Contracts & ASTs | Unstructured Context / Prompts |
| **Underlying Mathematics** | Armstrong Axioms, Poset Lattices | Homological Boundaries, Cochains | Operads, Posets, Join-Semilattices | Conservation Laws, Merkle Trees |
| **Core Invariant** | Lossless Join & Minimal Cover | Signed $\Delta$ Coboundary Equivalence | Admitted Cut, Structural Subsumption | Token Conservation ($\sum = \text{Src}$) |
| **Diagnostic Output** | Tableau Step Trace & Spurious Tuples | Terminal Route (`Repair`/`Invalidate`) | `ConstructiveWitnessPair` | Sealed `LossLedger` & Merkle Root |
| **Target Codegen** | Relational SQL DDL | Dynamic Cochain Index Queries | SQLite Triggers & Python Guards | Context Projection Envelopes |
| **Execution Dependency** | Python Standard Library | Python Standard Library + SQLite | Python Standard Library + SQLite | Python Standard Library |
| **Test Verification** | 100% Passing Unit Tests | Passing Cochain & Extrema Tests | 136 Passing Unit & Property Tests | Passing Conservation Tests |

---

## 3. Candidate MVP Options & Selection Rationale

### 3.1 Candidate MVP Options Evaluated

To determine the optimal product direction for `smplxnf.anomalon.com`, five distinct architectural options were formulated and evaluated:

#### Option A: Interactive Relational Schema Normalizer & Synthesis Studio
- **Scope:** An interactive relational normalization workbench. The user inputs attributes and functional dependencies (or selects presets). The system computes candidate keys, prime attributes, 1NF–6NF/BCNF compliance, minimal covers, Bernstein 3NF synthesis, Tsou-Fischer BCNF trees, and step-by-step Tableau Chase execution with spurious tuple generation.
- **Strengths:** High conceptual resonance across all software engineering disciplines. Directly demonstrates deep database internals that every software engineer and hiring manager understands. Highly visual through Chase tableau substitutions.
- **Limitations:** Focuses on data-at-rest; omits streaming and AI capabilities if deployed in isolation.

#### Option B: Streaming BQNF Boundary Quotient Delta Repair Workbench
- **Scope:** A live CDC stream simulator evaluating incremental view maintenance. Demonstrates $O(1)$ signed delta repairs, $O(\log K)$ extremum cochains on destructive deletions, dynamic dyadic-bucket quantile sketch rebalancing, and report insufficiency screens.
- **Strengths:** Demonstrates advanced distributed systems and stream processing concepts relevant to modern infrastructure engineering.
- **Limitations:** Higher conceptual barrier to entry; requires background in homological boundary notation to appreciate in a brief initial evaluation.

#### Option C: AI Agent Verifiable LossLedger Gateway
- **Scope:** A Model Context Protocol (MCP) gateway demonstrating verifiable context compression. Evaluates prompt truncation, enforces exact token conservation, generates SHA-256 Merkle LossLedgers, and validates freshness posets.
- **Strengths:** Addresses timely industry discussions regarding LLM context truncation and auditability.
- **Limitations:** Risks being perceived as decorative or tangential unless grounded in relational and compiler foundations.

#### Option D: Simplex Normal Form Compiler Explorer ("Godbolt for Normal Forms")
- **Scope:** A 4-pane compiler inspector showing contract specifications, lowered witness micro-kernels, poset lattice dead-check elimination, and generated SQLite triggers / Python guards.
- **Strengths:** High signal for compiler, programming languages, and query optimizer teams.
- **Limitations:** Abstract compiler intermediate representations can present a steep learning curve for non-specialist visitors within thirty seconds.

#### Option E: Unified "Simplex-NF Studio" (The Normal Form Workbench)
- **Scope:** An integrated multi-disciplinary web platform featuring **Option A (Relational Schema Normalizer & Synthesis Studio)** as the primary default landing interface, accompanied by dedicated, synchronized interactive tabs for **Streaming BQNF (Option B)**, **NF-IR Compiler Explorer (Option D)**, **AI LossLedger Gateway (Option C)**, and **Developer Onboarding / SDK Quickstart**.
- **Strengths:** Provides immediate 30-second visual engagement through the relational synthesis flagship while offering deep multi-disciplinary depth across streaming, compilers, and AI systems in secondary tabs.
- **Limitations:** Requires disciplined frontend architecture to maintain clean separation and sub-200ms page delivery.

---

### 3.2 Evaluation Criteria
Candidate options were evaluated against four weighted criteria:
- **C1: Intellectual & Engineering Depth (Weight: 25%):** Mathematical rigor, non-trivial algorithmic design, and verification discipline.
- **C2: 30-Second Web Visual Delight (Weight: 30%):** Immediate comprehensibility, interactive feedback, and engagement for a web visitor within thirty seconds.
- **C3: Resume & Employer Signal Across Tier-1 Tech (Weight: 25%):** Breadth and strength of signal conveyed to hiring managers in database systems, compilers, distributed infrastructure, and AI engineering.
- **C4: External Developer Adoption & Portability (Weight: 20%):** Ease with which an external developer can clone the repository, run tests, and import capabilities into their own codebase.

---

### 3.3 Comparative Scoring Matrix

| Criterion | Option A: Relational Studio | Option B: Streaming BQNF | Option C: AI LossLedger | Option D: NF-IR Compiler | Option E: Simplex-NF Studio (Selected) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **C1: Engineering Depth** | 9.0 / 10 | 9.2 / 10 | 8.0 / 10 | 9.5 / 10 | **9.6 / 10** |
| **C2: 30-Second Delight** | 9.5 / 10 | 7.0 / 10 | 7.5 / 10 | 7.8 / 10 | **9.5 / 10** |
| **C3: Resume Impact** | 9.0 / 10 | 8.8 / 10 | 8.2 / 10 | 9.2 / 10 | **9.8 / 10** |
| **C4: Developer Adoption** | 9.2 / 10 | 7.8 / 10 | 8.5 / 10 | 8.0 / 10 | **9.4 / 10** |
| **Weighted Total** | **9.20 / 10** | **8.15 / 10** | **7.98 / 10** | **8.63 / 10** | **9.59 / 10** |

---

### 3.4 Explicit Rationale for Selecting Option E (Simplex-NF Studio)

1. **Maximum Portfolio Surface with Zero Evaluator Confusion:**  
   Option E resolves the tension between visual immediacy and technical depth. By establishing the **Relational Normalizer & Synthesis Studio** as the default landing view, the application engages the visitor within five seconds using a widely recognized computer science foundation (functional dependencies, candidate keys, 3NF synthesis, and Chase tableaus). 

2. **Cross-Sector Resume Alignment:**  
   A single-focus MVP restricts evaluator resonance to one niche. A database optimizer manager might skip an AI-only demo, while an AI infrastructure engineer might overlook a pure relational tool. Option E provides immediate, dedicated tabs for each target sector:
   - Database Engineers engage with the **Relational Studio & Chase Tableau**.
   - Distributed Systems Engineers engage with the **Streaming BQNF Cochain Simulator**.
   - Compiler Engineers engage with the **NF-IR Poset Subsumption & Trigger Codegen**.
   - AI Platform Engineers engage with the **Merkle LossLedger Token Gateway**.

3. **Technical Integrity and Shared Core:**  
   These tabs are not disconnected facades; they share the same underlying repository modules (`normal_forms.domain.relational`, `normal_forms.ir_*`, `normal_forms.bqnf_*`, and `normal_forms.ai`). The relational synthesis algorithms lower into NF-IR kernel specifications, which in turn compile into the SQLite triggers displayed in the compiler tab.

---

## 4. Target User Personas & Resume Positioning

### 4.1 Tier-1 Technical Hiring Landscape & Evaluation Signals
Hiring managers at top-tier systems companies (such as DuckDB, Snowflake, Databricks, CockroachDB, ClickHouse, Modular, NVIDIA, Jane Street, Materialize, and OpenAI) evaluate candidates through signal-to-noise filters:
- **Low-Signal Anti-Patterns:** CRUD web wrappers, boilerplate AI wrapper scripts, tutorial reproductions without mathematical rigor, or projects with missing tests and unhandled edge cases.
- **High-Signal Indicators:** Formally grounded domain models, algorithmic implementations written from scratch without third-party black boxes, explicit handling of edge cases and counterexamples, reproducible property test suites, and clean systems architecture.

### 4.2 Detailed Persona Mappings

```
+---------------------------------------------------------------------------------------------------+
|                                  Target Resume Persona Alignment                                  |
+---------------------------------------------------------------------------------------------------+
| Persona 1: Database Kernel & Query Optimizer Engineers                                            |
| Target: DuckDB, Snowflake, Databricks, CockroachDB, SingleStore, ClickHouse                       |
| High-Leverage Skills Demonstrated:                                                                |
| - Pure-Python implementation of Armstrong's Axioms and attribute closure computation.             |
| - Bernstein (1976) 3NF synthesis producing dependency-preserving, lossless decompositions.        |
| - Tsou-Fischer BCNF decomposition trees and Graham-Yu-Ozsoyoglu (GYO) hypergraph reductions.      |
| - Relational Tableau Chase with constructive spurious tuple counterexample generation.            |
+---------------------------------------------------------------------------------------------------+
| Persona 2: Compiler & Systems Programming Languages Engineers                                     |
| Target: Modular, NVIDIA, Jane Street, Google Core, Meta Systems                                   |
| High-Leverage Skills Demonstrated:                                                                |
| - 4-layer compiler architecture (Micro-Kernel -> Lattice Poset -> Operadic DAG -> Target Codegen).|
| - Monotone poset lattice verification (reflexivity, antisymmetry, transitivity).                   |
| - Algebraic Dead-Check Elimination (DCE) eliding structurally subsumed runtime checks.            |
| - Code generation emitting fail-closed Python decorators and SQLite BEFORE INSERT/UPDATE triggers.|
+---------------------------------------------------------------------------------------------------+
| Persona 3: Streaming Infrastructure & Distributed Systems Engineers                               |
| Target: Materialize, Confluent, Apache Flink, ClickHouse, Redpanda                                |
| High-Leverage Skills Demonstrated:                                                                |
| - Boundary-Quotient Normal Form (BQNF) for incremental view maintenance (IVM).                    |
| - O(1) signed coboundary delta repair on additive stream mutations.                              |
| - Priority-queue extremum cochains servicing destructive deletions in O(log K) without scans.     |
| - Dynamic dyadic-bucket epsilon-quantile sketch rebalancing with mass conservation invariants.     |
+---------------------------------------------------------------------------------------------------+
| Persona 4: AI Infrastructure & Verifiable Agent Architects                                        |
| Target: OpenAI, Anthropic, Scale AI, Cloudflare Workers, LangChain                                |
| High-Leverage Skills Demonstrated:                                                                |
| - Verifiable context transport with strict token conservation laws (retained + truncated == src). |
| - Cryptographic SHA-256 Merkle LossLedger generation for auditable prompt truncation.             |
| - Fail-closed epistemic authority firewalls (certified_implies_authorized: false).                |
| - ASRF cycle refusal preventing hallucination loops in recursive agent architectures.             |
+---------------------------------------------------------------------------------------------------+
```

---

## 5. Complete System Architecture Specification

### 5.1 Presentation Layer & Application Topology
The Simplex-NF Studio web application is designed as a self-contained ASGI service adhering to Clean Architecture principles:

```
[Web Browser: Desktop / Mobile Client]
                  │
                  ▼ HTTPS / JSON REST
[Render Edge / CNAME: smplxnf.anomalon.com]
                  │
                  ▼ Reverse Proxy
[FastAPI Application: web/app.py (Uvicorn ASGI Runner)]
   ├── Static File Mount: web/static/ (Tailwind CSS, SVG diagrams, Alpine/Vanilla JS)
   ├── Template Engine: web/templates/index.html (Single-Page Studio Dashboard)
   │
   └── REST API Route Handlers:
         ├── GET  /healthz
         ├── POST /api/relational/normalize
         ├── POST /api/bqnf/simulate
         ├── POST /api/compiler/lower
         └── POST /api/ai/lossledger
                  │
                  ▼ Pure In-Memory Invocations (Sub-50ms)
[simplex-normal-forms Core Domain Libraries]
   ├── normal_forms.domain.relational & relational_advanced
   ├── normal_forms.domain.bqnf_validator, bqnf_repair, bqnf_extrema, sales_cochain
   ├── normal_forms.ir_kernel, ir_subsumption, ir_wiring, ir_lowering
   └── normal_forms.ai
```

### 5.2 API Interface Contract & JSON Schema Specifications

#### 5.2.1 Health Check Endpoint (`GET /healthz`)
- **Purpose:** Production liveness and readiness probe for Render orchestration.
- **Response Model:**
  ```json
  {
    "status": "ok",
    "service": "smplxnf-studio",
    "version": "0.1.0",
    "timestamp_utc": "2026-11-01T20:00:00Z"
  }
  ```

#### 5.2.2 Relational Synthesis & Chase Endpoint (`POST /api/relational/normalize`)
- **Request Body:**
  ```json
  {
    "attributes": ["order_id", "customer_id", "item_id", "price", "quantity", "customer_zip"],
    "dependencies": [
      {"determinant": ["order_id"], "dependent": ["customer_id"]},
      {"determinant": ["customer_id"], "dependent": ["customer_zip"]},
      {"determinant": ["item_id"], "dependent": ["price"]},
      {"determinant": ["order_id", "item_id"], "dependent": ["quantity"]}
    ],
    "run_chase": true
  }
  ```
- **Response Model:**
  ```json
  {
    "status": "success",
    "candidate_keys": [["item_id", "order_id"]],
    "prime_attributes": ["item_id", "order_id"],
    "non_prime_attributes": ["customer_id", "customer_zip", "price", "quantity"],
    "normal_form_status": {
      "1nf": {"passed": true, "reason": "Attributes atomic with no nested domain indicators."},
      "2nf": {"passed": false, "reason": "Partial dependency detected: item_id -> price"},
      "3nf": {"passed": false, "reason": "Transitive dependency detected: customer_id -> customer_zip"},
      "bcnf": {"passed": false, "reason": "Determinant customer_id is not a superkey."}
    },
    "minimal_cover": [
      {"determinant": ["order_id"], "dependent": ["customer_id"]},
      {"determinant": ["customer_id"], "dependent": ["customer_zip"]},
      {"determinant": ["item_id"], "dependent": ["price"]},
      {"determinant": ["item_id", "order_id"], "dependent": ["quantity"]}
    ],
    "bernstein_3nf_subschemas": [
      {"table_name": "rel_1", "attributes": ["customer_id", "order_id"], "primary_key": ["order_id"]},
      {"table_name": "rel_2", "attributes": ["customer_id", "customer_zip"], "primary_key": ["customer_id"]},
      {"table_name": "rel_3", "attributes": ["item_id", "price"], "primary_key": ["item_id"]},
      {"table_name": "rel_4", "attributes": ["item_id", "order_id", "quantity"], "primary_key": ["item_id", "order_id"]}
    ],
    "chase_verification": {
      "is_lossless": true,
      "step_count": 4,
      "distinguished_row_index": 3,
      "steps": [
        {"step_index": 1, "applied_fd": "order_id -> customer_id", "modified_symbols": {"b_4_customer_id": "a_customer_id"}}
      ],
      "spurious_tuple_witness": null
    },
    "sql_ddl": "CREATE TABLE rel_1 (order_id TEXT PRIMARY KEY, customer_id TEXT);\n..."
  }
  ```

#### 5.2.3 Streaming BQNF Delta Simulator Endpoint (`POST /api/bqnf/simulate`)
- **Request Body:**
  ```json
  {
    "boundary": {
      "target_relation": "sales",
      "attributes": ["region", "amount", "status"],
      "predicates": ["status = 'settled'"],
      "aggregates": ["SUM(amount)", "MAX(amount)"]
    },
    "cdc_event": {
      "op": "UPDATE",
      "relation": "sales",
      "old_row": {"id": "s1", "region": "US-West", "amount": 100.0, "status": "settled"},
      "new_row": {"id": "s1", "region": "US-West", "amount": 160.0, "status": "settled"}
    }
  }
  ```
- **Response Model:**
  ```json
  {
    "status": "success",
    "decision": "Repair",
    "maintenance_complexity": "O(1)",
    "signed_deltas": {
      "delta_sum_amount": 60.0
    },
    "extremum_status": {
      "type": "non_destructive_increase",
      "action": "scalar_update",
      "new_max": 160.0,
      "complexity": "O(1)"
    },
    "report_sufficiency": {
      "sufficient": true,
      "reason": "Monitored aggregate SUM(amount) admits closed coboundary delta."
    }
  }
  ```

#### 5.2.4 NF-IR Compiler Lowering Endpoint (`POST /api/compiler/lower`)
- **Request Body:**
  ```json
  {
    "contract_id": "nf.classical.bcnf",
    "table_name": "department_assignments",
    "heading": ["employee_id", "department_id", "manager_id"],
    "key_field": "employee_id",
    "functional_dependency": {
      "determinant": ["department_id"],
      "dependent": ["manager_id"]
    },
    "enable_poset_dce": true
  }
  ```
- **Response Model:**
  ```json
  {
    "status": "success",
    "kernel_spec": {
      "contract_id": "nf.classical.bcnf",
      "key_field": "employee_id",
      "collapse_fields": ["department_id"],
      "protected_fields": ["manager_id"]
    },
    "subsumption_analysis": {
      "evaluated_contracts": ["nf.classical.bcnf"],
      "elided_contracts": ["nf.classical.3nf", "nf.classical.2nf"],
      "reason": "Structural dominance: BCNF check subsumes weaker dependency constraints under identical heading."
    },
    "lowered_sqlite_ddl": {
      "table_sql": "CREATE TABLE department_assignments (\n  employee_id TEXT PRIMARY KEY,\n  department_id TEXT NOT NULL,\n  manager_id TEXT NOT NULL\n);",
      "before_insert_trigger_sql": "CREATE TRIGGER trg_bcnf_before_insert\nBEFORE INSERT ON department_assignments\nFOR EACH ROW\nBEGIN\n  SELECT RAISE(ABORT, 'NF_VIOLATION:nf.classical.bcnf:ObstructedCollision:manager_id')\n  WHERE EXISTS (\n    SELECT 1 FROM department_assignments\n    WHERE department_id = NEW.department_id AND manager_id != NEW.manager_id\n  );\nEND;",
      "before_update_trigger_sql": "CREATE TRIGGER trg_bcnf_before_update\nBEFORE UPDATE ON department_assignments\nFOR EACH ROW\nBEGIN\n  SELECT RAISE(ABORT, 'NF_VIOLATION:nf.classical.bcnf:ObstructedCollision:manager_id')\n  WHERE EXISTS (\n    SELECT 1 FROM department_assignments\n    WHERE department_id = NEW.department_id AND manager_id != NEW.manager_id AND rowid != OLD.rowid\n  );\nEND;"
    },
    "lowered_python_guard": "@compile_to_python_decorator(spec)\ndef process_records(rows): ..."
  }
  ```

#### 5.2.5 AI Merkle LossLedger Endpoint (`POST /api/ai/lossledger`)
- **Request Body:**
  ```json
  {
    "source_documents": [
      {"chunk_id": "c1", "text": "PostgreSQL manages concurrency using MVCC snapshot isolation.", "doc_title": "Postgres Internals", "internal_debug_score": 0.95},
      {"chunk_id": "c2", "text": "DuckDB utilizes vectorized Morsel-driven execution for OLAP queries.", "doc_title": "DuckDB Internals", "internal_debug_score": 0.91}
    ],
    "target_fields": ["chunk_id", "text", "doc_title"],
    "max_token_budget": 20
  }
  ```
- **Response Model:**
  ```json
  {
    "status": "success",
    "admitted": true,
    "token_metrics": {
      "source_tokens": 28,
      "retained_tokens": 16,
      "truncated_tokens": 12,
      "token_conservation_commutes": true
    },
    "loss_ledger": {
      "ledger_id": "ledger_coda_mur_1730491200",
      "erased_attributes": ["internal_debug_score"],
      "dropped_chunks_count": 1,
      "merkle_digest": "4a7d1ed414474e4033ac29ccb8653d9b168e40ceb7a70c8b2034e4a06a3297a7"
    },
    "authority_firewall": {
      "certified": true,
      "authorized": false,
      "reason": "certified_implies_authorized is false; execution authority requires independent policy gate."
    }
  }
  ```

---

### 5.3 Render Deployment Topology & Infrastructure Blueprint

#### 5.3.1 Service Configuration (`render.yaml`)
The application deploys as a standard Python Web Service on Render:

```yaml
services:
  - type: web
    name: smplxnf-live
    env: python
    region: oregon
    plan: free
    buildCommand: "pip install -e . && pip install -r web/requirements.txt"
    startCommand: "uvicorn web.app:app --host 0.0.0.0 --port $PORT"
    healthCheckPath: /healthz
    envVars:
      - key: PYTHONUNBUFFERED
        value: "1"
      - key: APP_ENVIRONMENT
        value: "production"
    domains:
      - smplxnf.anomalon.com
```

#### 5.3.2 Subdomain Routing via CNAME
1. **Render Hostname:** The separate `smplxnf-live` service was assigned `smplxnf-live.onrender.com` on 2026-11-02. See the [deployment record](verification/2026-11-02-deployment.md); the blueprint above matches the selected Free compute plan.
2. **DNS Configuration:** In the DNS control panel for `anomalon.com`, a canonical name record is created:
   ```text
   smplxnf.anomalon.com.  CNAME  smplxnf-live.onrender.com.
   ```
3. **Automated TLS Termination:** Render automatically provisions and renews a Let's Encrypt SSL/TLS certificate for `smplxnf.anomalon.com`.

#### 5.3.3 Operational Bounds & Resource Footprint
- **Memory Footprint:** The original design estimated approximately 45MB at idle. No retained production measurement establishes this figure; measure memory on the deployed instance.
- **CPU & Latency Profile:** Core synthesis, Tableau Chase fixed-point calculation, and trigger compilation execute in 5ms to 35ms on standard cloud vCPUs.
- **Cold-Start Latency:** Process startup takes approximately 1.2 seconds, ensuring rapid recovery on cold instances.

---

## 6. External Developer Onboarding Blueprint & Packaging

### 6.1 Packaging Gap Analysis & Remediation
Prior to this specification, the `simplex-normal-forms` repository contained functional library code in `normal_forms/`, but lacked a standard Python build definition (`pyproject.toml` or `setup.py`). As a consequence, running `pip install -e .` failed immediately.

To remediate this limitation and enable immediate external developer adoption, the repository introduces a PEP 517/518 compliant `pyproject.toml` at repository root.

### 6.2 The `pyproject.toml` Standard Specification

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "simplex-normal-forms"
version = "0.1.0"
description = "Boundary-Certified Relational Normalization, Streaming BQNF Cochain Retraction & NF-IR Compiler"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [
    { name = "Simplex Normal Forms Authors" }
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Database",
    "Topic :: Software Development :: Compilers",
]
dependencies = [
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "hypothesis>=6.0.0",
]
web = [
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.28.0",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["normal_forms*"]
```

---

### 6.3 5-Minute Developer Quickstart Walkthrough

An external engineer can install and execute the codebase locally in four terminal commands:

```bash
# Step 1: Clone the repository
git clone https://github.com/dbccpage/simplex-normal-forms.git
cd simplex-normal-forms

# Step 2: Create and activate a clean virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Step 3: Install in editable development mode
pip install -e ".[dev,web]"

# Step 4: Run automated test suite to verify installation
pytest tests/ -v
```

---

### 6.4 Runnable Copy-Paste Integration Snippets

#### Snippet 1: Schema Normalization & Bernstein 3NF Synthesis in User Code
```python
"""Example: Automated Relational Decomposition using simplex-normal-forms."""
from normal_forms.domain.relational import (
    FunctionalDependency,
    RelationalSchema,
    check_3nf,
    chase_join_dependency,
)
from normal_forms.domain.relational_advanced import synthesize_3nf_bernstein

# 1. Declare schema attributes and functional dependencies
schema = RelationalSchema(
    attributes=frozenset({"order_id", "item_id", "customer_id", "customer_zip", "price", "quantity"}),
    dependencies=frozenset({
        FunctionalDependency(frozenset({"order_id"}), frozenset({"customer_id"})),
        FunctionalDependency(frozenset({"customer_id"}), frozenset({"customer_zip"})),
        FunctionalDependency(frozenset({"item_id"}), frozenset({"price"})),
        FunctionalDependency(frozenset({"order_id", "item_id"}), frozenset({"quantity"})),
    })
)

# 2. Derive candidate keys and check normal forms
print("Candidate Keys:", [sorted(k) for k in schema.candidate_keys()])
is_3nf, reason = check_3nf(schema)
print(f"Satisfies 3NF: {is_3nf} (Diagnostic: {reason})")

# 3. Synthesize dependency-preserving, lossless-join 3NF decomposition
subschemas = synthesize_3nf_bernstein(schema)
print("\nSynthesized 3NF Subschemas:")
for idx, s in enumerate(subschemas, start=1):
    print(f"  Table {idx}: {sorted(s)}")

# 4. Verify lossless join via Tableau Chase
chase = chase_join_dependency(schema.attributes, schema.dependencies, subschemas)
print(f"\nLossless Join Verified via Chase: {chase.is_implied} in {len(chase.steps)} steps.")
```

#### Snippet 2: Compiling Relational Invariants to SQLite Triggers
```python
"""Example: Lowering a normal-form contract into executable SQLite triggers."""
import sqlite3
from normal_forms.domain.relational import FunctionalDependency
from normal_forms.ir_kernel import lower_fd_to_kernel_spec
from normal_forms.ir_lowering import compile_to_sqlite_triggers, install_and_verify_sqlite_bundle

# 1. Define functional dependency: department_id -> manager_id
spec = lower_fd_to_kernel_spec(
    fd=FunctionalDependency(frozenset({"department_id"}), frozenset({"manager_id"})),
    key_field="employee_id",
    heading=("employee_id", "department_id", "manager_id"),
    contract_id="nf.classical.bcnf",
)

# 2. Compile specification into SQLite trigger bundle
bundle = compile_to_sqlite_triggers(spec, table_name="employee_directory")
print("Generated Trigger SQL:\n", bundle.before_insert_trigger_sql)

# 3. Verify fail-closed trigger enforcement in SQLite
conn = sqlite3.connect(":memory:")
success, error = install_and_verify_sqlite_bundle(
    conn=conn,
    bundle=bundle,
    rows=[
        {"employee_id": "E1", "department_id": "D1", "manager_id": "Alice"},
        # Attempting conflicting insertion with distinct manager for department D1:
        {"employee_id": "E2", "department_id": "D1", "manager_id": "Bob"},
    ],
)
assert success is False
print(f"Trigger successfully intercepted violation: {error}")
```

#### Snippet 3: Incremental Streaming BQNF CDC Evaluation
```python
"""Example: Evaluating streaming CDC mutations with BQNF boundary retraction."""
from normal_forms.domain.bqnf_validator import BqnfBoundary, BqnfCdcEvent, BqnfValidator

# 1. Define query boundary
boundary = BqnfBoundary(
    target_relation="orders",
    attributes=("order_id", "amount", "status"),
    predicates=("status = 'shipped'",),
    aggregates=("SUM(amount)",),
)

# 2. Evaluate CDC UPDATE event modifying order amount
event = BqnfCdcEvent(
    op="UPDATE",
    relation="orders",
    old={"order_id": "101", "amount": 50.0, "status": "shipped"},
    new={"order_id": "101", "amount": 85.0, "status": "shipped"},
)

result = BqnfValidator.evaluate(boundary, event)
print("Boundary Route Decision:", result.decision)  # Output: Repair
print("Computed Coboundary Delta:", result.repair)    # Output: {'delta_sum_amount': 35.0}
```

#### Snippet 4: Auditable AI Context Compression with Merkle LossLedger
```python
"""Example: Auditable prompt context truncation with SHA-256 Merkle LossLedger."""
from normal_forms.ai import coda_mur_projection

# 1. Wrap prompt projection with exact token budget constraints
@coda_mur_projection(
    source_fields=("chunk_id", "content", "relevance_score"),
    target_fields=("chunk_id", "content"),
    key_field="chunk_id",
    protected_fields=("chunk_id",),
    max_token_budget=18,
)
def compress_prompt_context(chunks):
    return None  # Triggers canonical projection

# 2. Project candidate chunks
chunks = [
    {"chunk_id": "doc_1", "content": "Relational schemas require Boyce-Codd compliance.", "relevance_score": 0.96},
    {"chunk_id": "doc_2", "content": "Streaming engines maintain boundaries over changelogs.", "relevance_score": 0.92},
]

envelope = compress_prompt_context(chunks)
print("Context Admitted:", envelope.admitted)
print("Source Tokens:", envelope.source_token_count)
print("Retained Tokens:", envelope.retained_token_count)
print("Token Conservation Commutes:", envelope.token_conservation_commutes)
print("Cryptographic Merkle Digest:", envelope.loss_ledger["merkle_digest"])
print("Erased Fields in Ledger:", envelope.loss_ledger["erased_attributes"])
```

---

## 7. Epistemic Claim Hygiene Quadrant

In compliance with the project Claim Hygiene standard, all architectural evaluations and technical statements observe strict boundary conditions:

### 7.1 What this Specification Supports
1. Supports the deterministic computation of Armstrong attribute closures, minimal candidate keys, and canonical dependency covers over declared finite attribute sets.
2. Supports constructive 3NF synthesis (preserving dependencies and providing lossless joins) via Bernstein's 1976 algorithm, and BCNF decomposition trees via Tsou-Fischer.
3. Supports deterministic verification of join dependency implications via the Tableau Chase, generating concrete spurious tuple counterexamples when joins are lossy.
4. Supports exact $O(1)$ signed coboundary delta repair for additive boundary queries and $O(\log K)$ priority-queue extremum maintenance under destructive deletions in SQLite test models.
5. Supports lowering declarative normal-form kernel contracts into executable Python guards and SQLite `BEFORE INSERT` / `BEFORE UPDATE` trigger aborts.
6. Supports exact token conservation accounting (`retained_tokens + truncated_tokens == source_tokens`) and SHA-256 Merkle loss ledger generation for RAG context transport.

### 7.2 What this Specification Does Not Support
1. Does not confer operational authority or policy authorization (`AuthorityEffect: None`, `certified_implies_authorized: false`). Formal mathematical verification remains isolated from authorization decisions.
2. Does not assert that pure-Python relational algorithms scale without modification to tables with dozens of cyclic attributes without combinatorial bounding.
3. Does not claim that single-node SQLite test fixtures replace distributed consensus protocols (e.g., Raft, Paxos) or distributed query planners in production streaming clusters.
4. Does not assert that 3NF or BCNF normalization eliminates application-level anomalies outside declared functional dependencies.

### 7.3 Narrowest Defensible Claim
The original MVP handoff reported 136 pytest items (89 unittest methods). Subsequent correctness and packaging work was merged in PRs #18–19, with 232 tests passing in premerge verification. PR #21's lossy preset browser fix passed all five hosted CI jobs and was deployed at merge commit `f9c289c`. Separate HTTPS/API smoke checks passed on both public origins on 2026-11-02. These are bounded implementation and deployment checks, not certification of every contract or full live browser acceptance. See [current evidence and scope](PROJECT_STATUS.md).

### 7.4 Next Test Needed
The separate Render service is live and both origins passed HTTPS/API checks. Finish the public browser checklist when the user makes a browser available; it was interrupted after the default relational result was inspected. Use [DEPLOYMENT.md](DEPLOYMENT.md) for the remaining checks and `scripts/http_smoke.py` for future deployment regression checks. Recorded request durations do not establish the original sub-200 ms target or sustained-load capacity.

---

## 8. Conclusion & Actionable Execution Sequence

1. **Approved Architecture:** Option E (Simplex-NF Studio) is established as the single canonical MVP for `smplxnf.anomalon.com`.
2. **Original implementation milestones (implemented; HTTPS/API verified, full live browser acceptance incomplete):**
   - **M2 (Web Prototype & Deployment):** Author `pyproject.toml`, implement `web/app.py`, author `render.yaml`, and build the responsive single-page studio dashboard.
   - **M3 (Documentation & Import Guide):** Author comprehensive `docs/IMPORT_GUIDE.md` and update `README.md` with complete installation and code usage instructions.
   - **M4 (Automated Tests & Verification):** Add test suites covering API endpoints, UI rendering, and external package import workflows.
