# Executable scope and regression evidence

## Streaming workbench

`POST /api/bqnf/simulate` models one declared sales relation, grouped by
`region`, with finite numeric `amount` values, SUM/MIN/MAX(amount), and an
optional `status = value` predicate. Unsupported boundary shapes return HTTP
400. An explicit empty `initial_sales` means an empty initial state; omitted
initial state uses the demonstration fixture. Initial rows without `status`
retain the fixture convention of `paid`.

Only certified, evidence-sufficient `Repair` decisions mutate state. Unrelated
relations and inactive predicate rows preserve it; unsupported operations and
missing evidence do not mutate it. An active before-image must match one
retained occurrence of `(region, amount, status)` before deletion or update.
Duplicate sales are a multiset, not identified entities. This simulator does
not provide event deduplication, durable offsets, or transaction replay.

The scalar validator routes SUM changes; the simulator supplies its own exact
extremum cochain or explicit base-table fallback for MIN/MAX. Each event reports
`applied`; `final_cache`, region-labelled cochain entries, and per-region
quantile receipts expose the resulting state. The legacy singular quantile
receipt remains the North receipt. Quantile rebalancing traverses retained
value frequencies; the extremum lookup complexity is not an end-to-end stream
complexity bound.

`tests/test_streaming_correctness.py` independently recomputes aggregates and
value frequencies for every prefix of a stream containing ignored/refused
events, predicate entry/exit, duplicate values, new groups, group moves, and
deletions. It also checks quantile mass and exact bucket membership, with and
without extremum lookup.

## Python and SQLite lowering

Required functional-dependency determinant and dependent fields must be
present and non-null. SQLite columns have BLOB affinity, preserving bound
scalar storage types instead of coercing everything to text. Numeric `1` and
text `"1"` remain distinct; numeric `1`, `1.0`, and `True` compare equally.

The cross-target scalar tests cover finite SQLite-bindable values (signed
64-bit integers, finite floats, booleans, strings, and bytes), unique textual
row IDs, missing/null required fields, and INSERT/UPDATE constraints. Arbitrary
Python objects, custom SQLite adapters/collations, and non-finite values are
outside this equivalence evidence. Support-floor checks belong to the batch
installation helper; the emitted row triggers do not enforce batch cardinality
or policy authorization. Existing databases require an explicit migration to
adopt the new column affinities; generated DDL does not migrate them.

`tests/test_lowering_scalar_semantics.py` checks independently computed Python
equality outcomes and native SQLite storage/UPDATE behavior. Passing these
tests is scoped executable evidence, not a general compiler correctness proof.
