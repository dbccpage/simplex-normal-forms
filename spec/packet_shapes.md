# Packet Shapes

Status: Operational semantics / Mechanization target.

## Certified Data Packet

A certified data packet is not merely a relation instance. It is a predicate claim plus observer and verifier context.

```yaml
predicate_claim: string
relation_or_view_ref: string
observer: string
evidence_ref: string
representation_history_ref: string | null
loss_ledger_ref: string | null
freshness_packet_ref: string | null
terminal_route: string
certificate_ref: string
authorization_status: certified_not_authorized | authorized | refused
```

This packet shape extends, but does not replace, the Codd-Date-Darwen baseline. Predicate precision remains the data-at-rest foundation.

## CDC Evidence Packet

```yaml
event_id: string
source_relation: string
operation: insert | update | delete
primary_key: object
before: object | null
after: object | null
changed_columns: [string]
commit_lsn: string
commit_timestamp: string
source_transaction_id: string
```

## BQNF Repair Certificate

```yaml
certificate_id: string
contract_id: nf.change.bqnf
boundary_fingerprint: object
event_id: string
delta_program: string
omega: object
obstruction_class: string
alpha: object | null
terminal_route: string
evidence_packet_ref: string
verifier_id: string
verified_at: string
authorization_status: certified_not_authorized
```

## Freshness Packet

```yaml
value_ref: string
read_timestamp: string
source_epoch: string
replica_lag_ms: integer
cache_age_ms: integer
invalidation_status: fresh | stale | unknown | invalidated
freshness_sla_ms: integer
terminal_route: string
```

## Transport Certificate

```yaml
certificate_id: string
source_representation: string
target_representation: string
transport: F
finite_core_action: bar_F
descent_witness: chi_F
loss_ledger_ref: string | null
terminal_route: string
verifier_id: string
authorization_status: certified_not_authorized
```

Non-claims: does not replace Codd / relational theory; does not claim all data problems are normal forms; does not claim certification equals authorization; does not claim metadata creates authority; does not require category theory for implementation; does not prove all experimental regimes.
