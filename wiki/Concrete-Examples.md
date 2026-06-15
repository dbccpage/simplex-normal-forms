# Concrete Examples

The Simplex framework provides three concrete demonstration cases (mechanization targets) that illustrate how the theoretical cochain complex and observer-relative ontologies translate into operational rules.

---

## [Example 1: BQNF Orders & Paid Revenue](../examples/01_bqnf_orders_paid_revenue.md)

This demo illustrates a dynamic materialized view scenario where a database needs to evaluate if an incoming Change Data Capture (CDC) event stream can be used to incrementally repair a cached view.

* **Source Relation**: `Orders(order_id, customer_id, status, amount, updated_at)`
* **Target View**: `SUM(amount)` aggregated by `customer_id` for orders where `status = 'paid'`.
* **The BQNF Solution**: Instead of recomputing the entire view or blindly updating columns, the database evaluates the write defect $\omega(e)$ induced by the CDC stream:
  * **Repair**: Certified when the CDC event contains complete before/after values for the required columns (`status`, `amount`, `customer_id`), allowing the system to update the running sum locally.
  * **Invalidate**: Triggered if required predicate evidence is missing from the stream.
  * **Preserve**: Triggered for updates to columns that do not impact the view (e.g., `updated_at`).

---

## [Example 2: Certificate Table Without Verifier](../examples/02_certificate_table_without_verifier.md)

This demo clarifies the boundary between **certification** and **authorization**, addressing a key design rule of Simplex contracts.

* **Core Thesis**: A database table containing certificate metadata does not create authority on its own.
* **Certified Normal Form vs. Authorized Normal Form**:
    $$\text{CertifiedNF}(x) \not\Rightarrow \text{AuthorizedNF}(x)$$
* **Operational Rejection**:
  * If a certificate exists in the table but no verifier has replayed and verified its evidence, it resolves to `Reject` or `Refuse`.
  * If a verifier is active but the transaction request falls outside its declared scope, it resolves to `Reject`.

---

## [Example 3: Observer-Relative Freshness](../examples/03_observer_relative_freshness.md)

This demo illustrates the operational layout of an observer-relative freshness packet used by distributed replica caches.

* **Scenario**: A dashboard observer (`dashboard_region_us_east`) reads a value from a boundary relvar.
* **Freshness Packet Invariants**: The packet contains metadata detailing the source epoch, replica lag, cache age, and the observer's Service Level Agreement (SLA).
* **Resolution Rules**:
  * If the cache age exceeds the SLA, it resolves to `Invalidate`.
  * If the observer attempts to read outside its declared replica scope, it is blocked with `Refuse`.
  * If the freshness metadata is incomplete, it falls back to `ConservativeInvalidate`.
