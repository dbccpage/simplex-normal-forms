# Project status — 2026-11-02

Deployed source baseline: `main` at `f9c289cc33f91c2b653f65e6267fde0073c3cd6f`
([PR #21](https://github.com/dbccpage/simplex-normal-forms/pull/21)).
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
| Historical custom-domain check, 2026-11-02 22:25 UTC | [Receipt](verification/2026-11-02-domain-service-mismatch.json): valid HTTPS, HTTP 200, health service `smplcache-live`, HTML title SmplCache Live | Wrong application at that time; subsequently corrected |
| Lossy preset browser fix and status reconciliation | PR #21 merged at `f9c289c`; all five [hosted CI jobs](https://github.com/dbccpage/simplex-normal-forms/actions/runs/41537312875) passed at head `d2e331a`; merge tree matched that head | Implemented and deployed |
| Separate Render service | `smplxnf-live`, Oregon, Free compute, deployed `f9c289c`; [deployment record](verification/2026-11-02-deployment.md) | Live |
| Assigned Render origin, 2026-11-02 22:39 UTC | [Receipt](verification/2026-11-02-render-live-http.json): 15 checks passed with certificate validation enabled | HTTPS/API verified |
| Canonical domain, 2026-11-02 22:54 UTC | [Receipt](verification/2026-11-02-public-live-http.json): 15 checks passed with certificate validation enabled | HTTPS/API verified; full browser acceptance incomplete |

GitHub Pages completing its own deployment does not establish that the FastAPI
application is running on Render. The health response's fixed version `0.1.0`
also does not identify a deployed Git commit.

The user subsequently supplied a Render project screenshot showing
`owed-workbench` and `smplcache-live` as the two existing Production services,
and a new-web-service URL. These are distinct from the proposed Simplex service.
The earlier accidental `simplxnf` spelling and its failed HTTP/TLS probes are
retained in the receipts as history. The canonical target remains `smplxnf`.

**Latest recorded state:** [smplxnf.anomalon.com](https://smplxnf.anomalon.com)
serves Simplex-NF Studio from the separate `smplxnf-live` service. Render showed
the custom domain verified and its certificate issued. DNS points to the assigned
`smplxnf-live.onrender.com` hostname. The earlier mismatch is retained as history;
no Studio API POSTs were sent to SmplCache during that failed check. After the
move, `smplcache.anomalon.com/healthz` still identified `smplcache-live` at
`810fc7cf0d99`. Compute is on the Free plan; Render disclosed a $0.25/month
custom-domain charge, which the user approved. Billing was not audited.

Local browser checks exercised relational synthesis, streaming, compiler and AI
workbenches. Switching to the lossy decomposition preset exposed a frontend
parser defect: `(A, B), (B, C)` was flattened into one component and displayed a
lossless result. The correction preserves the two components and renders the
spurious-tuple witness; zero-step lossy traces also no longer claim an already
distinguished tableau. `node tests/test_frontend.cjs` checks the actual request
handler and rendering for parenthesized, semicolon and blank component inputs.
These changes passed review/CI in PR #21 and are included in deployed `f9c289c`.

On the live custom domain, the default relational page displayed “Lossless Join
Verified (7 steps).” The lossy preset was selected, but its resulting witness
was not inspected before the user stopped computer control. Full live browser
acceptance remains incomplete. Subsequent documentation work uses the terminal
only; no further browser checks are claimed.

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

1. Complete the remaining public browser checklist when the user makes a browser
   available for that purpose: lossy witness, streaming with cochain on/off,
   compiler outputs, AI ledger, quickstart/developer links, console and layout.
   The current documentation task does not resume computer control.
2. Rerun the HTTPS smoke after future application deployments and record the
   deployed SHA separately. The saved bounded probe does not establish sustained
   load capacity, cold-start latency or a sub-200 ms SLA.
3. Continue contract-by-contract evidence audits and replace generic wiki
   examples with executable witnesses where useful. Do not expand the MVP's
   advertised scope ahead of those checks.

See [DEPLOYMENT.md](DEPLOYMENT.md) for the runnable handoff.
