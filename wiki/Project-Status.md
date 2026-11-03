# Project status and evidence — 2026-11-02

The web MVP, correctness fixes, packaging and lossy preset browser fix are merged.
[Simplex-NF Studio](https://smplxnf.anomalon.com) is deployed on its own Render
service. HTTPS/API verification passed; full live browser acceptance is incomplete.

| Area | Verified state |
| --- | --- |
| MVP | [PR #17](https://github.com/dbccpage/simplex-normal-forms/pull/17) merged at `489f3e1` |
| Correctness | [PR #18](https://github.com/dbccpage/simplex-normal-forms/pull/18) merged at `d59f890`; tracked-field matching, exact quantile membership and per-region repair receipts corrected |
| Packaging / CI | [PR #19](https://github.com/dbccpage/simplex-normal-forms/pull/19) merged at `da498e5`; source and installed-distribution verification |
| Tests | 232 tests passed in premerge Python 3.12/3.14 runs; [merged-main hosted CI](https://github.com/dbccpage/simplex-normal-forms/actions/runs/41529136846) passed |
| Local HTTP | 15 smoke checks passed on 2026-11-02, including two repetitions of five API cases with two clients |
| DNS | User corrected CNAME to `smplxnf → smplxnf-live.onrender.com`; observed through resolver `1.1.1.1` at 22:07 UTC, TTL 3600 |
| Browser fix / CI | [PR #21](https://github.com/dbccpage/simplex-normal-forms/pull/21) merged at `f9c289c`; all five [CI jobs](https://github.com/dbccpage/simplex-normal-forms/actions/runs/41537312875) passed at `d2e331a`, with the same merge tree |
| Render service | `smplxnf-live`, `srv-dbkh1v3ncjis73bbg3ug`, Oregon, Free compute; deployed `f9c289cc33f91c2b653f65e6267fde0073c3cd6f` |
| Assigned origin | `https://smplxnf-live.onrender.com`: 15/15 HTTPS/API checks passed at 22:39 UTC |
| Custom domain | `https://smplxnf.anomalon.com`: 15/15 HTTPS/API checks passed at 22:54 UTC; Render showed domain verified and certificate issued |
| Live browser | Default relational result inspected; full workbench/browser checklist interrupted at the user's request |

The original Gemini/Teamwork notes' 136 pytest items / 89 unittest methods and
instructions to merge PR #17 are historical. A Render blueprint is configuration,
not proof that a service was provisioned. The service and custom-domain assignment
were separately inspected in Render; both origins then passed the HTTP script.

The 22:25 UTC response identifying SmplCache was a historical routing mismatch,
subsequently corrected by moving the Simplex domain to the separate service.
SmplCache remains intact: its own hostname returned healthy service
`smplcache-live`, app/engine commit `810fc7cf0d99`, after the move. No Studio API
POSTs were sent to it during the failed identity check.

The user chose Free compute and approved Render's disclosed $0.25/month custom
domain charge; billing was not audited. These bounded smoke results do not
establish cold-start performance, sustained capacity or a latency SLA. The app's
health identifier remains `smplxnf-studio`, distinct from the Render resource name.
See the [dated deployment record and raw receipts](https://github.com/dbccpage/simplex-normal-forms/blob/codex/render-deployment-receipt/docs/verification/2026-11-02-deployment.md).

## Catalog evidence levels

All 112 contracts pass structural catalog checks. Per-contract `identity`
metadata reports 24 active, 87 draft and 1 deprecated; verification status is
35 executable, 75 absent and 2 missing; theory status is 48 established,
42 proposed, 11 experimental, 9 admitted and 2 missing.

These are declared statuses, not independent verification of every contract.
The catalog index separately lists 25 active and 87 draft entries, plus a
deprecated ACNF entry; ACNF appears in both draft and deprecated lists.

Generic diagram labels and “Certified Output” tables describe intended contract
behavior. They are not successful-run receipts. In particular, `verification_status:
absent` cannot establish an executable result. Proposed/admitted physics and
research-forum scenarios retain their stated assumptions. Claim-word scans do
not establish mathematical correctness or originality. No metadata status or
certification confers operational authority.

The streaming API supports the bounded model documented in
[Executable scope](https://github.com/dbccpage/simplex-normal-forms/blob/main/docs/CORRECTNESS_SCOPE.md).
The compiler workbench demonstrates FD lowering and a constructed subsumption
comparison, rather than arbitrary DAG execution or compilation of the entire
catalog. AI token counts use whitespace splitting, not a model tokenizer.

## Next work

1. Complete live browser acceptance when the user makes a browser available:
   inspect the lossy witness, streaming with cochain on/off, compiler and AI
   outputs, quickstart/developer links, console and responsive layout. The user
   stopped computer control; documentation work does not resume it.
2. Rerun HTTPS/API checks after future application deployments and record the
   deployed SHA independently of `/healthz`. Fetch complete request objects from
   `/api/presets`; the old handoff's `preset_id` examples do not match these APIs.
3. Audit contract evidence and replace generic wiki examples with executable
   witnesses. Catalog size does not establish implementation breadth.
