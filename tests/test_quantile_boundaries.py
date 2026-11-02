"""Exact float interval membership through insertion, deletion, and rebalancing."""

import math

import pytest

from normal_forms.evaluator import NormalFormsEvaluator
from normal_forms.sales_cochain import quantile_cochain_remove, verify_quantile_cochain_invariants


def assert_membership(conn, values):
    buckets = conn.execute(
        "SELECT lower_bound, upper_bound, count FROM region_quantile_cochain ORDER BY lower_bound"
    ).fetchall()
    assert sum(b["count"] for b in buckets) == len(values)
    for b in buckets:
        assert b["count"] == sum(b["lower_bound"] <= a < b["upper_bound"] for a in values)
    for a in values:
        assert sum(b["lower_bound"] <= a < b["upper_bound"] for b in buckets) == 1
    assert verify_quantile_cochain_invariants(conn) == (True, [])


@pytest.mark.parametrize("width", [20.0, 0.1, 1e-14])
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("dynamic", [False, True])
def test_adjacent_floats_survive_insert_split_merge_and_removal(width, reverse, dynamic):
    values = [a for boundary in (-width, 0.0, width / 2, width)
              for a in (math.nextafter(boundary, -math.inf), boundary, math.nextafter(boundary, math.inf))]
    if reverse:
        values.reverse()
    settings = dict(bucket_width=width, min_bucket_width=width / 8,
                    split_threshold=2, merge_threshold=1, dynamic_buckets=dynamic)
    with NormalFormsEvaluator() as evaluator:
        retained = {}
        for key, value in enumerate(values):
            evaluator.apply_sales_cdc("INSERT", key, new_region="North", new_amount=value, **settings)
            retained[key] = value
            assert_membership(evaluator.conn, retained.values())
        # Remove every other occurrence first to leave holes, forcing merges
        # under dynamic rebalancing rather than just emptying adjacent cells.
        for key in [*range(0, len(values), 2), *range(1, len(values), 2)]:
            evaluator.apply_sales_cdc("DELETE", key, **settings)
            retained.pop(key)
            assert_membership(evaluator.conn, retained.values())


def test_remove_never_uses_bucket_identifier_as_interval_membership():
    with NormalFormsEvaluator() as evaluator:
        evaluator.apply_sales_cdc("INSERT", 1, new_region="North", new_amount=20.0, bucket_width=20.0)
        evaluator.conn.execute("UPDATE region_quantile_cochain SET bucket_id=0")
        quantile_cochain_remove(evaluator.conn, "North", 10.0, bucket_width=20.0)
        assert_membership(evaluator.conn, [20.0])


def test_invariant_checker_rejects_a_tolerance_shifted_bucket():
    with NormalFormsEvaluator() as evaluator:
        evaluator.apply_sales_cdc("INSERT", 1, new_region="North", new_amount=19.9999999999995,
                                  bucket_width=20.0)
        evaluator.conn.execute("UPDATE region_quantile_cochain SET lower_bound=20, upper_bound=40")
        ok, violations = verify_quantile_cochain_invariants(evaluator.conn)
        assert not ok
        assert any("actual base_sales rows=0" in v for v in violations)
