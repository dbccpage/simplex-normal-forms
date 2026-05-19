# Demo 03: Observer-Relative Freshness

Status: Mechanization target.

Freshness timestamp != freshness authority.

Example packet:

```yaml
value_ref: paid_revenue_by_customer:customer_42
observer: dashboard_region_us_east
read_timestamp: "2026-05-19T12:00:00Z"
source_epoch: cdc_lsn_10042
replica_lag_ms: 250
cache_age_ms: 1000
invalidation_status: fresh
freshness_sla_ms: 5000
terminal_route: Preserve
authorization_status: certified_not_authorized
```

Required outcomes:

| Case | Required terminal |
|---|---|
| timestamp present but invalidation status unknown | `BudgetUnknown` or `ConservativeInvalidate` |
| cache age exceeds SLA | `Invalidate` |
| observer reads outside declared replica scope | `Refuse` |
| freshness packet verifies but policy verifier absent | certified, not authorized |

Non-claims:

- Does not prove the value is correct.
- Does not authorize action.
- Does not replace BQNF repair.
