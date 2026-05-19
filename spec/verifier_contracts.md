# Verifier Contracts

Status: Operational semantics / Mechanization target.

A verifier turns packets and contracts into certified outcomes. It does not grant authorization unless it is explicitly an active authority verifier.

Certified means:

- packet well-formed
- evidence sufficient
- obstruction class computed
- terminal route declared
- certificate verifies

Authorized means:

- active authority verifier accepts under policy, lineage, trust, permission, and scope

```text
CertifiedNF(x) does not imply AuthorizedNF(x).
```

Minimum verifier interface:

```yaml
verifier_id: string
contract_id: string
input_packet_refs: [string]
obstruction_substrate_ref: string
computed_obstruction_class: string
terminal_route: string
certificate_id: string
authorization_boundary:
  certified_implies_authorized: false
  authority_verifier_required: true
```

A certificate table without a verifier is just another table.

Non-claims: does not replace Codd / relational theory; does not claim all data problems are normal forms; does not claim certification equals authorization; does not claim metadata creates authority; does not require category theory for implementation; does not prove all experimental regimes.
