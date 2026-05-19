# Terminal Routes

Status: Operational semantics.

Use the phrase **terminal route** consistently. A terminal route is the typed outcome emitted when a verifier cannot silently continue.

Canonical terminals:

| Terminal | Meaning |
|---|---|
| `Preserve` | event is outside the declared boundary; prior claim remains valid within scope |
| `Repair` | defect is exact: `omega = d0(alpha)` for an admissible repair |
| `Invalidate` | claim is no longer safe to serve as fresh or exact |
| `Recompute` | full recomputation is required instead of incremental repair |
| `Serialize` | concurrent events must be ordered before authority can be claimed |
| `Lift` | residual must move to a higher authority/comparison layer |
| `Escalate` | local verifier cannot decide within declared obligations |
| `Unsupported` | contract does not cover the shape/event/regime |
| `ClosureFailure` | `d1(omega) != 0`; defect fails higher consistency |
| `BudgetUnknown` | evidence, cost, freshness, or approximation budget is missing |
| `ConservativeInvalidate` | safe fallback when evidence is missing |
| `Quarantine` | isolate a packet until verifier or authority review |
| `Decompose` | split a composite object into independently checkable parts |
| `Refuse` | verifier declines the claim/action |
| `Reject` | verifier finds a declared rule violation |
| `Abstain` | verifier intentionally produces no authority-bearing decision |

Terminal routes are not exceptions, slogans, or comments. They are part of the contract surface and should be present in certificates and verifier logs.

Non-claims: does not replace Codd / relational theory; does not claim all data problems are normal forms; does not claim certification equals authorization; does not claim metadata creates authority; does not require category theory for implementation; does not prove all experimental regimes.
