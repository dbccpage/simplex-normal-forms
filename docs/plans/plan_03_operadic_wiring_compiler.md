# Plan 3: Operadic Pipeline Wiring Compiler (PR #14)

## 1. Gate Status

**Current status (2026-11-02):** Implemented and merged in PR #14 (`ce90d22`).
The approval gates below are retained as the original planning record, not
pending authorization. See [current project status](../PROJECT_STATUS.md).

### Original planning gates

* **Master Plan of Plans ([`plan_of_plans.md`](./plan_of_plans.md)):** Approved
* **Plan 1 ([`plan_01_wdp_obnf_micro_kernel.md`](./plan_01_wdp_obnf_micro_kernel.md)):** Merged in **PR #12** (`db4150f`)
* **Plan 2 ([`plan_02_subsumption_lattice.md`](./plan_02_subsumption_lattice.md)):** Executed (`normal_forms/ir_subsumption.py` + `tests/test_ir_subsumption.py` passing) & **PR #13** (`https://github.com/dbccpage/simplex-normal-forms/pull/13`) merging to `origin/main`.
* **Current Gate:** Review & Approve **Plan 3 (`plan_03_operadic_wiring_compiler.md`)** before writing any Plan 3 production code.
* **Next Gate After Approval:** Execute Plan 3 (`normal_forms/ir_wiring.py` + `tests/test_ir_wiring.py`) while drafting **Plan 4 (`plan_04_multi_target_lowering.md`)** in parallel; open, review, and merge **PR #14** before executing Plan 4.

---

## 2. Goal & Scope of Plan 3

With the `NFKernelSpec` micro-kernel (Plan 1) and the subsumption/dead-check elimination pass (Plan 2) in place, Plan 3 builds the **Operadic Pipeline Wiring Compiler (`normal_forms/ir_wiring.py`)** so any multi-hop DAG of normal-form passes can be composed algebraically rather than wired by hand.

Specifically, `normal_forms/ir_wiring.py` defines:
1. **The Canonical Terminal Join Semilattice ($\sqcup$):**
   Every normal-form pass emits one of the canonical terminals ordered by severity:
   $$\text{Preserve} < \text{Repair} < \text{Quarantine} < \text{Recompute} < \text{Invalidate} < \text{Reject} < \text{Refuse}$$
   * **Admitted terminals:** `{"Preserve", "Repair", "Quarantine"}` (`admitted == True`, `certified == True`)
   * **Blocking terminals:** `{"Recompute", "Invalidate", "Reject", "Refuse"}` (`admitted == False`, `certified == False`)
2. **Three Compositional Wiring Combinators (`NFWiringNode`):**
   * **`leaf(spec: NFKernelSpec)`:** Atomic kernel pass node.
   * **`seq(*nodes: NFWiringNode, enable_dce: bool = True)`:** Sequential pipeline composition ($A \fatsemi B$). Runs nodes in order, optionally applying Plan 2 dead-check elimination (`subsumes_kernel_spec`) across adjacent/upstream leaf passes, short-circuiting fail-closed on the first blocking terminal, and chaining any `CODA_MUR` `LossLedger` digests into a cumulative SHA-256 Merkle chain.
   * **`par(*nodes: NFWiringNode)`:** Parallel fan-out / fan-in composition ($A \otimes B$). Evaluates all branches on the carrier, joins their canonical terminals via the severity semilattice $\bigsqcup_i t_i$, aggregates all `ConstructiveWitnessPair` counterexamples, and merges branch `LossLedger` digests in canonical order.
   * **`guard(node: NFWiringNode, policy_verifier: Any, producer_identity: str = "nf_wiring_producer")`:** Epistemic authority gate (`AuthorityEffect: None`, `certified_implies_authorized: False`). Even when `node` evaluates to `admitted == True` and `certified == True`, `authorized` remains `False` unless `policy_verifier` is an independent mapping (`verifier_identity != producer_identity`) with `outcome == "authorized"`.

---

## 3. Exact Module Design: `normal_forms/ir_wiring.py`

### 3.1 Core Data Structures (Immutable Dataclasses)

* **`NFWiringNode`**
  * `kind: str` — `"leaf"`, `"seq"`, `"par"`, or `"guard"`
  * `spec: Optional[NFKernelSpec] = None`
  * `children: Tuple["NFWiringNode", ...] = ()`
  * `enable_dce: bool = True`
  * `policy_verifier: Any = None`
  * `producer_identity: str = "nf_wiring_producer"`

* **`MerkleLossChainEntry`**
  * `step_index: int`
  * `contract_id: str`
  * `erased_attributes: Tuple[str, ...]`
  * `ledger_digest: str`
  * `cumulative_chain_digest: str` — $\text{SHA256}(\text{prev\_chain\_digest} \mathbin{\Vert} \text{ledger\_digest})$

* **`WiringEvaluationReceipt`**
  * `node_kind: str`
  * `executed_specs_count: int`
  * `elided_specs_count: int`
  * `leaf_receipts: Tuple[KernelEvaluationReceipt, ...]`
  * `elided_records: Tuple[ElidedCheckRecord, ...]`
  * `loss_chain: Tuple[MerkleLossChainEntry, ...]`
  * `loss_chain_head_digest: Optional[str]`
  * `counterexamples: Tuple[ConstructiveWitnessPair, ...]`
  * `canonical_terminal: str`
  * `admitted: bool`
  * `certified: bool`
  * `authorized: bool`
  * `authorization_status: str`
  * `authority_effect: str = "None"`
  * `certified_implies_authorized: bool = False`
  * `reason: str = ""`

### 3.2 Combinator Constructors & Evaluator

1. **`leaf_pass(spec: NFKernelSpec) -> NFWiringNode`**
2. **`seq_passes(*nodes: NFWiringNode, enable_dce: bool = True) -> NFWiringNode`**
3. **`par_passes(*nodes: NFWiringNode) -> NFWiringNode`**
4. **`guard_pass(node: NFWiringNode, policy_verifier: Any, producer_identity: str = "nf_wiring_producer") -> NFWiringNode`**
5. **`join_canonical_terminals(terminals: Sequence[str]) -> str`**
6. **`evaluate_wiring_dag(root: NFWiringNode, carrier_rows: Sequence[Mapping[str, Any]]) -> WiringEvaluationReceipt`**

---

## 4. Verification Plan: `tests/test_ir_wiring.py`

We will add `tests/test_ir_wiring.py` with 4 test methods:

1. **`test_seq_associativity_and_short_circuit_equivalence_80_trials`:**
   * Across 80 randomized trials of 3-pass kernel sequences $(A, B, C)$ over randomized carriers (valid, failing at $A$, failing at $B$, failing at $C$), verifies categorical associativity:
     $$\text{eval}(\text{seq}(\text{seq}(A, B), C)) == \text{eval}(\text{seq}(A, \text{seq}(B, C))) == \text{eval}(\text{seq}(A, B, C))$$
     across `admitted`, `canonical_terminal`, `loss_chain_head_digest`, and `counterexamples`, plus fail-closed short-circuiting when an early stage fails.
2. **`test_par_commutativity_idempotence_and_counterexample_aggregation_80_trials`:**
   * Across 80 randomized trials of parallel fan-out/fan-in wiring $\text{par}(A, B)$, verifies that terminal severity join is commutative and associative, and that all failing branch counterexamples are preserved.
3. **`test_multi_hop_merkle_loss_chain_tamper_and_sensitivity`:**
   * Chains multiple `CODA_MUR` lossy projections via `seq_passes` and `par_passes`, verifying that every hop's `LossLedger` digest is chained into `loss_chain_head_digest` and that mutating any single erased attribute value changes `loss_chain_head_digest`.
4. **`test_guard_pass_epistemic_authority_firewall_matrix`:**
   * Verifies that `leaf_pass`, `seq_passes`, and `par_passes` always emit `authorized == False` (`authorization_status == "certified_not_authorized"` when certified), and that `guard_pass` grants `authorized == True` if and only if the underlying DAG is `admitted == True` AND `policy_verifier` is an independent mapping with `verifier_identity != producer_identity` and `outcome == "authorized"`.

---

## 5. Files to Create / Modify in PR #14

* **Create:** `normal_forms/ir_wiring.py`
* **Create:** `tests/test_ir_wiring.py`
* **Modify:** `normal_forms/__init__.py` (re-export `MerkleLossChainEntry`, `NFWiringNode`, `WiringEvaluationReceipt`, `evaluate_wiring_dag`, `guard_pass`, `join_canonical_terminals`, `leaf_pass`, `par_passes`, `seq_passes`)

