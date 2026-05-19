# normal form contracts

Typed contract objects for SMPLX-009. **Contracts are boring and checkable**; papers carry narrative.

> The first demos are JSON-first. SQL adapters come later. The theory is about finite packets, evidence, obstruction, and terminalization; a database engine is only one carrier.

## Canonical pipeline

Every certified adjudication follows this order (metaphors are not step zero):

```text
normal form contract
  → finite carrier
  → cochain complex (C0 → C1 → C2)
  → obstruction class in Q1 = C1 / im(d0)
  → gauge / metric / selector (optional)
  → terminal route
  → certificate
```

**Default substrate:** `finite_obstruction_cochain_complex` — see `substrate/default_finite_obstruction_policy.yaml`.

Graphs, streams, finite metric locality cones, horizon channels, presheaves, density matrices, thimbles, Maurer–Cartan, holography, etc. enter only as:

* `carrier_realization` — concrete finite model of C0/C1/C2 (`substrate/carrier_realizations_catalog.yaml`)
* `geometry_module` — quarantined diagnostics (`geometry_modules/*.yaml`)

## Layout

```text
schema/
  normal_form_contract_schema.yaml
  obstruction_substrate_schema.yaml
substrate/
  default_finite_obstruction_policy.yaml
  carrier_realizations_catalog.yaml
contracts/*.yaml
geometry_modules/*.yaml
index.yaml
symbol_dictionary.md
readme.md
```

## Design rules

1. **Normal form** contracts exclude an anomaly on a declared **subject** (`relvar`, `boundary_relvar`, …).
2. **Transport / authority** entries are **not** normal forms — `contract.transport.gtmur`, `contract.compilation.cpnf`.
3. `certified_implies_authorized` is always `false`.
4. Epistemic NFs stay `status: draft` until finite validation + substrate binding exist in a verifier.
5. Certificate rows without verifier = **out of contract**.
6. **Theorem hygiene** (GTLA guardrail): finite carrier, declared operators, cochain, diagnostics, hypotheses, replayable certificate, refusal semantics, non_claims — required to promote beyond `draft`.

## Exact / residual / open (default policy)

| Class | Condition | Typical terminals |
|---|---|---|
| Exact | `[omega] == 0` | Repair, Accept, TransportOk |
| Residual closed | `d1(omega)==0` and `[omega]!=0` | Escalate, Lift, Residual |
| Open | `d1(omega)!=0` | ClosureFailure, Refuse |
| Unknown | missing evidence | Invalidate, ConservativeInvalidate |

## Substrate vs geometry (do not conflate)

| Layer | Role |
|---|---|
| Cochain complex | canonical obstruction calculus |
| Directed graph | dependency / CDC / transition carrier |
| Presheaf | observer gluing / local-to-global |
| Matrix / density operator | weighted epistemic / projection state |
| Ordered stream | queues / CDC / flow control with backpressure, drop, replay, and watermark evidence |
| Finite metric graph | locality-bounded propagation, light-cone checks, and Lieb-Robinson-style finite shadows |
| Boundary channel | horizon, redaction, eviction, compaction, and emission accounting |
| Thimbles / MC / holography | **geometry_module only** — quarantined until finite bound |

## Motion frontier (draft contracts)

These are finite operational normal forms for data in motion that classical database theory leaves implicit:

| Contract | Excludes |
|---|---|
| `nf.motion.flow_control` | silent stream loss, lag, reorder, duplicate, overflow |
| `nf.relativistic.lightcone` | impossible causal ordering across distributed events |
| `nf.relativistic.time_sync` | exact global-time assumptions |
| `nf.motion.locality_lrb` | instantaneous global influence across local graphs |
| `nf.motion.horizon_emission` | exterior authority over horizon-crossed / erased / emitted data without a ledger |

Physics names are used as finite contract analogies unless a verifier binds a concrete physical carrier. The contract must state its non-claims.

## Hierarchy (atlas §0)

```text
Form ⊂ Normal Form ⊂ Certified Normal Form ⊂ Authorized Normal Form
```

## Related documents

| Path | Role |
|---|---|
| `symbol_dictionary.md` | formal substrate dictionary |
| `../0_relvar_relation_table_and_boundary_relvar.md` | subject ontology |
| `../1a_bqnf_incremental_repair.md` | BQNF paper |
| `../1b_gtmur_representation_transport.md` | GTMUR / CpNF |

## Verifier integration (planned)

```text
load contract.id
load substrate policy
optional: bind carrier_realization or geometry_module
validate declarations + finite evidence
classify [omega] → terminal
emit certificate
```
