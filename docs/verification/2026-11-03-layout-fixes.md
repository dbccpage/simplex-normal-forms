# Responsive layout fixes and local verification — 2026-11-03

This is the predeployment regression record for the fixes to the
[live headless findings](2026-11-03-live-browser.md). It does not replace those
historical failures with a production success claim.

## Changes

- Stack header branding and actions below the desktop breakpoint; let the
  header grow vertically instead of overflowing the viewport.
- Wrap AI ledger values, including the 64-character digest, inside shrinkable
  fields and stack their labels on narrow screens.
- Render compiler counterexample JSON as formatted text with wrapping inside
  each card. Assign it through `textContent` so values remain literal text.
- Allow the relational preset selector to shrink. The expanded 320px check
  exposed this additional overflow after the original three fixes passed at
  390px.
- Add the isolated [headless runner](../../scripts/browser_smoke.cjs) and a CI
  `browser` job. The runner never attaches to Chrome and uses an in-page sink
  for copy handlers, leaving the user's clipboard untouched.

## Verification before merge

The [final local receipt](2026-11-03-layout-local-final/report.json) records
**29/29 checks passed** against `http://127.0.0.1:8765` on Python 3.14 with
Playwright 1.58.0 / headless Chromium 145.0.7632.6. This run completed at
00:59:44 UTC. Its `checkout_commit` identifies the base commit; the edited
working-tree frontend was also checked against served asset hashes.

The checks exercise relational lossless/lossy results, streaming with cochain
on/off, all compiler output tabs, AI conservation, Quickstart and seven copy
handlers. All five views fit 1280, 768, 390 and 320px viewport widths, and the
targeted header, digest and fixture contents remain inside their containers.
Fixture JSON is parsed back and compared with the API response. There were no
JavaScript errors, failed requests or HTTP errors. The existing Tailwind CDN
production-use warning remains a separate deployment improvement.

Six web API tests passed, and the existing Node frontend regression passed.
Hosted CI and live verification must run on the final reviewed head before this
change is considered deployed; their results belong to the PR/deployment record.

Representative screenshots:

- [390px AI ledger](2026-11-03-layout-local-final/390px-ai-layout.png)
- [390px compiler fixtures](2026-11-03-layout-local-final/390px-compiler-layout.png)
- [320px relational view](2026-11-03-layout-local-final/320px-relational-layout.png)
- [Desktop compiler fixtures](2026-11-03-layout-local-final/desktop-compiler-fuzzers.png)

The [first local layout receipt](2026-11-03-layout-local/report.json) is retained:
28/29 checks passed, with only the 320px relational selector still overflowing.
An earlier sandboxed server startup stalled before binding its port; the
dependent attempt was stopped and only this task's processes were terminated.
The successful reruns used a normally launched loopback server and isolated
headless browsers. No desktop browser was controlled.
