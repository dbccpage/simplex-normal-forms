# Epistemic and Observer Forms

Status: Operational semantics / Proof obligation.

Distributed systems contain bounded claims about facts, not one omniscient global fact table. Observer / epistemic forms discipline locality, freshness, authority, context, provenance, and comparison.

Core packet:

```text
what_is_known
by_whom
as_of_when
under_which_authority
with_what_uncertainty
terminal_route_if_challenged
```

## Core Forms

| Form | Normalizes | Anomaly excluded | Status |
|---|---|---|---|
| Location NF | logical identity and physical placement | ghost locality | Proof obligation |
| Replica NF | origin, epoch, causal frontier, divergence budget | false sameness | Proof obligation |
| State NF | value, version, context, confidence, freshness, authority | state flattening | Proof obligation |
| Freshness NF | read timestamp, lag, age, invalidation state, SLA | stale authority | Mechanization target |
| Authority NF | available, valid, certified, authorized, actionable | authority laundering | Mechanization target |
| Context contract | typed user, retrieval, tool, and policy layers | context smuggling | Proof obligation |
| Observer contract | observer, measurements, equivalence, comparison envelope | observer overreach | Proof obligation |
| Epistemic packet | what/by whom/as of/authority/uncertainty/terminal | omniscience fiction | Proof obligation |

Freshness timestamp != freshness authority. Local validity != global authority.

Observer/domain extension provenance: [11_observer_distinguishability_domain_extensions.md](11_observer_distinguishability_domain_extensions.md).

## Non-Claims

- Does not replace Codd / relational theory.
- Does not claim all data problems are normal forms.
- Does not claim certification equals authorization.
- Does not claim metadata creates authority.
- Does not require category theory for implementation.
- Does not prove all experimental regimes.
