# Symbol Dictionary

Status: Definitional.

The canonical finite obstruction substrate is:

```text
C^0 -> C^1 -> C^2
```

| Symbol | Meaning |
|---|---|
| `C^0` | admissible repairs / witnesses / local patches |
| `C^1` | defects / write-event mismatches / representation defects |
| `C^2` | closure failures / higher consistency failures |
| `d0` | repair-to-defect map |
| `d1` | defect-to-closure map |
| `Q^1` | quotient obstruction space, `C^1 / im(d0)` |
| `omega` | event defect |
| `[omega]` | obstruction class in `Q^1` |
| `Phi` | quotient residual magnitude |
| `Gamma` | closure defect magnitude |
| `Xi` | evidence sufficiency / descent availability |
| `mu` | optional policy/gauge metric selector |
| `tau` | terminalizer |
| `Lambda` | lift/refusal discipline |
| `alpha` | admissible repair or witness |
| `F` | representation transport |
| `bar F` | finite-core action induced by `F` |
| `chi_F` | descent-compatibility witness |
| `Loss(F)` | loss ledger for erased distinctions |

Classification:

| Condition | Reading | Typical terminal route |
|---|---|---|
| `[omega] = 0` | exact; defect is repairable by declared `alpha` | `Repair`, `Preserve` |
| `[omega] != 0` and `d1(omega) = 0` | closed residual; coherent but not erased by declared repairs | `Lift`, `Escalate`, `Recompute` |
| `d1(omega) != 0` | open residual / closure failure | `ClosureFailure`, `Refuse` |
| `Xi = 0` | missing finite evidence | `BudgetUnknown`, `ConservativeInvalidate`, `Unsupported` |

Core warning:

```text
CertifiedNF(x) does not imply AuthorizedNF(x).
```

Non-claims: does not replace Codd / relational theory; does not claim all data problems are normal forms; does not claim certification equals authorization; does not claim metadata creates authority; does not require category theory for implementation; does not prove all experimental regimes.
