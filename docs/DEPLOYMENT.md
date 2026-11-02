# Render deployment and Phase 3 verification

The application and blueprint are implemented. Public deployment remains a
separate gate; see [the dated status](PROJECT_STATUS.md). PRs #17–19 are already
merged. Use the current reviewed `main`, not the old MVP feature branch.

## Render service

Inspect the existing [Render project](https://dashboard.render.com/project/prj-dbj5ei942hec73c30pu0)
before creating or syncing `smplxnf-studio` from [render.yaml](../render.yaml).

| Setting | Blueprint value |
| --- | --- |
| Repository / branch | `https://github.com/dbccpage/simplex-normal-forms` / `main` |
| Runtime / region / plan | Python / Oregon / Starter |
| Build | `pip install -e . && pip install -r web/requirements.txt` |
| Start | `uvicorn web.app:app --host 0.0.0.0 --port $PORT` |
| Health check | `/healthz` |
| Environment | `PYTHONUNBUFFERED=1`, `APP_ENVIRONMENT=production` |
| Custom domain | `smplxnf.anomalon.com` |

Record the selected Python version and successful deploy's Git SHA. The blueprint
does not pin a Python version; Render's default depends on service creation date
([Render Python version documentation](https://render.com/docs/python-version)).
Record the actual instance plan and associated account commitment before provisioning.

Run the check below against the **assigned** `https://…onrender.com` origin
first. A service name alone does not establish its assigned hostname.

## DNS handoff

The supplied handoff assigns the GoDaddy update to the user. Report the verified
Render hostname, then wait for their confirmation that the record is updated:

**2026-11-02 update:** The user has already created the canonical CNAME pointing
`smplxnf` to `smplxnf-live.onrender.com`; resolver `1.1.1.1` returned it with TTL
3600. This target returned HTTP 404 on `/healthz`. Confirm the new service's
assigned hostname before requesting another DNS change. The service still needs
`smplxnf.anomalon.com` added in **Settings → Custom Domains**.

**Latest check, 22:25 UTC:** The certificate is valid, but the custom domain
serves **SmplCache Live** (`service: smplcache-live`, commit `810fc7cf0d99`).
The user's Render screenshot lists `smplcache-live.onrender.com` as the target.
Create/verify the separate Simplex service first, then move this custom-domain
association to it and align DNS with that service's actual hostname. Do not
replace or rename the existing SmplCache application to perform this migration.
See the [application-identity receipt](verification/2026-11-02-domain-service-mismatch.json).

| GoDaddy field | Value |
| --- | --- |
| Type | `CNAME` |
| Name / Host | `smplxnf` (within the `anomalon.com` zone) |
| Value / Target | Actual assigned Render hostname, without `https://` or a path |
| TTL | 600 seconds if available, otherwise provider default |

Inspect any existing record for this name before replacing it. Leave unrelated
zone records unchanged. Verify the custom domain in Render and wait for its
certificate to become valid. Do not bypass certificate errors.
Provider references: [Render custom domains](https://render.com/docs/custom-domains),
[Render DNS configuration](https://render.com/docs/configure-other-dns),
[GoDaddy CNAME fields](https://www.godaddy.com/help/add-a-cname-record-19236).

## Repeatable HTTP smoke

Requires only Python 3.10+ standard library; no application imports or credentials.

```sh
python scripts/http_smoke.py https://ACTUAL-HOST.onrender.com --output render-http.json
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

Localhost results establish local behavior only. The deployment gate remains
open until these checks pass on the public custom domain.
