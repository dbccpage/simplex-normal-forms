# PostgreSQL Stack: Certified Normal Forms by Attempt

**Status:** engine-relative implementation notes (stronger structural substrate than SQL Server for this framework)  
**Target:** PostgreSQL 16/17/18 style feature set  
**Purpose:** same collision as `2_sql_server_certified_normal_forms_attempts.md` — plus **relational expressivity gradients** between engines.

**Theory stack:**

| Document | Role |
|---|---|
| `0_relvar_relation_table_and_boundary_relvar.md` | base ontology |
| `1a_bqnf_incremental_repair.md` / `1b_gtmur_representation_transport.md` | certified repair & transport semantics |
| `2_sql_server_certified_normal_forms_attempts.md` | parallel substrate (weaker structural layer; compare §14) |

---

## 0. Working definition

### 0.1 Engine-relative normal forms (shared framing)

\[
\text{NF} = (\text{invariant},\ \text{substrate},\ \text{attempt})
\]

PostgreSQL is not “more correct” than SQL Server. It sits **higher on the relational expressivity gradient** for many invariants: richer structure can be encoded **declaratively** before the system falls off the **external verifier cliff**.

> PostgreSQL does not “support BQNF.”  
> PostgreSQL can **host BQNF attempts** — and can enforce more **shape** invariants natively than SQL Server.

See `2_sql_server` §0 for enforcement vs certification vs authorization.

### 0.2 Why PostgreSQL is philosophically closer

PostgreSQL treats **semantic structure as data** more often than row-only engines:

```text
domains              -- semantic contracts on columns
exclusion constraints -- structural invariants (overlap, exclusion)
range types          -- time/space carriers in the type system
transition tables    -- before/after as queryable relations
deferrable constraints -- batch-correctable integrity
recursive CTEs     -- fixpoint-shaped queries in-SQL
```

You can push further **before** triggers + external verifiers become mandatory. That contrast is theoretically important, not a feature checklist.

### 0.3 Three levels of semantics (meta-theory)

Across SMPLX-009 documents, semantics stratify as:

\[
\boxed{
\text{Engine (structural)}
\subset
\text{Certified}
\subset
\text{Authority}
}
\]

| Level | What it covers | PostgreSQL examples |
|---|---|---|
| **1. Structural** | what the engine natively understands | keys, FKs, `CHECK`, domains, **exclusion**, ranges, partial indexes |
| **2. Certified** | evidence + verifier-adjudicated repair/transport | `repair_certificate`, provenance tables, transition-table BQNF triggers |
| **3. Authority** | policy, approximation legitimacy, trust lineage | external verifier, GTTC shadows (Paper C) |

**Structural ⊂ Certified ⊂ Authority** is not implication of truth — it is **scope of claim**: each outer layer may say less unless inner layers check out.

Traditional relational theory assumed storage and semantics were tightly coupled. Modern systems separate:

```text
storage  →  representation  →  verification  →  authority
```

### 0.4 The recurring pattern

```text
desired invariant
  → PostgreSQL may encode structurally (domains, EXCLUDE, ranges)
  → or via transition tables / triggers
  → or only via certificate + external verifier
```

**Calibrated claim (keep this sentence):**

> PostgreSQL can encode more structure than SQL Server, especially temporal non-overlap through exclusion constraints. But it still cannot make arbitrary certified normal forms first-class.

**Encoding ≠ first-class semantic understanding.** The quotient engine, transport witness $\chi_F$, and observer authority still live outside the catalog.

### 0.5 Relational expressivity gradients

Comparing engines is not “who has more features.” It is **depth of normal-form enforcement**:

| Gradient dimension | Question |
|---|---|
| anomaly expressibility | can the invariant be stated in DDL/types? |
| invariant enforceability | does the engine reject violations without app code? |
| observer-certification capacity | can visibility boundaries be stored and checked? |

PostgreSQL typically ranks **higher** on enforceability for temporal and domain-shaped invariants; **equal** on BQNF (no native $Q^1$); **equal** on authority (external).

### 0.6 Constraint-aware observer systems (future direction)

Observers declare visible structure; engines enforce **partial** invariants; verifiers enforce **semantic** invariants; certificates bridge the gap:

```text
observer relvar O  +  engine constraints  +  repair_certificate  +  verifier
```

Maps to retrieval pipelines, agent memory, tool calling, vector/cache repair — semantically rich, structurally weak, authority-fragile without this stack.

### 0.7 Conceptual shift: closed world → open world

| Era | Assumption |
|---|---|
| Codd | closed-world, centralized store; normalize **storage** |
| Distributed systems | normalize **replication** |
| This framework | open-world **observer systems**; normalize **authority-bearing transitions** |

A normal form is a decidable representation discipline that makes a chosen anomaly impossible to hide.

A certified normal form adds:

```text
residual obstruction
proof artifact
terminal route
```

PostgreSQL gives a stronger playground than SQL Server for structural semantics, but still has no general `CREATE ASSERTION` for arbitrary database-wide constraints. Higher normal forms require decomposition, triggers, generated structures, and certificate tables.

---

## 1. 1NF — Atomic Carrier Form

### Failed relvar

```sql
CREATE TABLE invoice_unf (
    invoice_id integer PRIMARY KEY,
    customer_id integer NOT NULL,
    item_skus text[] NOT NULL,
    item_qtys integer[] NOT NULL
);
```

PostgreSQL allows arrays. That is useful, but arrays violate 1NF when they represent multiple facts.

\[
R \hookrightarrow
D_{\text{invoice}}
\times D_{\text{customer}}
\times List(D_{\text{sku}})
\times List(D_{\text{qty}})
\]

### Refactor

```sql
CREATE TABLE invoice (
    invoice_id integer PRIMARY KEY,
    customer_id integer NOT NULL
);

CREATE TABLE invoice_line (
    invoice_id integer NOT NULL REFERENCES invoice(invoice_id),
    line_no integer NOT NULL,
    sku text NOT NULL,
    qty integer NOT NULL CHECK (qty > 0),
    PRIMARY KEY (invoice_id, line_no)
);
```

Now:

\[
InvoiceLine \hookrightarrow
D_{\text{invoice}}
\times D_{\text{line}}
\times D_{\text{sku}}
\times D_{\text{qty}}
\]

---

## 2. 2NF — No Partial-Key Dependency

### Failed relvar

```sql
CREATE TABLE enrollment_bad (
    student_id integer NOT NULL,
    course_id integer NOT NULL,
    student_name text NOT NULL,
    course_title text NOT NULL,
    grade text,
    PRIMARY KEY (student_id, course_id)
);
```

Dependencies:

\[
student\_id \to student\_name
\]

\[
course\_id \to course\_title
\]

### Refactor

```sql
CREATE TABLE student (
    student_id integer PRIMARY KEY,
    student_name text NOT NULL
);

CREATE TABLE course (
    course_id integer PRIMARY KEY,
    course_title text NOT NULL
);

CREATE TABLE enrollment (
    student_id integer NOT NULL REFERENCES student(student_id),
    course_id integer NOT NULL REFERENCES course(course_id),
    grade text,
    PRIMARY KEY (student_id, course_id)
);
```

Reconstruction:

```sql
CREATE VIEW enrollment_full AS
SELECT e.student_id, s.student_name, e.course_id, c.course_title, e.grade
FROM enrollment e
JOIN student s USING (student_id)
JOIN course c USING (course_id);
```

\[
Enrollment\_BAD \cong Student \Join Enrollment \Join Course
\]

---

## 3. 3NF — No Transitive Non-Key Dependency

### Failed relvar

```sql
CREATE TABLE employee_bad (
    employee_id integer PRIMARY KEY,
    employee_name text NOT NULL,
    department_id integer NOT NULL,
    department_name text NOT NULL
);
```

\[
employee\_id \to department\_id \to department\_name
\]

### Refactor

```sql
CREATE TABLE department (
    department_id integer PRIMARY KEY,
    department_name text NOT NULL UNIQUE
);

CREATE TABLE employee (
    employee_id integer PRIMARY KEY,
    employee_name text NOT NULL,
    department_id integer NOT NULL REFERENCES department(department_id)
);
```

---

## 4. BCNF — Every Determinant Is a Key

### Failed relvar

```sql
CREATE TABLE teaching_bad (
    student_id integer NOT NULL,
    subject text NOT NULL,
    teacher text NOT NULL,
    PRIMARY KEY (student_id, subject),
    UNIQUE (student_id, teacher)
);
```

Dependency:

\[
teacher \to subject
\]

but `teacher` is not a key of `teaching_bad`.

### Refactor

```sql
CREATE TABLE teacher_subject (
    teacher text PRIMARY KEY,
    subject text NOT NULL
);

CREATE TABLE student_teacher (
    student_id integer NOT NULL,
    teacher text NOT NULL REFERENCES teacher_subject(teacher),
    PRIMARY KEY (student_id, teacher)
);

CREATE VIEW teaching AS
SELECT st.student_id, ts.subject, st.teacher
FROM student_teacher st
JOIN teacher_subject ts USING (teacher);
```

---

## 5. 4NF — No Non-Key Multivalued Dependency

### Failed relvar

```sql
CREATE TABLE employee_skill_language_bad (
    employee_id integer NOT NULL,
    skill text NOT NULL,
    language_name text NOT NULL,
    PRIMARY KEY (employee_id, skill, language_name)
);
```

\[
employee\_id \twoheadrightarrow skill
\]

\[
employee\_id \twoheadrightarrow language
\]

### Refactor

```sql
CREATE TABLE employee_skill (
    employee_id integer NOT NULL,
    skill text NOT NULL,
    PRIMARY KEY (employee_id, skill)
);

CREATE TABLE employee_language (
    employee_id integer NOT NULL,
    language_name text NOT NULL,
    PRIMARY KEY (employee_id, language_name)
);
```

Reconstructed product, only if desired:

```sql
CREATE VIEW employee_skill_language AS
SELECT s.employee_id, s.skill, l.language_name
FROM employee_skill s
JOIN employee_language l USING (employee_id);
```

---

## 6. 5NF / PJNF — Join Dependency Discipline

### Failed relvar

```sql
CREATE TABLE spj_bad (
    supplier_id integer NOT NULL,
    part_id integer NOT NULL,
    project_id integer NOT NULL,
    PRIMARY KEY (supplier_id, part_id, project_id)
);
```

Business rule:

\[
SPJ = SP \Join SJ \Join PJ
\]

### Decompose

```sql
CREATE TABLE supplier_part (
    supplier_id integer NOT NULL,
    part_id integer NOT NULL,
    PRIMARY KEY (supplier_id, part_id)
);

CREATE TABLE supplier_project (
    supplier_id integer NOT NULL,
    project_id integer NOT NULL,
    PRIMARY KEY (supplier_id, project_id)
);

CREATE TABLE project_part (
    project_id integer NOT NULL,
    part_id integer NOT NULL,
    PRIMARY KEY (project_id, part_id)
);

CREATE VIEW supplier_part_project AS
SELECT sp.supplier_id, sp.part_id, sj.project_id
FROM supplier_part sp
JOIN supplier_project sj USING (supplier_id)
JOIN project_part pj
  ON pj.project_id = sj.project_id
 AND pj.part_id = sp.part_id;
```

### Enforcement issue

PostgreSQL cannot natively declare a general join dependency assertion:

\[
SPJ \subseteq SP \Join SJ \Join PJ
\quad\land\quad
SP \Join SJ \Join PJ \subseteq SPJ
\]

unless writes are routed through decomposed relvars and the triple view is treated as derived.

---

## 7. 6NF — Irreducible Temporal Facts

PostgreSQL gets closer than SQL Server here because range types and exclusion constraints can enforce no-overlap.

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE employee_name_6nf (
    employee_id integer NOT NULL,
    valid_period tstzrange NOT NULL,
    employee_name text NOT NULL,
    PRIMARY KEY (employee_id, valid_period),
    EXCLUDE USING gist (
        employee_id WITH =,
        valid_period WITH &&
    )
);
```

The exclusion constraint says no two rows with the same `employee_id` may have overlapping `valid_period`.

\[
R_{\text{name}} \to Employee \times Time
\]

with no overlapping sections over the same employee-time base.

Separate department fact:

```sql
CREATE TABLE employee_department_6nf (
    employee_id integer NOT NULL,
    valid_period tstzrange NOT NULL,
    department_id integer NOT NULL,
    PRIMARY KEY (employee_id, valid_period),
    EXCLUDE USING gist (
        employee_id WITH =,
        valid_period WITH &&
    )
);
```

This is a case where PostgreSQL can encode a temporal invariant more directly than SQL Server.

**Why this matters for the thesis:** the `EXCLUDE USING gist (... WITH &&)` pattern is **engine-structural** authority — the catalog understands non-overlap. SQL Server’s analogue is procedural trigger enforcement (see `2_sql_server` §7). Fewer escape hatches, less verifier burden for that slice of 6NF, more **declarative** invariant.

---

## 8. DKNF — Domain-Key Normal Form

### Use domains for true domain constraints

```sql
CREATE DOMAIN positive_quantity AS integer
CHECK (VALUE > 0);

CREATE DOMAIN discount_percent AS numeric(5,2)
CHECK (VALUE >= 0 AND VALUE <= 100);
```

### Failed relvar

```sql
CREATE TABLE order_line_dknf_bad (
    order_id integer NOT NULL,
    line_no integer NOT NULL,
    sku text NOT NULL,
    qty positive_quantity NOT NULL,
    unit_price numeric(12,2) NOT NULL CHECK (unit_price >= 0),
    discount_pct discount_percent NOT NULL,
    PRIMARY KEY (order_id, line_no)
);
```

Business rule:

```text
discount_pct > 20 only allowed for clearance SKUs
```

This is not reducible to a domain or key unless we remodel the business rule as data.

### Make policy explicit

```sql
CREATE TABLE sku (
    sku text PRIMARY KEY,
    is_clearance boolean NOT NULL
);

CREATE TABLE order_line (
    order_id integer NOT NULL,
    line_no integer NOT NULL,
    sku text NOT NULL REFERENCES sku(sku),
    qty positive_quantity NOT NULL,
    unit_price numeric(12,2) NOT NULL CHECK (unit_price >= 0),
    discount_pct discount_percent NOT NULL,
    PRIMARY KEY (order_id, line_no)
);
```

### Constraint trigger attempt

```sql
CREATE OR REPLACE FUNCTION enforce_discount_policy()
RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM new_rows n
        JOIN sku s ON s.sku = n.sku
        WHERE n.discount_pct > 20
          AND s.is_clearance = false
    ) THEN
        RAISE EXCEPTION 'DKNF violation: high discount requires clearance SKU';
    END IF;

    RETURN NULL;
END;
$$;

CREATE TRIGGER tr_order_line_discount_policy
AFTER INSERT OR UPDATE ON order_line
REFERENCING NEW TABLE AS new_rows
FOR EACH STATEMENT
EXECUTE FUNCTION enforce_discount_policy();
```

This is not pure DKNF. It is policy-certified enforcement.

---

## 9. SPJA + BQNF — Runtime Repair

Base table:

```sql
CREATE TABLE orders (
    order_id bigint PRIMARY KEY,
    customer_id bigint NOT NULL,
    amount numeric(18,2) NOT NULL CHECK (amount >= 0),
    status text NOT NULL CHECK (status IN ('open','paid','void'))
);
```

Cache:

```sql
CREATE TABLE customer_spend_cache (
    customer_id bigint PRIMARY KEY,
    order_count bigint NOT NULL,
    gross_sum numeric(18,2) NOT NULL,
    avg_order numeric(18,2) GENERATED ALWAYS AS (
        CASE WHEN order_count = 0 THEN 0
             ELSE gross_sum / order_count
        END
    ) STORED,
    last_repaired_at timestamptz NOT NULL DEFAULT now()
);
```

Query:

\[
Q =
\gamma_{customer\_id;\ COUNT(*), SUM(amount), AVG(amount)}
(\sigma_{status='paid'}(Orders))
\]

Delta equations:

\[
\Delta SUM =
1_{new.paid}new.amount - 1_{old.paid}old.amount
\]

\[
\Delta COUNT =
1_{new.paid} - 1_{old.paid}
\]

\[
AVG' = \frac{SUM+\Delta SUM}{COUNT+\Delta COUNT}
\]

### PostgreSQL trigger with transition tables

```sql
CREATE OR REPLACE FUNCTION repair_customer_spend_cache()
RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    WITH paired AS (
        SELECT
            COALESCE(n.order_id, o.order_id) AS order_id,
            COALESCE(n.customer_id, o.customer_id) AS customer_id,
            COALESCE(
                CASE WHEN n.status = 'paid' THEN n.amount ELSE 0 END, 0
            )
            -
            COALESCE(
                CASE WHEN o.status = 'paid' THEN o.amount ELSE 0 END, 0
            ) AS delta_sum,
            COALESCE(
                CASE WHEN n.status = 'paid' THEN 1 ELSE 0 END, 0
            )
            -
            COALESCE(
                CASE WHEN o.status = 'paid' THEN 1 ELSE 0 END, 0
            ) AS delta_count
        FROM old_rows o
        FULL JOIN new_rows n USING (order_id)
    ),
    grouped AS (
        SELECT customer_id,
               SUM(delta_sum) AS delta_sum,
               SUM(delta_count) AS delta_count
        FROM paired
        GROUP BY customer_id
    )
    INSERT INTO customer_spend_cache(customer_id, order_count, gross_sum)
    SELECT customer_id, delta_count, delta_sum
    FROM grouped
    ON CONFLICT (customer_id) DO UPDATE
    SET order_count = customer_spend_cache.order_count + EXCLUDED.order_count,
        gross_sum = customer_spend_cache.gross_sum + EXCLUDED.gross_sum,
        last_repaired_at = now();

    RETURN NULL;
END;
$$;

CREATE TRIGGER tr_orders_repair_customer_spend_cache
AFTER INSERT OR UPDATE OR DELETE ON orders
REFERENCING OLD TABLE AS old_rows NEW TABLE AS new_rows
FOR EACH STATEMENT
EXECUTE FUNCTION repair_customer_spend_cache();
```

### Hole

This works for SUM/COUNT/AVG only because the event evidence is sufficient.

For:

```sql
MIN(amount)
MAX(amount)
percentile_cont(0.5)
```

the event may not contain enough evidence. If the deleted row was the unique minimum, the cache cannot repair without an auxiliary ordered witness structure.

BQNF terminal route:

```text
if evidence sufficient: Repair
if changed row may be unique extremum: ConservativeInvalidate
if order-statistic state exists: Lift + Repair
```

---

## 10. Provenance Normal Form

PostgreSQL does not have native provenance semirings. Use explicit lineage tables.

```sql
CREATE TABLE query_tuple_provenance (
    query_name text NOT NULL,
    output_key jsonb NOT NULL,
    source_table text NOT NULL,
    source_pk jsonb NOT NULL,
    semiring text NOT NULL,
    weight numeric NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (query_name, output_key, source_table, source_pk)
);
```

For Boolean provenance:

\[
p_t = r_1 \wedge r_2 \wedge \cdots \wedge r_n
\]

For bag provenance:

\[
p_t \in \mathbb{N}[X]
\]

**Architectural line:** *The database stores the packet. The verifier interprets it.*

That is the modern truth-system shape: engines store evidence, lineage, embeddings, telemetry, certificates — **interpretation has escaped the engine**. This framework names that split instead of pretending `INSERT INTO provenance` equals semantic proof.

---

## 11. Boundary-Quotient Certificate Table

```sql
CREATE TABLE repair_certificate (
    certificate_id bigserial PRIMARY KEY,
    event_table text NOT NULL,
    event_pk jsonb NOT NULL,
    query_name text NOT NULL,
    obstruction_class text NOT NULL,
    terminal_route text NOT NULL CHECK (
        terminal_route IN (
            'Repair',
            'Invalidate',
            'Serialize',
            'Recompute',
            'Lift',
            'Unsupported',
            'ConservativeInvalidate',
            'Escalate'
        )
    ),
    evidence jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
```

Quotient interpretation:

\[
Q^1 = C^1 / \operatorname{im}(d_0)
\]

\[
[\omega(e)] = 0 \Rightarrow Repair
\]

\[
[\omega(e)] \ne 0 \Rightarrow Terminal
\]

SQL stores the finite witness. The quotient engine may live in application code.

---

## 12. PostgreSQL capability matrix

**Engine-relative summary.** Compare row-by-row with `2_sql_server` §11 — differences in **Native?** are expressivity gradient data, not marketing.

| Form | Native? | Attempt |
|---|---:|---|
| 1NF | partial | avoid arrays/jsonb for hidden facts; use child tables |
| 2NF/3NF/BCNF | design-time | decompose plus keys/FKs |
| 4NF | design-time | decompose independent MVDs |
| 5NF | weak | decompose and expose join view; no general assertion |
| 6NF | stronger than SQL Server | range types + exclusion constraints for temporal no-overlap |
| DKNF | partial | domains + keys + triggers for non-domain-key policies |
| SPJ/SPJA | yes | views/materialized views/manual refresh |
| Delta NF | partial | transition-table triggers |
| BQNF | no native quotient engine | certificate table + trigger/application verifier |
| GTMUR / CpNF | no native $\chi_F$ | `transport_certificate` + `loss_ledger` + compile verifier |
| Provenance NF | no native semiring | explicit provenance tables (verifier interprets) |
| Authority NF | no | external verifier |

---

## 13. Hard truth — what PostgreSQL still cannot know

PostgreSQL can encode more structure than SQL Server, especially temporal non-overlap through exclusion constraints. But it still cannot make arbitrary certified normal forms first-class.

### 13.1 Structural layer (engine knows)

```text
row, type, domain, key, foreign key, unique, check
partial index, exclusion constraint, range type
trigger, transition table, transaction, deferrable constraint
```

### 13.2 Certified layer (hosted, not native)

```text
quotient obstruction Q^1
repair soundness (omega = d_0 alpha)
loss ledger / erased distinctions
semantic rewrite witness chi_F
composed certificate chains
```

### 13.3 Authority layer (external)

```text
semantic equivalence of rewrites
approximation legitimacy (sketch vs billing)
transport trust / policy lineage
observer authority (what O may act on)
authorization (certified != permitted)
```

### 13.4 Expressivity gradient vs SQL Server (selected)

| Invariant slice | SQL Server | PostgreSQL |
|---|---|---|
| temporal no-overlap | trigger-certified | **EXCLUDE** structural |
| true domains | UDT + CHECK approximate | **CREATE DOMAIN** |
| CDC before/after as relations | inserted/deleted tables | **transition tables** |
| BQNF quotient $Q^1$ | external verifier | external verifier |
| GTMUR transport | external verifier | external verifier |

**Takeaway:** PostgreSQL delays the verifier cliff for **structural** NFs; it does not remove the cliff for **repair** or **authority** NFs.

---

## 14. Integrated demonstrator (next step — not more papers)

One end-to-end demo matters more than additional ontology:

| Step | Artifact |
|---|---|
| 1 | PostgreSQL source tables + materialized/cache relvar |
| 2 | CDC stream (logical decoding or trigger transition tables) |
| 3 | BQNF repair decisions (SUM/COUNT/AVG lane) |
| 4 | `repair_certificate` rows with `evidence` jsonb |
| 5 | `loss_ledger` on compile path (SQL → SPJA → boundary shape) |
| 6 | `ObserverBoundary` metadata (preserve vs repair) |
| 7 | GTMUR transport chain with composed ledgers |
| 8 | Verifier **refusal** cases (negative tests) |

**Negative examples the demo must show:**

| Failure | Expected terminal / refusal |
|---|---|
| stale cache after partial CDC | `ConservativeInvalidate` — not silent patch |
| sketch dashboard used for billing | `AuthorityLaundering` blocked by policy verifier |
| denorm drops constraint silently | `SilentMutation` |
| embedding treated as authoritative SQL | `LossLedgerMissing` / `TransportViolation` |
| agent on stale retrieval | `TransportViolation` |
| transport without ledger | verifier reject |

Framework strength is measured by **caught real failure modes** (`1a` §9, `1b` §9).

---

## 15. References (in-repo)

* `2_sql_server_certified_normal_forms_attempts.md` — expressivity gradient baseline  
* `0_relvar_relation_table_and_boundary_relvar.md` — observer / boundary relvars  
* `1a_bqnf_incremental_repair.md` — BQNF semantics  
* `1b_gtmur_representation_transport.md` — GTMUR, CpNF  
* `1_normal_forms.md` — epistemic normal forms (§7)  
