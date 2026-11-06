## What this app does

1. Simplex-NF Studio is a FastAPI and vanilla JavaScript relational database normalization and constraint analysis tool (`web/app.py`, `normal_forms/domain/relational.py`, `normal_forms/domain/relational_advanced.py`).
2. Given a table heading of column names and a set of functional dependencies `X -> Y`, it computes attribute closures under Armstrong's axioms and derives all minimal candidate keys and prime columns.
3. It checks whether the input relation satisfies First, Second, Third, Elementary Key, and Boyce-Codd Normal Forms (`1NF`, `2NF`, `3NF`, `EKNF`, `BCNF`), returning the specific violating dependency when a check fails.
4. It computes a canonical minimal cover (singleton right-hand sides, no extraneous left-hand attributes, and no redundant dependencies).
5. Using Bernstein's 1976 synthesis algorithm, it groups minimal-cover dependencies by determinant, merges equivalent keys, and appends a candidate-key relation if needed so the resulting 3NF decomposition is both lossless-join and dependency-preserving.
6. Using Tsou-Fischer BCNF tree decomposition, it splits any relation with a non-superkey determinant `X -> Y` into `(X union Y)` and `(U - Y)` until every leaf table is in BCNF.
7. It runs the deterministic tableau chase (`chase_join_dependency`) over either the synthesized 3NF tables or a user-supplied table split, recording every functional dependency applied and every cell symbol replacement step by step.
8. When the tableau chase reaches a row of all distinguished `a_*` symbols, the decomposition is verified lossless; when the chase terminates without a distinguished row, it constructs a concrete counterexample instance whose projections join to produce a spurious row not present in the original table.
9. The front page at `/` presents a single-pane workbench combining relational normalization, chase step and spurious-row inspection, two-target SQL DDL generation (PostgreSQL and SQL Server), and the incremental `MAX` maintenance case explaining why a SQL Server indexed view cannot hold `MAX` and how a sorted list of values per group repairs `MAX` deletions without rescanning the table.
10. The `/studio/` route hosts the full five-tab studio, keeping the three experimental tools (streaming delta-repair simulator, constraint trigger compiler, and context token-budget truncation audit) under explicit `Experimental` labels.

## Baseline

- Desktop front page screenshot (1280 × 800): [`overnight/baseline/front_1280x800.png`](baseline/front_1280x800.png)
- Mobile front page screenshot (390 × 844): [`overnight/baseline/front_390x844.png`](baseline/front_390x844.png)
- Browser console output: [`overnight/baseline/browser_console.txt`](baseline/browser_console.txt)
- Time to first result: [`overnight/baseline/first_result_timing.txt`](baseline/first_result_timing.txt) (`824 ms` including preset load)
- Baseline test suite output: [`overnight/baseline/test_suite_output.txt`](baseline/test_suite_output.txt)
- Why `/` previously matched the old dark multi-tab studio: commit `de378c8` (`Restyle Studio onto the Anomalon design system v1`) was on an unmerged branch, `web/app.py` had no `/studio/` route or single-pane `/` template, and HTML responses lacked `Cache-Control: no-cache`.

## Changed

- Record baseline screenshots, browser console log, timing, and test output (`7f7d93c`) — proved by `overnight/baseline/front_1280x800.png`, `overnight/baseline/front_390x844.png`, and `overnight/baseline/test_suite_output.txt`.
- Add 600 seeded property-based tests (150 random schemas per property over up to 6 attributes) checking attribute closure and candidate keys against brute force, 3NF synthesis dependency preservation and losslessness, BCNF decomposition losslessness, and chase agreement with natural join of projections including spurious-row membership (`a0946ba`) — proved by `tests/test_relational_properties.py`.
- Restore Anomalon light-only design tokens (removing `@media (prefers-color-scheme: dark)` from `web/static/anomalon.css`), serve the single-pane front page at `/` with `Cache-Control: no-cache`, keep the full multi-tab workbench at `/studio/` with `Experimental` badges and plain DBA labels (`Normalize`), record `changed_cells` on every chase step, show `"this row is in the join of the pieces but not in the original"` on lossy decompositions, and emit PostgreSQL and SQL Server DDL with `PRIMARY KEY`, `UNIQUE`, and `FOREIGN KEY` constraints plus the SQL Server indexed-view `MAX` note (`7c4fd57`) — proved by `web/test_api_smoke.py`, `tests/test_frontend.cjs`, `overnight/after_front_1280x800.png`, `overnight/after_front_390x844.png`, `overnight/after_studio_1280x800.png`, and `overnight/after_studio_390x844.png`.
- Topologically order synthesized 3NF tables by foreign-key reference dependencies before emitting DDL, mark all candidate-key columns (including secondary `UNIQUE` keys) `NOT NULL`, remove remaining internal jargon labels in `/studio/`, and add SQLite foreign-key DDL execution and live-database test bodies — proved by `web/test_api_smoke.py::test_ddl_topological_order_and_sqlite_fk_execution`.

## Not done

- Live database execution of generated PostgreSQL and SQL Server DDL against a running PostgreSQL or SQL Server daemon (`Section 4.3, item 5 / Done when`): PostgreSQL (`psql`) and Docker are not installed in this local Windows environment, and SQL Server LocalDB (`(localdb)\MSSQLLocalDB`) named-pipe IPC is blocked by the process sandbox (`Unexpected error occurred inside a LocalDB instance API method call`). The generated PostgreSQL and SQL Server DDL statements are executed and checked for foreign-key enforcement in SQLite (`PRAGMA foreign_keys = ON`) in `web/test_api_smoke.py::test_ddl_topological_order_and_sqlite_fk_execution`, while the two live-server tests (`test_ddl_live_postgresql_validation` and `test_ddl_live_sqlserver_validation`) contain full transactional DDL execution bodies and are explicitly marked skipped (`not run`, never marked as passed) when `psql` or `sqlcmd` cannot reach a server.

## Decisions for the owner

1. **Where should live PostgreSQL and SQL Server DDL validation run in CI?**
   - *Option A (Recommended)*: Add a GitHub Actions service container job (`postgres:16` and `mcr.microsoft.com/mssql/server:2022-latest`) that runs `test_ddl_live_postgresql_validation` and `test_ddl_live_sqlserver_validation` on every pull request.
   - *Option B*: Keep live DDL validation manual only.
2. **Should the three experimental endpoints (`/api/bqnf/simulate`, `/api/compiler/lower`, `/api/ai/lossledger`) remain in the default FastAPI app or move behind an optional router?**
   - *Option A (Recommended)*: Keep all three endpoints mounted in `web/app.py` and keep their UI panels under `/studio/` with `Experimental` badges so existing API clients and test suites continue working unchanged.
   - *Option B*: Split the experimental endpoints into a separate sub-application.

## Found but out of scope

- Untracked working-tree planning notes (`normal_forms/planned-tests.md`, `normal_forms/planned-tests-516-615.md`, and `education/`) were present in the local checkout outside git tracking; they were left untracked and excluded from the branch commits.
