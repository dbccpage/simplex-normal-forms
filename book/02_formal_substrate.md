# Formal Substrate

Status: Definitional / Mechanization target.

All certified contracts bind to the finite obstruction substrate:

```text
C^0 -> C^1 -> C^2
Q^1 = C^1 / im(d0)
```

Canonical symbols:

| Symbol | Meaning |
|---|---|
| `C^0` | repairs / witnesses / patches |
| `C^1` | defects / mismatches / representation defects |
| `C^2` | closure failures / higher consistency failures |
| `d0` | repair-to-defect map |
| `d1` | defect-to-closure map |
| `Q^1` | `C^1 / im(d0)` |
| `omega` | defect |
| `[omega]` | obstruction class |
| `Phi` | quotient residual magnitude |
| `Gamma` | closure defect magnitude |
| `Xi` | evidence sufficiency |
| `mu` | optional policy/gauge selector |
| `tau` | terminalizer |
| `Lambda` | lift/refusal discipline |

Classification:

| Case | Meaning | Terminal route |
|---|---|---|
| `[omega] = 0` | exact repair exists | `Repair` or `Preserve` |
| `[omega] != 0` and `d1(omega) = 0` | coherent residual | `Lift`, `Escalate`, `Recompute` |
| `d1(omega) != 0` | closure failure | `ClosureFailure`, `Refuse` |
| `Xi = 0` | missing evidence | `BudgetUnknown`, `ConservativeInvalidate`, `Invalidate` |

## Implementation Reading

The substrate is not a demand that implementers use category theory. A verifier can implement this as finite packet validation, matrix/rule evaluation, and terminal-route selection.

## Non-Claims

- Does not replace Codd / relational theory.
- Does not claim all data problems are normal forms.
- Does not claim certification equals authorization.
- Does not claim metadata creates authority.
- Does not require category theory for implementation.
- Does not prove all experimental regimes.
