# Quotient Normal Form and Boundary-Certified Databases

> Absorbed product-wedge paper copy from
> `omega_engine/research/in_work/simplex_cosmos_papers/SMPLX_009_Simplex Databases/crap/000_Quotient Normal Form and Boundary-Certified Databases.md`.
> The source folder was integrated into the root scaffold and removed.

**Author:** Jeremy H. Carroll  
**Date:** May 2026  
**Version:** v1.0 Pre-Print

## Status

Application and product-development paper. This paper states the finite database wedge: relational theory classifies data at rest; boundary-certified systems certify state change in motion.

**Expanded treatment:** `1a_bqnf_incremental_repair.md` (SMPLX-009 Paper A) — full BQNF definition, running example, terminal routes, theorems, SmplCache mapping.

## Introduction

Classical relational normal forms are static dependency disciplines. They describe how facts should be decomposed to avoid update anomalies, but they do not decide whether a runtime write can repair a cache, preserve an observer view, commute with another write, or safely update a materialized result. SmplCache and related systems treat writes as finite boundary events and decide repairability by quotient membership.

The core line is:

\[
\boxed{\text{A database should not guess what a write breaks. It should compute the obstruction.}}
\]

## Main Idea

For each database layer \(L_i\), declare

\[
C^0_i\xrightarrow{d_{0,i}}C^1_i,
\qquad
Q^1_i=C^1_i/\operatorname{im}(d_{0,i}).
\]

A write event \(e\) induces a finite layer defect

\[
\omega_i(e)\in C^1_i.
\]

After admissible repair, the selected residual is

\[
h_i(e)=\omega_i(e)-d_{0,i}\alpha_i^*.
\]

The layer can repair exactly iff

\[
[\omega_i(e)]=0\in Q^1_i,
\]

equivalently \(\omega_i(e)=d_{0,i}\alpha_i\) for some admissible repair \(\alpha_i\). If not, the selected residual \(h_i(e)\) is nonzero.

Otherwise it must follow a declared refusal or escalation route.

Classical normal-form violations can be represented as labeled quotient-obstruction slices once dependency-specific encodings are declared: partial-key, transitive, non-superkey determinant, elementary-key, multivalued, and join-dependency classes. The conservative theorem is one-way until explicit matrices are built:

\[
\text{known normal-form violation under a declared dependency encoding}
\Rightarrow
\text{nonzero labeled quotient obstruction}.
\]

The converse is not asserted until the dependency matrices, admissible repairs, and equivalence relation are explicitly fixed.

For SmplCache, repairability is a property of the triple

\[
(\mathsf{schema},\mathsf{workload},\mathsf{CDC/write\ stream}),
\]

not of schema alone. SUM, COUNT, and AVG repairs are complete for supported linear aggregate views when the CDC event supplies old value, new value, group key, before/after predicate truth evidence, and necessary sufficient statistics (e.g., AVG requires SUM and COUNT). MIN/MAX require auxiliary extremum state or conservative invalidation when the changed row may be the unique extremum. Unsupported SQL features must return \(\mathsf{Unsupported}\) or \(\mathsf{ConservativeInvalidate}\), never silent success.

### Diagnostic Routes

| Route | Meaning |
|---|---|
| `Repair` | quotient class zero; local delta update is certified |
| `Invalidate` | repair not certified; cached object marked stale |
| `Serialize` | concurrent boundary events do not commute |
| `Recompute` | repair unavailable but full materialization can be rebuilt |
| `Lift` | add auxiliary state, index, witness table, or dependency edge |
| `Unsupported` | SQL/workload feature outside declared fragment |
| `ConservativeInvalidate` | safe fallback when evidence is incomplete |

**Theorem (Boundary Repair Soundness).**  
Given a declared schema, workload, layer map, and CDC event evidence, a local repair is sound only if the induced write defect lies in the declared repair image. If the defect class is nonzero, any silent local patch is unsound; the system must invalidate, serialize, lift, escalate, or refuse.
