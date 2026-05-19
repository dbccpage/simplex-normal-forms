# Demo 01: BQNF Orders / Paid Revenue

Status: Mechanization target.

Source relation:

```sql
Orders(order_id, customer_id, status, amount, updated_at)
```

Observer:

```sql
paid_revenue_by_customer(customer_id, paid_revenue)
```

View:

```sql
SELECT customer_id, SUM(amount) AS paid_revenue
FROM Orders
WHERE status = 'paid'
GROUP BY customer_id;
```

Boundary:

```text
relations: Orders
attributes: customer_id, status, amount
predicate: status = 'paid'
group: customer_id
aggregate: SUM(amount)
```

BQNF checklist:

1. boundary declared
2. delta computable
3. quotient class computable
4. repair image declared
5. terminal route declared

Required outcomes:

| Case | Required terminal |
|---|---|
| Supported `SUM` delta with before/after status, amount, and customer evidence | `Repair` |
| Missing CDC status / missing predicate evidence | `Invalidate` |
| Unrelated column update, e.g. `updated_at` only | `Preserve` |
| `MAX` without extremum witness | `Unsupported` or `Lift` |

Non-claims:

- Does not prove source data is true.
- Does not authorize side effects.
- Does not certify representation transport.
