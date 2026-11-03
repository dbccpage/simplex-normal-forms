# Render deployment and Phase 3 verification

The separate `smplxnf-live` service is deployed. On 2026-11-02, HTTPS and all 15
API smoke checks passed on its Render origin and `smplxnf.anomalon.com`.
Full live browser acceptance remains incomplete. See [the dated status](PROJECT_STATUS.md)
and [deployment record](verification/2026-11-02-deployment.md).

## Render service

The [existing service](https://dashboard.render.com/web/srv-dbkh1v3ncjis73bbg3ug/settings)
is in the Production environment of the
[Render project](https://dashboard.render.com/project/prj-dbj5ei942hec73c30pu0).
[render.yaml](../render.yaml) now matches its name and compute plan. Inspect this
service before creating or syncing another resource.

| Setting | Recorded deployment / blueprint value |
| --- | --- |
| Repository / branch | `https://github.com/dbccpage/simplex-normal-forms` / `main` |
| Service name | `smplxnf-live` |
| Runtime / region / plan | Python / Oregon / Free |
| Build | `pip install -e . && pip install -r web/requirements.txt` |
| Start | `uvicorn web.app:app --host 0.0.0.0 --port $PORT` |
| Health check | `/healthz` |
| Environment | `PYTHONUNBUFFERED=1`, `APP_ENVIRONMENT=production` |
| Custom domain | `smplxnf.anomalon.com` |

The initial successful deploy used Python 3.14 and commit
`f9c289cc33f91c2b653f65e6267fde0073c3cd6f` (PR #21). The blueprint does not pin a
Python version. Capture the actual runtime and SHA again for future deployments.
The health response's application identifier remains `smplxnf-studio`; that
identifier is distinct from the Render resource name and does not identify a SHA.

Compute is Free ($0/month). Render disclosed a separate $0.25/month custom-domain
charge and the user approved it; no billing invoice was audited. This deployment
does not establish cold-start performance or an always-on availability commitment.

Run the check below against the **assigned** `https://…onrender.com` origin
first. A service name alone does not establish its assigned hostname.

## DNS handoff

The user configured the GoDaddy CNAME; resolver `1.1.1.1` returned it with TTL
3600. Render now associates `smplxnf.anomalon.com` with `smplxnf-live` and showed
both domain verification and certificate issuance complete. The 22:54 UTC
[canonical-domain receipt](verification/2026-11-02-public-live-http.json) verifies
HTTPS and Studio API behavior.

Earlier checks encountered DNS propagation, an unprovisioned target and then an
association with the existing SmplCache service. The
[22:25 UTC mismatch receipt](verification/2026-11-02-domain-service-mismatch.json)
is historical. The user authorized moving only the Simplex domain; the separate
SmplCache service and `smplcache.anomalon.com` remained intact and healthy afterward.

| GoDaddy field | Value |
| --- | --- |
| Type | `CNAME` |
| Name / Host | `smplxnf` (within the `anomalon.com` zone) |
| Value / Target | `smplxnf-live.onrender.com` |
| TTL | 3600 seconds observed |

Inspect any existing record for this name before replacing it. Leave unrelated
zone records unchanged. Verify the custom domain in Render and wait for its
certificate to become valid. Do not bypass certificate errors.
Provider references: [Render custom domains](https://render.com/docs/custom-domains),
[Render DNS configuration](https://render.com/docs/configure-other-dns),
[GoDaddy CNAME fields](https://www.godaddy.com/help/add-a-cname-record-19236).

## Repeatable HTTP smoke

Requires only Python 3.10+ standard library; no application imports or credentials.

```sh
python scripts/http_smoke.py https://smplxnf-live.onrender.com --output render-http.json
python scripts/http_smoke.py https://smplxnf.anomalon.com --output public-http.json
# Small, bounded concurrency probe: 5 GETs then 10 POSTs across two clients.
python scripts/http_smoke.py https://smplxnf.anomalon.com --workers 2 --repeats 2 --output public-concurrent.json
```

The script verifies `/healthz`, the HTML workbench, JavaScript and CSS assets,
and `/api/presets`. It submits full preset objects to:

| Endpoint | Preset and semantic check |
| --- | --- |
| `/api/relational/normalize` | `ecommerce`: lossless chase; `lossy_decomposition`: spurious tuple witness |
| `/api/bqnf/simulate` | `financial_ledger`: North total 280 and count 4 |
| `/api/compiler/lower` | `employee_bcnf`: verified SQLite, trigger SQL and counterexamples |
| `/api/ai/lossledger` | `rag_research_context`: admission, token conservation and ledger integrity |

It records HTTP status, elapsed time and response hashes, validates HTTPS
certificates normally, rejects redirects as passing results, and exits nonzero
on failure. If health fails, later checks are explicitly skipped. A DNS failure
provides no TLS verdict. The elapsed times include client/network costs; record
them without claiming an SLA. Source identity must be checked separately in Render.

## Browser acceptance

On the public HTTPS origin, execute the default relational preset and the lossy
counterexample preset; inspect the resulting keys, decomposition and chase.
Run streaming with cochain lookup on and off; check logs, region-labelled
buckets and totals against API results. Run compiler lowering and inspect all
three output tabs. Run AI projection and check conservation and ledger output.
Open the quickstart tab, check developer links, inspect browser errors, and
inspect layout at desktop and narrow viewport sizes. Record the URL, deployed
SHA, time, screenshots, observed results and any remaining failures.

Localhost results establish local behavior only. The live default relational
display was inspected; the remaining browser checklist was interrupted at the
user's request. HTTPS/API verification is complete for the recorded deploy, but
full browser acceptance remains open. Do not resume desktop automation without
the user making it available again.
