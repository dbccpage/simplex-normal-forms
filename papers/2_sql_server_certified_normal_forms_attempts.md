# SQL Server Stack: Certified Normal Forms by Attempt

**Status:** engine-relative implementation notes (theory × industrial substrate)  
**Target:** SQL Server / Azure SQL family  
**Purpose:** force certified normal forms to collide with a real engine — failed relvars, refactors, explicit holes, certificate tables, external verifiers.

**Theory stack (read in order):**

| Document | Role |
|---|---|
| `0_relvar_relation_table_and_boundary_relvar.md` | base ontology — what is being normalized |
| `1a_bqnf_incremental_repair.md` | BQNF semantics |
| `1b_gtmur_representation_transport.md` | transport certificates, loss ledgers |
| `3_postgresql_certified_normal_forms_attempts.md` | parallel substrate (compare matrices) |

---

## 0. Working definition

### 0.1 Engine-relative normal forms

A normal form is not only an abstract discipline. On this project it is always **engine-relative**:

\[
\text{NF} = (\text{invariant},\ \text{substrate},\ \text{attempt})
\]

* **invariant** — anomaly class made unrepresentable or detectable  
* **substrate** — SQL Server (optimizer, triggers, CDC, NULL, isolation, temporal limits, …)  
* **attempt** — how close the substrate can get (native, partial, certificate + verifier)

Classical literature often treats the logical model and the engine as separable. In practice, what you can *prevent* depends on triggers, CDC granularity, assertion support, and whether a quotient engine exists at all.

**Framing that matters professionally:**

> SQL Server does not “support BQNF.”  
> SQL Server can **host BQNF attempts** (certificate tables + repair procedures + external verifier).

Same for GTMUR transport: `dbo.RepairCertificate` stores witnesses; semantics live in procedures or application code.

### 0.2 The recurring pattern (intellectual honesty)

Every section in this file follows:

```text
desired invariant
  → SQL Server cannot express it natively (or only partially)
  → approximation via triggers / procedures / CDC / certificate tables / external verifier
```

This is a **certified attempt**, not first-class relational purity. Triggers do not become category theory; they become hosts for finite-evidence checks.

### 0.3 Enforcement, certification, authorization

Modern systems conflate these. This stack separates them:

| Concept | Meaning | SQL Server role |
|---|---|---|
| **Enforcement** | engine blocks invalid *states* (constraints, triggers) | `CHECK`, `FK`, `UNIQUE`, DML triggers |
| **Certification** | verifier attests validity / repairability / transport | `RepairCertificate`, procedures, app verifier |
| **Authorization** | policy permits *use* of certified data | external IAM / policy engine (not T-SQL alone) |

> A certificate table without a verifier is just another table.

Certification without enforcement can still allow bad writes; enforcement without certification cannot prove repair soundness. Neither implies authorization to act (billing, safety-critical automation).

### 0.4 Classical anomalies → modern anomalies

| Classical (state at rest) | Engine-relative extension (motion / observers) |
|---|---|
| dependency anomaly | **repair anomaly** — cannot certify $\omega = d_0\alpha$ |
| redundancy | **observer inconsistency** — layers disagree under $\mathcal O$ |
| update anomaly | **uncertifiable transition** — CDC/evidence insufficient |
| insertion anomaly | **unsupported authority creation** — no ledger / witness |
| deletion anomaly | **irreversible authority loss** — no rollback / provenance |

Shape NFs (§1–8) address the left column. BQNF + certificates (§9–10) address the right.

### 0.5 Verifier-extended databases

SQL Server is no longer the sole semantic authority in this model. Authority is distributed across:

```text
engine (rows, keys, transactions)
  + triggers / procedures
  + CDC / change tracking
  + certificate / loss-ledger tables
  + external verifier (quotient, transport, policy)
```

That is already true in enterprises; this framework makes it explicit — a **semantic superstructure** above the engine for data mesh, federated analytics, cache hierarchies, and agent orchestration.

A normal form is a decidable representation discipline that makes a chosen anomaly impossible to hide.

A certified normal form adds:

```text
residual obstruction
proof artifact
terminal route
```

SQL Server can enforce many shape constraints, but not arbitrary database-wide assertions. In practice the stack is:

```text
keys
foreign keys
unique constraints
filtered unique indexes
computed columns
indexed views
triggers
stored procedures
CDC/change tracking
audit/certificate tables
external verifier
```

---

## 1. 1NF — Atomic Carrier Form

### Failed relvar

```sql
CREATE TABLE dbo.Invoice_UNF (
    invoice_id int PRIMARY KEY,
    customer_id int NOT NULL,
    item_skus nvarchar(max) NOT NULL,   -- 'A12,B34,C77'
    item_qtys nvarchar(max) NOT NULL    -- '1,2,1'
);
```

This is not a relation over atomic domains.

\[
R \not\hookrightarrow
D_{\text{invoice}}
\times D_{\text{customer}}
\times D_{\text{sku}}
\times D_{\text{qty}}
\]

It is closer to:

\[
R \hookrightarrow
D_{\text{invoice}}
\times D_{\text{customer}}
\times List(D_{\text{sku}})
\times List(D_{\text{qty}})
\]

### Refactor

```sql
CREATE TABLE dbo.Invoice (
    invoice_id int PRIMARY KEY,
    customer_id int NOT NULL
);

CREATE TABLE dbo.InvoiceLine (
    invoice_id int NOT NULL,
    line_no int NOT NULL,
    sku nvarchar(40) NOT NULL,
    qty int NOT NULL CHECK (qty > 0),
    CONSTRAINT PK_InvoiceLine PRIMARY KEY (invoice_id, line_no),
    CONSTRAINT FK_InvoiceLine_Invoice
        FOREIGN KEY (invoice_id) REFERENCES dbo.Invoice(invoice_id)
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
CREATE TABLE dbo.Enrollment_BAD (
    student_id int NOT NULL,
    course_id int NOT NULL,
    student_name nvarchar(100) NOT NULL,
    course_title nvarchar(100) NOT NULL,
    grade char(2) NULL,
    CONSTRAINT PK_Enrollment_BAD PRIMARY KEY (student_id, course_id)
);
```

Dependencies:

\[
(student\_id, course\_id) \to grade
\]

but also:

\[
student\_id \to student\_name
\]

\[
course\_id \to course\_title
\]

The non-key attributes depend on only part of the composite key.

### Refactor

```sql
CREATE TABLE dbo.Student (
    student_id int PRIMARY KEY,
    student_name nvarchar(100) NOT NULL
);

CREATE TABLE dbo.Course (
    course_id int PRIMARY KEY,
    course_title nvarchar(100) NOT NULL
);

CREATE TABLE dbo.Enrollment (
    student_id int NOT NULL,
    course_id int NOT NULL,
    grade char(2) NULL,
    CONSTRAINT PK_Enrollment PRIMARY KEY (student_id, course_id),
    CONSTRAINT FK_Enrollment_Student FOREIGN KEY (student_id)
        REFERENCES dbo.Student(student_id),
    CONSTRAINT FK_Enrollment_Course FOREIGN KEY (course_id)
        REFERENCES dbo.Course(course_id)
);
```

Reconstruction:

\[
Enrollment\_BAD \cong Student \Join Enrollment \Join Course
\]

provided the stated dependencies were true.

---

## 3. 3NF — No Transitive Non-Key Dependency

### Failed relvar

```sql
CREATE TABLE dbo.Employee_BAD (
    employee_id int PRIMARY KEY,
    department_id int NOT NULL,
    department_name nvarchar(100) NOT NULL,
    employee_name nvarchar(100) NOT NULL
);
```

Dependencies:

\[
employee\_id \to department\_id
\]

\[
department\_id \to department\_name
\]

So:

\[
employee\_id \to department\_name
\]

is transitive through a non-key determinant.

### Refactor

```sql
CREATE TABLE dbo.Department (
    department_id int PRIMARY KEY,
    department_name nvarchar(100) NOT NULL UNIQUE
);

CREATE TABLE dbo.Employee (
    employee_id int PRIMARY KEY,
    employee_name nvarchar(100) NOT NULL,
    department_id int NOT NULL,
    CONSTRAINT FK_Employee_Department FOREIGN KEY (department_id)
        REFERENCES dbo.Department(department_id)
);
```

\[
Employee\_BAD \cong Employee \Join Department
\]

---

## 4. BCNF — Every Determinant Is a Key

### Failed relvar

Assume each teacher teaches exactly one subject, but a subject may have many teachers.

```sql
CREATE TABLE dbo.Teaching_BAD (
    student_id int NOT NULL,
    subject nvarchar(100) NOT NULL,
    teacher nvarchar(100) NOT NULL,
    CONSTRAINT PK_Teaching_BAD PRIMARY KEY (student_id, subject),
    CONSTRAINT UQ_Teaching_BAD_StudentTeacher UNIQUE (student_id, teacher)
);
```

Dependency:

\[
teacher \to subject
\]

but `teacher` is not a key of `Teaching_BAD`.

### Refactor

```sql
CREATE TABLE dbo.TeacherSubject (
    teacher nvarchar(100) PRIMARY KEY,
    subject nvarchar(100) NOT NULL
);

CREATE TABLE dbo.StudentTeacher (
    student_id int NOT NULL,
    teacher nvarchar(100) NOT NULL,
    CONSTRAINT PK_StudentTeacher PRIMARY KEY (student_id, teacher),
    CONSTRAINT FK_StudentTeacher_TeacherSubject FOREIGN KEY (teacher)
        REFERENCES dbo.TeacherSubject(teacher)
);
```

View reconstruction:

```sql
CREATE VIEW dbo.Teaching AS
SELECT st.student_id, ts.subject, st.teacher
FROM dbo.StudentTeacher AS st
JOIN dbo.TeacherSubject AS ts
  ON ts.teacher = st.teacher;
```

\[
Teaching\_BAD \cong StudentTeacher \Join TeacherSubject
\]

---

## 5. 4NF — No Non-Key Multivalued Dependency

### Failed relvar

One employee can have many skills and many languages independently.

```sql
CREATE TABLE dbo.EmployeeSkillLanguage_BAD (
    employee_id int NOT NULL,
    skill nvarchar(100) NOT NULL,
    language_name nvarchar(100) NOT NULL,
    CONSTRAINT PK_ESL_BAD PRIMARY KEY (employee_id, skill, language_name)
);
```

Multivalued dependencies:

\[
employee\_id \twoheadrightarrow skill
\]

\[
employee\_id \twoheadrightarrow language
\]

The independent facts are multiplied.

### Refactor

```sql
CREATE TABLE dbo.EmployeeSkill (
    employee_id int NOT NULL,
    skill nvarchar(100) NOT NULL,
    CONSTRAINT PK_EmployeeSkill PRIMARY KEY (employee_id, skill)
);

CREATE TABLE dbo.EmployeeLanguage (
    employee_id int NOT NULL,
    language_name nvarchar(100) NOT NULL,
    CONSTRAINT PK_EmployeeLanguage PRIMARY KEY (employee_id, language_name)
);
```

The old relvar was the artificial product:

\[
EmployeeSkillLanguage = EmployeeSkill \Join EmployeeLanguage
\]

SQL Server cannot infer independence of `skill` and `language_name`; the designer declares the MVD by decomposition.

---

## 6. 5NF / PJNF — Join Dependency Discipline

### Failed relvar

Supplier-Part-Project triples:

```sql
CREATE TABLE dbo.SPJ_BAD (
    supplier_id int NOT NULL,
    part_id int NOT NULL,
    project_id int NOT NULL,
    CONSTRAINT PK_SPJ_BAD PRIMARY KEY (supplier_id, part_id, project_id)
);
```

Suppose the business rule is:

\[
SPJ = SP \Join SJ \Join PJ
\]

where all three pairwise relationships must hold.

SQL Server has no general `CREATE ASSERTION` for:

\[
SPJ \subseteq SP \Join SJ \Join PJ
\quad\land\quad
SP \Join SJ \Join PJ \subseteq SPJ
\]

### Refactor

```sql
CREATE TABLE dbo.SupplierPart (
    supplier_id int NOT NULL,
    part_id int NOT NULL,
    CONSTRAINT PK_SupplierPart PRIMARY KEY (supplier_id, part_id)
);

CREATE TABLE dbo.SupplierProject (
    supplier_id int NOT NULL,
    project_id int NOT NULL,
    CONSTRAINT PK_SupplierProject PRIMARY KEY (supplier_id, project_id)
);

CREATE TABLE dbo.ProjectPart (
    project_id int NOT NULL,
    part_id int NOT NULL,
    CONSTRAINT PK_ProjectPart PRIMARY KEY (project_id, part_id)
);
```

Derived view:

```sql
CREATE VIEW dbo.SupplierPartProject AS
SELECT sp.supplier_id, sp.part_id, sj.project_id
FROM dbo.SupplierPart AS sp
JOIN dbo.SupplierProject AS sj
  ON sj.supplier_id = sp.supplier_id
JOIN dbo.ProjectPart AS pj
  ON pj.project_id = sj.project_id
 AND pj.part_id = sp.part_id;
```

This implements the decomposition. It does not make arbitrary JDs first-class.

---

## 7. 6NF — Irreducible Temporal Fact Form

6NF decomposes into key-plus-one-fact relvars, often useful for temporal facts.

```sql
CREATE TABLE dbo.EmployeeName_6NF (
    employee_id int NOT NULL,
    valid_from datetime2 NOT NULL,
    valid_to datetime2 NOT NULL,
    employee_name nvarchar(100) NOT NULL,
    CONSTRAINT PK_EmployeeName_6NF PRIMARY KEY (employee_id, valid_from),
    CONSTRAINT CK_EmployeeName_Period CHECK (valid_from < valid_to)
);

CREATE TABLE dbo.EmployeeDepartment_6NF (
    employee_id int NOT NULL,
    valid_from datetime2 NOT NULL,
    valid_to datetime2 NOT NULL,
    department_id int NOT NULL,
    CONSTRAINT PK_EmployeeDepartment_6NF PRIMARY KEY (employee_id, valid_from),
    CONSTRAINT CK_EmployeeDepartment_Period CHECK (valid_from < valid_to)
);
```

### SQL Server hole

SQL Server can check:

\[
valid\_from < valid\_to
\]

but cannot natively enforce this multi-row assertion with a simple constraint:

\[
\neg \exists a,b:
a.employee\_id=b.employee\_id
\land a.period \cap b.period \neq \emptyset
\]

### Trigger attempt

```sql
CREATE OR ALTER TRIGGER dbo.TR_EmployeeName_NoOverlap
ON dbo.EmployeeName_6NF
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS (
        SELECT 1
        FROM dbo.EmployeeName_6NF AS a
        JOIN dbo.EmployeeName_6NF AS b
          ON a.employee_id = b.employee_id
         AND a.valid_from < b.valid_to
         AND b.valid_from < a.valid_to
         AND NOT (
             a.employee_id = b.employee_id
             AND a.valid_from = b.valid_from
         )
    )
    BEGIN
        THROW 51000, '6NF temporal violation: overlapping employee-name periods.', 1;
    END
END;
```

This is not pure declarative 6NF enforcement. It is trigger-certified enforcement.

---

## 8. DKNF — Domain-Key Normal Form

DKNF says every constraint follows from domains and keys.

### Failed relvar

```sql
CREATE TABLE dbo.OrderLine_DKNF_BAD (
    order_id int NOT NULL,
    line_no int NOT NULL,
    sku nvarchar(40) NOT NULL,
    qty int NOT NULL CHECK (qty > 0),
    unit_price decimal(12,2) NOT NULL CHECK (unit_price >= 0),
    discount_pct decimal(5,2) NOT NULL CHECK (discount_pct >= 0 AND discount_pct <= 100),
    CONSTRAINT PK_OrderLine_DKNF_BAD PRIMARY KEY (order_id, line_no)
);
```

Business rule:

```text
discount_pct > 20 only allowed for clearance SKUs
```

This is not a domain rule and not a key rule. It references classification data.

### Make the policy explicit

```sql
CREATE TABLE dbo.Sku (
    sku nvarchar(40) PRIMARY KEY,
    is_clearance bit NOT NULL
);

CREATE TABLE dbo.OrderLine (
    order_id int NOT NULL,
    line_no int NOT NULL,
    sku nvarchar(40) NOT NULL,
    qty int NOT NULL CHECK (qty > 0),
    unit_price decimal(12,2) NOT NULL CHECK (unit_price >= 0),
    discount_pct decimal(5,2) NOT NULL CHECK (discount_pct >= 0 AND discount_pct <= 100),
    CONSTRAINT PK_OrderLine PRIMARY KEY (order_id, line_no),
    CONSTRAINT FK_OrderLine_Sku FOREIGN KEY (sku) REFERENCES dbo.Sku(sku)
);
```

But SQL Server cannot express:

\[
discount > 20 \Rightarrow Sku.is\_clearance = 1
\]

as a declarative `CHECK`, because it requires another table.

### Trigger attempt

```sql
CREATE OR ALTER TRIGGER dbo.TR_OrderLine_DiscountPolicy
ON dbo.OrderLine
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS (
        SELECT 1
        FROM inserted AS i
        JOIN dbo.Sku AS s ON s.sku = i.sku
        WHERE i.discount_pct > 20
          AND s.is_clearance = 0
    )
    BEGIN
        THROW 51001, 'DKNF violation: high discount requires clearance SKU.', 1;
    END
END;
```

Verdict: trigger-enforced policy is not pure DKNF. It is certified policy enforcement.

---

## 9. SPJA + BQNF — Runtime Repair

Base table:

```sql
CREATE TABLE dbo.Orders (
    order_id bigint PRIMARY KEY,
    customer_id bigint NOT NULL,
    amount decimal(18,2) NOT NULL CHECK (amount >= 0),
    status nvarchar(20) NOT NULL CHECK (status IN ('open','paid','void'))
);
```

Cache table:

```sql
CREATE TABLE dbo.CustomerSpendCache (
    customer_id bigint PRIMARY KEY,
    order_count bigint NOT NULL,
    gross_sum decimal(18,2) NOT NULL,
    avg_order AS (
        CASE WHEN order_count = 0
             THEN CONVERT(decimal(18,2), 0)
             ELSE gross_sum / NULLIF(CONVERT(decimal(18,2), order_count), 0)
        END
    ) PERSISTED,
    last_repaired_at datetime2 NOT NULL DEFAULT sysdatetime()
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
\mathbf{1}_{new.paid}new.amount
-
\mathbf{1}_{old.paid}old.amount
\]

\[
\Delta COUNT =
\mathbf{1}_{new.paid}
-
\mathbf{1}_{old.paid}
\]

\[
AVG' =
\frac{SUM+\Delta SUM}{COUNT+\Delta COUNT}
\]

### Trigger repair attempt

```sql
CREATE OR ALTER TRIGGER dbo.TR_Orders_CustomerSpendCache
ON dbo.Orders
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;

    WITH paired AS (
        SELECT
            COALESCE(i.order_id, d.order_id) AS order_id,
            COALESCE(i.customer_id, d.customer_id) AS customer_id,
            CAST(
                CASE WHEN i.status = 'paid' THEN i.amount ELSE 0 END
                -
                CASE WHEN d.status = 'paid' THEN d.amount ELSE 0 END
                AS decimal(18,2)
            ) AS delta_sum,
            CAST(
                CASE WHEN i.status = 'paid' THEN 1 ELSE 0 END
                -
                CASE WHEN d.status = 'paid' THEN 1 ELSE 0 END
                AS bigint
            ) AS delta_count
        FROM inserted AS i
        FULL OUTER JOIN deleted AS d
          ON i.order_id = d.order_id
    ),
    grouped AS (
        SELECT customer_id,
               SUM(delta_sum) AS delta_sum,
               SUM(delta_count) AS delta_count
        FROM paired
        GROUP BY customer_id
    )
    MERGE dbo.CustomerSpendCache AS tgt
    USING grouped AS src
       ON tgt.customer_id = src.customer_id
    WHEN MATCHED THEN
        UPDATE SET
            order_count = tgt.order_count + src.delta_count,
            gross_sum = tgt.gross_sum + src.delta_sum,
            last_repaired_at = sysdatetime()
    WHEN NOT MATCHED THEN
        INSERT (customer_id, order_count, gross_sum)
        VALUES (src.customer_id, src.delta_count, src.delta_sum);
END;
```

### Hole

This works only for linear aggregates where the event carries sufficient evidence.

For:

```sql
MIN(amount)
MAX(amount)
PERCENTILE_CONT(...)
```

the write event may not prove repairability. If the deleted row was the unique minimum, the cache cannot repair without auxiliary state.

Terminal route:

```text
[omega] = 0       -> Repair
[omega] != 0      -> Invalidate/Recompute/Lift
missing evidence  -> ConservativeInvalidate
```

---

## 10. Certificate table

```sql
CREATE TABLE dbo.RepairCertificate (
    certificate_id bigint IDENTITY PRIMARY KEY,
    event_table sysname NOT NULL,
    event_pk nvarchar(200) NOT NULL,
    query_name sysname NOT NULL,
    obstruction_class nvarchar(100) NOT NULL,
    terminal_route nvarchar(40) NOT NULL CHECK (
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
    evidence_json nvarchar(max) NOT NULL,
    created_at datetime2 NOT NULL DEFAULT sysdatetime()
);
```

SQL Server stores the witness. The quotient engine lives in procedures or application code.

---

## 11. SQL Server capability matrix

**Engine-relative summary.** “Native?” means declaratively enforceable inside T-SQL/DDL without an external semantic verifier. “Attempt” is the certified hosting pattern when native is insufficient.

| Form | Native? | Attempt |
|---|---:|---|
| 1NF | partial | avoid CSV/JSON/list columns; use child tables |
| 2NF/3NF/BCNF | design-time | decompose plus keys/FKs |
| 4NF | design-time | decompose MVDs into separate relvars |
| 5NF | weak | decompose; use views/procedures/triggers |
| 6NF | partial | temporal tables help history; no native no-overlap assertion |
| DKNF | mostly no | domains/checks/keys plus triggers for non-domain-key rules |
| SPJ/SPJA | yes as query shape | views/indexed views under restrictions |
| Delta NF | no general native proof | triggers/CDC/manual delta programs |
| BQNF | no native quotient engine | certificate tables + repair procedures |
| GTMUR / CpNF | no native transport witness | `transport_certificate` + loss ledger + compile-time verifier (see Paper B) |
| Provenance NF | no native semiring | lineage/audit tables |
| Authority NF | no | external verifier |

---

## 12. Hard truth — what SQL engines cannot know

SQL Server can host certified normal-form **attempts**. It cannot make arbitrary certified normal forms **first-class**.

### 12.1 What the engine knows

```text
row
key
foreign key
unique
check
index
trigger
transaction
isolation level
```

### 12.2 What the engine does not know (verifier territory)

```text
semantic equivalence of rewrites
observer authority (what O may distinguish)
quotient obstruction [omega] in Q^1
repair soundness (omega = d_0 alpha)
loss ledger / erased distinctions
approximation legitimacy (sketch vs exact)
transport witness chi_F (updates commute with F)
join dependency (general case)
authority descent / policy lineage
```

A future paper title that captures this file’s convergence:

> **What SQL Engines Cannot Know**

### 12.3 Recognizable architecture (SQL Server slice)

| Layer | Responsibility on SQL Server |
|---|---|
| Classical relational theory | valid **states** (decomposition, keys) |
| SQL Server engine | physical **enforcement** |
| BQNF (§9) | **repair** semantics on boundary relvars |
| GTMUR / CpNF | **compilation** between regimes (cert + ledger) |
| Observer boundaries | visibility / preserve vs repair (views + metadata) |
| Certificates / ledgers | explicit **evidence** rows |
| External verifier | **certification** adjudication |
| GTTC (Paper C) | **approximation** authority via finite shadows |

Coherent with `0_relvar` Part XII; not complete until executable.

### 12.4 Hole sections are features

Sections marked **Hole** (e.g. MIN/MAX without auxiliary state, no arbitrary assertions, no native quotient) are deliberate. They show **exact limits**, not marketing capabilities. Real systems papers state what fails.

### 12.5 Relational expressivity gradient (PostgreSQL contrast)

This file is the **lower structural tier** in a pairwise comparison. PostgreSQL (`3_postgresql` §0.5, §13.4) encodes more invariants declaratively (domains, `EXCLUDE`, ranges, transition tables) before requiring external verifiers. **Both engines** still host BQNF/GTMUR/authority semantics outside the catalog. The gradient is about **how far engine semantics reach**, not which engine “wins.”

---

## 13. Implementation north star (beyond more ontology)

Theory at this depth gains value from **executable evidence**, not additional vocabulary.

| Deliverable | Purpose |
|---|---|
| Minimal verifier (T-SQL + app) | accept/reject BQNF + transport chains |
| Generated certificates | real rows in `RepairCertificate` / transport tables |
| Negative tests | missing CDC columns → `ConservativeInvalidate`; silent denorm → `SilentMutation` |
| Repair vs recompute benchmark | prove cost of certified repair on SPJA cache |
| Stale-cache prevention demo | partial CDC cannot patch aggregate |
| Approximation ledger example | sketch dashboard cannot bill without policy |

That separates “interesting conceptual framework” from “new systems methodology.” Priority: ship the operational subset (SPJA + CDC + certificates + verifier) before extending epistemic normal forms in the atlas.

---

## 14. References (in-repo)

* `0_relvar_relation_table_and_boundary_relvar.md` — relvar / boundary / observer ontology  
* `1a_bqnf_incremental_repair.md` — BQNF + failure pathology  
* `1b_gtmur_representation_transport.md` — GTMUR, CpNF, failure pathology  
* `3_postgresql_certified_normal_forms_attempts.md` — PostgreSQL capability matrix  
