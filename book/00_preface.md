# Preface

Status: Definitional.

This book scaffold organizes the Simplex / Anomalon database theory program into a disciplined, implementation-oriented structure. The aim is not to replace Codd-style relational theory. The aim is to extend the engineering surface to data that moves, changes representation, becomes evidence, expires, or is claimed by an observer.

Core thesis:

> Classical database theory ensures structural consistency of stored data; a complete modern theory must also ensure that every claimed fact is a replayable, observer-relative, authority-bounded statement whose failure modes are explicitly terminalized through finite obstruction.

The relational baseline is Codd-Date-Darwen predicate discipline: relation is not table, tuple is not row, attribute is not column, type is not representation, predicate is not storage, and logic is not implementation accident. The Simplex layer begins only after that baseline is respected.

## Reader Contract

- Normative definitions live in chapters 00-08, `glossary/`, `spec/`, and `contracts/`.
- Absorbed source appendices are provenance, not the authority for current taxonomy.
- Experimental regimes stay quarantined unless they satisfy the protected-term checklist.
- Proof-status labels indicate how much authority a claim has.

## Reading Order

1. Codd-Date-Darwen baseline.
2. Formal substrate.
3. BQNF data in motion.
4. GTMUR representation transport.
5. Epistemic / observer forms.
6. Gauge and higher data regimes quarantine.
7. Implementation contracts.
8. Open problems.

## Non-Claims

- Does not replace Codd / relational theory.
- Does not claim all data problems are normal forms.
- Does not claim certification equals authorization.
- Does not claim metadata creates authority.
- Does not require category theory for implementation.
- Does not prove all experimental regimes.
