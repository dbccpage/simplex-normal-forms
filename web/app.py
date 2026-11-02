"""Simplex Normal Forms Studio Web Backend.

FastAPI application delivering interactive access to classical relational normalization,
streaming BQNF boundary repair with dyadic quantile sketches, the 4-layer NF-IR compiler,
and cryptographic AI Model Context Protocol LossLedger token accounting.

AuthorityEffect: None.
certified_implies_authorized: false.
"""

from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
import json
import math
import os
import re
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# Core normal_forms library imports
from normal_forms.domain.relational import (
    FunctionalDependency,
    RelationalSchema,
    check_1nf,
    check_2nf,
    check_3nf,
    check_bcnf,
    compute_attribute_closure,
    compute_minimal_cover,
    chase_join_dependency,
)
from normal_forms.domain.relational_advanced import (
    check_eknf,
    decompose_bcnf_tree,
    synthesize_3nf_bernstein,
)
from normal_forms.domain.bqnf_validator import (
    BqnfBoundary,
    BqnfCdcEvent,
    BqnfEvaluationResult,
    BqnfValidator,
)
from normal_forms.bqnf_extrema import (
    RepairTally,
    accumulate_delta,
    apply_addition,
    apply_removal,
)
from normal_forms.sales_cochain import (
    cochain_add,
    cochain_remove,
    quantile_cochain_add,
    quantile_cochain_remove,
    rebalance_quantile_cochain,
)
from normal_forms.ir_kernel import (
    ConstructiveWitnessPair,
    NFKernelSpec,
    evaluate_nf_kernel,
    lower_fd_to_kernel_spec,
)
from normal_forms.ir_subsumption import (
    run_kernel_pipeline_with_dce,
    subsumes_kernel_spec,
)
from normal_forms.ir_lowering import (
    SqliteLoweredBundle,
    compile_to_sqlite_triggers,
    install_and_verify_sqlite_bundle,
    synthesize_counterexample_fixtures,
)
from normal_forms.ai import (
    coda_mur_projection,
    tokenize_whitespace,
    verify_loss_ledger_integrity,
)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Simplex Normal Forms Studio",
    description="Interactive Relational Synthesis, Streaming BQNF Delta Repair & NF-IR Compiler Workbench",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = BASE_DIR / "static"
templates_dir = BASE_DIR / "templates"
static_dir.mkdir(parents=True, exist_ok=True)
templates_dir.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))


# =============================================================================
# Healthcheck Endpoint
# =============================================================================

@app.get("/healthz")
async def healthz() -> Dict[str, str]:
    return {
        "status": "ok",
        "service": "smplxnf-studio",
        "version": "0.1.0",
    }


# =============================================================================
# Presets Catalog
# =============================================================================

PRESETS: Dict[str, Dict[str, Any]] = {
    "ecommerce": {
        "title": "E-Commerce Orders & Fulfillment (3NF Violation)",
        "description": "Customer order fulfillment exhibiting transitive dependency (customer_id -> customer_email, zip -> city) and non-prime partial dependencies.",
        "attributes": [
            "order_id",
            "item_id",
            "customer_id",
            "customer_email",
            "quantity",
            "unit_price",
            "zip_code",
            "city",
        ],
        "dependencies": [
            "order_id -> customer_id, zip_code",
            "customer_id -> customer_email",
            "item_id -> unit_price",
            "order_id, item_id -> quantity",
            "zip_code -> city",
        ],
    },
    "supply_chain": {
        "title": "Supply Chain Dispatch & Logistics Fleet",
        "description": "Logistics tracking system where carrier and vehicle assignments violate BCNF.",
        "attributes": [
            "dispatch_id",
            "carrier_code",
            "carrier_name",
            "origin_hub",
            "destination_hub",
            "vehicle_vin",
            "driver_license",
            "driver_name",
        ],
        "dependencies": [
            "dispatch_id -> carrier_code, origin_hub, destination_hub, vehicle_vin, driver_license",
            "carrier_code -> carrier_name",
            "driver_license -> driver_name",
            "vehicle_vin -> carrier_code",
        ],
    },
    "healthcare": {
        "title": "Healthcare Clinic & Attending Staff Wards",
        "description": "Patient clinic management with candidate keys (patient_id, ssn) and ward head-nurse dependencies.",
        "attributes": [
            "patient_id",
            "ssn",
            "patient_name",
            "ward_id",
            "ward_building",
            "head_nurse",
        ],
        "dependencies": [
            "patient_id -> ssn, patient_name, ward_id",
            "ssn -> patient_id",
            "ward_id -> ward_building, head_nurse",
        ],
    },
    "lossy_decomposition": {
        "title": "Lossy Decomposition Demonstration (Spurious Tuples)",
        "description": "A classic lossy decomposition of R(A, B, C) with A -> B into R1(A, B) and R2(B, C), demonstrating how the Chase produces a non-distinguished row and spurious counterexample witness.",
        "attributes": ["A", "B", "C"],
        "dependencies": ["A -> B"],
        "custom_components": [["A", "B"], ["B", "C"]],
    },
}

BQNF_PRESETS: Dict[str, Dict[str, Any]] = {
    "financial_ledger": {
        "title": "Financial Ledger CDC Stream",
        "description": "Real-time CDC stream on financial orders with status transitions and destructive extremum deletions.",
        "boundary": {
            "relations": ["sales"],
            "attributes": ["amount", "status", "region"],
            "predicates": ["status = paid"],
            "aggregates": ["SUM(amount)", "MAX(amount)"],
            "groups": ["region"],
        },
        "initial_sales": [
            {"region": "North", "amount": 25.0},
            {"region": "North", "amount": 60.0},
            {"region": "North", "amount": 120.0},
            {"region": "North", "amount": 250.0},
            {"region": "South", "amount": 80.0},
        ],
        "events": [
            {
                "op": "INSERT",
                "relation": "sales",
                "old": None,
                "new": {"region": "North", "amount": 45.0, "status": "paid"},
            },
            {
                "op": "UPDATE",
                "relation": "sales",
                "old": {"region": "North", "amount": 45.0, "status": "paid"},
                "new": {"region": "North", "amount": 75.0, "status": "paid"},
            },
            {
                "op": "DELETE",
                "relation": "sales",
                "old": {"region": "North", "amount": 250.0, "status": "paid"},
                "new": None,
            },
        ],
    }
}

COMPILER_PRESETS: Dict[str, Dict[str, Any]] = {
    "employee_bcnf": {
        "title": "Department Manager BCNF Kernel Guard",
        "contract_id": "nf.classical.bcnf",
        "key_field": "employee_id",
        "heading": ["employee_id", "dept_id", "manager_id", "office_location"],
        "determinant": ["dept_id"],
        "dependent": ["manager_id"],
        "table_name": "employees",
        "test_carrier": [
            {"employee_id": "E101", "dept_id": "D1", "manager_id": "M1", "office_location": "Bldg-A"},
            {"employee_id": "E102", "dept_id": "D1", "manager_id": "M1", "office_location": "Bldg-B"},
            {"employee_id": "E103", "dept_id": "D2", "manager_id": "M2", "office_location": "Bldg-C"},
        ],
    }
}

AI_PRESETS: Dict[str, Dict[str, Any]] = {
    "rag_research_context": {
        "title": "Database Research RAG Context Budgeting",
        "source_chunks": [
            {
                "chunk_id": "chunk_1",
                "doc_title": "Relational Theory",
                "text": "First normal form requires that all attribute values be atomic scalars with zero repeating groups.",
                "relevance_score": 0.98,
                "internal_debug_trace": "embed_0.9812",
                "vector_norm": 1.002,
            },
            {
                "chunk_id": "chunk_2",
                "doc_title": "Relational Theory",
                "text": "Boyce Codd normal form guarantees under the declared assumptions that every non trivial determinant is a superkey of the relation.",
                "relevance_score": 0.94,
                "internal_debug_trace": "embed_0.9401",
                "vector_norm": 0.998,
            },
            {
                "chunk_id": "chunk_3",
                "doc_title": "Compiler Optimizations",
                "text": "Dead check elimination on partial orders elides redundant downstream verifications with zero loss of safety.",
                "relevance_score": 0.88,
                "internal_debug_trace": "embed_0.8810",
                "vector_norm": 1.011,
            },
            {
                "chunk_id": "chunk_4",
                "doc_title": "Incremental Computing",
                "text": "Boundary quotients maintain streaming aggregates without expensive full recomputations on base relations.",
                "relevance_score": 0.72,
                "internal_debug_trace": "embed_0.7230",
                "vector_norm": 0.995,
            },
        ],
        "target_fields": ["chunk_id", "doc_title", "text", "relevance_score"],
        "max_token_budget": 35,
        "key_field": "chunk_id",
        "protected_fields": ["chunk_id", "doc_title"],
        "score_field": "relevance_score",
        "text_field": "text",
    }
}


@app.get("/api/presets")
async def get_presets() -> Dict[str, Any]:
    return {
        "relational": PRESETS,
        "bqnf": BQNF_PRESETS,
        "compiler": COMPILER_PRESETS,
        "ai": AI_PRESETS,
    }


# =============================================================================
# Module 1: Relational Synthesis & Chase Tableau
# =============================================================================

class RelationalNormalizeRequest(BaseModel):
    attributes: List[str]
    dependencies: List[Any]
    custom_components: Optional[List[List[str]]] = None


def _parse_fd(fd_item: Any) -> FunctionalDependency:
    if isinstance(fd_item, str):
        if "->" not in fd_item:
            raise ValueError(f"Invalid dependency string '{fd_item}', must contain '->'")
        det_str, dep_str = fd_item.split("->", 1)
        det = frozenset(x.strip() for x in det_str.split(",") if x.strip())
        dep = frozenset(x.strip() for x in dep_str.split(",") if x.strip())
        return FunctionalDependency(det, dep)
    elif isinstance(fd_item, dict):
        det = frozenset(fd_item.get("determinant", []))
        dep = frozenset(fd_item.get("dependent", []))
        return FunctionalDependency(det, dep)
    raise ValueError(f"Unsupported functional dependency format: {fd_item}")


@app.post("/api/relational/normalize")
async def normalize_relational_schema(payload: RelationalNormalizeRequest) -> Dict[str, Any]:
    if len(payload.attributes) > 20:
        raise HTTPException(
            status_code=400,
            detail="Attribute count exceeds maximum limit (20)",
        )
    try:
        attrs = frozenset(a.strip() for a in payload.attributes if a.strip())
        if not attrs:
            raise ValueError("Attribute heading cannot be empty")
        if len(attrs) > 20:
            raise HTTPException(
                status_code=400,
                detail="Attribute count exceeds maximum limit (20)",
            )

        fds = frozenset(_parse_fd(item) for item in payload.dependencies)
        schema = RelationalSchema(attributes=attrs, dependencies=fds)

        # 1. Candidate Keys and Prime/Non-Prime Attributes
        cand_keys = [sorted(k) for k in schema.candidate_keys()]
        prime_attrs = sorted(schema.prime_attributes())
        non_prime_attrs = sorted(attrs - schema.prime_attributes())

        # 2. Normal Form Decision Verifications
        ok_1nf, reason_1nf = check_1nf(schema)
        ok_2nf, reason_2nf = check_2nf(schema)
        ok_3nf, reason_3nf = check_3nf(schema)
        ok_bcnf, reason_bcnf = check_bcnf(schema)
        ok_eknf, reason_eknf = check_eknf(schema)

        # 3. Minimal (Canonical) Cover
        min_cover_fds = compute_minimal_cover(schema.dependencies)
        minimal_cover = [str(fd) for fd in sorted(min_cover_fds, key=lambda f: (tuple(sorted(f.determinant)), tuple(sorted(f.dependent))))]

        # 4. Bernstein's (1976) 3NF Synthesis (Lossless-Join & Dependency-Preserving)
        synthesized_raw = synthesize_3nf_bernstein(schema)
        synthesized_3nf: List[Dict[str, Any]] = []
        for idx, sub_attrs in enumerate(synthesized_raw, 1):
            sub_keys = [sorted(k) for k in cand_keys if frozenset(k).issubset(sub_attrs)]
            synthesized_3nf.append({
                "table_name": f"rel_3nf_table_{idx}",
                "attributes": sorted(sub_attrs),
                "candidate_keys": sub_keys if sub_keys else [sorted(sub_attrs)],
            })

        # 5. Tsou-Fischer BCNF Decomposition Tree
        bcnf_leaves = decompose_bcnf_tree(schema)
        bcnf_tree: List[Dict[str, Any]] = []
        for idx, s in enumerate(bcnf_leaves, 1):
            bcnf_tree.append({
                "table_name": f"bcnf_table_{idx}",
                "attributes": sorted(s.attributes),
                "dependencies": [str(f) for f in sorted(s.dependencies, key=str)],
                "candidate_keys": [sorted(k) for k in s.candidate_keys()],
            })

        # 6. Relational Tableau Chase Execution
        components_to_chase = (
            [frozenset(c) for c in payload.custom_components]
            if payload.custom_components
            else synthesized_raw
        )
        chase_res = chase_join_dependency(
            heading=sorted(attrs),
            dependencies=schema.dependencies,
            components=components_to_chase,
        )

        steps_data: List[Dict[str, Any]] = []
        for s in chase_res.steps:
            steps_data.append({
                "step_number": s.step_number,
                "fd": str(s.fd_applied),
                "rows_matched": list(s.rows_matched),
                "attribute_equated": s.attribute_equated,
                "old_symbol": s.old_symbol,
                "new_symbol": s.new_symbol,
            })

        # Generate SQL DDL
        sql_ddl_statements: List[str] = []
        for table in synthesized_3nf:
            cols = ", ".join(f'"{col}" TEXT' for col in table["attributes"])
            pk_cols = ", ".join(f'"{c}"' for c in table["candidate_keys"][0]) if table["candidate_keys"] else ""
            pk_clause = f", PRIMARY KEY ({pk_cols})" if pk_cols else ""
            sql_ddl_statements.append(f'CREATE TABLE "{table["table_name"]}" ({cols}{pk_clause});')

        return {
            "attributes": sorted(attrs),
            "candidate_keys": cand_keys,
            "prime_attributes": prime_attrs,
            "non_prime_attributes": non_prime_attrs,
            "normal_forms": {
                "1NF": {"passed": ok_1nf, "reason": reason_1nf},
                "2NF": {"passed": ok_2nf, "reason": reason_2nf},
                "3NF": {"passed": ok_3nf, "reason": reason_3nf},
                "EKNF": {"passed": ok_eknf, "reason": reason_eknf},
                "BCNF": {"passed": ok_bcnf, "reason": reason_bcnf},
            },
            "minimal_cover": minimal_cover,
            "synthesized_3nf": synthesized_3nf,
            "bcnf_tree": bcnf_tree,
            "chase": {
                "is_implied": chase_res.is_implied,
                "status": chase_res.status,
                "heading": list(chase_res.heading),
                "components": [list(c) for c in chase_res.components],
                "steps_count": len(chase_res.steps),
                "steps": steps_data,
                "initial_tableau": list(chase_res.initial_tableau),
                "final_tableau": list(chase_res.final_tableau),
                "distinguished_row_index": chase_res.distinguished_row_index,
                "spurious_tuple_witness": chase_res.spurious_tuple_witness,
            },
            "sql_ddl": "\n".join(sql_ddl_statements),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# =============================================================================
# Module 2: Streaming BQNF Delta Repair & Quantile Rebalancer
# =============================================================================

class BqnfSimulateRequest(BaseModel):
    boundary: Dict[str, Any]
    events: List[Dict[str, Any]]
    initial_sales: Optional[List[Dict[str, Any]]] = None
    use_cochain: bool = True
    bucket_width: float = 20.0
    split_threshold: int = 4
    merge_threshold: int = 1
    min_bucket_width: float = 2.5


@app.post("/api/bqnf/simulate")
async def simulate_bqnf_stream(payload: BqnfSimulateRequest) -> Dict[str, Any]:
    conn = None
    try:
        boundary = BqnfBoundary.from_dict(payload.boundary)
        # This workbench maintains a single sales relation grouped by region.
        # Its exact extremum state (or base-table fallback) supplies MIN/MAX;
        # the scalar domain validator handles routing and SUM predicate deltas.
        if (len(boundary.relations) != 1 or boundary.groups != ("region",)
                or not {"region", "amount"} <= set(boundary.attributes)
                or not boundary.aggregates
                or not set(boundary.aggregates) <= {"SUM(amount)", "MIN(amount)", "MAX(amount)"}):
            raise ValueError("Simulator requires one relation, region grouping, region/amount attributes, and SUM/MIN/MAX(amount).")
        if len(boundary.predicates) > 1:
            raise ValueError("Simulator supports at most one equality predicate.")
        predicate_parts = None
        if boundary.predicates:
            match = re.fullmatch(r"\s*(\w+)\s*=\s*([^=<>!]+)\s*", boundary.predicates[0])
            if not match or match[1] != "status" or "status" not in boundary.attributes:
                raise ValueError("Simulator predicate must be status = value with status declared.")
            predicate_parts = (match[1], match[2].strip().strip("'\""))
        if (not math.isfinite(payload.bucket_width) or not math.isfinite(payload.min_bucket_width)
                or not 0 < payload.min_bucket_width <= payload.bucket_width
                or payload.split_threshold < 2
                or not 0 <= payload.merge_threshold < payload.split_threshold):
            raise ValueError("Invalid quantile widths or split/merge thresholds.")
        routing_boundary = replace(boundary, aggregates=("SUM(amount)",))
        eval_results: List[Dict[str, Any]] = []

        # 2. In-Memory SQLite Cochain & Dyadic-Bucket Quantile Simulation
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE base_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT,
                amount REAL,
                status TEXT
            );
        """)
        cur.execute("""
            CREATE TABLE region_extremum_cochain (
                region TEXT,
                amount REAL,
                frequency INTEGER,
                PRIMARY KEY (region, amount)
            );
        """)
        cur.execute("""
            CREATE TABLE region_quantile_cochain (
                region TEXT,
                bucket_id INTEGER,
                lower_bound REAL,
                upper_bound REAL,
                count INTEGER,
                PRIMARY KEY (region, bucket_id)
            );
        """)
        cur.execute("""
            CREATE TABLE extrema_repair_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT,
                op_type TEXT,
                affected_amount REAL,
                is_destructive INTEGER,
                cochain_available INTEGER,
                terminal_route TEXT,
                old_min REAL,
                new_min REAL,
                old_max REAL,
                new_max REAL,
                recomputation_fallback_executed INTEGER
            );
        """)

        # Populate initial state
        initial_sales = payload.initial_sales if payload.initial_sales is not None else [
            {"region": "North", "amount": 25.0},
            {"region": "North", "amount": 60.0},
            {"region": "North", "amount": 120.0},
            {"region": "North", "amount": 250.0},
            {"region": "South", "amount": 80.0},
        ]
        current_cache: Dict[str, Dict[str, Any]] = {}
        tally = RepairTally()

        def active(image: Dict[str, Any]) -> bool:
            return predicate_parts is None or str(image.get(predicate_parts[0], "")) == predicate_parts[1]

        def sale(image: Dict[str, Any]) -> Tuple[str, float, str]:
            region = image["region"]
            amount = float(image["amount"])
            if not isinstance(region, str) or not region or not math.isfinite(amount):
                raise ValueError("Sales require a nonempty region and finite amount.")
            return region, amount, str(image.get("status", "paid"))

        def add_sale(image: Dict[str, Any]) -> None:
            r, a, status = sale(image)
            cur.execute("INSERT INTO base_sales (region, amount, status) VALUES (?, ?, ?);", (r, a, status))
            cochain_add(conn, r, a)
            quantile_cochain_add(conn, r, a, payload.bucket_width, payload.min_bucket_width)
            apply_addition(cur, current_cache, r, a, "INSERT", payload.use_cochain, tally)

        for s in initial_sales:
            image = {"status": "paid", **s}
            sale(image)
            if active(image):
                add_sale(image)

        # Initialization is not a CDC repair.
        cur.execute("DELETE FROM extrema_repair_log;")
        tally = RepairTally()
        # Execute CDC events
        for ev_dict in payload.events:
            ev = BqnfCdcEvent.from_dict(ev_dict)
            res = BqnfValidator.evaluate(routing_boundary, ev)
            # The scalar routing delta is not a grouped mutation receipt.
            # Populate repair only from the removals/additions actually applied.
            decision = {**res.to_dict(), "op": ev.op, "relation": ev.relation, "applied": False, "repair": None}
            eval_results.append(decision)
            if res.decision != "Repair" or not res.certified or not res.evidence_sufficient:
                continue
            old_img, new_img = ev.old or {}, ev.new or {}
            remove = ev.op in {"UPDATE", "DELETE"} and active(old_img)
            insert = ev.op in {"UPDATE", "INSERT"} and active(new_img)
            region_deltas: Dict[str, Dict[str, Any]] = {}

            def record_delta(region: str, amount: float, count: int) -> None:
                delta = region_deltas.setdefault(region, {"delta_revenue": 0.0, "delta_count": 0})
                delta["delta_revenue"] += amount
                delta["delta_count"] += count

            # Validate both halves before making any state change.
            if insert:
                sale(new_img)
            if remove:
                r, a, status = sale(old_img)
                # A Preserve event need not maintain untracked metadata. Do not
                # use that metadata as identity for a later active before-image.
                match_sql = "SELECT id FROM base_sales WHERE region = ? AND amount = ?"
                match_values: List[Any] = [r, a]
                if "status" in boundary.attributes:
                    match_sql += " AND status = ?"
                    match_values.append(status)
                old_row = cur.execute(match_sql + " LIMIT 1;", match_values).fetchone()
                if old_row is None:
                    decision.update(decision="Invalidate", terminal_route="Invalidate", certified=False,
                                    evidence_sufficient=False, repair=None,
                                    obstruction_class="[NonZero - MissingEvidence]",
                                    reason="Before-image has no matching retained sale; event was not applied.")
                    continue
                cur.execute("DELETE FROM base_sales WHERE id = ?;", (old_row["id"],))
                cochain_remove(conn, r, a)
                quantile_cochain_remove(conn, r, a, payload.bucket_width)
                apply_removal(cur, current_cache, r, a, payload.use_cochain, tally)
                record_delta(r, -a, -1)
            if insert:
                add_sale(new_img)
                r, a, _ = sale(new_img)
                record_delta(r, a, 1)
            decision["applied"] = remove or insert
            if decision["applied"]:
                decision["repair"] = {"region_deltas": region_deltas}

        conn.commit()

        # Rebalance quantiles after event stream
        reb_receipts = {
            region: rebalance_quantile_cochain(
                conn, region=region, bucket_width=payload.bucket_width,
                split_threshold=payload.split_threshold, merge_threshold=payload.merge_threshold,
                min_bucket_width=payload.min_bucket_width,
            ) for region in sorted(set(current_cache) | {"North"})
        }

        # Retrieve repair log entries
        cur.execute("SELECT * FROM extrema_repair_log ORDER BY id ASC;")
        repair_log = [dict(row) for row in cur.fetchall()]

        # Retrieve active quantile buckets
        cur.execute("SELECT region, bucket_id, lower_bound, upper_bound, count FROM region_quantile_cochain WHERE count > 0 ORDER BY region, lower_bound ASC;")
        buckets = [dict(row) for row in cur.fetchall()]

        # Active extremum cochain entries
        cur.execute("SELECT region, amount, frequency FROM region_extremum_cochain ORDER BY region, amount ASC;")
        extremum_entries = [dict(row) for row in cur.fetchall()]

        return {
            "events_evaluated": len(eval_results),
            "event_decisions": eval_results,
            "extrema_repair_log": repair_log,
            "extremum_cochain_entries": extremum_entries,
            "quantile_rebalance_receipt": reb_receipts["North"],
            "quantile_rebalance_receipts": reb_receipts,
            "final_cache": {
                region: {key: state[key] for key in ("total_sales", "sale_count", "min_amount", "max_amount")}
                for region, state in current_cache.items()
            },
            "quantile_buckets": buckets,
            "repair_tally": asdict(tally),
            "cochain_speedup": (
                "O(log K) priority queue lookup executed without full table scan"
                if payload.use_cochain
                else "O(N) full table scan executed via fallback recomputation"
            ),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        if conn is not None:
            conn.close()


# =============================================================================
# Module 3: NF-IR Compiler Playground (Godbolt-Style Inspector)
# =============================================================================

class CompilerLowerRequest(BaseModel):
    contract_id: str = "nf.classical.bcnf"
    key_field: str = "employee_id"
    heading: List[str] = ["employee_id", "dept_id", "manager_id", "office_location"]
    determinant: List[str] = ["dept_id"]
    dependent: List[str] = ["manager_id"]
    law_mode: str = "functional_dependency"
    table_name: str = "employees"
    test_carrier: Optional[List[Dict[str, Any]]] = None


@app.post("/api/compiler/lower")
async def lower_nf_ir(payload: CompilerLowerRequest) -> Dict[str, Any]:
    try:
        fd = FunctionalDependency(frozenset(payload.determinant), frozenset(payload.dependent))
        spec = lower_fd_to_kernel_spec(
            fd=fd,
            key_field=payload.key_field,
            heading=payload.heading,
            contract_id=payload.contract_id,
            require_support_floor=False,
        )

        # 1. Target B: Lower to SQLite Triggers
        bundle: SqliteLoweredBundle = compile_to_sqlite_triggers(spec, table_name=payload.table_name)

        # 2. Poset Subsumption & Dead-Check Elimination (DCE) analysis
        contract_downgrade = {
            "nf.classical.6nf": "nf.classical.5nf",
            "nf.classical.5nf": "nf.classical.4nf",
            "nf.classical.4nf": "nf.classical.bcnf",
            "nf.classical.bcnf": "nf.classical.3nf",
            "nf.classical.3nf": "nf.classical.2nf",
            "nf.classical.2nf": "nf.classical.1nf",
            "nf.classical.1nf": "nf.classical.0nf",
        }
        weaker_contract = contract_downgrade.get(
            payload.contract_id,
            "nf.classical.2nf" if payload.contract_id == "nf.classical.3nf" else "nf.classical.3nf",
        )
        weaker_spec = lower_fd_to_kernel_spec(
            fd=FunctionalDependency(frozenset(payload.determinant), frozenset(payload.dependent)),
            key_field=payload.key_field,
            heading=payload.heading,
            contract_id=weaker_contract,
            require_support_floor=False,
        )
        is_subsumed, subsume_reason = subsumes_kernel_spec(spec, weaker_spec)

        dce_pipeline = [spec, weaker_spec]
        if payload.test_carrier:
            carrier_for_dce = payload.test_carrier
        else:
            row1: Dict[str, Any] = {payload.key_field: "1"}
            row2: Dict[str, Any] = {payload.key_field: "2"}
            for col in payload.heading:
                if col != payload.key_field:
                    row1[col] = f"{col}_v1"
                    row2[col] = f"{col}_v2"
            carrier_for_dce = [row1, row2]
        dce_receipt = run_kernel_pipeline_with_dce(dce_pipeline, carrier_for_dce)

        # 3. Automated Counterexample Fuzzing Synthesizer
        valid_rows, failing_fixtures = synthesize_counterexample_fixtures(spec, seed=42)
        counterexamples = [
            {
                "failure_kind": f.failure_kind,
                "expected_terminal": f.expected_canonical_terminal,
                "carrier_rows": list(f.carrier_rows),
            }
            for f in failing_fixtures
        ]

        # 4. Target A: Generate Python Guard Decorator Code
        python_guard_code = f'''from normal_forms.ir_lowering import compile_to_python_decorator
from normal_forms.ir_kernel import lower_fd_to_kernel_spec
from normal_forms.domain.relational import FunctionalDependency

spec = lower_fd_to_kernel_spec(
    fd=FunctionalDependency(frozenset({payload.determinant!r}), frozenset({payload.dependent!r})),
    key_field={payload.key_field!r},
    heading={payload.heading!r},
    contract_id={payload.contract_id!r},
)

@compile_to_python_decorator(spec)
def process_batch(rows):
    """Executes with fail-closed security only if rows satisfy {payload.contract_id}."""
    return f"Successfully processed {{len(rows)}} certified rows."
'''

        # 5. Optional verification on test carrier
        eval_result = None
        sqlite_test_ok = None
        sqlite_test_err = None
        if payload.test_carrier:
            k_receipt = evaluate_nf_kernel(spec, payload.test_carrier)
            eval_result = {
                "contract_id": k_receipt.contract_id,
                "canonical_terminal": k_receipt.canonical_terminal,
                "admitted": k_receipt.admitted,
                "certified": k_receipt.certified,
                "authorized": k_receipt.authorized,
                "witness_pair": (
                    {
                        "left_id": k_receipt.minimal_counterexample.left_id,
                        "right_id": k_receipt.minimal_counterexample.right_id,
                        "witness_kind": k_receipt.minimal_counterexample.witness_kind,
                        "feature": k_receipt.minimal_counterexample.feature,
                        "left_value": k_receipt.minimal_counterexample.left_value,
                        "right_value": k_receipt.minimal_counterexample.right_value,
                    }
                    if k_receipt.minimal_counterexample
                    else None
                ),
                "reason": k_receipt.reason,
            }

            test_conn = sqlite3.connect(":memory:")
            sqlite_test_ok, sqlite_test_err = install_and_verify_sqlite_bundle(test_conn, bundle, payload.test_carrier)
            test_conn.close()

        return {
            "kernel_spec": {
                "contract_id": spec.contract_id,
                "key_field": spec.key_field,
                "distinction_fields": list(spec.distinction_fields),
                "collapse_fields": list(spec.collapse_fields),
                "protected_law_fields": list(spec.protected_law_fields),
                "law_mode": spec.law_mode,
            },
            "subsumption_analysis": {
                "compared_against": weaker_spec.contract_id,
                "is_subsumed": is_subsumed,
                "subsume_reason": subsume_reason,
                "executed_specs_count": dce_receipt.executed_pass_count,
                "elided_specs_count": dce_receipt.elided_pass_count,
                "elided_records": [
                    {
                        "elided_spec": r.elided_contract_id,
                        "subsuming_spec": r.subsumed_by_contract_id,
                        "reason": r.reason,
                    }
                    for r in dce_receipt.elided_records
                ],
            },
            "sqlite_ddl": {
                "table_name": bundle.table_name,
                "create_table_sql": bundle.create_table_sql,
                "before_insert_trigger_sql": bundle.before_insert_trigger_sql,
                "before_update_trigger_sql": bundle.before_update_trigger_sql,
            },
            "sqlite_verification": {
                "verified": sqlite_test_ok,
                "error": sqlite_test_err,
            },
            "python_guard_code": python_guard_code,
            "synthesized_counterexamples": counterexamples,
            "carrier_evaluation": eval_result,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# =============================================================================
# Module 4: AI Agent LossLedger Gateway
# =============================================================================

class AiLossLedgerRequest(BaseModel):
    source_chunks: List[Dict[str, Any]]
    target_fields: List[str]
    max_token_budget: Optional[int] = 30
    key_field: str = "chunk_id"
    protected_fields: List[str] = ["chunk_id", "doc_title"]
    score_field: str = "relevance_score"
    text_field: str = "text"


@app.post("/api/ai/lossledger")
async def evaluate_ai_lossledger(payload: AiLossLedgerRequest) -> Dict[str, Any]:
    try:
        source_fields = tuple(
            dict.fromkeys(
                k for chunk in payload.source_chunks for k in chunk.keys()
            )
        )
        target_fields = tuple(payload.target_fields)

        @coda_mur_projection(
            source_fields=source_fields,
            target_fields=target_fields,
            key_field=payload.key_field,
            protected_fields=tuple(payload.protected_fields),
            score_field=payload.score_field,
            text_field=payload.text_field,
            max_token_budget=payload.max_token_budget,
        )
        def project_chunks(chunks: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
            return [{k: c[k] for k in target_fields if k in c} for c in chunks]

        envelope = project_chunks(payload.source_chunks)

        # Cryptographic verification of ledger if present
        is_ledger_valid = True
        ledger_error = None
        if envelope.loss_ledger:
            is_ledger_valid, ledger_error = verify_loss_ledger_integrity(envelope.loss_ledger)

        return {
            "admitted": envelope.admitted,
            "certified": envelope.certified,
            "authorized": envelope.authorized,
            "authorization_status": envelope.authorization_status,
            "canonical_terminal": envelope.canonical_terminal,
            "local_route": envelope.local_route,
            "reason": envelope.reason,
            "token_accounting": {
                "source_token_count": envelope.source_token_count,
                "retained_token_count": envelope.retained_token_count,
                "truncated_token_count": envelope.truncated_token_count,
                "max_token_budget": envelope.max_token_budget,
                "token_conservation_commutes": envelope.token_conservation_commutes,
                "conservation_equation": f"{envelope.source_token_count} == {envelope.retained_token_count} (retained) + {envelope.truncated_token_count} (truncated)",
            },
            "chunk_accounting": {
                "source_chunk_count": envelope.source_chunk_count,
                "retained_chunk_count": envelope.retained_chunk_count,
                "dropped_chunk_count": envelope.dropped_chunk_count,
            },
            "erased_attributes": list(envelope.erased_attributes),
            "loss_ledger": envelope.loss_ledger,
            "loss_ledger_integrity_verified": is_ledger_valid,
            "loss_ledger_error": ledger_error,
            "merkle_digest": (envelope.loss_ledger or {}).get("merkle_digest"),
            "projected_chunks": list(envelope.projected_chunks),
            "epistemic_firewall": {
                "authority_effect": envelope.authority_effect,
                "certified_implies_authorized": envelope.certified_implies_authorized,
                "note": "A mathematically certified context envelope remains unauthorized until evaluated by an independent policy verifier.",
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# =============================================================================
# Frontend SPA Route
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")
