# Simplex Normal Forms: External Developer Adoption & System Import Guide

**Boundary-Certified Data Architecture, Relational Normalization, Cochain Retraction & NF-IR Compiler**  
**Epistemic Standard:** Landau Rigor / Claim Discipline Compliant (`AuthorityEffect: None`, `certified_implies_authorized: false`)

---

## 1. Introduction & Overview

`simplex-normal-forms` provides a mathematically grounded, pure-Python data architecture framework spanning classical database normalization, incremental Change Data Capture (CDC) boundary quotient repair, an intermediate representation compiler stack (NF-IR), and verifiable Model Context Protocol (MCP) context projection decorators.

This guide provides external software engineers, database architects, and distributed systems developers with the exact instructions and code patterns required to install the repository and import its capabilities into external production systems in under fifteen minutes.

### Key Architectural Dimensions

| Subsystem | Core Module Path | Primary Abstraction | Practical Value |
| :--- | :--- | :--- | :--- |
| **Relational Dependency Algebra** | `normal_forms.domain.relational`, `relational_advanced` | `RelationalSchema`, `FunctionalDependency`, `synthesize_3nf_bernstein` | Pre-flight migration validation, candidate key derivation, dependency-preserving 3NF synthesis, and Chase lossless join verification. |
| **Streaming BQNF Delta Repair** | `normal_forms.domain.bqnf_validator`, `bqnf_extrema`, `sales_cochain` | `BqnfValidator`, `apply_removal`, `rebalance_quantile_cochain` | Incremental view maintenance over CDC streams; $O(\log K)$ extremum tracking and dynamic dyadic quantile sketches without full table scans. |
| **4-Layer NF-IR Compiler Stack** | `normal_forms.ir_kernel`, `ir_subsumption`, `ir_wiring`, `ir_lowering` | `NFKernelSpec`, `compile_to_sqlite_triggers`, `compile_to_python_decorator` | Compiles declarative invariants into database-native `BEFORE INSERT/UPDATE` triggers and fail-closed Python runtime guard decorators. |
| **AI Context LossLedger Gateway** | `normal_forms.ai` | `coda_mur_projection`, `build_context_loss_ledger`, `verify_loss_ledger_integrity` | Cryptographic SHA-256 Merkle loss ledgers tracking prompt token truncation, attribute erasure, and exact token conservation in RAG/agent workflows. |

---

## 2. Quickstart (30 Seconds)

### 2.1 Clone and Install in Development Mode

The core evaluation engines depend on the Python Standard Library, `pyyaml`, and
Pydantic 2. Optional web dependencies are provided through the `web` extra.
Wheels include the contract resources and Studio templates/static assets.

```bash
# 1. Clone the repository
git clone https://github.com/dbccpage/simplex-normal-forms.git
cd simplex-normal-forms

# 2. Create and activate a clean virtual environment
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# 3. Install in editable development mode (with dev and web extras)
pip install -e ".[dev,web]"
```

### 2.2 Verify Installation via Test Suite

Execute the automated test suite to confirm that all relational decision procedures, compiler lowering passes, and property-based invariance tests pass:

```bash
pytest tests/ -v
```

---

## 3. Four Concrete Integration Blueprints

For the bounded streaming profile and Python/SQLite input semantics, read
[Executable scope and regression evidence](docs/CORRECTNESS_SCOPE.md).
For source-distribution and isolated wheel checks, read
[Distribution verification](docs/DISTRIBUTION.md).

Below are four complete, syntax-checked, runnable Python blueprints demonstrating how to integrate `simplex-normal-forms` into production application architectures.

---

### Blueprint 1: Relational Schema Normalizer in FastAPI / Pydantic APIs

This blueprint demonstrates embedding the relational algebra engine into a FastAPI service or CI/CD pre-deployment pipeline to inspect proposed database migrations, detect 2NF/3NF anomalies, derive candidate keys, and synthesize dependency-preserving 3NF subschemas with Tableau Chase lossless join verification.

```python
"""Blueprint 1: Relational Schema Normalizer in FastAPI / Pydantic APIs."""
from typing import List, Optional
from pydantic import BaseModel, Field

from normal_forms.domain.relational import (
    FunctionalDependency,
    RelationalSchema,
    check_3nf,
    chase_join_dependency,
)
from normal_forms.domain.relational_advanced import synthesize_3nf_bernstein


# 1. Define strongly typed Pydantic models for incoming schema migration payloads
class FunctionalDependencyPayload(BaseModel):
    determinant: List[str] = Field(..., description="Determinant attribute set X")
    dependent: List[str] = Field(..., description="Dependent attribute set Y")


class SchemaMigrationRequest(BaseModel):
    table_name: str = Field(..., description="Target database table name")
    attributes: List[str] = Field(..., description="List of all attribute columns")
    dependencies: List[FunctionalDependencyPayload] = Field(
        ..., description="Declared functional dependencies"
    )


class SchemaNormalizationResponse(BaseModel):
    table_name: str
    candidate_keys: List[List[str]]
    prime_attributes: List[str]
    is_3nf: bool
    diagnostic: Optional[str]
    synthesized_3nf_subschemas: List[List[str]]
    lossless_join_verified: bool
    chase_steps_count: int


# 2. Pipeline execution function
def evaluate_and_normalize_migration(
    request: SchemaMigrationRequest,
) -> SchemaNormalizationResponse:
    """Evaluates an incoming relational schema and synthesizes 3NF subschemas."""
    # Convert payload into immutable domain sets
    attrs = frozenset(request.attributes)
    fds = frozenset(
        FunctionalDependency(frozenset(dep.determinant), frozenset(dep.dependent))
        for dep in request.dependencies
    )

    # Initialize RelationalSchema domain model
    schema = RelationalSchema(attributes=attrs, dependencies=fds)

    # Compute minimal candidate keys and prime attribute partition
    cand_keys = [sorted(list(k)) for k in schema.candidate_keys()]
    prime_attrs = sorted(list(schema.prime_attributes()))

    # Check Third Normal Form (3NF) compliance
    is_3nf, reason = check_3nf(schema)

    # Synthesize 3NF subschemas using Bernstein's (1976) algorithm
    synthesized = synthesize_3nf_bernstein(schema)
    subschemas_list = [sorted(list(s)) for s in synthesized]

    # Verify lossless join property using the deterministic Tableau Chase
    chase_result = chase_join_dependency(schema.attributes, schema.dependencies, synthesized)

    return SchemaNormalizationResponse(
        table_name=request.table_name,
        candidate_keys=cand_keys,
        prime_attributes=prime_attrs,
        is_3nf=is_3nf,
        diagnostic=reason,
        synthesized_3nf_subschemas=subschemas_list,
        lossless_join_verified=chase_result.is_implied,
        chase_steps_count=len(chase_result.steps),
    )


# 3. Executable verification example
if __name__ == "__main__":
    # Example: E-commerce order fulfillment schema with transitive dependency
    payload = SchemaMigrationRequest(
        table_name="order_fulfillment_raw",
        attributes=["order_id", "customer_id", "customer_zip", "item_id", "unit_price", "quantity"],
        dependencies=[
            FunctionalDependencyPayload(determinant=["order_id"], dependent=["customer_id"]),
            FunctionalDependencyPayload(determinant=["customer_id"], dependent=["customer_zip"]),
            FunctionalDependencyPayload(determinant=["item_id"], dependent=["unit_price"]),
            FunctionalDependencyPayload(determinant=["order_id", "item_id"], dependent=["quantity"]),
        ],
    )

    result = evaluate_and_normalize_migration(payload)
    print("Schema Analysis for:", result.table_name)
    print("  Candidate Keys:", result.candidate_keys)
    print("  Satisfies 3NF:", result.is_3nf)
    if not result.is_3nf:
        print("  Diagnostic Violation:", result.diagnostic)
    print("  Synthesized 3NF Subschemas:")
    for idx, subschema in enumerate(result.synthesized_3nf_subschemas, start=1):
        print(f"    Table {idx}: {subschema}")
    print("  Lossless Join Verified via Chase:", result.lossless_join_verified)
    print("  Chase Steps Executed:", result.chase_steps_count)
```

---

### Blueprint 2: Streaming BQNF Delta Repair in Change Data Capture (CDC) Pipelines

This blueprint demonstrates consuming streaming Change Data Capture (CDC) mutation records (e.g., from Debezium, Kafka, or logical replication logs) and applying Boundary-Quotient Normal Form (BQNF) delta repair. It executes exact $O(1)$ coboundary repairs on additive aggregates, uses priority-queue extremum cochains to service destructive deletions in $O(\log K)$ without scanning base tables, and rebalances dynamic dyadic quantile sketches under skewed stream conditions.

```python
"""Blueprint 2: Streaming BQNF Delta Repair in Change Data Capture (CDC) Pipelines."""
import sqlite3
from typing import Any, Dict

from normal_forms.domain.bqnf_validator import BqnfValidator, BqnfBoundary, BqnfCdcEvent
from normal_forms.bqnf_extrema import apply_removal, RepairTally
from normal_forms.sales_cochain import (
    rebalance_quantile_cochain,
    quantile_cochain_add,
    cochain_add,
)


def run_cdc_streaming_pipeline() -> None:
    # 1. Initialize in-memory SQLite storage representing base table, cache, and cochains
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("CREATE TABLE base_sales (id INTEGER PRIMARY KEY, region TEXT, amount REAL);")
    cur.execute(
        """
        CREATE TABLE region_sales_cache (
            region TEXT PRIMARY KEY,
            total_sales REAL,
            sale_count INTEGER,
            min_amount REAL,
            max_amount REAL,
            median_amount REAL
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE region_extremum_cochain (
            region TEXT,
            amount REAL,
            frequency INTEGER,
            PRIMARY KEY (region, amount)
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE region_quantile_cochain (
            region TEXT,
            bucket_id INTEGER,
            lower_bound REAL,
            upper_bound REAL,
            count INTEGER,
            PRIMARY KEY (region, bucket_id)
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE extrema_repair_log (
            region TEXT, op_type TEXT, affected_amount REAL, is_destructive INTEGER,
            cochain_available INTEGER, terminal_route TEXT, old_min REAL, new_min REAL,
            old_max REAL, new_max REAL, recomputation_fallback_executed INTEGER
        );
        """
    )

    # 2. Seed baseline data for region 'EMEA'
    region = "EMEA"
    initial_sales = [20.0, 45.0, 80.0, 150.0]
    for val in initial_sales:
        cur.execute("INSERT INTO base_sales (region, amount) VALUES (?, ?);", (region, val))
        cochain_add(conn, region, val)
        quantile_cochain_add(conn, region, val, bucket_width=10.0)

    cur.execute(
        "INSERT INTO region_sales_cache VALUES (?, 295.0, 4, 20.0, 150.0, 62.5);",
        (region,),
    )
    conn.commit()

    # 3. Evaluate incoming CDC UPDATE event against declared query boundary via BqnfValidator
    boundary = BqnfBoundary(
        relations=("orders",),
        attributes=("amount", "status"),
        predicates=("status = completed",),
        aggregates=("SUM(amount)",),
    )
    cdc_event = BqnfCdcEvent(
        op="UPDATE",
        relation="orders",
        old={"amount": 45.0, "status": "completed"},
        new={"amount": 85.0, "status": "completed"},
    )

    eval_result = BqnfValidator.evaluate(boundary, cdc_event)
    print(f"CDC Event Evaluated: op={cdc_event.op}")
    print(f"  BQNF Terminal Decision: {eval_result.decision}")
    print(f"  Coboundary Repair Delta: {eval_result.repair}")

    # 4. Process destructive deletion of maximum value (150.0) using priority-queue extremum cochain
    cache_state: Dict[str, Dict[str, Any]] = {
        region: {
            "total_sales": 295.0,
            "sale_count": 4,
            "min_amount": 20.0,
            "max_amount": 150.0,
        }
    }
    tally = RepairTally()

    # Invalidate cochain record for the deleted 150.0 sale
    cur.execute("DELETE FROM region_extremum_cochain WHERE region = ? AND amount = ?;", (region, 150.0))

    # apply_removal retrieves next extremum via O(log K) query:
    # SELECT amount FROM region_extremum_cochain WHERE region = ? ORDER BY amount DESC LIMIT 1;
    apply_removal(cur, cache_state, region, 150.0, use_cochain=True, tally=tally)

    print(f"Destructive Deletion Applied for Region: {region}")
    print(f"  New Max Amount: {cache_state[region]['max_amount']} (Retrieved via Extremum Cochain)")
    print(f"  Extrema Repairs Recorded: {tally.extrema_repairs}")
    print(f"  Fallback Full Scans Avoided: {tally.fallback_recomputations == 0}")

    # 5. Rebalance dynamic dyadic quantile cochain under stream evolution
    rebalance_receipt = rebalance_quantile_cochain(
        conn, region, split_threshold=4, merge_threshold=1, bucket_width=10.0
    )
    print(f"Dyadic Quantile Cochain Rebalance:")
    print(f"  Region: {rebalance_receipt['region']}")
    print(f"  Splits Executed: {rebalance_receipt['splits_executed']}")
    print(f"  Merges Executed: {rebalance_receipt['merges_executed']}")
    print(f"  Active Bucket Count: {rebalance_receipt['active_bucket_count']}")


if __name__ == "__main__":
    run_cdc_streaming_pipeline()
```

---

### Blueprint 3: 4-Layer NF-IR Verification in SQLAlchemy / SQLite ORM

This blueprint demonstrates compiling declarative normal-form specifications via the 4-layer NF-IR stack (`ir_kernel.py`, `ir_subsumption.py`, `ir_wiring.py`, `ir_lowering.py`) into two runtime targets:
1. Executable SQLite `BEFORE INSERT` and `BEFORE UPDATE` trigger DDL for database-level write isolation.
2. Python `@compile_to_python_decorator` (`@nf_kernel_guard`) function wrappers that inspect in-memory batches before executing application persistence logic.

```python
"""Blueprint 3: 4-Layer NF-IR Verification in SQLAlchemy / SQLite ORM."""
import sqlite3
from normal_forms.domain.relational import FunctionalDependency
from normal_forms.ir_kernel import lower_fd_to_kernel_spec
from normal_forms.ir_lowering import (
    compile_to_sqlite_triggers,
    compile_to_python_decorator,
    install_and_verify_sqlite_bundle,
)


def run_nf_ir_lowering_example() -> None:
    # 1. Lower declared functional dependency: department_id -> manager_id
    # Contract: Each department has a single designated manager.
    fd = FunctionalDependency(frozenset({"department_id"}), frozenset({"manager_id"}))
    spec = lower_fd_to_kernel_spec(
        fd=fd,
        key_field="employee_id",
        heading=("employee_id", "department_id", "manager_id"),
        contract_id="nf.classical.bcnf",
    )

    print("Compiled NFKernelSpec:")
    print(f"  Contract ID: {spec.contract_id}")
    print(f"  Key Field: {spec.key_field}")
    print(f"  Collapse Fields (Determinant): {spec.collapse_fields}")
    print(f"  Protected Fields (Dependent): {spec.protected_law_fields}")

    # 2. Compile to Python in-memory guard decorator (@nf_kernel_guard)
    @compile_to_python_decorator(spec)
    def persist_employee_batch(records):
        """Application write handler protected by the NF-IR kernel guard."""
        return f"Successfully committed {len(records)} employee records."

    # Test execution with valid records conforming to department_id -> manager_id
    valid_batch = [
        {"employee_id": "E101", "department_id": "D1", "manager_id": "Alice"},
        {"employee_id": "E102", "department_id": "D1", "manager_id": "Alice"},
        {"employee_id": "E103", "department_id": "D2", "manager_id": "Bob"},
    ]
    valid_receipt = persist_employee_batch(valid_batch)
    print("\nTarget A: Python In-Memory Kernel Guard (Valid Batch):")
    print(f"  Function Executed: {valid_receipt.function_executed}")
    print(f"  Terminal Outcome: {valid_receipt.canonical_terminal}")
    print(f"  Output: {valid_receipt.function_output}")

    # Test execution with conflicting records (department D1 assigned to both Alice and Carol)
    violating_batch = [
        {"employee_id": "E101", "department_id": "D1", "manager_id": "Alice"},
        {"employee_id": "E102", "department_id": "D1", "manager_id": "Carol"},
    ]
    invalid_receipt = persist_employee_batch(violating_batch)
    print("\nTarget A: Python In-Memory Kernel Guard (Violating Batch):")
    print(f"  Function Executed: {invalid_receipt.function_executed}")
    print(f"  Terminal Outcome: {invalid_receipt.canonical_terminal}")
    print(f"  Reason: {invalid_receipt.wiring_receipt.reason}")

    # 3. Target B: Compile to SQLite Triggers DDL
    bundle = compile_to_sqlite_triggers(spec, table_name="employee_directory")
    print("\nTarget B: Lowered SQLite Trigger DDL:")
    print(bundle.before_insert_trigger_sql.strip())

    # Install trigger bundle into SQLite database and verify transaction abort
    conn = sqlite3.connect(":memory:")
    success, error_msg = install_and_verify_sqlite_bundle(
        conn=conn, bundle=bundle, rows=violating_batch
    )
    print("\nTarget B: SQLite Database Execution Verification:")
    print(f"  Batch Insertion Succeeded: {success}")
    print(f"  Database Trigger Intercept: {error_msg}")


if __name__ == "__main__":
    run_nf_ir_lowering_example()
```

---

### Blueprint 4: AI Agent LossLedger in LangChain / LlamaIndex / MCP Workflows

This blueprint demonstrates wrapping AI retrieval-augmented generation (RAG) context compression and Model Context Protocol (MCP) tool pipelines with `@coda_mur_projection`. It enforces that prompt context truncation and attribute erasure emit a cryptographic SHA-256 Merkle `LossLedger`, verifies exact additive token conservation ($\text{retained\_tokens} + \text{truncated\_tokens} == \text{source\_tokens}$), and asserts the epistemic authority firewall (`certified_implies_authorized: false`).

Here, tokens are deterministic whitespace-separated units from
`tokenize_whitespace`, not provider/model tokenizer counts. The budget alone
does not establish that a prompt fits a particular model's context window.

```python
"""Blueprint 4: AI Agent LossLedger in LangChain / LlamaIndex / MCP Workflows."""
from typing import Any, List, Mapping
from normal_forms.ai import (
    coda_mur_projection,
    verify_loss_ledger_integrity,
)


def run_ai_context_lossledger_pipeline() -> None:
    # 1. Wrap a RAG context compression step with @coda_mur_projection
    # Enforces that protected fields (chunk_id) cannot be dropped,
    # tracks attribute erasure (internal_score, doc_url), and applies token ceilings.
    @coda_mur_projection(
        source_fields=("chunk_id", "text", "doc_title", "internal_score", "doc_url"),
        target_fields=("chunk_id", "text", "doc_title"),
        key_field="chunk_id",
        protected_fields=("chunk_id",),
        max_token_budget=16,
    )
    def prepare_llm_prompt_context(chunks: List[Mapping[str, Any]]):
        """Compresses context for downstream LLM prompts. Returning None triggers canonical projection."""
        return None

    # 2. Candidate retrieved document chunks from vector search
    retrieved_chunks = [
        {
            "chunk_id": "doc_01",
            "text": "PostgreSQL uses multi-version concurrency control with write-ahead logging.",
            "doc_title": "PostgreSQL Architecture",
            "internal_score": 0.98,
            "doc_url": "https://docs.postgresql.org",
        },
        {
            "chunk_id": "doc_02",
            "text": "ClickHouse utilizes vectorized columnar execution for high-throughput analytical query processing.",
            "doc_title": "ClickHouse Internals",
            "internal_score": 0.94,
            "doc_url": "https://clickhouse.com/docs",
        },
    ]

    # 3. Execute projection decorator
    envelope = prepare_llm_prompt_context(retrieved_chunks)

    print("CODA_MUR Context Projection Envelope:")
    print(f"  Context Admitted: {envelope.admitted}")
    print(f"  Canonical Terminal: {envelope.canonical_terminal}")
    print(f"  Source Tokens: {envelope.source_token_count}")
    print(f"  Retained Tokens: {envelope.retained_token_count}")
    print(f"  Truncated Tokens: {envelope.truncated_token_count}")
    print(f"  Token Conservation Commutes: {envelope.token_conservation_commutes}")

    # 4. Inspect and cryptographically verify the LossLedger artifact
    loss_ledger = envelope.loss_ledger
    assert loss_ledger is not None, "LossLedger must be generated on attribute erasure or truncation."
    assert loss_ledger["sealed"] is True, "LossLedger must be cryptographically sealed."

    is_valid, err_msg = verify_loss_ledger_integrity(loss_ledger)
    print(f"\nCryptographic LossLedger Verification:")
    print(f"  Integrity Verified: {is_valid}")
    print(f"  SHA-256 Merkle Digest: {loss_ledger['merkle_digest']}")
    print(f"  Erased Attributes Recorded: {loss_ledger['erased_attributes']}")
    print(f"  Tracked Entries Count: {loss_ledger['record_count']}")

    # 5. Enforce Epistemic Authority Firewall
    print(f"\nEpistemic Authority Firewall:")
    print(f"  Certified: {envelope.certified}")
    print(f"  Authorized: {envelope.authorized} (Enforces certified_implies_authorized == False)")
    print(f"  Authority Effect: {envelope.authority_effect}")


if __name__ == "__main__":
    run_ai_context_lossledger_pipeline()
```

---

## 4. Architecture & Extensibility: Adding Custom Normal Forms

An external developer can extend `simplex-normal-forms` or integrate proprietary validation rules into their own data pipelines through two extension paths:

```
+-------------------------------------------------------------------------------+
|                       Extension Architecture Overview                         |
+-------------------------------------------------------------------------------+
|                                                                               |
|  Path A: Compiler IR Kernel Extension (normal_forms/ir_kernel.py)             |
|    - Define an NFKernelSpec(contract_id, key, collapse, protected, mode)      |
|    - Leverage poset subsumption optimization (ir_subsumption.py)             |
|    - Compose via Operadic DAG combinators (ir_wiring.py: seq, par, guard)     |
|    - Lower to SQLite triggers and Python guards (ir_lowering.py)              |
|                                                                               |
|  Path B: Relational Domain Extension (normal_forms/domain/)                   |
|    - Implement an Armstrong axiom decision procedure                         |
|    - Expose check_<custom_nf>(schema: RelationalSchema) -> tuple[bool, str]   |
|    - Plug into synthesize_3nf_bernstein or Tableau Chase pipelines            |
|                                                                               |
+-------------------------------------------------------------------------------+
```

### 4.1 Path A: Creating Custom Normal Forms via NF-IR Micro-Kernel

Every verification rule in the NF-IR compiler stack is modeled as a mathematical triple:
$$K = (\text{Carrier } X, \text{Collapse Map } F: X \to Y, \text{Protected Law } L)$$

To define a custom normal form:
1. Create an `NFKernelSpec` declaring the key field, determinant collapse fields, and protected fields.
2. Evaluate via `evaluate_nf_kernel`:

```python
from normal_forms.ir_kernel import NFKernelSpec, evaluate_nf_kernel

# Define custom tenant isolation normal form
custom_tenant_spec = NFKernelSpec(
    contract_id="nf.custom.tenant_isolation",
    key_field="resource_id",
    distinction_fields=("resource_id",),
    collapse_fields=("tenant_id", "cluster_id"),
    protected_law_fields=("security_zone", "encryption_key_id"),
    law_mode="functional_dependency",
    require_support_floor=True,  # Requires at least 2 records to test distinction
)

carrier_rows = [
    {"resource_id": "res_1", "tenant_id": "T1", "cluster_id": "C1", "security_zone": "zone-a", "encryption_key_id": "k1"},
    {"resource_id": "res_2", "tenant_id": "T1", "cluster_id": "C1", "security_zone": "zone-b", "encryption_key_id": "k1"},
]

receipt = evaluate_nf_kernel(custom_tenant_spec, carrier_rows)
print("Custom Kernel Evaluation Outcome:", receipt.canonical_terminal)  # Output: Reject
print("Witness Pair:", receipt.minimal_counterexample)
```

### 4.2 Path B: Extending Relational Decision Procedures

To add domain-specific relational normalization checks, implement a function accepting a `RelationalSchema` and returning a `(is_valid: bool, diagnostic: Optional[str])` tuple:

```python
from typing import Optional, Tuple
from normal_forms.domain.relational import RelationalSchema, FunctionalDependency

def check_strict_auditing_nf(schema: RelationalSchema) -> Tuple[bool, Optional[str]]:
    """Custom Normal Form: Asserts that every update audit field depends directly on candidate keys."""
    cand_keys = schema.candidate_keys()
    for fd in schema.dependencies:
        if "updated_by" in fd.dependent or "updated_at" in fd.dependent:
            if not schema.is_superkey(fd.determinant):
                return False, f"Audit attribute in {fd.dependent} determined by non-superkey {fd.determinant}"
    return True, None
```

---

## 5. Deployment Guide: Companion Web Interface

The repository includes a companion web application, **Simplex-NF Studio ("The Normal Form Workbench")**, configured for production deployment at `smplxnf.anomalon.com` on Render (`onrender.com`).

### 5.1 Local Development Server

Run the interactive web dashboard locally:

```bash
# Start local ASGI server with hot-reloading
uvicorn web.app:app --reload --host 127.0.0.1 --port 8000
```

Verify the health check endpoint:

```bash
curl http://127.0.0.1:8000/healthz
# Response: {"status":"ok","service":"smplxnf-studio","version":"0.1.0"}
```

Open `http://127.0.0.1:8000` in any modern web browser to interact with the Relational Studio, Streaming BQNF Simulator, NF-IR Compiler Explorer, and AI LossLedger Gateway.

### 5.2 Deploying to Render (`onrender.com`)

The repository includes a declarative `render.yaml` blueprint:

```yaml
services:
  - type: web
    name: smplxnf-studio
    env: python
    region: oregon
    plan: starter
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

#### Step-by-Step Render Deployment:
1. Connect your GitHub repository to Render at [dashboard.render.com](https://dashboard.render.com).
2. Select **New > Blueprint** and link the repository. Render will automatically parse `render.yaml`.
3. Configure the custom domain in your DNS provider:
   - Record Type: `CNAME`
   - Host: `smplxnf.anomalon.com`
   - Value: `smplxnf-studio.onrender.com`
4. Render provisions and renews TLS/SSL certificates automatically via Let's Encrypt.

---

## 6. Epistemic Claim Hygiene Quadrant

In adherence to project claim discipline, the capabilities and operational bounds of the software in this guide are summarized across four dimensions:

### 1. What it supports:
- Supports deterministic computation of Armstrong attribute closures, candidate keys, prime attribute partitions, and minimal covers.
- Supports dependency-preserving, lossless-join 3NF decomposition via Bernstein's (1976) algorithm, and BCNF tree decompositions.
- Supports deterministic Tableau Chase verification with concrete spurious tuple counterexample generation for lossy join dependencies.
- Supports exact $O(1)$ signed coboundary delta repair on additive boundary queries and $O(\log K)$ extremum maintenance under destructive deletions via priority-queue cochains in the tested SQLite model.
- Supports dynamic dyadic bucket bisection splitting and bottom-up cousin merging under skewed data streams, maintaining mass conservation and disjointness invariants.
- Supports lowering declarative kernel contracts to executable Python guards and SQLite `BEFORE INSERT` / `BEFORE UPDATE` trigger DDL.
- Supports exact token conservation accounting ($\text{retained\_tokens} + \text{truncated\_tokens} == \text{source\_tokens}$) and SHA-256 Merkle loss ledger generation for RAG context transport.

### 2. What it does not support:
- Does not confer operational or execution authority (`AuthorityEffect: None`, `certified_implies_authorized: false`).
- Does not assert that pure-Python relational algorithms scale to tables with dozens of cyclic attributes without combinatorial bounding.
- Does not claim that single-node SQLite test fixtures replace distributed consensus or multi-node fault-tolerant replication protocols.
- Does not assert that 3NF or BCNF normalization eliminates application-level semantic errors outside declared functional dependencies.

### 3. The narrowest defensible claim:
- In the declared discrete Python implementation, the relational synthesis algorithms, Chase tableau procedures, BQNF delta accumulation, and 4-layer NF-IR pipeline execute deterministically and pass all 136 automated tests in `simplex-normal-forms/tests/`.

### 4. The next test needed:
- A high-concurrency multi-tenant benchmark measuring end-to-end latency and memory utilization when streaming 100,000 PostgreSQL WAL replication events through the deployed FastAPI service on Render.
