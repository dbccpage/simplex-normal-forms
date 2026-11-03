# Deployment record — 2026-11-02

This records the observed deployment and saved HTTP results from this session.
It is not a new browser check, a billing audit or a sustained-load benchmark.

## Source and service

| Field | Observed value |
| --- | --- |
| Repository / branch | `dbccpage/simplex-normal-forms` / `main` |
| Deployed commit | `f9c289cc33f91c2b653f65e6267fde0073c3cd6f` |
| Source review | [PR #21](https://github.com/dbccpage/simplex-normal-forms/pull/21) |
| Tested PR head | `d2e331aea62c1c2eff3686ab03681c49e8107515`; merge tree matched this head |
| Hosted CI | All five jobs passed in [run 41537312875](https://github.com/dbccpage/simplex-normal-forms/actions/runs/41537312875) |
| Render project | `prj-dbj5ei942hec73c30pu0` |
| Production environment | `evm-dbj5ei942hec73c30pug` |
| Service | [`smplxnf-live`](https://dashboard.render.com/web/srv-dbkh1v3ncjis73bbg3ug/settings), `srv-dbkh1v3ncjis73bbg3ug` |
| Initial deploy | [`dep-dbkh1vbncjis73bbg4e0`](https://dashboard.render.com/web/srv-dbkh1v3ncjis73bbg3ug/deploys/dep-dbkh1vbncjis73bbg4e0) |
| Runtime / region | Python 3.14 observed in build logs / Oregon |
| Compute | Free, $0/month, 0.1 CPU / 512 MB |
| Build | `pip install -e . && pip install -r web/requirements.txt` |
| Start | `uvicorn web.app:app --host 0.0.0.0 --port $PORT` |
| Environment | `PYTHONUNBUFFERED=1`, `APP_ENVIRONMENT=production` |
| Health / auto-deploy | `/healthz` / On Commit |
| Assigned origin | <https://smplxnf-live.onrender.com> |
| Canonical origin | <https://smplxnf.anomalon.com> |

Render showed the deploy Live, with successful startup at 17:39:52 EST
(22:39:52 UTC). Source checkout in its logs identified the deployed commit above.
The fixed health identifier `smplxnf-studio` and version `0.1.0` alone do not
identify a deployed Git commit. The subsequent blueprint name/plan reconciliation
is documentation of the manually selected configuration, not part of that commit.

## DNS, certificate and application identity

The user configured `smplxnf.anomalon.com CNAME smplxnf-live.onrender.com`;
resolver `1.1.1.1` returned TTL 3600. The earlier domain binding to SmplCache was
removed and the domain appeared on the new Simplex service after the user
authorized the move. Render showed Domain Verified and Certificate Issued.
The final UI state was observed; this record does not attribute the final form
submission to the assistant.

The user chose Free compute and separately approved the $0.25/month custom-domain
charge disclosed by Render after the two included domain slots were reported in
use. No invoice or subsequent billing state was audited.

The existing SmplCache resource `srv-dbk076c9v7es73balvng` was preserved. After
the move, `https://smplcache.anomalon.com/healthz` returned `status: ok`, service
`smplcache-live`, API version `1.0.0`, and app/engine commit `810fc7cf0d99`.

## Saved HTTPS/API checks

| Origin | Receipt start (UTC) | Result |
| --- | --- | --- |
| Assigned Render origin | 2026-11-02T22:39:54.959208+00:00 | [15/15 passed](2026-11-02-render-live-http.json) |
| Canonical custom domain | 2026-11-02T22:54:43.678713+00:00 | [15/15 passed](2026-11-02-public-live-http.json) |

Both runs used `scripts/http_smoke.py` with `--workers 2 --repeats 2`, normal
certificate validation, and timeouts of 40 and 45 seconds respectively. Five
GETs checked health, HTML, JavaScript, CSS and presets. Ten POSTs repeated five
semantic cases: relational lossless/lossy, streaming ledger, compiler lowering
and AI loss ledger. All returned HTTP 200 and passed the script's semantic checks.

Canonical-domain request durations ranged from 113.68 to 452.34 ms. These are
client/network measurements from a bounded smoke probe; they do not establish
sustained capacity, cold-start behavior or a sub-200 ms SLA. Earlier failed
receipts are retained as history rather than replaced.

## Browser acceptance boundary

Local browser work exercised all four workbenches; PR #21 corrected lossy preset
component parsing and added a frontend regression check. On the live canonical
origin, the default relational display showed “Lossless Join Verified (7 steps).”
The lossy preset was selected, but its resulting witness was not inspected.
The user then stopped computer control. Full live browser acceptance, streaming
cochain on/off, compiler output tabs, AI output, quickstart/developer links,
console inspection and narrow viewport checks remain incomplete. No later
browser checks are claimed by this documentation update.
