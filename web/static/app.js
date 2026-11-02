/**
 * Simplex Normal Forms Studio Frontend Application
 * smplxnf.anomalon.com
 */

let PRESETS = {};

// -----------------------------------------------------------------------------
// Navigation & Tab Switching
// -----------------------------------------------------------------------------

function switchTab(tabName) {
  const tabs = ['relational', 'bqnf', 'compiler', 'ai', 'quickstart'];
  tabs.forEach(t => {
    const view = document.getElementById(`view-${t}`);
    const btn = document.getElementById(`tab-btn-${t}`);
    if (t === tabName) {
      if (view) view.classList.remove('hidden');
      if (btn) {
        btn.classList.add('active-tab', 'text-cyan-400');
        btn.classList.remove('text-slate-400');
      }
    } else {
      if (view) view.classList.add('hidden');
      if (btn) {
        btn.classList.remove('active-tab', 'text-cyan-400');
        btn.classList.add('text-slate-400');
      }
    }
  });
}

function switchCompilerSubTab(subTab) {
  const subTabs = ['sqlite', 'python', 'fuzzers'];
  subTabs.forEach(s => {
    const panel = document.getElementById(`compiler-subpanel-${s}`);
    const btn = document.getElementById(`subtab-btn-${s}`);
    if (s === subTab) {
      if (panel) panel.classList.remove('hidden');
      if (btn) {
        btn.classList.add('bg-slate-800', 'text-purple-300', 'border', 'border-slate-700');
        btn.classList.remove('text-slate-400');
      }
    } else {
      if (panel) panel.classList.add('hidden');
      if (btn) {
        btn.classList.remove('bg-slate-800', 'text-purple-300', 'border', 'border-slate-700');
        btn.classList.add('text-slate-400');
      }
    }
  });
}

function copyToClipboard(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const text = el.innerText || el.textContent;
  navigator.clipboard.writeText(text).then(() => {
    showToast("Copied to clipboard!");
  }).catch(() => {
    // Fallback
    const ta = document.createElement("textarea");
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
    showToast("Copied to clipboard!");
  });
}

function showToast(msg) {
  const toast = document.createElement("div");
  toast.className = "fixed bottom-5 right-5 bg-cyan-500 text-black font-semibold text-xs px-4 py-2 rounded-lg shadow-lg shadow-cyan-500/20 z-50 transition transform duration-200";
  toast.innerText = msg;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 2000);
}


// -----------------------------------------------------------------------------
// Module 1: Relational Synthesis & Chase Tableau
// -----------------------------------------------------------------------------

function loadRelationalPreset(presetKey) {
  if (!PRESETS.relational || !PRESETS.relational[presetKey]) return;
  const p = PRESETS.relational[presetKey];
  document.getElementById('relational-attributes-input').value = p.attributes.join(', ');
  document.getElementById('relational-dependencies-input').value = p.dependencies.join('\n');
  const compInput = document.getElementById('relational-components-input');
  if (p.custom_components) {
    compInput.value = p.custom_components.map(c => `(${c.join(', ')})`).join(', ');
  } else {
    compInput.value = '';
  }
  executeRelationalNormalize();
}

async function executeRelationalNormalize() {
  const attrStr = document.getElementById('relational-attributes-input').value;
  const depStr = document.getElementById('relational-dependencies-input').value;
  const compStr = document.getElementById('relational-components-input').value;

  const attributes = attrStr.split(',').map(s => s.trim()).filter(Boolean);
  const dependencies = depStr.split('\n').map(s => s.trim()).filter(Boolean);

  let custom_components = null;
  if (compStr.trim()) {
    // Parse "(A, B), (B, C)" or "A, B; B, C"
    const parts = compStr.replace(/[()]/g, '').split(';').map(x => x.split(',').map(y => y.trim()).filter(Boolean));
    if (parts.length > 0 && parts[0].length > 0) {
      custom_components = parts;
    }
  }

  const btn = document.getElementById('btn-run-relational');
  if (btn) btn.disabled = true;

  try {
    const res = await fetch('/api/relational/normalize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ attributes, dependencies, custom_components })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Relational normalization failed');
    }
    const data = await res.json();
    renderRelationalResults(data);
  } catch (err) {
    alert(`Error: ${err.message}`);
  } finally {
    if (btn) btn.disabled = false;
  }
}

function renderRelationalResults(data) {
  // 1. Status Cards
  const candKeysEl = document.getElementById('relational-cand-keys');
  candKeysEl.innerText = data.candidate_keys.map(k => `{${k.join(', ')}}`).join('  ') || 'None';

  const primeEl = document.getElementById('relational-prime-attrs');
  primeEl.innerText = `{${data.prime_attributes.join(', ')}}`;

  const chaseStatusEl = document.getElementById('relational-chase-status');
  if (data.chase.is_implied) {
    chaseStatusEl.innerHTML = `<span class="text-emerald-400">Lossless Join Verified (${data.chase.steps_count} steps)</span>`;
  } else {
    chaseStatusEl.innerHTML = `<span class="text-rose-400">Lossy Join (Spurious Tuples)</span>`;
  }

  // 2. Normal Form Decision Scorecard
  const scorecard = document.getElementById('relational-nf-scorecard');
  scorecard.innerHTML = '';
  const nfs = ['1NF', '2NF', '3NF', 'EKNF', 'BCNF'];
  nfs.forEach(nf => {
    const info = data.normal_forms[nf] || { passed: false, reason: 'N/A' };
    const div = document.createElement('div');
    const badgeClass = info.passed ? 'badge-pass' : 'badge-fail';
    const statusText = info.passed ? 'PASSED' : 'VIOLATION';
    div.className = `p-2.5 rounded-lg border text-center ${badgeClass}`;
    div.innerHTML = `
      <div class="text-xs font-bold font-mono">${nf}</div>
      <div class="text-[10px] uppercase font-semibold mt-0.5">${statusText}</div>
    `;
    if (!info.passed && info.reason) {
      div.title = info.reason;
    }
    scorecard.appendChild(div);
  });

  // 3. Minimal Cover & 3NF Tables
  const minCoverBadge = document.getElementById('relational-mincover-badge');
  minCoverBadge.innerText = `Minimal Cover: ${data.minimal_cover.length} FDs`;

  const tablesContainer = document.getElementById('relational-3nf-tables');
  tablesContainer.innerHTML = '';
  data.synthesized_3nf.forEach(t => {
    const card = document.createElement('div');
    card.className = 'p-3 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between text-xs font-mono';
    const pk = t.candidate_keys[0] ? `{${t.candidate_keys[0].join(', ')}}` : 'None';
    card.innerHTML = `
      <div>
        <span class="text-cyan-400 font-bold">${t.table_name}</span>
        <span class="text-slate-400 ml-2">(${t.attributes.join(', ')})</span>
      </div>
      <div class="text-[11px] text-slate-500">
        Primary Key: <span class="text-emerald-400 font-semibold">${pk}</span>
      </div>
    `;
    tablesContainer.appendChild(card);
  });

  // 4. Chase Trace & Tableau
  const pill = document.getElementById('chase-result-pill');
  pill.classList.remove('hidden', 'bg-emerald-950', 'text-emerald-400', 'border-emerald-800', 'bg-rose-950', 'text-rose-400', 'border-rose-800');
  if (data.chase.is_implied) {
    pill.classList.add('bg-emerald-950', 'text-emerald-400', 'border', 'border-emerald-800');
    pill.innerText = `Lossless Join Entailed (Distinguished Row #${data.chase.distinguished_row_index !== null ? data.chase.distinguished_row_index + 1 : '1'})`;
  } else {
    pill.classList.add('bg-rose-950', 'text-rose-400', 'border', 'border-rose-800');
    pill.innerText = 'Non-Lossless Decomposition';
  }

  // Spurious tuple witness box
  const witnessBox = document.getElementById('chase-witness-box');
  if (!data.chase.is_implied && data.chase.spurious_tuple_witness) {
    witnessBox.classList.remove('hidden');
    witnessBox.className = 'p-3 rounded-lg border border-rose-800/80 bg-rose-950/40 text-xs font-mono text-rose-300 space-y-1';
    witnessBox.innerHTML = `
      <div class="font-bold text-rose-400 flex items-center gap-1.5">
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
        <span>Concrete Spurious Tuple Counterexample Witness Produced:</span>
      </div>
      <div>Projecting base relations produces spurious tuple: <span class="text-white font-bold">${JSON.stringify(data.chase.spurious_tuple_witness)}</span></div>
      <div class="text-[11px] text-slate-400">Natural join fails to reconstruct original relation without extraneous artifacts.</div>
    `;
  } else {
    witnessBox.classList.add('hidden');
  }

  // Step Trace Table
  const tbody = document.getElementById('chase-steps-tbody');
  tbody.innerHTML = '';
  if (data.chase.steps.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="p-3 text-center text-slate-500">Initial tableau was already distinguished (0 substitution steps needed).</td></tr>';
  } else {
    data.chase.steps.forEach(s => {
      const tr = document.createElement('tr');
      tr.className = 'hover:bg-slate-900/50 transition';
      tr.innerHTML = `
        <td class="p-2 text-cyan-400 font-semibold">${s.step_number}</td>
        <td class="p-2 text-slate-200">${s.fd}</td>
        <td class="p-2 text-slate-400">Rows (${s.rows_matched[0] + 1}, ${s.rows_matched[1] + 1})</td>
        <td class="p-2 text-amber-300">${s.attribute_equated}</td>
        <td class="p-2 font-mono"><span class="text-rose-400">${s.old_symbol}</span> &rarr; <span class="text-emerald-400 font-bold">${s.new_symbol}</span></td>
      `;
      tbody.appendChild(tr);
    });
  }

  // Tableau Matrix View
  const matrixEl = document.getElementById('chase-tableau-matrix');
  if (data.chase.final_tableau && data.chase.final_tableau.length > 0) {
    const heading = data.chase.heading;
    let html = '<table class="w-full text-left border-collapse"><thead><tr class="border-b border-slate-800 text-slate-400"><th class="p-1.5">Row</th>';
    heading.forEach(a => { html += `<th class="p-1.5">${a}</th>`; });
    html += '</tr></thead><tbody>';
    data.chase.final_tableau.forEach((r, idx) => {
      const isDist = idx === data.chase.distinguished_row_index;
      const rowClass = isDist ? 'bg-emerald-950/40 text-emerald-300 font-bold' : '';
      html += `<tr class="border-b border-slate-900 ${rowClass}"><td class="p-1.5 text-slate-500">${idx + 1}</td>`;
      heading.forEach(a => {
        const val = r[a] || '-';
        const isA = val.startsWith('a_');
        html += `<td class="p-1.5 ${isA ? 'text-cyan-400' : 'text-slate-400'}">${val}</td>`;
      });
      html += '</tr>';
    });
    html += '</tbody></table>';
    matrixEl.innerHTML = html;
  }

  // SQL DDL Output
  document.getElementById('relational-sql-ddl').innerText = data.sql_ddl;
}


// -----------------------------------------------------------------------------
// Module 2: Streaming BQNF Delta Repair
// -----------------------------------------------------------------------------

async function executeBqnfSimulation() {
  const boundary = PRESETS.bqnf.financial_ledger.boundary;
  let events = [];
  try {
    const raw = document.getElementById('bqnf-events-input').value;
    events = JSON.parse(raw);
  } catch (e) {
    events = PRESETS.bqnf.financial_ledger.events;
  }

  const useCochain = document.getElementById('bqnf-use-cochain-toggle').checked;
  const splitThresh = parseInt(document.getElementById('bqnf-split-thresh').value, 10) || 4;
  const mergeThresh = parseInt(document.getElementById('bqnf-merge-thresh').value, 10) || 1;

  try {
    const res = await fetch('/api/bqnf/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        boundary,
        events,
        use_cochain: useCochain,
        split_threshold: splitThresh,
        merge_threshold: mergeThresh
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'BQNF simulation failed');
    }
    const data = await res.json();
    renderBqnfResults(data);
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
}

function renderBqnfResults(data) {
  document.getElementById('bqnf-events-count').innerText = data.events_evaluated;
  document.getElementById('bqnf-cochain-hits').innerText = data.repair_tally.extrema_repairs;
  document.getElementById('bqnf-fallback-count').innerText = data.repair_tally.fallback_recomputations;
  document.getElementById('bqnf-speedup-badge').innerText = data.cochain_speedup;

  // Repair Log Table
  const tbody = document.getElementById('bqnf-repair-log-tbody');
  tbody.innerHTML = '';
  if (data.extrema_repair_log.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="p-3 text-center text-slate-500">Zero destructive deletions occurred in stream.</td></tr>';
  } else {
    data.extrema_repair_log.forEach(l => {
      const tr = document.createElement('tr');
      tr.className = 'hover:bg-slate-900/50 transition';
      const isDest = l.is_destructive === 1;
      const isRecomp = l.recomputation_fallback_executed === 1;
      tr.innerHTML = `
        <td class="p-2 text-cyan-400 font-semibold">${l.op_type}</td>
        <td class="p-2">$${l.affected_amount.toFixed(2)}</td>
        <td class="p-2 ${isDest ? 'text-amber-400 font-semibold' : 'text-slate-500'}">${isDest ? 'Yes (Max)' : 'No'}</td>
        <td class="p-2"><span class="px-1.5 py-0.5 rounded text-[10px] ${l.terminal_route === 'Repair' ? 'bg-cyan-950 text-cyan-400 border border-cyan-800' : 'bg-amber-950 text-amber-400'}">${l.terminal_route}</span></td>
        <td class="p-2 text-slate-300">[$${l.old_min ?? '-'}, $${l.old_max ?? '-'}] &rarr; [$${l.new_min ?? '-'}, $${l.new_max ?? '-'}]</td>
        <td class="p-2 ${isRecomp ? 'text-rose-400 font-bold' : 'text-emerald-400'}">${isRecomp ? 'Full Scan (O(N))' : 'Bypassed (O(log K))'}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  // Quantile histogram
  const reb = Object.values(data.quantile_rebalance_receipts).reduce((total, receipt) => ({
    splits_executed: total.splits_executed + receipt.splits_executed,
    merges_executed: total.merges_executed + receipt.merges_executed,
    total_mass: total.total_mass + receipt.total_mass,
  }), {splits_executed: 0, merges_executed: 0, total_mass: 0});
  document.getElementById('bqnf-rebalance-badge').innerText = `Splits: ${reb.splits_executed} | Merges: ${reb.merges_executed} | Mass: ${reb.total_mass}`;

  const bucketsContainer = document.getElementById('bqnf-buckets-visual');
  bucketsContainer.innerHTML = '';
  data.quantile_buckets.forEach(b => {
    const div = document.createElement('div');
    div.className = 'flex items-center justify-between p-2 rounded bg-slate-900 border border-slate-800';
    div.innerHTML = `
      <div>
        <span class="text-cyan-400 font-bold">Bucket #${b.bucket_id}</span>
        <span class="text-slate-400 ml-2">[${b.lower_bound.toFixed(1)}, ${b.upper_bound.toFixed(1)})</span>
      </div>
      <div class="flex items-center space-x-2">
        <span class="text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-mono">Count: ${b.count}</span>
      </div>
    `;
    const regionLabel = document.createElement('span');
    regionLabel.className = 'text-slate-400 mr-2';
    regionLabel.textContent = b.region;
    div.firstElementChild.prepend(regionLabel);
    bucketsContainer.appendChild(div);
  });
}


// -----------------------------------------------------------------------------
// Module 3: NF-IR Compiler Playground
// -----------------------------------------------------------------------------

async function executeCompilerLowering() {
  const contractId = document.getElementById('compiler-contract-id').value;
  const keyField = document.getElementById('compiler-key-field').value;
  const tableName = document.getElementById('compiler-table-name').value;
  const heading = document.getElementById('compiler-heading').value.split(',').map(s => s.trim()).filter(Boolean);
  const determinant = document.getElementById('compiler-determinant').value.split(',').map(s => s.trim()).filter(Boolean);
  const dependent = document.getElementById('compiler-dependent').value.split(',').map(s => s.trim()).filter(Boolean);

  let testCarrier = null;
  try {
    const raw = document.getElementById('compiler-carrier-json').value;
    if (raw.trim()) testCarrier = JSON.parse(raw);
  } catch (e) {
    // optional
  }

  try {
    const res = await fetch('/api/compiler/lower', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contract_id: contractId,
        key_field: keyField,
        table_name: tableName,
        heading,
        determinant,
        dependent,
        test_carrier: testCarrier
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Compiler lowering failed');
    }
    const data = await res.json();
    renderCompilerResults(data);
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
}

function renderCompilerResults(data) {
  // Subsumption card
  const subCard = document.getElementById('compiler-subsumption-card');
  const sub = data.subsumption_analysis;
  subCard.innerHTML = `
    <div class="flex items-center justify-between">
      <span class="text-slate-300 font-bold">Poset Ordering:</span>
      <span class="px-2 py-0.5 rounded text-[10px] font-bold ${sub.is_subsumed ? 'bg-purple-950 text-purple-300 border border-purple-800' : 'bg-slate-800 text-slate-400'}">${sub.is_subsumed ? 'SUBSUMPTION ELIDED' : 'INDEPENDENT PASS'}</span>
    </div>
    <div class="text-slate-400 text-[11px]">${sub.subsume_reason}</div>
    <div class="text-cyan-400 text-[11px] mt-1">Passes Executed: ${sub.executed_specs_count} | Passes Elided via Poset DCE: ${sub.elided_specs_count}</div>
  `;

  // SQLite code
  const sql = `${data.sqlite_ddl.create_table_sql}\n\n${data.sqlite_ddl.before_insert_trigger_sql}\n\n${data.sqlite_ddl.before_update_trigger_sql}`;
  document.getElementById('compiler-sqlite-code').innerText = sql;

  // Python code
  document.getElementById('compiler-python-code').innerText = data.python_guard_code;

  // Fuzzers
  const fuzzersCont = document.getElementById('compiler-fuzzers-container');
  fuzzersCont.innerHTML = '';
  data.synthesized_counterexamples.forEach(f => {
    const card = document.createElement('div');
    card.className = 'p-2.5 bg-slate-950 rounded border border-slate-800 space-y-1';
    card.innerHTML = `
      <div class="flex items-center justify-between">
        <span class="text-purple-400 font-bold font-mono">${f.failure_kind}</span>
        <span class="text-[10px] px-1.5 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-800">Expected: ${f.expected_terminal}</span>
      </div>
      <div class="text-slate-400 text-[11px]">${JSON.stringify(f.carrier_rows)}</div>
    `;
    fuzzersCont.appendChild(card);
  });
}


// -----------------------------------------------------------------------------
// Module 4: AI Context LossLedger Gateway
// -----------------------------------------------------------------------------

async function executeAiLossLedger() {
  const budget = parseInt(document.getElementById('ai-token-budget').value, 10) || 35;
  const targetFields = document.getElementById('ai-target-fields').value.split(',').map(s => s.trim()).filter(Boolean);

  let sourceChunks = [];
  try {
    const raw = document.getElementById('ai-chunks-input').value;
    sourceChunks = JSON.parse(raw);
  } catch (e) {
    sourceChunks = PRESETS.ai.rag_research_context.source_chunks;
  }

  try {
    const res = await fetch('/api/ai/lossledger', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_chunks: sourceChunks,
        target_fields: targetFields,
        max_token_budget: budget
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'AI LossLedger evaluation failed');
    }
    const data = await res.json();
    renderAiResults(data);
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
}

function renderAiResults(data) {
  document.getElementById('ai-source-tokens').innerText = data.token_accounting.source_token_count;
  document.getElementById('ai-retained-tokens').innerText = data.token_accounting.retained_token_count;
  document.getElementById('ai-truncated-tokens').innerText = data.token_accounting.truncated_token_count;

  const verifiedBadge = document.getElementById('ai-merkle-verified-badge');
  if (data.loss_ledger_integrity_verified) {
    verifiedBadge.innerText = 'SHA-256 Merkle Seal Verified';
    verifiedBadge.className = 'text-[11px] font-mono text-emerald-400';
  } else {
    verifiedBadge.innerText = 'Cryptographic Seal Failed';
    verifiedBadge.className = 'text-[11px] font-mono text-rose-400';
  }

  document.getElementById('ai-merkle-digest').innerText = data.merkle_digest || 'None (Lossless Transport)';
  document.getElementById('ai-erased-fields').innerText = data.erased_attributes.join(', ') || 'None';
  document.getElementById('ai-conservation-equation').innerText = data.token_accounting.conservation_equation;
}


// -----------------------------------------------------------------------------
// Initialization
// -----------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', async () => {
  try {
    const res = await fetch('/api/presets');
    if (res.ok) {
      PRESETS = await res.json();
      // Populate defaults
      if (PRESETS.relational) {
        loadRelationalPreset('ecommerce');
      }
      if (PRESETS.bqnf) {
        document.getElementById('bqnf-events-input').value = JSON.stringify(PRESETS.bqnf.financial_ledger.events, null, 2);
        executeBqnfSimulation();
      }
      if (PRESETS.compiler) {
        document.getElementById('compiler-carrier-json').value = JSON.stringify(PRESETS.compiler.employee_bcnf.test_carrier, null, 2);
        executeCompilerLowering();
      }
      if (PRESETS.ai) {
        document.getElementById('ai-chunks-input').value = JSON.stringify(PRESETS.ai.rag_research_context.source_chunks, null, 2);
        executeAiLossLedger();
      }
    }
  } catch (err) {
    console.error('Failed to initialize presets:', err);
  }
});
