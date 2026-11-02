# Project status — 2026-11-02

Source baseline: `main` at `da498e507ebf6c35cac4355d711e3be30c23a07c`.
Implementation, catalog declarations, and public deployment have separate gates.

## Implementation and verification

| Work | Evidence | Status |
| --- | --- | --- |
| MVP selection, four workbenches, import guide, Render blueprint | [PR #17](https://github.com/dbccpage/simplex-normal-forms/pull/17), merged at `489f3e1` | Implemented |
| Streaming and scalar lowering corrections | [PR #18](https://github.com/dbccpage/simplex-normal-forms/pull/18), merged at `d59f890` | Implemented; scope in [CORRECTNESS_SCOPE.md](CORRECTNESS_SCOPE.md) |
| Bundled resources, installed distribution checks, CI | [PR #19](https://github.com/dbccpage/simplex-normal-forms/pull/19), merged at `da498e5` | Implemented |
| Corrected source suite | 232 tests passed on Python 3.12 and 3.14 during premerge verification | Scoped regression evidence |
| Hosted checks on merged `da498e5` | [tests-and-distribution](https://github.com/dbccpage/simplex-normal-forms/actions/runs/41529136846): Windows/Linux × Python 3.10/3.14 and isolated distribution job | Passed |
| Local HTTP smoke, 2026-11-02 22:02 UTC | [Receipt](verification/2026-11-02-local-http.json): 15 checks, two clients, two repetitions of five POST cases | Passed; not a public latency benchmark |
| Initial custom-domain HTTP smoke, 2026-11-02 22:03 UTC | [Receipt](verification/2026-11-02-public-http.json): `/healthz` failed at DNS lookup | Historical failure before DNS correction; TLS not reached |
| Corrected CNAME, 2026-11-02 22:07 UTC | Public resolver `1.1.1.1` returned `smplxnf.anomalon.com → smplxnf-live.onrender.com`, TTL 3600 | DNS record observed; assignment to the intended service not yet verified |
| Supplied Render target, 2026-11-02 22:07 UTC | [Receipt](verification/2026-11-02-corrected-render-http.json): HTTPS `/healthz` returned 404 | Application health check failed |
| Canonical hostname retry, 2026-11-02 22:08 UTC | [Receipt](verification/2026-11-02-corrected-domain-http.json): local resolver still failed | Propagation/cache discrepancy; no TLS verdict for this hostname |
| Latest custom-domain check, 2026-11-02 22:25 UTC | [Receipt](verification/2026-11-02-domain-service-mismatch.json): valid HTTPS, HTTP 200, health service `smplcache-live`, HTML title SmplCache Live | Wrong application attached to the domain; Studio acceptance failed |
| Render account/service state | User screenshot shows certificate issued and target `smplcache-live.onrender.com`; account inspection still unavailable | Custom domain is attached to the existing SmplCache application; intended Studio service remains unverified |

GitHub Pages completing its own deployment does not establish that the FastAPI
application is running on Render. The health response's fixed version `0.1.0`
also does not identify a deployed Git commit.

The user subsequently supplied a Render project screenshot showing
`owed-workbench` and `smplcache-live` as the two existing Production services,
and a new-web-service URL. These are distinct from the proposed Simplex service.
The earlier accidental `simplxnf` spelling and its failed HTTP/TLS probes are
retained in the receipts as history. The canonical target remains `smplxnf`.

**Latest state:** DNS still points to `smplxnf-live.onrender.com`, but Render
serves SmplCache Live for the custom Host header. The certificate is now valid.
This is a routing/application mismatch, not a successful Studio deployment.
Create/verify the separate service from `dbccpage/simplex-normal-forms`, move
only this custom-domain association from the SmplCache service to it, and
align the CNAME with its assigned hostname. Preserve the existing SmplCache
service and its application. No Studio API POSTs were sent to that application.

Local browser checks exercised relational synthesis, streaming, compiler and AI
workbenches. Switching to the lossy decomposition preset exposed a frontend
parser defect: `(A, B), (B, C)` was flattened into one component and displayed a
lossless result. The correction preserves the two components and renders the
spurious-tuple witness; zero-step lossy traces also no longer claim an already
distinguished tableau. `node tests/test_frontend.cjs` checks the actual request
handler and rendering for parenthesized, semicolon and blank component inputs.
These changes require their own review/CI and are not part of baseline `da498e5`.

## How to read the catalog and wiki

All **112 contracts** pass the catalog's structural checks. Reading their
`identity` metadata gives:

| Field | Declared counts |
| --- | --- |
| `status` | 24 active, 87 draft, 1 deprecated |
| `verification_status` | 35 executable, 75 absent, 2 missing |
| `theory_status` | 48 established, 42 proposed, 11 experimental, 9 admitted, 2 missing |

These counts describe declarations, not independent audits of every verifier.
The index separately lists 25 active and 87 draft entries plus a deprecated
ACNF entry; ACNF occurs in both draft and deprecated lists. Index membership
and per-contract status are different fields and have not been silently aligned.

Wiki diagrams and generic phrases such as “Certified Output” describe intended
contract behavior; they are not receipts for a successful execution. In
particular, a contract marked `verification_status: absent` supplies no
executable verification by that declaration. Proposed/admitted physics contracts
and research-forum scenarios remain subject to their stated assumptions. Regex
claim-word checks do not establish mathematical correctness, originality, or
the absence of plagiarism. Certification does not confer authority.

The browser compiler endpoint demonstrates functional-dependency lowering and
a constructed subsumption comparison. It does not execute an arbitrary
four-layer operadic DAG or compile all 112 contracts. The AI workbench accounts
for whitespace-separated tokens, not a model tokenizer or semantic preservation.

## Reconciliation with the supplied MVP notes

The user supplied the recent Gemini/Teamwork handoff on 2026-11-02. Its source
text SHA-256 is
`39b3d8f2ce39853808e862145693040f5f2b7767f20cdb4bbb4ffc9dd3d82b37`.
That narrative records milestones 1–4, the original 136 pytest items / 89
unittest methods, and the creation of PR #17. It is historical implementation
evidence, not proof of a completed Render deployment. Its worker and panel
sign-offs have not been independently reconstructed here.

The handoff's old checkout path and instruction to merge PR #17 are superseded.
Its four example `preset_id` request bodies do not match the implemented API:
relational, streaming and AI requests need explicit fields, while the compiler
can fall back to defaults and ignore an unknown preset ID. Use the complete
objects returned by `/api/presets`, as [the HTTP smoke script](../scripts/http_smoke.py)
does. The original 136-test count is preserved as history, not current coverage.

## Next work, in order

1. Obtain authenticated Render access; inspect the supplied project before
   creating a duplicate service. Deploy the current reviewed `main` and record
   its exact SHA, service ID, deploy ID, region, plan and assigned hostname.
2. Verify the assigned `onrender.com` origin with the HTTP smoke script. Compare
   the **actual** hostname with the user's existing CNAME target
   `smplxnf-live.onrender.com`; report any needed correction.
3. Add `smplxnf.anomalon.com` to the service's Custom Domains, verify DNS and TLS;
   run the same HTTPS checks and all four browser workflows on the public origin.
4. Record deployment receipts and measured latencies. A bounded concurrency
   smoke is not evidence of sustained load capacity or a sub-200 ms SLA.
5. Continue contract-by-contract evidence audits and replace generic wiki
   examples with executable witnesses where useful. Do not expand the MVP's
   advertised scope ahead of those checks.

See [DEPLOYMENT.md](DEPLOYMENT.md) for the runnable handoff.
