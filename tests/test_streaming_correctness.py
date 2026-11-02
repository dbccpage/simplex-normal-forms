"""Replay the workbench against an independent full-recomputation oracle."""

from collections import Counter
from copy import deepcopy

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
