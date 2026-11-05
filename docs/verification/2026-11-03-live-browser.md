# Live headless browser checks — 2026-11-03 UTC

The remaining live browser checks were executed against
<https://smplxnf.anomalon.com> at 00:50:31–00:50:39 UTC on November 3
(19:50 EST on November 2). Functional checks passed. Full UI acceptance remains
open because of the three layout findings below.

## Environment and evidence

- Playwright 1.58.0, headless Chromium 145.0.7632.6, Windows.
- New temporary browser context; no attachment to an existing browser, Chrome
  profile, CDP session, desktop window or user input device.
- HTTPS certificate validation enabled; desktop viewport 1280×900 and narrow
  viewport 390×844. This is Chromium coverage, not Safari/Firefox or physical
  mobile-device coverage.
- [Final machine-readable report](2026-11-03-headless-browser-final/report.json):
  14 of 19 checks passed; all five narrow-layout checks failed. The failures
  represent two shared layout defects rather than five independent bugs.
- [UI-submitted requests and API responses](2026-11-03-headless-browser-final/api-results.json).
- [Additional compiler clipping measurement](2026-11-03-headless-browser-final/layout-details.json)
  at 00:51:33 UTC: failed readability check for three counterexample cards.
- Nineteen screenshots are listed in the final report. Representative screenshots
  were visually inspected in addition to the DOM measurements.

The served HTML, JavaScript and CSS matched the checkout at
`300f6d03fba0dd08a5746186c2291066bbab025b` after normalizing CRLF and trailing
whitespace. Raw response hashes are retained in the report. This correspondence
does not identify the backend's exact deployed Git SHA; `/healthz` does not expose
one. The last dashboard-verified deployment identity remains in the
[November 2 deployment record](2026-11-02-deployment.md). No Render dashboard was
opened during this pass.

## Passed checks

| Workflow | Observed result |
| --- | --- |
| HTTPS and initialization | HTTP 200, Studio identity, presets and all four initial workbench results loaded |
| Relational default | Candidate key `{item_id, order_id}`, five synthesized relations, seven chase steps, expanded tableau and SQL matched the API |
| Relational lossy preset | Request retained `[["A","B"],["B","C"]]`; UI displayed the non-lossless result and witness `{"A":"a_A","B":"a_B","C":"a_C"}` |
| Streaming with cochain enabled | Four extrema operations, no fallback scan; North total 280/count 4, South total 80/count 1; displayed log, region labels, bucket counts and mass 5 matched the API |
| Streaming with cochain disabled | Three extrema repairs and one fallback scan; identical final grouped totals and bucket mass |
| Compiler functional output | SQLite verification succeeded; INSERT/UPDATE SQL and Python guard matched API output; all three counterexample cards and output tabs rendered; one pass executed and one elided |
| AI | 62 source tokens = 35 retained + 27 truncated; conservation equation, digest and verified seal matched the API |
| Quickstart and developer target | Header anchor opened Quickstart; all four snippets were present; the repository URL in the install snippet returned HTTP 200 |
| Copy handlers | Seven buttons copied their full displayed source text into an isolated in-page clipboard sink |
| Desktop page width | All five views fit the 1280px page width; this global check did not detect clipped nested compiler content, which was found during screenshot review |
| Console/runtime/network | No JavaScript errors, failed requests, HTTP errors or alert dialogs |

The page has one actual hyperlink, the internal Quickstart anchor. The developer
repository URL is text in the install snippet, not a separate clickable link.
Copy-handler checks substituted `navigator.clipboard.writeText` inside the test
context. They verify handler text and success behavior, not native OS clipboard
permissions or the fallback path. The user's clipboard was never accessed.

## Findings that keep UI acceptance open

1. **[P2] Header overflows every narrow view.** At a 390px viewport the page is
   446px wide. The fixed-height flex header cannot fit the brand, version,
   hostname and Clone & Import action. The action extends beyond the viewport.
   Source: `web/templates/index.html`, header layout. Allow wrapping or rearrange
   secondary header content at small widths, then verify all five views.
   [Screenshot](2026-11-03-headless-browser-final/mobile-relational-layout.png).
2. **[P2] AI digest increases narrow-page overflow.** The unbroken 64-character
   digest in `#ai-merkle-digest` extends outside its card and makes the AI page
   514px wide at the same 390px viewport. Give the digest a shrinkable container
   and a wrapping or accessible scrolling treatment.
   [Screenshot](2026-11-03-headless-browser-final/mobile-ai-layout.png).
3. **[P2] Compiler counterexample JSON is clipped on desktop.** The three fuzzing
   cards are 663px wide but their content measures 826–947px. A surrounding
   `overflow-x: hidden` container clips the JSON, with no scrollable area on the
   cards. The data exists in the DOM/API, but visitors cannot inspect all fields
   visually. Wrap or scroll each JSON block inside the card.
   [Screenshot](2026-11-03-headless-browser-final/desktop-compiler-fuzzers.png).

The only console warning was Tailwind's CDN production-use warning. It did not
prevent rendering; replacing runtime CDN styling with a built stylesheet remains
a separate deployment improvement.

## Attempt history and repeatability

The [first run](2026-11-03-headless-browser/report.json) and
[second run](2026-11-03-headless-browser-confirmed/report.json) are retained.
Their extra functional failures came from the harness: CSS text transformation,
trailing copied newlines, and `textContent` omitting `<br>` line breaks inserted
by the application's `innerText` setter. The corrected final run compares the
appropriate DOM representations while preserving exact clipboard-handler text.
Those earlier harness failures are not application defects. The mobile overflow
reproduced in all three runs.

Use the [headless runner](../../scripts/browser_smoke.cjs) with a separately
installed Playwright browser:

```sh
node scripts/browser_smoke.cjs https://smplxnf.anomalon.com OUTPUT_DIRECTORY
```

`PLAYWRIGHT_MODULE` can point to an existing Playwright module installation. The
runner always launches headless with a fresh context and closes its browser in
`finally`; it does not connect to Chrome. Its nonzero exit is intentional when
the layout checks fail. The additional compiler-clipping measurement was a
focused follow-up to screenshot review and is recorded separately above.

Next: repair the three layout defects, deploy the reviewed change, and repeat
the headless checks and screenshot inspection. No desktop takeover is needed.
