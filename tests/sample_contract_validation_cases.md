# Sample Contract Validation Cases

Status: Mechanization target.

## Positive

- `nf.change.bqnf` contains all required schema fields.
- `nf.transport.gtmur` declares `chi_F`.
- `nf.epistemic.freshness` includes freshness evidence and terminal routes.
- Experimental observer-ontology local terminal routes map to canonical terminal routes.

## Negative

- A contract omits `terminal_routes`.
- A contract uses a non-canonical emitted terminal route.
- A contract sets `certified_implies_authorized: true`.
- GTMUR transport erases a predicate without `Loss(F)`.
- BQNF repairs an aggregate after a boundary hit with `Xi = 0`.
- A freshness timestamp is treated as freshness authority without invalidation evidence.

Non-claims: does not replace Codd / relational theory; does not claim all data problems are normal forms; does not claim certification equals authorization; does not claim metadata creates authority; does not require category theory for implementation; does not prove all experimental regimes.
