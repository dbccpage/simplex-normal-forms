"""Multi-Target Lowering & Automated Counterexample Fuzzer (NF-IR Layer 4).

Compiles declarative `NFKernelSpec` and `NFWiringNode` contracts into three
executable verification and enforcement targets:

  1. Target A — Python `@nf_kernel_guard` Decorator (`compile_to_python_decorator`):
     Wraps any Python data-processing or tool handler function `fn(rows, *args, **kwargs)`,
     evaluating the underlying `NFKernelSpec` / `NFWiringNode` DAG before execution,
     enforcing fail-closed blocking on `Reject` / `Refuse`, and enforcing the
     epistemic authority firewall (`certified_implies_authorized == False`).

  2. Target B — SQLite Constraint & Trigger DDL (`compile_to_sqlite_triggers`,
     `install_and_verify_sqlite_bundle`):
     Lowers an `NFKernelSpec` (`functional_dependency` or `representation_transport`
     mode) into executable SQLite `CREATE TABLE`, `BEFORE INSERT`, and `BEFORE UPDATE`
     triggers that abort invalid inserts and in-place updates with structured
     `NF_VIOLATION:<contract_id>:<reason>` diagnostics.

  3. Target C — Automated Counterexample Synthesizer (`synthesize_counterexample_fixtures`):
     Given an `NFKernelSpec` and a deterministic seed, synthesizes both a valid
     carrier instance and minimal failing counterexample fixtures covering
     obstructed collisions, missing/null protected determinants, self-difference,
     ghost distinctions, and subsingleton collapse.

AuthorityEffect: None.
certified_implies_authorized: false.
"""

from __future__ import annotations

from dataclasses import dataclass
import functools
import random
import re
import sqlite3
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from normal_forms.ir_kernel import (
    NFKernelSpec,
)
from normal_forms.ir_wiring import (
    NFWiringNode,
    WiringEvaluationReceipt,
    evaluate_wiring_dag,
    guard_pass,
    leaf_pass,
)


@dataclass(frozen=True)
class LoweredDecoratorReceipt:
    """Receipt returned by a function wrapped with `compile_to_python_decorator`."""

    wiring_receipt: WiringEvaluationReceipt
    function_executed: bool
    function_output: Any
    canonical_terminal: str
    admitted: bool
    certified: bool
    authorized: bool = False
    authority_effect: str = "None"
    certified_implies_authorized: bool = False


@dataclass(frozen=True)
class SqliteLoweredBundle:
    """Compiled SQLite DDL and trigger bundle for an NFKernelSpec."""

    contract_id: str
    table_name: str
    key_field: str
    columns: Tuple[str, ...]
    required_columns: Tuple[str, ...]
    require_support_floor: bool
    create_table_sql: str
    before_insert_trigger_sql: str
    before_update_trigger_sql: str


@dataclass(frozen=True)
class SynthesizedCounterexampleFixture:
    """Minimal failing counterexample fixture synthesized from an NFKernelSpec."""

    failure_kind: str
    expected_canonical_terminal: str
    carrier_rows: Tuple[Dict[str, Any], ...]
    asserted_pairs: Optional[Tuple[Tuple[str, str], ...]] = None


def _sanitize_ident(identifier: str) -> str:
    """Validates and quotes a SQLite identifier safely."""
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_.:-]*$", identifier):
        raise ValueError(f"Unsafe SQL identifier: {identifier!r}")
    return f'"{identifier}"'


def compile_to_python_decorator(
    spec_or_node: NFKernelSpec | NFWiringNode,
    require_authorization: bool = False,
    policy_verifier: Any = None,
    producer_identity: str = "nf_lowered_guard",
) -> Callable[[Callable[..., Any]], Callable[..., LoweredDecoratorReceipt]]:
    """Compiles an NFKernelSpec or NFWiringNode into a fail-closed Python decorator."""
    base_node = (
        leaf_pass(spec_or_node)
        if isinstance(spec_or_node, NFKernelSpec)
        else spec_or_node
    )

    def decorator(fn: Callable[..., Any]) -> Callable[..., LoweredDecoratorReceipt]:
        @functools.wraps(fn)
        def wrapper(
            rows: Sequence[Mapping[str, Any]],
            *args: Any,
            policy_verifier_override: Any = None,
            **kwargs: Any,
        ) -> LoweredDecoratorReceipt:
            active_verifier = (
                policy_verifier_override
                if policy_verifier_override is not None
                else policy_verifier
            )
            if require_authorization or active_verifier is not None:
                eval_node = guard_pass(
                    base_node,
                    policy_verifier=active_verifier,
                    producer_identity=producer_identity,
                )
            else:
                eval_node = base_node

            w_receipt = evaluate_wiring_dag(eval_node, rows)

            should_execute = (
                (w_receipt.admitted and w_receipt.certified and w_receipt.authorized)
                if require_authorization
                else (w_receipt.admitted and w_receipt.certified)
            )

            if not should_execute:
                return LoweredDecoratorReceipt(
                    wiring_receipt=w_receipt,
                    function_executed=False,
                    function_output=None,
                    canonical_terminal=w_receipt.canonical_terminal,
                    admitted=w_receipt.admitted,
                    certified=w_receipt.certified,
                    authorized=w_receipt.authorized,
                )

            out = fn(rows, *args, **kwargs)
            return LoweredDecoratorReceipt(
                wiring_receipt=w_receipt,
                function_executed=True,
                function_output=out,
                canonical_terminal=w_receipt.canonical_terminal,
                admitted=w_receipt.admitted,
                certified=w_receipt.certified,
                authorized=w_receipt.authorized,
            )

        return wrapper

    return decorator


def compile_to_sqlite_triggers(
    spec: NFKernelSpec,
    table_name: str = "nf_carrier",
) -> SqliteLoweredBundle:
    """Compiles an NFKernelSpec into SQLite CREATE TABLE + BEFORE INSERT/UPDATE triggers."""
    q_table = _sanitize_ident(table_name)
    all_cols = tuple(
        dict.fromkeys(
            (spec.key_field,)
            + spec.distinction_fields
            + spec.collapse_fields
            + spec.protected_law_fields
        )
    )
    col_defs = ", ".join(f"{_sanitize_ident(c)} TEXT" for c in all_cols)
    create_table_sql = f"CREATE TABLE {q_table} ({col_defs});"

    cid = spec.contract_id
    ins_trig_name = _sanitize_ident(f"trg_{table_name}_before_insert")
    upd_trig_name = _sanitize_ident(f"trg_{table_name}_before_update")

    ins_statements: List[str] = []
    upd_statements: List[str] = []

    if spec.require_protected_law_declaration and not spec.protected_law_fields:
        abort_unrel = (
            f"SELECT RAISE(ABORT, 'NF_VIOLATION:{cid}:RequireProtectedLawDeclaration');"
        )
        ins_statements.append(abort_unrel)
        upd_statements.append(abort_unrel)
        required_cols: Tuple[str, ...] = ()
    elif spec.law_mode == "representation_transport":
        required_cols = tuple(spec.protected_law_fields)
        dropped_prot = [
            pf for pf in spec.protected_law_fields if pf not in spec.collapse_fields
        ]
        if dropped_prot:
            bad_pf = dropped_prot[0]
            abort_drop = (
                f"SELECT RAISE(ABORT, 'NF_VIOLATION:{cid}:TransportViolation:{bad_pf}');"
            )
            ins_statements.append(abort_drop)
            upd_statements.append(abort_drop)
        else:
            for pf in spec.protected_law_fields:
                q_pf = _sanitize_ident(pf)
                null_check = (
                    f"SELECT CASE WHEN NEW.{q_pf} IS NULL THEN "
                    f"RAISE(ABORT, 'NF_VIOLATION:{cid}:TransportViolation:{pf}') END;"
                )
                ins_statements.append(null_check)
                upd_statements.append(null_check)

            if spec.protected_law_fields:
                prot_eq = " AND ".join(
                    f"existing.{_sanitize_ident(pf)} = NEW.{_sanitize_ident(pf)}"
                    for pf in spec.protected_law_fields
                )
                q_key = _sanitize_ident(spec.key_field)
                first_pf = spec.protected_law_fields[0]
                ins_dup_check = (
                    f"SELECT CASE WHEN EXISTS ("
                    f"SELECT 1 FROM {q_table} AS existing "
                    f"WHERE existing.{q_key} != NEW.{q_key} AND {prot_eq}"
                    f") THEN RAISE(ABORT, 'NF_VIOLATION:{cid}:TransportViolation:{first_pf}') END;"
                )
                upd_dup_check = (
                    f"SELECT CASE WHEN EXISTS ("
                    f"SELECT 1 FROM {q_table} AS existing "
                    f"WHERE existing.rowid != OLD.rowid AND existing.{q_key} != NEW.{q_key} AND {prot_eq}"
                    f") THEN RAISE(ABORT, 'NF_VIOLATION:{cid}:TransportViolation:{first_pf}') END;"
                )
                ins_statements.append(ins_dup_check)
                upd_statements.append(upd_dup_check)
    else:
        # functional_dependency mode
        required_cols = tuple(
            dict.fromkeys(spec.collapse_fields + spec.protected_law_fields)
        )
        for col in required_cols:
            q_col = _sanitize_ident(col)
            null_check = (
                f"SELECT CASE WHEN NEW.{q_col} IS NULL THEN "
                f"RAISE(ABORT, 'NF_VIOLATION:{cid}:MissingAttribute:{col}') END;"
            )
            ins_statements.append(null_check)
            upd_statements.append(null_check)

        if spec.collapse_fields and spec.protected_law_fields:
            col_eq = " AND ".join(
                f"existing.{_sanitize_ident(c)} = NEW.{_sanitize_ident(c)}"
                for c in spec.collapse_fields
            )
            prot_neq = " OR ".join(
                f"existing.{_sanitize_ident(p)} != NEW.{_sanitize_ident(p)}"
                for p in spec.protected_law_fields
            )
            first_pf = spec.protected_law_fields[0]
            ins_fd_check = (
                f"SELECT CASE WHEN EXISTS ("
                f"SELECT 1 FROM {q_table} AS existing "
                f"WHERE ({col_eq}) AND ({prot_neq})"
                f") THEN RAISE(ABORT, 'NF_VIOLATION:{cid}:PromoteToObstruction:{first_pf}') END;"
            )
            upd_fd_check = (
                f"SELECT CASE WHEN EXISTS ("
                f"SELECT 1 FROM {q_table} AS existing "
                f"WHERE existing.rowid != OLD.rowid AND ({col_eq}) AND ({prot_neq})"
                f") THEN RAISE(ABORT, 'NF_VIOLATION:{cid}:PromoteToObstruction:{first_pf}') END;"
            )
            ins_statements.append(ins_fd_check)
            upd_statements.append(upd_fd_check)

    ins_body = "\n  ".join(ins_statements) if ins_statements else "SELECT 1;"
    upd_body = "\n  ".join(upd_statements) if upd_statements else "SELECT 1;"

    before_insert_sql = (
        f"CREATE TRIGGER {ins_trig_name}\n"
        f"BEFORE INSERT ON {q_table}\n"
        f"FOR EACH ROW\n"
        f"BEGIN\n"
        f"  {ins_body}\n"
        f"END;"
    )
    before_update_sql = (
        f"CREATE TRIGGER {upd_trig_name}\n"
        f"BEFORE UPDATE ON {q_table}\n"
        f"FOR EACH ROW\n"
        f"BEGIN\n"
        f"  {upd_body}\n"
        f"END;"
    )

    return SqliteLoweredBundle(
        contract_id=cid,
        table_name=table_name,
        key_field=spec.key_field,
        columns=all_cols,
        required_columns=required_cols,
        require_support_floor=spec.require_support_floor,
        create_table_sql=create_table_sql,
        before_insert_trigger_sql=before_insert_sql,
        before_update_trigger_sql=before_update_sql,
    )


def install_and_verify_sqlite_bundle(
    conn: sqlite3.Connection,
    bundle: SqliteLoweredBundle,
    rows: Sequence[Mapping[str, Any]],
) -> Tuple[bool, Optional[str]]:
    """Installs a SqliteLoweredBundle in `conn` and tests inserting `rows`."""
    q_table = _sanitize_ident(bundle.table_name)
    cur = conn.cursor()
    cur.execute(f"DROP TABLE IF EXISTS {q_table};")
    cur.execute(bundle.create_table_sql)
    cur.execute(bundle.before_insert_trigger_sql)
    cur.execute(bundle.before_update_trigger_sql)

    placeholders = ", ".join("?" for _ in bundle.columns)
    col_list = ", ".join(_sanitize_ident(c) for c in bundle.columns)
    insert_sql = f"INSERT INTO {q_table} ({col_list}) VALUES ({placeholders});"

    try:
        cur.execute("SAVEPOINT nf_bundle_check;")
        if bundle.require_support_floor and len(rows) < 2:
            raise sqlite3.IntegrityError(
                f"NF_VIOLATION:{bundle.contract_id}:SubsingletonCollapseRefusal"
            )
        for row in rows:
            vals = [
                str(row[c]) if (c in row and row[c] is not None) else None
                for c in bundle.columns
            ]
            cur.execute(insert_sql, vals)
        cur.execute("RELEASE SAVEPOINT nf_bundle_check;")
        return True, None
    except sqlite3.IntegrityError as exc:
        cur.execute("ROLLBACK TO SAVEPOINT nf_bundle_check;")
        cur.execute("RELEASE SAVEPOINT nf_bundle_check;")
        return False, str(exc)


def synthesize_counterexample_fixtures(
    spec: NFKernelSpec,
    seed: int = 42,
) -> Tuple[List[Dict[str, Any]], List[SynthesizedCounterexampleFixture]]:
    """Synthesizes a valid baseline carrier and minimal failing counterexample fixtures for `spec`."""
    rng = random.Random(seed)
    all_cols = tuple(
        dict.fromkeys(
            (spec.key_field,)
            + spec.distinction_fields
            + spec.collapse_fields
            + spec.protected_law_fields
        )
    )

    # 1. Construct a valid 3-row baseline carrier (where every row has distinct values on all columns)
    valid_rows: List[Dict[str, Any]] = []
    for idx in range(3):
        row: Dict[str, Any] = {}
        for col in all_cols:
            if col == spec.key_field:
                row[col] = f"id_{seed}_{idx}"
            else:
                row[col] = f"{col}_val_{idx}_{rng.randint(10, 99)}"
        valid_rows.append(row)

    counterexamples: List[SynthesizedCounterexampleFixture] = []

    # Counterexample A: Subsingleton carrier (when require_support_floor=True)
    if spec.require_support_floor:
        counterexamples.append(
            SynthesizedCounterexampleFixture(
                failure_kind="subsingleton_carrier",
                expected_canonical_terminal="Refuse",
                carrier_rows=(dict(valid_rows[0]),),
                asserted_pairs=None,
            )
        )

    # Counterexample B: Self-difference assertion (x, x) -> IrreflexivityViolation -> Reject
    r0_id = str(valid_rows[0][spec.key_field])
    counterexamples.append(
        SynthesizedCounterexampleFixture(
            failure_kind="self_difference",
            expected_canonical_terminal="Reject",
            carrier_rows=(dict(valid_rows[0]), dict(valid_rows[1])),
            asserted_pairs=((r0_id, r0_id),),
        )
    )

    # Counterexample C: Ghost distinction (two rows identical on distinction_fields asserted distinct)
    ghost_0 = dict(valid_rows[0])
    ghost_1 = dict(valid_rows[1])
    for df in spec.distinction_fields:
        if df != spec.key_field:
            ghost_1[df] = ghost_0[df]
    if spec.key_field not in spec.distinction_fields:
        r1_id = str(ghost_1[spec.key_field])
        counterexamples.append(
            SynthesizedCounterexampleFixture(
                failure_kind="ghost_distinction",
                expected_canonical_terminal="Reject",
                carrier_rows=(ghost_0, ghost_1),
                asserted_pairs=((r0_id, r1_id),),
            )
        )

    # Counterexample D: Obstructed collision on protected_law_fields
    if spec.protected_law_fields:
        obs_0 = dict(valid_rows[0])
        obs_1 = dict(valid_rows[1])
        if spec.law_mode == "representation_transport":
            # Duplicate protected determinant signature across two distinct row_ids
            for pf in spec.protected_law_fields:
                if pf != spec.key_field:
                    obs_1[pf] = obs_0[pf]
            if any(pf != spec.key_field for pf in spec.protected_law_fields):
                counterexamples.append(
                    SynthesizedCounterexampleFixture(
                        failure_kind="obstructed_collision",
                        expected_canonical_terminal="Reject",
                        carrier_rows=(obs_0, obs_1),
                        asserted_pairs=None,
                    )
                )
        else:
            # functional_dependency mode: agree on collapse_fields, disagree on protected_law_fields[0]
            for cf in spec.collapse_fields:
                obs_1[cf] = obs_0[cf]
            target_pf = spec.protected_law_fields[0]
            obs_1[target_pf] = f"{obs_0[target_pf]}_obstructed_conflict"
            counterexamples.append(
                SynthesizedCounterexampleFixture(
                    failure_kind="obstructed_collision",
                    expected_canonical_terminal="Reject",
                    carrier_rows=(obs_0, obs_1),
                    asserted_pairs=None,
                )
            )

        # Counterexample E: Missing / null required protected field
        miss_0 = dict(valid_rows[0])
        miss_1 = dict(valid_rows[1])
        target_pf = spec.protected_law_fields[0]
        if spec.law_mode == "representation_transport":
            miss_0[target_pf] = None
        else:
            del miss_0[target_pf]
        counterexamples.append(
            SynthesizedCounterexampleFixture(
                failure_kind="missing_required_field",
                expected_canonical_terminal="Reject",
                carrier_rows=(miss_0, miss_1),
                asserted_pairs=None,
            )
        )

    return valid_rows, counterexamples


# -----------------------------------------------------------------------------
# Canonical NF-IR Public API Lowering Aliases
# -----------------------------------------------------------------------------
lower_to_sqlite_trigger = compile_to_sqlite_triggers
lower_kernel_to_sqlite_trigger = compile_to_sqlite_triggers
lower_to_python_guard = compile_to_python_decorator
lower_kernel_to_python_guard = compile_to_python_decorator
