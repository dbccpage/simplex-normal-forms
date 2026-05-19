# Domain Contract Registry

Status: Domain extension.

This directory contains domain/application contracts that may instantiate the finite-authority grammar but are not core database normal forms.

Rules:

- Do not call these normal forms.
- Keep physics-inspired names in notes, not titles.
- Emit canonical terminal routes; map local diagnostic terminals if needed.
- Preserve non-claims and verifier obligations.

Current contracts:

- `contract.motion.locality_bound.yaml`
- `contract.spacetime.lightcone_causality.yaml`
- `contract.time.clock_sync.yaml`

Non-claims: does not replace Codd / relational theory; does not claim all data problems are normal forms; does not claim certification equals authorization; does not claim metadata creates authority; does not require category theory for implementation; does not prove all experimental regimes.
