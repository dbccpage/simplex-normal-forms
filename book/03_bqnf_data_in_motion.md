# BQNF: Data in Motion

Status: Operational semantics / Mechanization target.

Boundary-Quotient Normal Form (BQNF) is the core change normal form. It disciplines CDC events, cache repair, and materialized-view repair by asking whether a write event can be applied as a certified repair to an observer boundary.

## Five-Clause Checklist

1. boundary declared
2. delta computable
3. quotient class computable
4. repair image declared
5. terminal route declared

## Operational Rule

```text
if event misses boundary:
  Preserve
elif omega = d0(alpha):
  Repair(alpha)
elif Xi = 0:
  Invalidate or ConservativeInvalidate
elif d1(omega) != 0:
  ClosureFailure
else:
  Lift, Escalate, Recompute, or Invalidate
```

## Orders / paid_revenue_by_customer

Canonical demo: [../examples/01_bqnf_orders_paid_revenue.md](../examples/01_bqnf_orders_paid_revenue.md).

Required outcomes:

| Case | Required terminal |
|---|---|
| Missing CDC status / missing predicate evidence | `Invalidate` |
| Unrelated column update | `Preserve` |
| `MAX` without extremum witness | `Unsupported` or `Lift` |
| Exact supported aggregate delta | `Repair` |

## Non-Claims

- Does not replace Codd / relational theory.
- Does not claim all data problems are normal forms.
- Does not claim certification equals authorization.
- Does not claim metadata creates authority.
- Does not require category theory for implementation.
- Does not prove all experimental regimes.
