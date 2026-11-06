// Regression checks for the actual frontend request handler and chase renderer.
// Node built-ins only; run with: node tests/test_frontend.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function element() {
  return { value: '', innerHTML: '', classList: { add() {}, remove() {} }, appendChild() {} };
}
const elements = new Map();
const getElement = id => {
  if (!elements.has(id)) elements.set(id, element());
  return elements.get(id);
};
let submitted;
const response = {
  candidate_keys: [['A', 'C']], prime_attributes: ['A', 'C'], normal_forms: {},
  minimal_cover: [], synthesized_3nf: [], sql_ddl: '',
  chase: { is_implied: false, steps: [], steps_count: 0, final_tableau: [],
    distinguished_row_index: null, spurious_tuple_witness: { A: 'a_A', B: 'a_B', C: 'a_C' } },
};
const context = vm.createContext({
  document: { addEventListener() {}, getElementById: getElement, createElement: element },
  alert(message) { throw new Error(message); },
  fetch: async (url, options) => {
    assert.equal(url, '/api/relational/normalize');
    submitted = JSON.parse(options.body);
    return { ok: true, json: async () => response };
  },
});
vm.runInContext(fs.readFileSync(path.join(__dirname, '../web/static/app.js'), 'utf8'), context);

(async () => {
  getElement('relational-attributes-input').value = 'A, B, C';
  getElement('relational-dependencies-input').value = 'A -> B';
  for (const text of ['(A, B), (B, C)', '(A,B) ,(B,C)', 'A, B; B, C']) {
    getElement('relational-components-input').value = text;
    await context.executeRelationalNormalize();
    assert.deepEqual(submitted.custom_components, [['A', 'B'], ['B', 'C']]);
    assert.match(getElement('relational-chase-status').innerHTML, /Lossy Join/);
    assert.match(getElement('chase-witness-box').innerHTML, /a_C/);
    assert.match(
      getElement('chase-witness-box').innerHTML,
      /this row is in the join of the pieces but not in the original/
    );
    assert.match(getElement('chase-steps-tbody').innerHTML, /no distinguished row/);
    assert.equal(getElement('btn-run-relational').disabled, false);
  }
  getElement('relational-components-input').value = '';
  response.chase.is_implied = true;
  await context.executeRelationalNormalize();
  assert.equal(submitted.custom_components, null);
  assert.match(getElement('chase-steps-tbody').innerHTML, /already distinguished/);
  console.log('Frontend component parsing and zero-step chase rendering passed.');
})().catch(error => { console.error(error); process.exitCode = 1; });
