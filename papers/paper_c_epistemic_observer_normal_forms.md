# Paper C: Epistemic and Observer Normal Forms

Status: Specification target.

Distributed systems contain bounded claims about facts. They do not contain one omniscient global fact table.

Core packet:

```text
what_is_known
by_whom
as_of_when
under_which_authority
with_what_uncertainty
terminal_route_if_challenged
```

Core forms:

- Location NF
- Replica NF
- State NF
- Freshness NF
- Authority NF
- Context NF
- Observer NF
- Epistemic NF

Primary anomalies:

- ghost locality
- false sameness
- state flattening
- stale authority
- authority laundering
- context smuggling
- observer overreach
- omniscience fiction

Non-claim: epistemic packet structure does not authorize action. Authorization requires an active authority verifier.

TODO: expand each form into a full verifier contract and example packet.
