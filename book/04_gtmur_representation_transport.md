# GTMUR Representation Transport

Status: Operational semantics / Conditional theorem.

GTMUR is an authority contract for representation transport. A representation may be equivalent for query evaluation while not equivalent for authority.

Core witness:

```text
chi_F: D_target F => bar F D_source
```

Operational reading:

> Updates commute with representation change, up to declared loss.

## Required Objects

- source representation
- target representation
- transport `F`
- finite-core action `bar F`
- descent witness `chi_F`
- certificate form
- loss ledger `Loss(F)` when distinctions are erased
- target verifier record

## Failure Terminals

- `Refuse` for missing witness.
- `Quarantine` for unverified certificate packet.
- `Lift` when policy/authority must be checked externally.
- `Reject` for authority laundering.

```text
CertifiedNF(x) does not imply AuthorizedNF(x).
A certificate table without a verifier is just another table.
```

## Non-Claims

- Does not replace Codd / relational theory.
- Does not claim all data problems are normal forms.
- Does not claim certification equals authorization.
- Does not claim metadata creates authority.
- Does not require category theory for implementation.
- Does not prove all experimental regimes.
