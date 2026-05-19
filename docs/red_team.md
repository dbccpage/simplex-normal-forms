# Red-Team Review

Status: Operational semantics / Proof obligation.

This document names the attacks a hostile reader will make and how the repo should defend itself.

## What Database Theorists Will Attack

- Calling too many things normal forms.
- Confusing relations with SQL tables.
- Treating metadata as semantics.
- Treating cache repair as classical dependency theory.
- Using category notation without executable content.

Defense:

- Keep Codd-Date-Darwen predicate discipline as chapter 01.
- Protect the term NF.
- Classify evidence, certificate, ledger, observer, and authority material separately.
- Require finite packets and verifier behavior for every claimed normal form.

## What Distributed Engineers Will Reject

- Claims that do not mention clocks, replicas, lag, partial failure, cache invalidation, or operational terminals.
- Claims that sound like “consistency” without an implementation failure.
- Any certificate story without a verifier.

Defense:

- Keep BQNF focused on CDC/cache/materialized-view repair.
- Keep Freshness NF executable or mark it as proof obligation.
- Require terminal routes for missing evidence, stale reads, and unsupported repairs.

## What Category Theorists Will Call Sloppy

- Unspecified objects and morphisms.
- Using quotient/cochain language without finite carriers.
- Claiming transport equivalence without naturality/descent obligations.

Defense:

- Treat category language as optional implementation-independent notation.
- Require `C^0 -> C^1 -> C^2`, `Q^1`, `omega`, `[omega]`, `d0`, and `d1`.
- For GTMUR, require `chi_F: D_target F => bar F D_source`.
- Downgrade unsupported claims to proof obligations.

## What Naming Looks Unserious

- Quantum NF, Market NF, Legal NF, Satellite NF, Condensed Matter NF.
- Lieb-Robinson Locality Normal Form, Light-Cone Causality Normal Form, or Clock Synchronization Normal Form when the content is really a contract.
- UnGodLy NF in the core taxonomy.
- Any comedy or folklore label appearing as normative machinery.

Defense:

- Put domain material under experimental/domain/comedy namespaces only.
- Keep observer-ontology material quarantined.
- Preserve serious names in core: BQNF, GTMUR, Freshness, Authority, Observer, Evidence, Certificate, Ledger.
- Prefer Locality-Bound Propagation Contract, Light-Cone Causality Contract, and Clock Synchronization Authority Contract for domain material.

## Claims to Downgrade to Operational Semantics

- BQNF repair behavior before full theorem proofs.
- GTMUR transport behavior before mechanized proof.
- Freshness authority before verifier fixtures.
- Authority gates before executable policy checks.

## Claims Needing Proof Obligations

- BQNF exact repair soundness for supported SPJA aggregate lanes.
- No silent repair when `Xi = 0`.
- GTMUR transport soundness under declared loss.
- Observer local-to-global comparison envelopes.
- Authority gate preservation across transport.

## Claims Needing Executable Tests

- Missing CDC status returns `Invalidate`.
- Unrelated column update returns `Preserve`.
- `MAX` without witness returns `Unsupported` or `Lift`.
- Certificate row without verifier returns `Reject` or `Refuse`.
- Freshness timestamp without invalidation authority returns `BudgetUnknown` or `ConservativeInvalidate`.
- GTMUR missing `Loss(F)` returns `Refuse`.

## Non-Claims

- Does not replace Codd / relational theory.
- Does not claim all data problems are normal forms.
- Does not claim certification equals authorization.
- Does not claim metadata creates authority.
- Does not require category theory for implementation.
- Does not prove all experimental regimes.
