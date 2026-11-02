# Normal-form Python tools

Executable validators, schema inventory, evaluators, and examples live here.
Their YAML contracts, SQL schemas, and JSON example data remain in
`../contracts` in the checkout and ship as `normal_forms.resources` in a wheel.
`contract_paths.py` selects that resource home without depending on the current
working directory.

The four descriptive `*_example.py` modules are executable examples. Exact
mathematical predicates live in the `normal_forms.domain` modules;
infrastructure modules provide only filesystem, SQLite, and YAML adapters.

AuthorityEffect: None.
