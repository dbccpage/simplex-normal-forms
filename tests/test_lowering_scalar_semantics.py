"""Independent scalar cases for Python and native SQLite constraint behavior."""

import sqlite3

import pytest

from normal_forms.domain.relational import FunctionalDependency
from normal_forms.ir_kernel import evaluate_nf_kernel, lower_fd_to_kernel_spec, lower_coda_mur_to_kernel_spec
from normal_forms.ir_lowering import compile_to_sqlite_triggers, install_and_verify_sqlite_bundle


def fd_spec():
    return lower_fd_to_kernel_spec(FunctionalDependency(frozenset({"x"}), frozenset({"y"})),
                                  key_field="id", heading=("id", "x", "y"), require_support_floor=False)


@pytest.mark.parametrize("left", [1, 1.0, True, "1", b"1", "other"])
@pytest.mark.parametrize("right", [1, 1.0, True, "1", b"1", "other"])
def test_scalar_fd_equality_matches_python_and_native_sql(left, right):
    spec = fd_spec()
    rows = [{"id": "a", "x": left, "y": "first"}, {"id": "b", "x": right, "y": "second"}]
    expected = left != right
    assert evaluate_nf_kernel(spec, rows).admitted == expected
    with sqlite3.connect(":memory:") as conn:
        assert install_and_verify_sqlite_bundle(conn, compile_to_sqlite_triggers(spec), rows)[0] == expected


@pytest.mark.parametrize("field", ["x", "y"])
@pytest.mark.parametrize("missing", [False, True])
def test_required_missing_and_null_fields_are_rejected(field, missing):
    rows = [{"id": "a", "x": "dept", "y": "mgr"}, {"id": "b", "x": "dept", "y": "mgr"}]
    if missing:
        del rows[0][field]
    else:
        rows[0][field] = None
    spec = fd_spec()
    assert not evaluate_nf_kernel(spec, rows).admitted
    with sqlite3.connect(":memory:") as conn:
        assert not install_and_verify_sqlite_bundle(conn, compile_to_sqlite_triggers(spec), rows)[0]


def test_sqlite_updates_preserve_types_and_enforce_null_and_collision_guards():
    with sqlite3.connect(":memory:") as conn:
        rows = [{"id": "a", "x": 1, "y": "first"}, {"id": "b", "x": "1", "y": "second"}]
        assert install_and_verify_sqlite_bundle(conn, compile_to_sqlite_triggers(fd_spec()), rows)[0]
        assert conn.execute("SELECT typeof(x) FROM nf_carrier ORDER BY id").fetchall() == [("integer",), ("text",)]
        for value in [1, None]:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute("UPDATE nf_carrier SET x=? WHERE id='b'", (value,))
        conn.execute("UPDATE nf_carrier SET x=? WHERE id='b'", ("2",))


def test_transport_protected_values_do_not_collapse_numeric_and_text_keys():
    spec = lower_coda_mur_to_kernel_spec(source_fields=("id", "key"), target_fields=("id", "key"),
                                        key_field="id", protected_fields=("key",))
    rows = [{"id": "a", "key": 1}, {"id": "b", "key": "1"}]
    assert evaluate_nf_kernel(spec, rows).admitted
    with sqlite3.connect(":memory:") as conn:
        assert install_and_verify_sqlite_bundle(conn, compile_to_sqlite_triggers(spec), rows)[0]
