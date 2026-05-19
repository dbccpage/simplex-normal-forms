# Relvar, Relation, Table, Record, Field — and a Different Kind of Relvar

Status: Archived source / Definitional provenance.

> Absorbed base ontology copy from
> `omega_engine/research/in_work/simplex_cosmos_papers/SMPLX_009_Simplex Databases/crap/0_relvar_relation_table_and_boundary_relvar.md`.
> The source folder was integrated into the root scaffold and removed.
>
> Non-normative archive: current definitions are controlled by `book/00_preface.md` through `book/08_open_problems.md`, `glossary/`, `spec/`, and `contracts/`. If this appendix conflicts with the cleaned taxonomy, the cleaned taxonomy wins.

**Status:** base ontology / terminology anchor for SMPLX-009  
**Tone:** deliberately strict  
**Purpose:** answer *what exactly is being normalized, repaired, transported, or authorized?* before quotient repair, transport certificates, or epistemic normal forms appear.

**Companion papers (built on this vocabulary):**

| Document | Object in focus |
|---|---|
| `1_normal_forms.md` | taxonomy atlas |
| `1a_bqnf_incremental_repair.md` | certified **transition** on a boundary relvar |
| `1b_gtmur_representation_transport.md` | certified **compilation** between relvar regimes |
| `1c_*` (planned) | finite-shadow **authorization** over approximations |

---

## 0. Why this file exists

### 0.1 The anchor question

Every later paper risks floating abstractions unless this is settled first:

> **What is the thing being normalized, repaired, transported, or authorized?**

Answer, in order of introduction:

| Layer | Thing | Kind |
|---|---|---|
| Classical | **relvar** $\mathcal R$ | variable ranging over **relation values** $R_t$ |
| Motion | **boundary relvar** $\mathcal B$ | relvar + admissible **transitions** and repair semantics |
| Observation | **observer relvar** $\mathcal O$ | relvar + declared **visibility** / indistinguishability |
| Evidence | **certificates & ledgers** | proof artifacts about transitions and compilations |
| Governance | **verifier** | separates certified from **authorized** |

Without this file, BQNF and GTMUR are syntax without a subject. With it, the stack has a base ontology.

### 0.2 Conservative extension (why the order matters)

This note does **not** open with quotient spaces, transport morphisms, epistemic authority, or AI orchestration. It opens with:

```text
domain → attribute → tuple → relation → relvar
```

Only after that vocabulary is fixed do we extend to boundary relvars and observer relvars. That order earns trust from relational readers: Codd is continued, not discarded.

Database people often say:

```text
table
row
column
field
record
relation
```

as if those words were interchangeable.

They are not.

That sloppiness matters. Once the terminology is loose, every later idea becomes mush: normal forms, keys, dependency theory, SQL implementation, change repair, cache invalidation, provenance, and authority transport.

So this file begins in the older, stricter relational style: relation, tuple, attribute, domain, relvar. Then it explains why SQL tables, rows, columns, records, and fields are implementation-adjacent terms, not exact logical equivalents.

After that, we introduce a different kind of relvar: not a classical relvar that only ranges over relation values at rest, but a **certified boundary relvar** whose admissible changes are part of its declared type.

This is not a rejection of Codd. It is a continuation of the same discipline applied to data in motion.

---

# Part I — The strict vocabulary

## 1. Domain

A **domain** is a set of permitted values.

Examples:

```text
StudentId
CourseId
MoneyAmount
EmailAddress
Timestamp
```

Mathematically:

\[
D = \{v \mid v \text{ satisfies the domain predicate}\}
\]

A domain is not merely a SQL type.

For example:

```sql
email varchar(320)
```

is not really an email domain. It is a character string column with a length limit.

A better approximation is:

```sql
CREATE DOMAIN email_address AS text
CHECK (
    VALUE ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'
);
```

PostgreSQL supports `CREATE DOMAIN`. SQL Server does not support domains in the same relational sense; user-defined data types and `CHECK` constraints can approximate some of the behavior, but they do not give a full domain theory.

Curmudgeon rule:

> A data type is storage machinery. A domain is a semantic contract.

---

## 2. Attribute

An **attribute** is a named role whose values come from a domain.

Example:

```text
StudentId : StudentIdDomain
StudentName : NameDomain
BirthDate : DateDomain
```

An attribute is not just “a column.”

A column is a common physical or SQL representation of an attribute. But the attribute is part of the logical heading of a relation.

A relation heading is a set of attributes:

\[
H = \{A_1:D_1,\dots,A_n:D_n\}
\]

Order does not matter.

That is already different from most SQL displays, where columns appear left-to-right.

Curmudgeon rule:

> An attribute is logical. A column is representational.

---

## 3. Tuple

A **tuple** is a set of attribute-value pairs, one value for each attribute in a heading.

For heading:

\[
H = \{StudentId, CourseId, Grade\}
\]

a tuple may be:

\[
t =
\{
StudentId \mapsto 42,
CourseId \mapsto 1001,
Grade \mapsto 'A'
\}
\]

A tuple is not a row.

A row is an implementation/display object. It often has an order, can contain `NULL`, may be duplicated in SQL query results, and is processed by the DBMS in ways that are not identical to the mathematical tuple.

A tuple has:

```text
no duplicate identity
no physical position
no hidden row number
no order of attributes
```

Curmudgeon rule:

> A tuple is a fact-shaped value. A row is how a system happens to show or store something.

---

## 4. Relation

A **relation** is a set of tuples with the same heading.

\[
R \subseteq \prod_{A_i \in H} D_i
\]

or, more precisely:

\[
R = (H, B)
\]

where:

```text
H = heading
B = body, a set of tuples over H
```

Because the body is a set:

```text
no duplicate tuples
no tuple order
no attribute order
```

Example relation value:

```text
ENROLLMENT
Heading:
  StudentId : StudentId
  CourseId  : CourseId
  Grade     : Grade

Body:
  {StudentId=1, CourseId=10, Grade='A'}
  {StudentId=2, CourseId=10, Grade='B'}
```

This relation is a **value**.

That point is crucial.

A relation is like the integer value `7`. It is not a storage location. It does not change. If something “changes,” then some variable now holds a different relation value.

Curmudgeon rule:

> A relation does not update. A relvar is assigned a new relation value.

**Structural hinge.** The entire later framework depends on separating:

```text
value        (relation at an instant)
variable     (relvar — name for a sequence of values)
transition   (event e : R_t → R_{t+1})
observer     (projection O — what may be distinguished)
authority    (verifier — what may be acted upon)
```

Most systems discourse collapses these. This project does not.

---

## 5. Relvar

A **relvar** is a relation variable.

It is a named variable whose possible values are relations of a declared type.

```text
Enrollment
```

is a relvar if it can hold different relation values over time, all with the same heading:

\[
Enrollment_t \subseteq StudentId \times CourseId \times Grade
\]

At time \(t_0\):

\[
Enrollment := R_0
\]

At time \(t_1\):

\[
Enrollment := R_1
\]

The relvar persists as a variable. Its value changes.

A base relvar is stored directly. A derived relvar is defined by an expression over other relvars.

Example derived relvar:

\[
CurrentPaidOrders =
\sigma_{status='paid'}(Orders)
\]

SQL approximation:

```sql
CREATE VIEW CurrentPaidOrders AS
SELECT order_id, customer_id, amount
FROM Orders
WHERE status = 'paid';
```

Curmudgeon rule:

> The table name in SQL is usually trying to be a relvar name. It only partly succeeds.

---

## 6. Table

A **table** is a representation.

In SQL practice, a table often acts like a relvar, but it is not identical to a relation or relvar.

Reasons:

1. SQL tables may allow duplicate rows unless constrained.
2. SQL has `NULL`; the classical relational model does not treat null as an ordinary domain value.
3. SQL columns are ordered in metadata and output.
4. SQL result sets may be bags, not sets.
5. SQL tables may contain implementation artifacts: identity columns, rowversion columns, computed columns, sparse columns, system-period columns.
6. SQL constraints are not the same thing as full relational predicates.

Example:

```sql
CREATE TABLE Enrollment (
    student_id int NOT NULL,
    course_id int NOT NULL,
    grade char(2) NULL
);
```

This is not yet a good relvar approximation.

Better:

```sql
CREATE TABLE Enrollment (
    student_id int NOT NULL,
    course_id int NOT NULL,
    grade char(2) NOT NULL,
    CONSTRAINT PK_Enrollment PRIMARY KEY (student_id, course_id),
    CONSTRAINT CK_Enrollment_Grade CHECK (grade IN ('A','B','C','D','F'))
);
```

Closer, but still SQL.

Curmudgeon rule:

> A SQL table is not a relation. It is an industrial approximation to a relvar, with compromises.

---

## 7. Record

A **record** is a programming or storage structure: a compound value with named or positional fields.

Example in C#:

```csharp
public record EnrollmentRecord(int StudentId, int CourseId, string Grade);
```

Example in JSON:

```json
{
  "student_id": 1,
  "course_id": 10,
  "grade": "A"
}
```

A record may represent a tuple, but it is not the same thing as a tuple.

A record can:

```text
have field order
have optional fields
have missing fields
have null fields
have nested structure
carry object identity
exist outside a relation
```

A tuple in the relational sense is a value over a heading.

Curmudgeon rule:

> A record is a programming object. A tuple is a relational value.

---

## 8. Field

A **field** is usually a component of a record.

In casual SQL speech, people say “field” when they mean column or attribute. That habit is common. It is also imprecise.

There are at least three different things people call “field”:

| Casual phrase | More precise term |
|---|---|
| field in a table | column, or better, attribute |
| field in a row | scalar value at an attribute in a tuple/row |
| field in a record | component of a record structure |

In a relation, the closest formal idea is:

\[
t(A)
\]

the value of attribute \(A\) in tuple \(t\).

Example:

\[
t(StudentName) = 'Ada'
\]

Curmudgeon rule:

> If you mean attribute, say attribute. If you mean column, say column. If you mean record component, say field.

---

## 9. Column

A **column** is a tabular representation of an attribute.

SQL column:

```sql
student_id int NOT NULL
```

Relational attribute:

\[
StudentId : StudentIdDomain
\]

A column can approximate an attribute if:

```text
it has a declared type/domain
it rejects nulls when the model requires total values
it participates in the correct constraints
it is understood as unordered with respect to other attributes
```

Curmudgeon rule:

> Columns are what SQL gives you. Attributes are what the relational model talks about.

---

## 10. Row

A **row** is a tabular representation of a tuple.

A SQL row may be:

```text
ordered by display position
duplicated in a result set
partially unknown through NULL
extended with hidden system fields
physically stored, moved, locked, versioned, or indexed
```

A relational tuple is a logical value.

Curmudgeon rule:

> Rows are implementation artifacts. Tuples are logical facts.

---

# Part II — A compact dictionary

| Strict relational term | SQL-ish term | Programming-ish term | Warning |
|---|---|---|---|
| domain | data type / domain / check constraint | type | SQL type is not full semantic domain |
| attribute | column | property / field name | attribute is logical, column is representation |
| tuple | row | record instance | tuple is unordered and set-valued |
| relation | table value / result set | collection of records | SQL result may be a bag, not a set |
| relvar | base table / view name | variable / repository | relvar is a variable over relation values |
| relation predicate | table meaning | invariant / contract | often missing from SQL DDL |
| key | primary/unique key | identity constraint | key is logical uniqueness, not surrogate decoration |
| foreign key | FK constraint | reference | FK approximates inclusion dependency |
| null | NULL | null / None | not a value in the classical relational sense |

---

# Part III — What a relvar really declares

A serious relvar declaration should contain more than a SQL table name.

It should declare:

```text
name
heading
domains
candidate keys
foreign keys / inclusion dependencies
relation predicate
allowed updates
derived dependencies
integrity constraints
```

Example:

```text
Relvar: Enrollment

Heading:
  StudentId : StudentId
  CourseId  : CourseId
  Grade     : Grade

Predicate:
  Student StudentId is enrolled in Course CourseId and currently has Grade.

Candidate key:
  {StudentId, CourseId}

Dependencies:
  {StudentId, CourseId} -> Grade

Foreign keys:
  StudentId references Student
  CourseId references Course
```

SQL approximation:

```sql
CREATE TABLE Enrollment (
    student_id int NOT NULL,
    course_id int NOT NULL,
    grade char(2) NOT NULL,
    CONSTRAINT PK_Enrollment PRIMARY KEY (student_id, course_id),
    CONSTRAINT CK_Enrollment_Grade CHECK (grade IN ('A','B','C','D','F')),
    CONSTRAINT FK_Enrollment_Student FOREIGN KEY (student_id)
        REFERENCES Student(student_id),
    CONSTRAINT FK_Enrollment_Course FOREIGN KEY (course_id)
        REFERENCES Course(course_id)
);
```

The SQL is useful. It is not the whole declaration.

The missing piece is the predicate:

> Student `student_id` is enrolled in course `course_id` and has grade `grade`.

That sentence is not decoration. It is the meaning of the relvar.

---

# Part IV — Why this matters for normal forms

Normal forms are not table beautification.

A normal form is a discipline on relvars.

Classical normal forms ask:

```text
Can dependency anomalies hide inside this relvar?
```

Examples:

\[
student\_id \to student\_name
\]

does not belong inside:

\[
Enrollment(student\_id, course\_id, student\_name, course\_title, grade)
\]

because the relvar is mixing at least three predicates:

```text
student_id names student_name
course_id names course_title
student_id is enrolled in course_id with grade
```

The repair is not cosmetic. It separates predicates:

```text
Student(student_id, student_name)
Course(course_id, course_title)
Enrollment(student_id, course_id, grade)
```

Equation:

\[
EnrollmentBad \cong Student \Join Enrollment \Join Course
\]

when the dependencies are true and the decomposition is lossless.

Curmudgeon rule:

> Bad normalization usually means several predicates are being stuffed into one relvar.

---

# Part V — SQL does not rescue bad thinking

SQL can enforce some relational discipline:

```text
PRIMARY KEY
UNIQUE
FOREIGN KEY
CHECK
NOT NULL
EXCLUDE, in PostgreSQL
triggers, with caution
```

But SQL cannot infer your intended predicate.

This table is legal:

```sql
CREATE TABLE Thing (
    id int PRIMARY KEY,
    name text NOT NULL,
    amount numeric(12,2) NOT NULL,
    status text NOT NULL
);
```

It is also mostly meaningless.

A relvar without a predicate is just a bucket with constraints.

Curmudgeon rule:

> DDL without a predicate is not design. It is furniture assembly.

---

# Part VI — The bridge to our work

Classical relational theory disciplines **data at rest**.

It asks whether relation values are shaped so that dependency anomalies do not hide.

Our newer work asks a different question:

```text
When a relvar changes, what else is allowed to change,
what can be repaired,
what must be invalidated,
and what authority survives the transition?
```

This is the movement from:

\[
R_t
\]

to:

\[
R_t \xrightarrow{e} R_{t+1}
\]

A classical relvar declares the admissible relation values.

A certified change-aware relvar declares admissible relation values **and** admissible transitions.

The key distinction from the current framework is:

\[
\text{Form}
\subset
\text{Normal Form}
\subset
\text{Certified Normal Form}
\subset
\text{Authorized Normal Form}
\]

where a certified normal form must carry a residual obstruction, proof artifact, and terminal route. This hierarchy is the guardrail against calling every convenient representation a normal form.

### Unifying invariant (across the whole stack)

Category theory, quotients, and obstruction calculus are **tools**. The recurring invariant is:

\[
\boxed{
\text{No silent authority degradation.}
}
\]

Everything else names a mechanism:

| Mechanism | What it forbids silently |
|---|---|
| BQNF / boundary relvar | uncertified repair, stale cache as fresh |
| GTMUR / CpNF | erasure without ledger, compile drift |
| loss ledger | forgotten distinctions |
| observer boundary | acting on invisible attributes as if seen |
| repair terminals | pretending knowledge when evidence is missing |
| certified vs authorized | treating validity as permission |
| finite shadows (GTTC) | limit objects without approximating towers |

**Systems must declare where authority was lost** — or prove it was preserved.

### Scope discipline (what may enter the framework)

The framework can absorb AI, streams, vectors, and federation — but only under this admission rule:

\[
\boxed{
\text{Can this anomaly be detected, typed, and terminalized with finite evidence?}
}
\]

* **Yes** → operational normal form (BQNF, CpNF, evidence packets, verifier terminals).  
* **No** → philosophical / speculative layer (atlas §7 epistemic NFs until checklists exist).

This criterion prevents abstraction drift: a theory that explains everything operationalizes nothing.

### Philosophical shift (post-relational, not anti-relational)

Classical relational theory assumes **global truth** at a snapshot: one admissible relation value $R_t$.

This work assumes **bounded observable authority**: what observer $\mathcal O$ may rely on, as of a declared time, under a policy, with explicit uncertainty.

Not a rejection of relations. A **runtime semantics layer** for distributed authoritative computation — *relational transition semantics with certified observer boundaries.*

---

# Part VII — A different kind of relvar

## 1. Classical relvar

A classical relvar is:

\[
\mathcal R : Time \to Rel(H)
\]

At each time:

\[
\mathcal R(t) = R_t
\]

where \(R_t\) is a relation over heading \(H\).

This says:

```text
at time t, this relvar holds this relation value
```

It does not, by itself, say whether a particular update can safely repair a cache, preserve a materialized view, commute with another update, or transport authority.

---

## 2. Boundary relvar

A **boundary relvar** is a relvar with an explicit boundary for change.

It declares:

```text
relation heading
ordinary integrity constraints
change event type
boundary map
repair image
obstruction quotient
terminal routes
```

Mathematically:

\[
\mathcal B =
(H,\Sigma,C^0 \xrightarrow{d_0} C^1,Q^1,\mathsf{Term})
\]

where:

\[
Q^1 = C^1 / \operatorname{im}(d_0)
\]

A write event \(e\) induces a defect:

\[
\omega(e) \in C^1
\]

The event is exactly repairable iff:

\[
[\omega(e)] = 0 \in Q^1
\]

equivalently:

\[
\omega(e) = d_0\alpha
\]

for some admissible repair \(\alpha\).

If not, the relvar must terminalize:

```text
Invalidate
Serialize
Recompute
Lift
Unsupported
ConservativeInvalidate
Escalate
Refuse
```

This follows the boundary-certified database idea: a database should not guess what a write breaks; it should compute the obstruction.

**Evolution in one line:** Codd disciplined **valid states**; boundary relvars discipline **valid transitions and certified repairs**.

\[
\underbrace{Rel(H)}_{\text{states at rest}}
\quad\leadsto\quad
\underbrace{(C^0 \xrightarrow{d_0} C^1,\ Q^1,\ \mathsf{Term})}_{\text{transitions in motion}}
\]

Full operational treatment: `1a_bqnf_incremental_repair.md`.

---

## 3. Why this is still relational

This is not replacing relations with vibes.

The ordinary relation is still present:

\[
R \subseteq \prod_{A \in H} D_A
\]

The new structure is attached to transitions:

\[
R_t \xrightarrow{e} R_{t+1}
\]

The classical relvar says what states are valid.

The boundary relvar says which state transitions are certified, repairable, or terminal.

Plainly:

```text
Classical relvar:
  What facts are currently true?

Boundary relvar:
  What facts are currently true, and what did this change break?
```

---

# Part VIII — Example: ordinary relvar versus boundary relvar

## 1. Ordinary base relvar

```sql
CREATE TABLE Orders (
    order_id bigint PRIMARY KEY,
    customer_id bigint NOT NULL,
    amount numeric(18,2) NOT NULL CHECK (amount >= 0),
    status text NOT NULL CHECK (status IN ('open','paid','void'))
);
```

Relational predicate:

```text
Order order_id belongs to customer customer_id,
has monetary amount amount,
and currently has lifecycle status status.
```

Relation type:

\[
Orders \subseteq
OrderId \times CustomerId \times Money \times Status
\]

---

## 2. Derived relvar

```sql
CREATE VIEW PaidCustomerSpend AS
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(amount) AS gross_sum,
    AVG(amount) AS avg_order
FROM Orders
WHERE status = 'paid'
GROUP BY customer_id;
```

Algebra:

\[
Q =
\gamma_{customer\_id;\ COUNT(*), SUM(amount), AVG(amount)}
(\sigma_{status='paid'}(Orders))
\]

This is a derived relvar: a relation variable whose value is determined by another relvar expression.

---

## 3. Boundary declaration

Boundary fingerprint:

\[
\partial Q =
(
Orders,
\{customer\_id,amount,status\},
status='paid',
GROUP BY\ customer\_id,
\{COUNT,SUM,AVG\}
)
\]

That says which part of `Orders` can affect the derived relvar.

If an update changes only an irrelevant column, the view does not care.

If an update changes `amount`, `status`, or `customer_id`, the boundary is touched.

---

## 4. Delta equations

For a write event \(e\) with old row \(o\) and new row \(n\):

\[
\Delta SUM =
1_{n.status='paid'}n.amount
-
1_{o.status='paid'}o.amount
\]

\[
\Delta COUNT =
1_{n.status='paid'}
-
1_{o.status='paid'}
\]

\[
AVG' =
\frac{SUM+\Delta SUM}{COUNT+\Delta COUNT}
\]

The repair is exact when the event evidence contains:

```text
old amount
new amount
old status
new status
old customer_id
new customer_id
```

If that evidence is missing, the system must not pretend.

---

## 5. Certified boundary relvar declaration

Pseudo-DDL:

```text
CREATE BOUNDARY RELVAR PaidCustomerSpend_Boundary
ON VIEW PaidCustomerSpend
SOURCE Orders
BOUNDARY (
    attributes: customer_id, amount, status,
    predicate: status = 'paid',
    group_key: customer_id,
    aggregates: count, sum, avg
)
REPAIR IMAGE (
    count: delta_count(old.status, new.status),
    sum: delta_sum(old.status, new.status, old.amount, new.amount),
    avg: sum / count
)
EVIDENCE REQUIRED (
    old.customer_id,
    new.customer_id,
    old.status,
    new.status,
    old.amount,
    new.amount
)
TERMINALS (
    Repair,
    Invalidate,
    Recompute,
    ConservativeInvalidate,
    Unsupported
);
```

That is not standard SQL. It is the shape of the missing declaration.

---

## 6. SQL approximation

Cache table:

```sql
CREATE TABLE CustomerSpendCache (
    customer_id bigint PRIMARY KEY,
    order_count bigint NOT NULL,
    gross_sum numeric(18,2) NOT NULL,
    avg_order numeric(18,2) NOT NULL,
    last_repaired_at timestamp NOT NULL DEFAULT current_timestamp
);
```

Repair certificate:

```sql
CREATE TABLE RepairCertificate (
    certificate_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_relvar text NOT NULL,
    target_relvar text NOT NULL,
    event_key text NOT NULL,
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
            'Escalate',
            'Refuse'
        )
    ),
    evidence_json text NOT NULL,
    created_at timestamp NOT NULL DEFAULT current_timestamp
);
```

The table stores the evidence packet. It does not magically prove the repair. The verifier does that.

Curmudgeon rule:

> A certificate table without a verifier is just another table.

---

# Part IX — Another different kind: observer relvar

A derived relvar can also declare what it ignores.

For example:

```sql
CREATE VIEW CustomerNames AS
SELECT customer_id, display_name
FROM Customer;
```

This observer sees:

```text
customer_id
display_name
```

It ignores:

```text
email
phone
credit_limit
internal_notes
```

Observer equivalence:

\[
e_1 \sim_{\mathcal O} e_2
\]

when both events produce the same visible effect under observer \(\mathcal O\).

Functorially:

\[
\mathcal O : Rel(H) \to Rel(H_{\mathcal O})
\]

The observer relvar declares the kernel of that projection:

\[
\ker(\mathcal O)
=
\{(r_1,r_2) \mid \mathcal O(r_1)=\mathcal O(r_2)\}
\]

Plain English:

> This relvar knows what it cannot see.

SQL approximation:

```sql
CREATE TABLE ObserverBoundary (
    observer_name text NOT NULL,
    source_relvar text NOT NULL,
    visible_attribute text NOT NULL,
    PRIMARY KEY (observer_name, source_relvar, visible_attribute)
);
```

Example:

```sql
INSERT INTO ObserverBoundary(observer_name, source_relvar, visible_attribute)
VALUES
('CustomerNames', 'Customer', 'customer_id'),
('CustomerNames', 'Customer', 'display_name');
```

A change to `email` does not intersect the observer boundary. A change to `display_name` does.

This is not a classical relvar. It is a relvar plus declared observational authority.

### Observational Normal Form (candidate)

An **observer relvar** is in **Observational Normal Form** when every admissible representation declares:

```text
observer identity
visible heading H_O
ignored attributes (kernel of projection)
equivalence: e_1 ~_O e_2  iff  indistinguishable to O
intersection rule for change events
```

**Anomaly excluded:** treating observer-relative state as if it were global truth.

Plain English for $e_1 \sim_{\mathcal O} e_2$:

```text
changes indistinguishable to observer O
```

Connections (operational, not metaphorical):

| Domain | Role of $\sim_{\mathcal O}$ |
|---|---|
| cache / MV | disjoint column change → preserve |
| CQRS | read model sees subset of write stream |
| RBAC | policy-masked attributes |
| federated views | remote columns invisible to local observer |
| differential privacy | indistinguishability under noise |
| AI context window | retrieved vs hidden fields (ledger when collapsed) |

Observer relvars may outlive any single transport acronym because modern systems are **observer-relative** by construction. GTMUR compiles between regimes; observers declare what each regime may distinguish.

---

# Part X — What not to say

Do not say:

```text
A relation is a table.
A tuple is a row.
An attribute is a column.
A field is a column.
A record is a row.
```

Those are compromises, not definitions.

Better:

```text
A SQL table usually attempts to implement a relvar.
A SQL row often represents a tuple.
A SQL column often represents an attribute.
A record may encode a tuple.
A field may encode an attribute-value component.
```

That language is less convenient. It is also less wrong.

---

# Part XI — Final kernel

\[
\boxed{
\text{Relation} = \text{set of tuples over a heading}
}
\]

\[
\boxed{
\text{Relvar} = \text{variable whose values are relations}
}
\]

\[
\boxed{
\text{Table} = \text{SQL representation that may approximate a relvar}
}
\]

\[
\boxed{
\text{Tuple} \ne \text{row}
}
\]

\[
\boxed{
\text{Attribute} \ne \text{column}
}
\]

\[
\boxed{
\text{Field} \ne \text{attribute}
}
\]

\[
\boxed{
\text{Record} \ne \text{tuple}
}
\]

And the extension:

\[
\boxed{
\text{Boundary relvar}
=
\text{relvar}
+
\text{declared transition boundary}
+
\text{repair quotient}
+
\text{terminal route}
}
\]

A classical relvar disciplines facts at rest.

A boundary relvar disciplines facts in motion.

The serious version of the project is not “let us invent cute names.” It is:

```text
make every hidden dependency,
hidden boundary,
hidden repair assumption,
and hidden authority claim explicit.
```

That is the professional standard.

---

# Part XII — Stack map (what this file enables)

| Question | Subject | Primary artifact |
|---|---|---|
| What are the facts? | relation value $R_t$ | classical NF, keys, dependencies |
| What may change? | relvar assignment $\mathcal R(t):=R_t$ | transactions, constraints |
| What did a write break? | boundary relvar $\mathcal B$, defect $\omega(e)$ | BQNF, Paper A |
| Was compilation honest? | morphism $F:A\to A_{\mathrm{nf}}$, witness $\chi_F$ | GTMUR / CpNF, Paper B |
| What may this observer see? | observer relvar $\mathcal O$, $\sim_{\mathcal O}$ | Observational NF, §IX |
| May we trust this approximation? | finite shadow tower | GTTC, Paper C (planned) |
| May we act on it? | authority verifier | certified $\neq$ authorized |

**Landing position (publishable framing):**

> Relational transition semantics with certified observer boundaries.

Less grandiose than “replacing Codd”; more accurate for distributed caches, replicas, compiled views, and agent-mediated writes.

**Implementation north star:** resist infinite extensibility — ship finite-evidence verifiers, real certificates, failure pathologies, and repair-vs-recompute benchmarks first (`1a` §9, `1b` §9). Ontology follows executable proof.
