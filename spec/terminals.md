# Terminal Route Specification

Status: Operational semantics.

Every verifier result must emit one canonical terminal route or a contract-specific terminal mapped to one canonical terminal.

Required verifier fields:

```yaml
terminal_route: Repair
canonical_terminal: Repair
reason: exact obstruction class
obstruction_class: "[omega] == 0"
evidence_sufficiency: true
authorization_status: certified_not_authorized
```

Rules:

- Use `Preserve` only when the declared boundary is not intersected.
- Use `Repair` only when `omega = d0(alpha)` is witnessed.
- Use `Invalidate` or `ConservativeInvalidate` when evidence is missing and stale service would be unsafe.
- Use `ClosureFailure` when `d1(omega) != 0`.
- Use `Refuse`, `Reject`, or `Abstain` when the verifier must decline authority.
- Never use certificate success as authorization success.

Non-claims: does not replace Codd / relational theory; does not claim all data problems are normal forms; does not claim certification equals authorization; does not claim metadata creates authority; does not require category theory for implementation; does not prove all experimental regimes.
