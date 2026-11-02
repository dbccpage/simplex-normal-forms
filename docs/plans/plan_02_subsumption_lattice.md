# Plan 2: Subsumption Lattice & Dead-Check Elimination Pass (PR #13)

## 1. Gate Status

**Current status (2026-11-02):** Implemented and merged in PR #13 (`d0e834c`).
The approval gates below are retained as the original planning record, not
pending authorization. See [current project status](../PROJECT_STATUS.md).

### Original planning gates

* **Master Plan of Plans ([`plan_of_plans.md`](./plan_of_plans.md)):** Approved
* **Plan 1 ([`plan_01_wdp_obnf_micro_kernel.md`](./plan_01_wdp_obnf_micro_kernel.md)):** Executed (`normal_forms/ir_kernel.py` + `tests/test_ir_kernel.py` passing) & PR #12 (`https://github.com/dbccpage/simplex-normal-forms/pull/12`) merging to `origin/main`.
* **Current Gate:** Review & Approve **Plan 2 (`plan_02_subsumption_lattice.md`)** before writing any Plan 2 production code.
* **Next Gate After Approval:** Execute Plan 2 (`normal_forms/ir_subsumption.py` + `tests/test_ir_subsumption.py`) while drafting **Plan 3 (`plan_03_operadic_wiring_compiler.md`)** in parallel; open, review, and merge **PR #13** before executing Plan 3.

---

## 2. Goal & Scope of Plan 2

In a multi-stage normal-form pipeline, checking a weaker normal form $\text{NF}_B$ after a strictly stronger normal form $\text{NF}_A$ ($\text{NF}_A \preceq \text{NF}_B$, read "$\text{NF}_A$ refines/subsumes $\text{NF}_B$ under shared scope and determinants") wastes compute and duplicates receipt objects.

Plan 2 introduces `normal_forms/ir_subsumption.py` to:
1. Encode a machine-checkable **Subsumption DAG / Poset ($\text{NF}_A \preceq \text{NF}_B$)** over four contract families:
   * **Classical Relational Hierarchy (under shared schema & dependency cover):**
     $$\text{nf.classical.6nf} \preceq \text{nf.classical.5nf} \preceq \text{nf.classical.4nf} \preceq \text{nf.classical.bcnf} \preceq \text{nf.classical.3nf} \preceq \text{nf.classical.2nf} \preceq \text{nf.classical.1nf} \preceq \text{nf.classical.0nf}$$
   * **Genesis / WDP Derivation Hierarchy (under shared carrier & distinction relation):**
     $$\text{nf.derivation.apnf} \preceq \text{nf.wdp.wdnf} \preceq \text{nf.derivation.pdnf}$$
   * **Representation & Transport Hierarchy (under shared source/target projection):**
     $$\text{nf.derivation.sernf} \preceq \text{nf.coda.mur.transport:TransportOk} \preceq \text{nf.coda.mur.transport:DegradedTransportWithLoss}$$
   * **Kernel Determinant Subsumption (for `NFKernelSpec` from Plan 1):**
     Given two `NFKernelSpec` passes $K_1, K_2$ in `functional_dependency` mode over the same carrier and `key_field`:
     $$K_1 \preceq K_2 \iff \text{collapse}(K_1) \subseteq \text{collapse}(K_2) \quad\text{and}\quad \text{protected}(K_2) \subseteq \text{protected}(K_1)$$
     (Because if a smaller determinant $X_1 \subseteq X_2$ already determines a larger dependent set $Y_1 \supseteq Y_2$, then any pair agreeing on $X_2$ also agrees on $X_1$, and therefore agrees on $Y_1 \supseteq Y_2$).
2. Provide a **Dead-Check Elimination Optimizer (`eliminate_redundant_kernel_checks`)** that takes a sequence of `NFKernelSpec` passes (plus an optional set of already-certified upstream specs), elides every pass $K_j$ that is subsumed by an earlier admitted pass $K_i \preceq K_j$, and emits a `SubsumptionOptimizationReceipt` recording every elided check and its subsuming witness.

---

## 3. Exact Module Design: `normal_forms/ir_subsumption.py`

### 3.1 Core Data Structures (Immutable Dataclasses)

* **`SubsumptionEdge`**
  * `stronger_id: str`
  * `weaker_id: str`
  * `family: str` — `"classical"`, `"derivation_wdp"`, `"representation_transport"`, or `"kernel_fd"`
  * `condition: str` — explicit scope assumption under which $\text{stronger} \preceq \text{weaker}$ holds

* **`ElidedCheckRecord`**
  * `elided_index: int`
  * `elided_contract_id: str`
  * `subsumed_by_index: int`
  * `subsumed_by_contract_id: str`
  * `reason: str`

* **`SubsumptionOptimizationReceipt`**
  * `input_pass_count: int`
  * `executed_pass_count: int`
  * `elided_pass_count: int`
  * `elided_records: Tuple[ElidedCheckRecord, ...]`
  * `executed_receipts: Tuple[KernelEvaluationReceipt, ...]`
  * `final_terminal: str`
  * `admitted: bool`
  * `certified: bool`
  * `authorized: bool = False` (`AuthorityEffect: None`, `certified_implies_authorized: False`)

### 3.2 Core Functions in `normal_forms/ir_subsumption.py`

1. **` verify_subsumption_poset_laws() -> Tuple[bool, List[str]]`**
   * Verifies reflexivity ($A \preceq A$), antisymmetry (no directed cycles $A \preceq B \preceq A$ with $A \neq B$), and transitive closure over the canonical subsumption graph.
2. **`subsumes_contract(stronger_id: str, weaker_id: str) -> bool`**
   * Decides whether `stronger_id` refines `weaker_id` in the transitive closure of the declared subsumption poset.
3. **`subsumes_kernel_spec(stronger: NFKernelSpec, weaker: NFKernelSpec) -> Tuple[bool, str]`**
   * Checks whether `stronger` subsumes `weaker` by checking (a) identical `key_field`, `law_mode`, and compatible `require_support_floor`, and (b) either contract-level subsumption with identical collapse/protected fields OR FD determinant/dependent inclusion ($\text{collapse}(\text{stronger}) \subseteq \text{collapse}(\text{weaker})$ and $\text{protected}(\text{weaker}) \subseteq \text{protected}(\text{stronger})$) in `functional_dependency` mode, OR target/protected inclusion in `representation_transport` mode.
4. **`run_kernel_pipeline_with_dce(specs: Sequence[NFKernelSpec], carrier_rows: Sequence[Mapping[str, Any]], enable_dce: bool = True) -> SubsumptionOptimizationReceipt`**
   * Evaluates a sequence of `NFKernelSpec` passes on `carrier_rows`. When `enable_dce=True`, skips any pass $K_j$ subsumed by an already-admitted earlier pass $K_i \preceq K_j$. Short-circuits fail-closed on the first rejected/refused pass.

---

## 4. Verification Plan: `tests/test_ir_subsumption.py`

We will add `tests/test_ir_subsumption.py` with 4 test methods:

1. **`test_subsumption_poset_reflexivity_antisymmetry_and_transitivity`:**
   * Checks `verify_subsumption_poset_laws()` across all classical (`6NF` $\to$ `0NF`), derivation (`APNF` $\to$ `WDNF` $\to$ `PDNF`), and transport (`SERNF` $\to$ `TransportOk` $\to$ `DegradedTransportWithLoss`) chains, and verifies that reverse edges (`1NF` $\preceq$ `BCNF`) and cross-family non-edges return `False`.
2. **`test_fd_kernel_subsumption_dead_check_elimination_equivalence_80_trials`:**
   * Across 80 randomized trials with 4-to-8 `NFKernelSpec` passes (containing both independent FDs and subsumed FDs where $X_1 \subseteq X_2$ and $Y_2 \subseteq Y_1$) over randomized relation instances (both valid and violation-injected):
     * Verifies `dce_receipt.executed_pass_count < unopt_receipt.executed_pass_count` whenever a stronger admitted FD precedes a weaker FD.
     * Verifies 100% semantic equivalence between `enable_dce=True` and `enable_dce=False`: `dce_receipt.admitted == unopt_receipt.admitted` and `dce_receipt.final_terminal == unopt_receipt.final_terminal`.
3. **`test_coda_mur_and_wdnf_subsumption_dce_80_trials`:**
   * Across 80 randomized trials of `representation_transport` and `WDNF` kernel chains, verifies that dead-check elimination never masks a `TransportViolation` (`Reject`) or `SubsingletonCollapseRefusal` (`Refuse`).
4. **`test_subsumption_authority_firewall_invariants`:**
   * Verifies `authorized == False`, `authority_effect == "None"`, and `certified_implies_authorized == False` on all `SubsumptionOptimizationReceipt` instances.

---

## 5. Files to Create / Modify in PR #13

* **Create:** `normal_forms/ir_subsumption.py`
* **Create:** `tests/test_ir_subsumption.py`
* **Modify:** `normal_forms/__init__.py` (re-export `SubsumptionEdge`, `ElidedCheckRecord`, `SubsumptionOptimizationReceipt`, `verify_subsumption_poset_laws`, `subsumes_contract`, `subsumes_kernel_spec`, `run_kernel_pipeline_with_dce`)

