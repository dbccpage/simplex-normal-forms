"""Replay the workbench against an independent full-recomputation oracle."""

from collections import Counter
from copy import deepcopy
import math

import pytest
from fastapi.testclient import TestClient

from normal_forms.domain.bqnf_validator import BqnfBoundary, BqnfCdcEvent, BqnfValidator
from web.app import app, BQNF_PRESETS


def row(region, amount, status="paid"):
    return {"region": region, "amount": amount, "status": status}


def event(op, old=None, new=None, relation="sales"):
    return {"op": op, "relation": relation, "old": old, "new": new}


@pytest.mark.parametrize("use_cochain", [True, False])
def test_every_prefix_matches_full_recomputation(use_cochain):
    initial = [row("North", 10), row("North", 10), row("South", 30), row("North", 99, "unpaid")]
    events = [
        event("INSERT", new=row("North", 999), relation="unrelated"),
        event("TRUNCATE", new=row("North", 999)),
        event("INSERT", new={"amount": 999}),
        event("UPDATE", row("South", 999), row("West", 999)),
        event("INSERT", new=row("East", 40)),
        event("UPDATE", row("North", 99, "unpaid"), row("North", 99)),
        event("UPDATE", row("South", 30), row("South", 30, "unpaid")),
        event("UPDATE", row("North", 10), row("West", 20)),
        event("DELETE", row("North", 10)),
        event("DELETE", row("West", 20)),
        event("INSERT", new=row("West", 5)),
        event("INSERT", new=row("East", 70, "unpaid")),
        event("UPDATE", row("East", 40), row("East", 40)),
    ]
    expected_routes = ["Preserve", "Unsupported", "Invalidate", "Invalidate", "Repair", "Repair",
                       "Repair", "Repair", "Repair", "Repair", "Repair", "Preserve", "Preserve"]
    reference = deepcopy(initial)
    with TestClient(app) as client:
        for count in range(len(events) + 1):
            if count and count > 4:
                ev = events[count - 1]
                if ev["op"] in {"UPDATE", "DELETE"}:
                    reference.remove(ev["old"])
                if ev["op"] in {"INSERT", "UPDATE"}:
                    reference.append(ev["new"])
            active = [r for r in reference if r["status"] == "paid"]
            payload = {"boundary": BQNF_PRESETS["financial_ledger"]["boundary"],
                       "initial_sales": initial, "events": events[:count], "use_cochain": use_cochain}
            response = client.post("/api/bqnf/simulate", json=payload)
            assert response.status_code == 200, response.text
            result = response.json()
            assert [d["decision"] for d in result["event_decisions"]] == expected_routes[:count]
            expected = {}
            for region in {r["region"] for r in active}:
                amounts = [r["amount"] for r in active if r["region"] == region]
                expected[region] = dict(total_sales=sum(amounts), sale_count=len(amounts),
                                        min_amount=min(amounts), max_amount=max(amounts))
            assert result["final_cache"] == expected
            assert {(r["region"], r["amount"]): r["frequency"] for r in result["extremum_cochain_entries"]} == dict(
                Counter((r["region"], r["amount"]) for r in active))
            buckets = result["quantile_buckets"]
            assert sum(b["count"] for b in buckets) == len(active)
            for b in buckets:
                assert b["count"] == sum(r["region"] == b["region"] and
                    b["lower_bound"] <= r["amount"] < b["upper_bound"] for r in active)
            for r in active:
                assert sum(b["region"] == r["region"] and b["lower_bound"] <= r["amount"] < b["upper_bound"]
                           for b in buckets) == 1
            for decision in result["event_decisions"]:
                if decision["decision"] != "Repair":
                    assert decision["applied"] is False


def test_empty_initial_state_and_emptying_then_recreating_group():
    with TestClient(app) as client:
        payload = {"boundary": BQNF_PRESETS["financial_ledger"]["boundary"], "initial_sales": [], "events": []}
        assert client.post("/api/bqnf/simulate", json=payload).json()["final_cache"] == {}
        payload["events"] = [event("INSERT", new=row("West", 4)), event("DELETE", row("West", 4)),
                             event("INSERT", new=row("West", 7))]
        result = client.post("/api/bqnf/simulate", json=payload).json()
        assert result["final_cache"] == {"West": dict(total_sales=7, sale_count=1, min_amount=7, max_amount=7)}


@pytest.mark.parametrize("change", [
    {"aggregates": ["AVG(amount)"]}, {"groups": ["customer_id"]},
    {"predicates": ["status != paid"]}, {"predicates": ["status = paid", "region = North"]},
])
def test_unsupported_simulator_boundaries_are_explicit(change):
    boundary = {**BQNF_PRESETS["financial_ledger"]["boundary"], **change}
    with TestClient(app) as client:
        assert client.post("/api/bqnf/simulate", json={"boundary": boundary, "events": []}).status_code == 400


def test_domain_relation_scope_precedes_image_validation():
    boundary = BqnfBoundary.from_dict(BQNF_PRESETS["financial_ledger"]["boundary"])
    assert BqnfValidator.evaluate(boundary, BqnfCdcEvent("INSERT", "unrelated")).decision == "Preserve"
    assert BqnfValidator.evaluate(boundary, BqnfCdcEvent("TRUNCATE", "sales")).decision == "Unsupported"


@pytest.mark.parametrize("use_cochain", [True, False])
@pytest.mark.parametrize("track_status", [False, True])
def test_status_only_update_then_delete_without_predicate(use_cochain, track_status):
    boundary = deepcopy(BQNF_PRESETS["financial_ledger"]["boundary"])
    boundary["predicates"] = []
    boundary["attributes"] = ["region", "amount"] + (["status"] if track_status else [])
    payload = {"boundary": boundary, "initial_sales": [row("North", 10)],
               "events": [event("UPDATE", row("North", 10), row("North", 10, "refunded")),
                          event("DELETE", row("North", 10, "refunded"))],
               "use_cochain": use_cochain}
    with TestClient(app) as client:
        response = client.post("/api/bqnf/simulate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert [d["decision"] for d in result["event_decisions"]] == ["Repair" if track_status else "Preserve", "Repair"]
    assert result["final_cache"] == {}
    assert result["extremum_cochain_entries"] == []
    assert result["quantile_buckets"] == []


@pytest.mark.parametrize("values", [
    [20.0, 19.9999999999995], [19.9999999999995, 20.0],
    *[[math.nextafter(b, -math.inf), b, math.nextafter(b, math.inf)] for b in (-20.0, 0.0, 10.0, 20.0)],
    *[[math.nextafter(b, math.inf), b, math.nextafter(b, -math.inf)] for b in (-20.0, 0.0, 10.0, 20.0)],
])
@pytest.mark.parametrize("split_threshold", [2, 4])
def test_initial_quantile_membership_is_exact_in_both_orders(values, split_threshold):
    payload = {"boundary": BQNF_PRESETS["financial_ledger"]["boundary"],
               "initial_sales": [row("North", a) for a in values], "events": [],
               "split_threshold": split_threshold}
    with TestClient(app) as client:
        response = client.post("/api/bqnf/simulate", json=payload)
    assert response.status_code == 200, response.text
    buckets = response.json()["quantile_buckets"]
    assert sum(b["count"] for b in buckets) == len(values)
    for b in buckets:
        assert b["count"] == sum(b["lower_bound"] <= a < b["upper_bound"] for a in values)
    for a in values:
        assert sum(b["lower_bound"] <= a < b["upper_bound"] for b in buckets) == 1


@pytest.mark.parametrize("use_cochain", [True, False])
def test_applied_region_deltas_replay_grouped_totals_and_counts(use_cochain):
    initial = [row("North", 10), row("South", 5)]
    events = [
        event("UPDATE", row("North", 10), row("South", 10)),
        event("UPDATE", row("South", 5), row("South", 8)),
        event("UPDATE", row("South", 10), row("South", 10, "unpaid")),
        event("UPDATE", row("West", 4, "unpaid"), row("West", 4)),
        event("INSERT", new=row("West", 6)),
        event("DELETE", row("West", 4)),
        event("DELETE", row("West", 999)),
        event("INSERT", new=row("North", 100), relation="unrelated"),
    ]
    totals, counts = {"North": 10, "South": 5}, {"North": 1, "South": 1}
    with TestClient(app) as client:
        for length in range(1, len(events) + 1):
            response = client.post("/api/bqnf/simulate", json={
                "boundary": BQNF_PRESETS["financial_ledger"]["boundary"],
                "initial_sales": initial, "events": events[:length], "use_cochain": use_cochain})
            assert response.status_code == 200, response.text
            result = response.json()
            receipt = result["event_decisions"][-1]
            if receipt["applied"]:
                deltas = receipt["repair"]["region_deltas"]
                if length == 1:
                    assert deltas == {"North": {"delta_revenue": -10, "delta_count": -1},
                                      "South": {"delta_revenue": 10, "delta_count": 1}}
                for region, delta in deltas.items():
                    totals[region] = totals.get(region, 0) + delta["delta_revenue"]
                    counts[region] = counts.get(region, 0) + delta["delta_count"]
            else:
                assert receipt["repair"] is None
            assert {r: {"total_sales": totals[r], "sale_count": counts[r]} for r in totals if counts[r]} == {
                r: {"total_sales": s["total_sales"], "sale_count": s["sale_count"]} for r, s in result["final_cache"].items()}
