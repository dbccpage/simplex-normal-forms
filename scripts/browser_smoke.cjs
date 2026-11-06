// Live UI acceptance in an isolated headless Chromium process.
// Install Playwright separately; PLAYWRIGHT_MODULE may point to an existing install.
// Usage: node scripts/browser_smoke.cjs https://smplxnf.anomalon.com OUTPUT_DIRECTORY
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { execFileSync } = require('node:child_process');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.argv[2];
const out = path.resolve(process.argv[3] || 'browser-smoke-results');
const origin = new URL(base);
assert(origin.protocol === 'https:' || (origin.protocol === 'http:' && ['127.0.0.1', 'localhost', '[::1]'].includes(origin.hostname)), 'Use HTTPS or HTTP loopback only');
assert.equal(origin.origin, base);
assert(!origin.username && !origin.password);
fs.mkdirSync(out, { recursive: true });
const report = { started_at_utc: new Date().toISOString(), origin: base,
  checkout_commit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: path.join(__dirname, '..'), encoding: 'utf8' }).trim(),
  identity_scope: 'Rendered HTML/JS/CSS comparison only; backend deployment SHA is not exposed by health.',
  mode: 'isolated headless Chromium; no existing browser/profile/CDP connection',
  clipboard_scope: 'Copy handlers use an in-page clipboard sink; OS clipboard is untouched and not tested.',
  checks: [], screenshots: [], console: [], page_errors: [], failed_requests: [], http_errors: [], assets: [] };
const responses = {};
let browser, page;
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
async function step(name, action) {
  try { const details = await action(); report.checks.push({ name, passed: true, details }); }
  catch (error) { report.checks.push({ name, passed: false, error: String(error.message) }); }
  console.log(`${report.checks.at(-1).passed ? 'PASS' : 'FAIL'} ${name}`);
}
async function text(id) { return (await page.locator(`#${id}`).innerText()).trim(); }
async function rendered(id, expected) {
  try {
    await page.waitForFunction(({ id, expected }) => {
      const el = document.getElementById(id);
      // innerText preserves <br> inserted by the application's innerText setter;
      // textContent avoids CSS text-transform for single-line status badges.
      return el && (el.innerText.trim() === expected || el.textContent.trim() === expected);
    },
      { id, expected: String(expected).trim() });
  } catch (error) {
    throw new Error(`${id}: expected ${JSON.stringify(expected)}, actual ${JSON.stringify(await page.locator(`#${id}`).textContent())}; ${error.message}`);
  }
}
async function shot(name) {
  await page.evaluate(() => scrollTo(0, 0));
  await page.waitForFunction(() => !document.querySelector('body > .fixed'));
  await page.screenshot({ path: path.join(out, `${name}.png`), fullPage: true });
  report.screenshots.push(`${name}.png`);
}
async function post(name, endpoint, action) {
  const [response] = await Promise.all([
    page.waitForResponse(r => r.request().method() === 'POST' && r.url() === base + endpoint), action(),
  ]);
  assert.equal(response.status(), 200);
  const data = await response.json();
  responses[name] = { request: response.request().postDataJSON(), response: data };
  return data;
}
async function tab(name) {
  await page.evaluate(() => scrollTo(0, 0));
  await page.locator(`#tab-btn-${name}`).click();
  assert(await page.locator(`#view-${name}`).isVisible());
}
async function layout(name) {
  await page.evaluate(() => scrollTo(0, 0));
  const geometry = await page.evaluate(() => ({
    viewport: innerWidth, width: document.documentElement.scrollWidth,
    results: [...document.querySelectorAll('header a, #ai-merkle-digest, #compiler-fuzzers-container > div')].filter(e => e.getBoundingClientRect().height > 0).map(e => {
      const r = e.getBoundingClientRect();
      return {id: e.id || e.tagName, width: e.clientWidth, content_width: e.scrollWidth, left: r.left, right: r.right};
    }),
    overflow: [...document.querySelectorAll('body *')].filter(e => {
      const r = e.getBoundingClientRect();
      if (!r.width || !r.height || getComputedStyle(e).position === 'fixed') return false;
      let parent = e.parentElement;
      while (parent && parent !== document.body) {
        if (['auto','scroll','hidden','clip'].includes(getComputedStyle(parent).overflowX)) return false;
        parent = parent.parentElement;
      }
      return r.right > innerWidth + 1 || r.left < -1;
    }).slice(0, 12).map(e => ({tag: e.tagName, id: e.id, text: e.innerText?.slice(0, 90)})),
  }));
  report.layout ||= {};
  report.layout[name] = geometry;
  await shot(name);
  assert(geometry.width <= geometry.viewport + 1, `Page width ${geometry.width}px exceeds ${geometry.viewport}px viewport: ${JSON.stringify(geometry.overflow)}`);
  for (const result of geometry.results) {
    assert(result.left >= -1 && result.right <= geometry.viewport + 1, `${result.id} extends outside viewport`);
    assert(result.content_width <= result.width + 1, `${result.id} clips ${result.content_width}px content inside ${result.width}px`);
  }
  return geometry;
}
async function copy(id) {
  const expected = await page.locator(`#${id}`).innerText();
  assert(expected.length > 0);
  await page.locator(`button[onclick="copyToClipboard('${id}')"]`).click();
  assert.equal(await page.evaluate(() => window.__smokeClipboard), expected);
}
(async () => {
  try {
    browser = await chromium.launch({ headless: true });
    report.browser_version = browser.version();
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, ignoreHTTPSErrors: false });
    await context.addInitScript(() => {
      Object.defineProperty(navigator, 'clipboard', { configurable: true, value: {
        writeText: async value => { window.__smokeClipboard = value; },
      } });
    });
    page = await context.newPage();
    page.setDefaultTimeout(20000);
    page.on('console', m => report.console.push({ type: m.type(), text: m.text() }));
    page.on('pageerror', e => report.page_errors.push(e.message));
    page.on('requestfailed', r => report.failed_requests.push({ url: r.url(), error: r.failure()?.errorText }));
    page.on('response', r => { if (r.status() >= 400) report.http_errors.push({ url: r.url(), status: r.status() }); });
    page.on('dialog', async dialog => { report.page_errors.push(`Dialog: ${dialog.message()}`); await dialog.dismiss(); });
    await step('Application identity, assets and initial rendering', async () => {
      const front = await page.goto(base + '/', { waitUntil: 'networkidle', timeout: 120000 });
      assert.equal(front.status(), 200);
      assert.match(await page.title(), /Simplex Normal Forms Studio/);
      await page.waitForFunction(() => document.querySelector('#relational-chase-status').innerText.includes('Lossless'));
      const r = await page.goto(base + '/studio/', { waitUntil: 'networkidle', timeout: 120000 });
      assert.equal(r.status(), 200);
      assert.match(await page.title(), /Simplex Normal Forms Studio/);
      await rendered('ai-source-tokens', '62');
      await rendered('bqnf-events-count', '3');
      await page.waitForFunction(() => document.querySelector('#relational-chase-status').innerText.includes('Lossless'));
      const health = await context.request.get(base + '/healthz');
      assert.equal(health.status(), 200);
      report.health = await health.json();
      assert.equal(report.health.service, 'smplxnf-studio');
      for (const [urlPath, local] of [['/', 'web/templates/front.html'], ['/', 'web/templates/overview.html'], ['/studio/', 'web/templates/index.html'], ['/static/app.js', 'web/static/app.js'], ['/static/style.css', 'web/static/style.css']]) {
        const response = await context.request.get(base + urlPath);
        assert.equal(response.status(), 200);
        const bytes = await response.body();
        const normalized = bytes.toString().replace(/\r\n/g, '\n');
        report.assets.push({ path: urlPath, sha256: hash(bytes), normalized_matches_checkout: normalized.trimEnd() === fs.readFileSync(path.join(__dirname, '..', local), 'utf8').replace(/\r\n/g, '\n').trimEnd() });
      }
      assert(report.assets.every(a => a.normalized_matches_checkout), 'Served frontend assets differ from the checkout');
      return { title: await page.title(), tls_validation: origin.protocol === 'https:' ? 'enabled' : 'loopback HTTP', assets_match: true };
    });
    if (!report.checks.at(-1).passed) throw new Error('Initial application check failed; dependent UI checks skipped');
    await step('Relational lossless keys, decomposition, chase and SQL', async () => {
      const data = await post('relational_lossless', '/api/relational/normalize', () => page.locator('#btn-run-relational').click());
      assert.equal(data.chase.is_implied, true);
      assert.equal(data.chase.steps_count, 7);
      await rendered('relational-cand-keys', data.candidate_keys.map(k => `{${k.join(', ')}}`).join('  '));
      await rendered('relational-sql-ddl', data.sql_ddl.trim());
      assert.equal(await page.locator('#relational-3nf-tables > div').count(), data.synthesized_3nf.length);
      assert.equal(await page.locator('#chase-steps-tbody > tr').count(), data.chase.steps.length);
      await page.locator('details').filter({ has: page.locator('#chase-tableau-matrix') }).locator('summary').click();
      assert(await page.locator('#chase-tableau-matrix').isVisible());
      assert.equal(await page.locator('#chase-tableau-matrix tbody > tr').count(), data.chase.final_tableau.length);
      await copy('relational-sql-ddl');
      await shot('desktop-relational-lossless');
      return { keys: data.candidate_keys, chase_steps: data.chase.steps_count, tables: data.synthesized_3nf.length };
    });
    await step('Relational lossy preset and spurious witness', async () => {
      const data = await post('relational_lossy', '/api/relational/normalize', () => page.locator('#relational-preset-select').selectOption('lossy_decomposition'));
      assert.deepEqual(responses.relational_lossy.request.custom_components, [['A','B'],['B','C']]);
      assert.equal(data.chase.is_implied, false);
      await rendered('chase-result-pill', 'Non-Lossless Decomposition');
      assert(await page.locator('#chase-witness-box').isVisible());
      assert((await text('chase-witness-box')).includes(JSON.stringify(data.chase.spurious_tuple_witness)));
      assert.match(await text('chase-steps-tbody'), /no distinguished row/);
      await shot('desktop-relational-lossy');
      return { witness: data.chase.spurious_tuple_witness };
    });
    for (const enabled of [true, false]) await step(`Streaming cochain ${enabled ? 'on' : 'off'}`, async () => {
      await tab('bqnf');
      await page.locator('#bqnf-use-cochain-toggle').setChecked(enabled);
      const name = `bqnf_${enabled}`;
      const data = await post(name, '/api/bqnf/simulate', () => page.locator('button[onclick="executeBqnfSimulation()"]' ).click());
      assert.equal(responses[name].request.use_cochain, enabled);
      assert.equal(data.final_cache.North.total_sales, 280);
      assert.equal(data.final_cache.North.sale_count, 4);
      await rendered('bqnf-cochain-hits', data.repair_tally.extrema_repairs);
      await rendered('bqnf-fallback-count', data.repair_tally.fallback_recomputations);
      await rendered('bqnf-speedup-badge', data.cochain_speedup);
      assert.equal(await page.locator('#bqnf-repair-log-tbody > tr').count(), data.extrema_repair_log.length);
      const logs = await page.locator('#bqnf-repair-log-tbody > tr').allInnerTexts();
      for (const [i, event] of data.extrema_repair_log.entries()) {
        assert(logs[i].includes(event.op_type) && logs[i].includes(event.terminal_route));
        assert(logs[i].includes(`$${event.affected_amount.toFixed(2)}`));
        assert(logs[i].includes(event.recomputation_fallback_executed === 1 ? 'Full Scan' : 'Bypassed'));
      }
      const rows = await page.locator('#bqnf-buckets-visual > div').allInnerTexts();
      assert.equal(rows.length, data.quantile_buckets.length);
      for (const [i, b] of data.quantile_buckets.entries()) {
        assert(rows[i].includes(b.region) && rows[i].includes(`Count: ${b.count}`));
        assert(rows[i].includes(`[${b.lower_bound.toFixed(1)}, ${b.upper_bound.toFixed(1)})`));
      }
      const mass = data.quantile_buckets.reduce((sum, b) => sum + b.count, 0);
      assert.equal(mass, Object.values(data.final_cache).reduce((sum, g) => sum + g.sale_count, 0));
      if (!enabled) assert.deepEqual(data.final_cache, responses.bqnf_true.response.final_cache);
      await shot(`desktop-streaming-${enabled ? 'on' : 'off'}`);
      return { final_cache: data.final_cache, tally: data.repair_tally, mass };
    });
    await step('Compiler SQLite, Python and fuzzing output tabs', async () => {
      await tab('compiler');
      const data = await post('compiler', '/api/compiler/lower', () => page.locator('button[onclick="executeCompilerLowering()"]' ).click());
      assert.equal(data.sqlite_verification.verified, true);
      await rendered('compiler-sqlite-code', `${data.sqlite_ddl.create_table_sql}\n\n${data.sqlite_ddl.before_insert_trigger_sql}\n\n${data.sqlite_ddl.before_update_trigger_sql}`.trim());
      await copy('compiler-sqlite-code');
      await shot('desktop-compiler-sqlite');
      await page.locator('#subtab-btn-python').click();
      assert(await page.locator('#compiler-subpanel-python').isVisible());
      await rendered('compiler-python-code', data.python_guard_code.trim());
      await copy('compiler-python-code');
      await shot('desktop-compiler-python');
      await page.locator('#subtab-btn-fuzzers').click();
      assert(await page.locator('#compiler-subpanel-fuzzers').isVisible());
      assert.equal(await page.locator('#compiler-fuzzers-container > div').count(), data.synthesized_counterexamples.length);
      assert(data.synthesized_counterexamples.length > 0);
      const fixtures = await page.locator('.compiler-fixture-json').allTextContents();
      assert.deepEqual(fixtures.map(value => JSON.parse(value)), data.synthesized_counterexamples.map(f => f.carrier_rows));
      await shot('desktop-compiler-fuzzers');
      return { subsumption: data.subsumption_analysis, counterexamples: data.synthesized_counterexamples.length };
    });
    await step('AI conservation and loss-ledger rendering', async () => {
      await tab('ai');
      const data = await post('ai', '/api/ai/lossledger', () => page.locator('button[onclick="executeAiLossLedger()"]' ).click());
      const t = data.token_accounting;
      assert.equal(t.source_token_count, t.retained_token_count + t.truncated_token_count);
      assert.equal(t.token_conservation_commutes, true);
      assert.equal(data.loss_ledger_integrity_verified, true);
      for (const [id, value] of [['source', t.source_token_count], ['retained', t.retained_token_count], ['truncated', t.truncated_token_count]]) await rendered(`ai-${id}-tokens`, value);
      await rendered('ai-merkle-digest', data.merkle_digest);
      await rendered('ai-conservation-equation', t.conservation_equation);
      await rendered('ai-merkle-verified-badge', 'SHA-256 Merkle Seal Verified');
      await shot('desktop-ai');
      return t;
    });
    await step('Quickstart navigation, developer targets and copy handlers', async () => {
      await page.locator('a[href="#quickstart"]').click();
      assert(await page.locator('#view-quickstart').isVisible());
      for (const id of ['install-bash','snippet-relational','snippet-compiler','snippet-ai']) await copy(id);
      const links = await page.locator('a[href]').evaluateAll(elements => elements.map(e => ({ text: e.innerText, href: e.getAttribute('href') })));
      // The current page has only an internal quickstart anchor; developer URLs are text in snippets.
      assert((await text('install-bash')).includes('https://github.com/dbccpage/simplex-normal-forms.git'));
      const developer = await context.request.get('https://github.com/dbccpage/simplex-normal-forms');
      assert.equal(developer.status(), 200);
      await shot('desktop-quickstart');
      return { links, developer_repository_status: developer.status(), copy_handlers: '7 checked with isolated sink; native clipboard not accessed' };
    });
    for (const width of [1280, 768, 390, 320]) {
      await page.setViewportSize({ width, height: width < 768 ? 844 : 900 });
      for (const view of ['relational','bqnf','compiler','ai','quickstart']) await step(`${width}px layout: ${view}`, async () => {
        await tab(view);
        return layout(`${width}px-${view}-layout`);
      });
    }
    await page.goto(base + '/', { waitUntil: 'networkidle', timeout: 120000 });
    await page.waitForFunction(() => document.querySelector('#relational-chase-status').innerText.includes('Lossless'));
    for (const width of [1280, 768, 390, 320]) {
      await step(`${width}px layout: front`, async () => {
        await page.setViewportSize({ width, height: width < 768 ? 844 : 900 });
        return layout(`${width}px-front-layout`);
      });
    }
    await step('Browser console, runtime and network errors', async () => {
      assert.deepEqual(report.page_errors, []);
      assert.deepEqual(report.failed_requests, []);
      assert.deepEqual(report.console.filter(m => m.type === 'error'), []);
      assert.deepEqual(report.http_errors, []);
      return { warnings: report.console.filter(m => m.type === 'warning') };
    });
  } catch (error) { report.fatal_error = String(error.stack); }
  finally {
    if (browser) await browser.close();
    report.completed_at_utc = new Date().toISOString();
    report.passed = !report.fatal_error && report.checks.length > 0 && report.checks.every(c => c.passed);
    fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
    fs.writeFileSync(path.join(out, 'api-results.json'), JSON.stringify(responses, null, 2) + '\n');
    console.log(JSON.stringify({ passed: report.passed, checks: report.checks.length, failed: report.checks.filter(c => !c.passed), fatal: report.fatal_error, output: out }));
    process.exitCode = report.passed ? 0 : 1;
  }
})();
