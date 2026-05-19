# Paper E: Finite Obstruction Substrate

Status: Definitional / Mechanization target.

The substrate for certified contracts is:

```text
C^0 -> C^1 -> C^2
Q^1 = C^1 / im(d0)
```

The substrate turns informal failure into finite terminalization:

- exact repair
- closed residual
- closure failure
- missing evidence

The goal is not to prove all mathematics at once. The immediate goal is a disciplined machine-readable shape that can be validated, tested, and extended without category drift.

Mechanization targets:

- schema validation
- terminal validation
- contract completeness checks
- sample verifier traces
- negative test packets
