# Project status and evidence — 2026-11-02

The web MVP, correctness fixes and packaging work are merged. Public Render
deployment is a separate, unfinished gate.

| Area | Verified state |
| --- | --- |
| MVP | [PR #17](https://github.com/dbccpage/simplex-normal-forms/pull/17) merged at `489f3e1` |
| Correctness | [PR #18](https://github.com/dbccpage/simplex-normal-forms/pull/18) merged at `d59f890`; tracked-field matching, exact quantile membership and per-region repair receipts corrected |
| Packaging / CI | [PR #19](https://github.com/dbccpage/simplex-normal-forms/pull/19) merged at `da498e5`; source and installed-distribution verification |
| Tests | 232 tests passed in premerge Python 3.12/3.14 runs; [merged-main hosted CI](https://github.com/dbccpage/simplex-normal-forms/actions/runs/41529136846) passed |
| Local HTTP | 15 smoke checks passed on 2026-11-02, including two repetitions of five API cases with two clients |
| DNS | User corrected CNAME to `smplxnf → smplxnf-live.onrender.com`; observed through resolver `1.1.1.1` at 22:07 UTC, TTL 3600 |
| Render / HTTPS | At 22:25 UTC HTTPS succeeded and returned HTTP 200, but `/healthz` identified `smplcache-live` and the page title identified SmplCache Live. Certificate issuance is complete; the domain is attached to the wrong application |

The original Gemini/Teamwork notes' 136 pytest items / 89 unittest methods and
instructions to merge PR #17 are historical. A Render blueprint is configuration,
not proof that a service was provisioned. The new service must have the custom
domain registered in Render; the CNAME alone does not establish routing or TLS.

The latest user screenshot lists `smplcache-live.onrender.com` as Render's
target, while public DNS still points to `smplxnf-live.onrender.com`. The custom
domain currently serves the existing SmplCache application, commit `810fc7cf0d99`.
Create/verify the separate service from `dbccpage/simplex-normal-forms`, then
move this custom-domain association to it and align the CNAME with its assigned
hostname. Preserve the existing SmplCache service. No Studio API POSTs were
attempted against that application; HTTP 200 alone does not pass acceptance.

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

1. Create/inspect the Simplex service in the supplied Render project, deploy the
   reviewed `main`, and record the deployed Git SHA and assigned hostname.
2. Confirm that hostname matches `smplxnf-live.onrender.com`; ask the user to
   adjust their CNAME only if needed. Register `smplxnf.anomalon.com` as the
   service's custom domain and verify its certificate.
3. Execute live HTTP and browser checks on the assigned Render origin and then
   the custom domain. Fetch full request bodies from `/api/presets`; the old
   handoff's `preset_id` examples do not match these API request models.
4. Review the follow-up browser fix for the lossy decomposition preset. Its
   parenthesized components were being flattened into one component in the UI,
   unlike the correct direct API call. Local verification now displays the
   lossy witness; this follow-up is not included in baseline `da498e5`.
5. Audit contract evidence and replace generic wiki examples with executable
   witnesses. Catalog size does not establish implementation breadth.
