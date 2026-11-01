# Plan 1: Primitive `WDP` / `OBNF` Witness Micro-Kernel (PR #12)

## 1. Gate Status

* **Master Plan of Plans ([`plan_of_plans.md`](./plan_of_plans.md)):** Approved
* **Current Gate:** Review & Approve **Plan 1 (`plan_01_wdp_obnf_micro_kernel.md`)** before writing any production code.
* **Next Gate After Approval:** Execute Plan 1 (`normal_forms/ir_kernel.py` + `tests/test_ir_kernel.py`) while drafting **Plan 2 (`plan_02_subsumption_lattice.md`)** in parallel; open, review, and merge **PR #12** before executing Plan 2.

---

## 2. Goal & Scope of Plan 1

In Genesis (`19L57G1` / `nf.derivation.pdnf` / `nf.derivation.obnf`) and the Witnessed Difference Programme (`nf.wdp.wdnf`), every normal-form check reduces to a single primitive micro-kernel:
$$\mathcal{K} = (\text{Carrier } X,\ \text{Collapse Map } F: X \to Y,\ \text{Protected Law } \mathcal{L})$$

1. **Level 00 Admitted Cut (`WDNF` / `PDNF`):** Does the carrier $X$ have at least two distinct elements ($|X| \ge 2$), is the distinction relation irreflexive ($\neg(x \mathrel{\Delta} x)$), and does every asserted distinction carry a concrete witness ($w(x, y) \ge 1$) with multiplicity normalized to boolean presence?
2. **Obstruction Relativization (`OBNF`):** When $F: X \to Y$ collapses two distinct elements ($x \mathrel{\Delta} y$ and $F(x) = F(y)$), does that collision preserve the declared protected law $\mathcal{L}$ (`AcceptAdmissibleCollision` $\to$ `Preserve` / `Quarantine`), or does it violate $\mathcal{L}$ (`PromoteToObstruction` $\to$ `Reject` / `Refuse`) with an explicit minimal counterexample pair $(x, y, w)$?

---

## 3. Exact Module Design: `normal_forms/ir_kernel.py`

### 3.1 Core Data Structures (Immutable Dataclasses)

* **`ConstructiveWitnessPair`**
  * `left_id: str` — canonical key of the first element $x \in X$
  * `right_id: str` — canonical key of the second element $y \in X$
  * `witness_kind: str` — `"distinction"`, `"admissible_collision"`, `"obstructed_collision"`, `"self_difference"`, or `"ghost_distinction"`
  * `feature: str` — attribute or determinant name witnessing the difference or violation
  * `left_value: Any` — value on $x$
  * `right_value: Any` — value on $y$
  * `collapsed_image: Any` — $F(x) = F(y)$ when a collision occurs (or `None`)

* **`NFKernelSpec`**
  * `contract_id: str` — target contract ID (e.g., `"nf.wdp.wdnf"`, `"nf.derivation.obnf"`, `"nf.classical.bcnf"`, `"nf.coda.mur.transport"`)
  * `key_field: str` — element identifier attribute on carrier records
  * `distinction_fields: Tuple[str, ...]` — attributes defining Level 00 witnessed differences $\Delta$ on $X$
  * `collapse_fields: Tuple[str, ...]` — attributes defining the coarse-graining / projection map $F: X \to Y$
  * `protected_law_fields: Tuple[str, ...]` — attributes that must remain functionally determined or collision-free when $F(x) = F(y)$
  * `require_support_floor: bool = True` — whether $|X| \ge 2$ is required (`True` for `WDNF`/`PDNF`, configurable for relational tables)
  * `require_loss_ledger_on_admissible_collision: bool = False` — whether admissible collisions route to `Quarantine` (with sealed `LossLedger`) vs `Preserve`

* **`KernelEvaluationReceipt`**
  * `contract_id: str`
  * `carrier_size: int`
  * `admitted_cut_ok: bool`
  * `distinction_witnesses: Tuple[ConstructiveWitnessPair, ...]`
  * `admissible_collisions: Tuple[ConstructiveWitnessPair, ...]`
  * `obstructed_collisions: Tuple[ConstructiveWitnessPair, ...]`
  * `minimal_counterexample: Optional[ConstructiveWitnessPair]` — first deterministic counterexample pair when `admitted == False`
  * `loss_ledger: Optional[Dict[str, Any]]`
  * `local_terminal: str`
  * `canonical_terminal: str` — one of the 6 canonical terminals (`Preserve`, `Repair`, `Recompute`, `Invalidate`, `Quarantine`, `Refuse`/`Reject`)
  * `admitted: bool`
  * `certified: bool`
  * `authorized: bool = False` (`AuthorityEffect: None`, `certified_implies_authorized: False`)
  * `reason: str`

### 3.2 Core Evaluators & Domain Adapters in `normal_forms/ir_kernel.py`

1. **`evaluate_nf_kernel(spec: NFKernelSpec, carrier_rows: Sequence[Mapping[str, Any]], asserted_pairs: Optional[Sequence[Tuple[str, str]]] = None) -> KernelEvaluationReceipt`**
   * Runs Stage A (Level 00 `WDNF`/`PDNF` cut check) followed by Stage B (`OBNF` collision and protected-law check) and deterministic minimal-counterexample extraction.
2. **`lower_fd_to_kernel_spec(fd: FunctionalDependency, key_field: str, heading: Sequence[str]) -> NFKernelSpec`**
   * Lowers any classical functional dependency $X_{\text{det}} \to Y_{\text{dep}}$ into an `NFKernelSpec`:
     * `collapse_fields = tuple(sorted(fd.determinant))` ($F$ projects rows onto determinant $X_{\text{det}}$)
     * `protected_law_fields = tuple(sorted(fd.dependent))` (if $F(r_1) = F(r_2)$, then $r_1$ and $r_2$ must agree on $Y_{\text{dep}}$; any disagreement emits an `obstructed_collision` witness pair $(r_1, r_2)$ with the exact offending dependent attribute!).
3. **`lower_coda_mur_to_kernel_spec(source_fields: Sequence[str], target_fields: Sequence[str], key_field: str, protected_fields: Sequence[str]) -> NFKernelSpec`**
   * Lowers a `CODA_MUR` representation projection into an `NFKernelSpec` that classifies key-preserving attribute drops as `admissible_collisions` (with sealed `LossLedger`) and protected-field collisions/mutations as `obstructed_collisions`.

---

## 4. Verification Plan: `tests/test_ir_kernel.py`

We will add `tests/test_ir_kernel.py` to the `unittest` suite with 4 test methods:

1. **`test_wdnf_and_obnf_kernel_refusal_and_witness_matrix`:**
   * Verifies exact `minimal_counterexample` extraction for:
     * Subsingleton carrier ($|X| < 2 \implies \text{SubsingletonCollapseRefusal} \to \text{Refuse}$)
     * Self-difference assertion ($(x, x) \implies \text{IrreflexivityViolation} \to \text{Reject}$)
     * Ghost distinction ($(x, y)$ with identical `distinction_fields` $\implies \text{GhostDistinctionViolation} \to \text{Reject}$)
     * Missing protected law declaration ($\text{RequireProtectedLawDeclaration} \to \text{Refuse}$)
     * Admissible collision (`AcceptAdmissibleCollision` $\to$ `Preserve` / `Quarantine`) vs obstructed collision (`PromoteToObstruction` $\to$ `Reject`).
2. **`test_relational_fd_lowering_equivalence_and_minimal_witness_80_trials`:**
   * Across 80 randomized relation instances and functional dependencies $X \to Y$ (both satisfied and injected with 1-to-3 tuple violations), verifies that `evaluate_nf_kernel(lower_fd_to_kernel_spec(...))` agrees 100% with `check_instance_satisfies_fds` in `normal_forms/multi_hop_composition.py` AND extracts a valid pair of rows $(r_1, r_2)$ where $r_1[X] = r_2[X]$ and $r_1[Y] \neq r_2[Y]$.
3. **`test_coda_mur_lowering_equivalence_and_loss_ledger_80_trials`:**
   * Across 80 randomized projection schemas and row sets, verifies that `evaluate_nf_kernel(lower_coda_mur_to_kernel_spec(...))` matches `@coda_mur_projection` terminal routing (`Preserve`, `Quarantine`, `Reject`) and produces a valid SHA-256 Merkle `LossLedger`.
4. **`test_authority_firewall_invariants_across_all_kernel_receipts`:**
   * Verifies `authorized == False`, `authority_effect == "None"`, and `certified_implies_authorized == False` on every receipt.

---

## 5. Files to Create / Modify in PR #12

* **Create:** `normal_forms/ir_kernel.py`
* **Create:** `tests/test_ir_kernel.py`
* **Modify:** `normal_forms/__init__.py` (re-export `ConstructiveWitnessPair`, `NFKernelSpec`, `KernelEvaluationReceipt`, `evaluate_nf_kernel`, `lower_fd_to_kernel_spec`, `lower_coda_mur_to_kernel_spec`)

