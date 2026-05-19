# Loss Ledgers

Status: Operational semantics.

A loss ledger records distinctions erased by representation transport, compression, redaction, summarization, projection, approximation, or forgetting.

Use `Loss(F)` for a transport `F`.

Required fields:

```yaml
loss_ledger_id: string
transport: F
source_representation: string
target_representation: string
erased_distinctions:
  - field: string
    reason: projection | aggregation | compression | redaction | precision_loss | token_budget | retention_policy
    authority_impact: none | bounded | authority_reducing | unknown
residual_budget:
  Phi: number | null
  Gamma: number | null
  Xi: number | null
terminal_route: string
non_claims: [string]
```

Rule: if `F` erases attributes, precision, lineage, predicates, joins, or provenance and no loss ledger is present, `TransportOK(F)` must fail.

Non-claims: does not replace Codd / relational theory; does not claim all data problems are normal forms; does not claim certification equals authorization; does not claim metadata creates authority; does not require category theory for implementation; does not prove all experimental regimes.
