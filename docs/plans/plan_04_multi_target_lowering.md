# Plan 4: Multi-Target Lowering & Automated Counterexample Fuzzer (PR #15)

## 1. Gate Status

**Current status (2026-11-02):** Implemented and merged in PR #15 (`dffdb87`).
The approval gates below are retained as the original planning record, not
pending authorization. See [current project status](../PROJECT_STATUS.md).

### Original planning gates

* **Master Plan of Plans ([`plan_of_plans.md`](./plan_of_plans.md)):** Approved
* **Plan 1 ([`plan_01_wdp_obnf_micro_kernel.md`](./plan_01_wdp_obnf_micro_kernel.md)):** Merged in **PR #12** (`db4150f`)
* **Plan 2 ([`plan_02_subsumption_lattice.md`](./plan_02_subsumption_lattice.md)):** Merged in **PR #13** (`d0e834c`)
* **Plan 3 ([`plan_03_operadic_wiring_compiler.md`](./plan_03_operadic_wiring_compiler.md)):** Executed (`normal_forms/ir_wiring.py` + `tests/test_ir_wiring.py` passing) & **PR #14** (`https://github.com/dbccpage/simplex-normal-forms/pull/14`) merging to `origin/main`.
* **Current Gate:** Review & Approve **Plan 4 (`plan_04_multi_target_lowering.md`)** before writing any Plan 4 production code.
* **Next Gate After Approval:** Execute Plan 4 (`normal_forms/ir_lowering.py` + `tests/test_ir_lowering.py`), run the complete 36+ test suite across the entire repository, and open, review, and merge **PR #15** into `origin/main` to complete the 4-plan `NF-IR` roadmap.

---

## 2. Goal & Scope of Plan 4

With the primitive `NFKernelSpec` micro-kernel (Plan 1), the `ir_subsumption` dead-check elimination pass (Plan 2), and the `ir_wiring` DAG compiler (Plan 3) merged, Plan 4 builds the final layer of the `NF-IR` stack: **Multi-Target Lowering & Counterexample Fuzzing (`normal_forms/ir_lowering.py`)**.

Instead of writing separate SQLite triggers, Python decorators, and negative-control test fixtures by hand for each normal form, `normal_forms/ir_lowering.py` compiles a single declarative `NFKernelSpec` (or `NFWiringNode`) into **three executable targets**:

1. **Target A — Python `@nf_kernel_guard` Decorator (`compile_to_python_decorator`):**
   * Compiles any `NFKernelSpec` or `NFWiringNode` into a Python function decorator `@nf_kernel_guard(spec_or_node, policy_verifier=None, producer_identity="nf_lowered_guard")`.
   * Before executing the wrapped Python function `fn(rows, *args, **kwargs)`, runs `evaluate_wiring_dag`, attaches the `WiringEvaluationReceipt`, and blocks execution (`executed=False`) if `admitted == False` or if an explicit `policy_verifier` is required and absent/unverified.
2. **Target B — SQLite Constraint & Trigger DDL Generator (`compile_to_sqlite_triggers`):**
   * Compiles any `NFKernelSpec` into executable SQLite `CREATE TABLE` + `CREATE TRIGGER ... BEFORE INSERT` and `BEFORE UPDATE` statements that enforce the exact same `OBNF` / `FD` / `CODA_MUR` protected laws inside an in-memory or on-disk SQLite database using `RAISE(ABORT, 'NF_VIOLATION:<contract_id>:<feature>')`:
     * In `"functional_dependency"` mode ($X_{\text{collapse}} \to Y_{\text{protected}}$): generates `BEFORE INSERT` and `BEFORE UPDATE` triggers checking `EXISTS (SELECT 1 FROM <table> WHERE <collapse_eq> AND (<protected_neq>))` plus `NOT NULL` guards on required columns.
     * In `"representation_transport"` mode: generates `BEFORE INSERT` and `BEFORE UPDATE` triggers enforcing non-null protected determinants and uniqueness across `protected_law_fields`.
3. **Target C — Automated Counterexample Fixture Synthesizer (`synthesize_counterexample_fixtures`):**
   * Given any `NFKernelSpec` and a seed, automatically synthesizes:
     * A valid baseline carrier (`valid_rows`) satisfying `spec`, and
     * Minimal failing counterexample fixtures (`counterexample_fixtures`) targeting each failure mode applicable to `spec` (`"obstructed_collision"`, `"subsingleton_carrier"`, `"self_difference"`, `"ghost_distinction"`, `"null_protected_field"`), verifying that every synthesized counterexample is rejected by both the Python kernel evaluator and the lowered SQLite trigger!

---

## 3. Exact Module Design: `normal_forms/ir_lowering.py`

### 3.1 Core Data Structures (Immutable Dataclasses)

* **`LoweredDecoratorReceipt`**
  * `wiring_receipt: WiringEvaluationReceipt`
  * `function_executed: bool`
  * `function_output: Any`
  * `canonical_terminal: str`
  * `admitted: bool`
  * `certified: bool`
  * `authorized: bool = False`
  * `authority_effect: str = "None"`
  * `certified_implies_authorized: bool = False`

* **`SqliteLoweredBundle`**
  * `contract_id: str`
  * `table_name: str`
  * `columns: Tuple[str, ...]`
  * `create_table_sql: str`
  * `before_insert_trigger_sql: str`
  * `before_update_trigger_sql: str`

* **`SynthesizedCounterexampleFixture`**
  * `failure_kind: str` — `"obstructed_collision"`, `"subsingleton_carrier"`, `"self_difference"`, `"ghost_distinction"`, or `"missing_required_field"`
  * `expected_canonical_terminal: str` — `"Reject"` or `"Refuse"`
  * `carrier_rows: Tuple[Dict[str, Any], ...]`
  * `asserted_pairs: Optional[Tuple[Tuple[str, str], ...]] = None`

### 3.2 Core Lowering & Fuzzing Functions in `normal_forms/ir_lowering.py`

1. **`compile_to_python_decorator(spec_or_node: NFKernelSpec | NFWiringNode, require_authorization: bool = False, policy_verifier: Any = None, producer_identity: str = "nf_lowered_guard") -> Callable[[Callable[..., Any]], Callable[..., LoweredDecoratorReceipt]]`**
2. **`compile_to_sqlite_triggers(spec: NFKernelSpec, table_name: str = "nf_carrier") -> SqliteLoweredBundle`**
3. **`install_and_verify_sqlite_bundle(conn: sqlite3.Connection, bundle: SqliteLoweredBundle, rows: Sequence[Mapping[str, Any]]) -> Tuple[bool, Optional[str]]`**
   * Installs the lowered SQLite table and triggers in `conn` and attempts to insert `rows` inside a savepoint, returning `(True, None)` if all rows pass the SQLite triggers or `(False, sqlite_error_message)` if a trigger aborts with `NF_VIOLATION:...`.
4. **`synthesize_counterexample_fixtures(spec: NFKernelSpec, seed: int = 42) -> Tuple[List[Dict[str, Any]], List[SynthesizedCounterexampleFixture]]`**

---

## 4. Verification Plan: `tests/test_ir_lowering.py`

We will add `tests/test_ir_lowering.py` with 4 test methods:

1. **`test_sqlite_trigger_and_python_kernel_cross_target_equivalence_80_trials`:**
   * Across 80 randomized `NFKernelSpec` configurations (`functional_dependency` and `representation_transport` modes with 1-to-3 collapse/protected columns) and randomized row batches (valid and violation-injected):
     * Compiles each `spec` into both a Python `@nf_kernel_guard` decorator and a `SqliteLoweredBundle`.
     * Executes both against the row batch (using an in-memory SQLite connection) and verifies 100% agreement between the Python kernel (`py_res.admitted`) and the SQLite `BEFORE INSERT` trigger (`sql_ok`), and verifies that every SQLite rejection message contains `NF_VIOLATION:<contract_id>`.
2. **`test_automated_counterexample_fuzzer_completeness_80_trials`:**
   * Across 80 randomized `NFKernelSpec` specifications, runs `synthesize_counterexample_fixtures(spec, seed=trial)` and verifies that:
     * The synthesized `valid_rows` fixture is admitted (`Preserve` or `Quarantine`) by both `evaluate_nf_kernel` and the lowered SQLite trigger.
     * Every synthesized `SynthesizedCounterexampleFixture` is rejected (`admitted == False`, matching `expected_canonical_terminal`) with a non-null `minimal_counterexample`, and row-level counterexamples (`"obstructed_collision"`, `"missing_required_field"`) are also aborted by the lowered SQLite trigger.
3. **`test_sqlite_before_update_trigger_blocks_in_place_fd_and_transport_corruption`:**
   * Verifies that after valid rows are inserted into the lowered SQLite table, an `UPDATE` statement that mutates a dependent column to break $X \to Y$ or duplicates a protected key is blocked by the `BEFORE UPDATE` trigger while valid `UPDATE`s succeed.
4. **`test_lowered_decorator_epistemic_authority_firewall_matrix`:**
   * Verifies that `compile_to_python_decorator` with `require_authorization=False` certifies valid inputs (`certified=True`, `authorized=False`) and that with `require_authorization=True` it blocks execution of the wrapped function (`function_executed=False`) unless an independent `policy_verifier` (`verifier_identity != producer_identity`, `outcome == "authorized"`) is provided.

---

## 5. Files to Create / Modify in PR #15

* **Create:** `normal_forms/ir_lowering.py`
* **Create:** `tests/test_ir_lowering.py`
* **Modify:** `normal_forms/__init__.py` (re-export `LoweredDecoratorReceipt`, `SqliteLoweredBundle`, `SynthesizedCounterexampleFixture`, `compile_to_python_decorator`, `compile_to_sqlite_triggers`, `install_and_verify_sqlite_bundle`, `synthesize_counterexample_fixtures`)

