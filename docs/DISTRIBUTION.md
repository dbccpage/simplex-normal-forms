# Distribution verification

`contracts/` remains the source owner for YAML, SQL, and JSON resources. The
package-directory mapping installs these files under `normal_forms/resources/`.
The library resolves this installed directory first and uses the checkout's
`contracts/` directory during source development. `web` ships templates and
static assets; install the `web` extra to run Studio. Changes to the package
list or runtime resource extensions must also update `pyproject.toml`.

Build a source distribution and then a wheel from that source distribution:

```sh
python -m pip install build
python -m build
```

Install the generated wheel with its web extra into a new virtual environment.
From a directory outside this checkout, run that environment's interpreter:

```sh
python -I /absolute/path/to/simplex-normal-forms/scripts/installed_smoke.py
python -I -m normal_forms.catalog
```

The smoke check requires a virtual environment and asserts that the library,
web app, and contract resources resolve inside its installed package. It
validates all 112 contracts, loads JSON fixtures, installs the SQL schema, serves
the HTML/JS/CSS assets, and exercises the four API workbenches. This prevents a
checkout or editable install from concealing missing distribution files.

`.github/workflows/ci.yml` runs the suite and catalog on Linux and Windows with
Python 3.10 and 3.14, and runs the isolated distribution check on Linux. The
workflow has read-only repository permissions and contains no deployment or
publication step. Build checks establish installation behavior; they do not
establish live service availability or general mathematical correctness.

The original NF-IR plan documents record historical design intentions. Current
implementation boundaries are documented in [CORRECTNESS_SCOPE.md](CORRECTNESS_SCOPE.md).
