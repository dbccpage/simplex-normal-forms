# Tests

Status: Mechanization target.

This directory defines research-contract tests, not a complete verifier implementation.

Initial test priorities:

1. YAML contracts parse recursively, including `contracts/experimental/`.
2. Every concrete contract has required schema fields.
3. Terminal routes belong to the canonical terminal set.
4. Local experimental terminal routes map to canonical routes.
5. `certified_implies_authorized` is false in every authorization boundary.
6. There are exactly three canonical demos in `examples/`.
7. BQNF Orders demo has positive and negative cases.
8. GTMUR rejects missing `Loss(F)` when distinctions are erased.
9. Freshness timestamp without freshness authority fails.

Non-claims: does not replace Codd / relational theory; does not claim all data problems are normal forms; does not claim certification equals authorization; does not claim metadata creates authority; does not require category theory for implementation; does not prove all experimental regimes.
