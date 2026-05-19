# Implementation Contracts

Status: Mechanization target.

The machine-readable contract system lives in `/contracts`. Every concrete YAML contract must include:

- `id`
- `title`
- `version`
- `status`
- `category`
- `normalized_object`
- `anomaly_excluded`
- `required_declarations`
- `required_evidence`
- `obstruction_substrate`
- `validation_rules`
- `terminal_routes`
- `certificate_requirements`
- `authorization_boundary`
- `proof_obligations`
- `non_claims`
- `examples`

Core schema:

- [../contracts/normal_form_contract_schema.yaml](../contracts/normal_form_contract_schema.yaml)
- [../contracts/obstruction_substrate_schema.yaml](../contracts/obstruction_substrate_schema.yaml)

Core contracts:

- [../contracts/nf.change.bqnf.yaml](../contracts/nf.change.bqnf.yaml)
- [../contracts/nf.transport.gtmur.yaml](../contracts/nf.transport.gtmur.yaml)
- [../contracts/nf.epistemic.freshness.yaml](../contracts/nf.epistemic.freshness.yaml)
- [../contracts/nf.epistemic.authority.yaml](../contracts/nf.epistemic.authority.yaml)
- [../contracts/nf.epistemic.observer.yaml](../contracts/nf.epistemic.observer.yaml)
- [../contracts/authority_observer_stack.yaml](../contracts/authority_observer_stack.yaml)

Quarantined contracts:

- [../contracts/experimental/nf.experimental.gauge.yaml](../contracts/experimental/nf.experimental.gauge.yaml)
- [../contracts/experimental/nf.experimental.bell_contextuality.yaml](../contracts/experimental/nf.experimental.bell_contextuality.yaml)
- [../contracts/experimental/nf.experimental.quantum_observer_ontology.yaml](../contracts/experimental/nf.experimental.quantum_observer_ontology.yaml)

Domain contracts:

- [../contracts/domain/contract.motion.locality_bound.yaml](../contracts/domain/contract.motion.locality_bound.yaml)
- [../contracts/domain/contract.spacetime.lightcone_causality.yaml](../contracts/domain/contract.spacetime.lightcone_causality.yaml)
- [../contracts/domain/contract.time.clock_sync.yaml](../contracts/domain/contract.time.clock_sync.yaml)

## Implementation Priorities

1. YAML shape validation.
2. Canonical terminal validation.
3. BQNF Orders verifier.
4. GTMUR transport certificate checker.
5. Loss ledger checker.
6. Freshness packet checker.
7. Authority boundary checker.

## Non-Claims

- Does not replace Codd / relational theory.
- Does not claim all data problems are normal forms.
- Does not claim certification equals authorization.
- Does not claim metadata creates authority.
- Does not require category theory for implementation.
- Does not prove all experimental regimes.
