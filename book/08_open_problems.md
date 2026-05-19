# Open Problems

Status: Proof obligation / Mechanization target.

## Proof Obligations

- BQNF exact repair soundness for supported SPJA aggregate lanes.
- No silent repair when `Xi = 0`.
- GTMUR transport soundness for SQL-to-SPJA compilation under declared loss.
- Authority gate soundness: available, valid, certified, authorized, actionable.
- Observer comparison envelopes for local-to-global claims.

## Executable Tests Needed

- YAML schema validation.
- Terminal route validation.
- BQNF Orders positive/negative cases.
- GTMUR rejects missing `Loss(F)` when distinctions are erased.
- Freshness timestamp without invalidation authority fails.
- Certificate table without verifier fails authorization.

## TODO Ranked by Implementation Value

1. Write a recursive contract validator for required fields.
2. Add canonical terminal-route checker.
3. Add BQNF Orders verifier fixture.
4. Add GTMUR transport fixture with missing loss ledger negative case.
5. Add freshness packet fixture.
6. Add authority boundary fixture proving `certified_implies_authorized: false`.
7. Add link checker for internal Markdown links.
8. Add archived-source disclaimer checker for absorbed appendices.

## Non-Claims

- Does not replace Codd / relational theory.
- Does not claim all data problems are normal forms.
- Does not claim certification equals authorization.
- Does not claim metadata creates authority.
- Does not require category theory for implementation.
- Does not prove all experimental regimes.
