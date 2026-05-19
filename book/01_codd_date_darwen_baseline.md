# Codd-Date-Darwen Baseline

Status: Definitional.

Classical relational theory is the foundation. It disciplines data at rest by requiring predicate precision, declared types, keys, dependencies, domains, joins, and constraints. Simplex / Anomalon does not replace this baseline; it extends the engineering surface to claims that move, transform, cache, replicate, expire, or become authority-bearing.

## Baseline Rule

A relation is not a bag of rows. It is a predicate extension under a declared type system.

Keep these distinctions strict:

| Relational concept | Implementation term to keep separate |
|---|---|
| relation | table |
| tuple | row |
| attribute | column |
| type | representation |
| predicate | storage layout |
| logic | implementation accident |

Date/Darwen and Tutorial D matter here because they insist that a relational language should expose predicates, types, and relational operators instead of hiding them behind SQL storage idioms. Celko matters from the production side: SQL idioms, constraints, hierarchies, production modeling, and common ways implementations lose the logical predicate.

```text
Date/Darwen:
  predicate discipline, relational purity, type clarity

Celko:
  SQL idioms, constraints, hierarchies, production modeling, failure patterns
```

## Simplex Extension

Simplex normal forms start from the Date/Darwen demand for predicate precision, then extend it to distributed and agent-mediated systems where the predicate alone is no longer enough.

A modern data claim also needs:

```text
predicate claim
observer
evidence
freshness
representation history
loss ledger
verifier
terminal route
authorization boundary
```

This extension is conservative. It does not weaken relational theory. It asks what must be added when clean predicates are cached, transported, observed, summarized, expired, delegated, or used to authorize action.

## Non-Claims

- Does not replace Codd / relational theory.
- Does not claim all data problems are normal forms.
- Does not claim certification equals authorization.
- Does not claim metadata creates authority.
- Does not require category theory for implementation.
- Does not prove experimental regimes.

## TODO

- Add a compact Tutorial D example mapping relation, tuple, attribute, type, predicate, and operator to the Simplex packet vocabulary.
- Add Celko-style SQL implementation examples showing where predicate discipline is lost in production schemas.
