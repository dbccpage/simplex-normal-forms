import json
import os
from typing import Any, Dict

# Load the CDC events from JSON
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "cdc_events.json")

def evaluate_bqnf(case: Dict[str, Any]) -> Dict[str, Any]:
    #view_name = case.get("view", "unknown")
    boundary = case.get("boundary", {})
    event = case.get("event", {})
    
    # 1. Evidence Check: Verify all required attributes exist in the event payload
    req_attrs = boundary.get("attributes", [])
    old_val = event.get("old", {})
    new_val = event.get("new", {})
    
    # If the payload lacks the necessary identifiers or values to evaluate predicates
    missing_old = [a for a in req_attrs if a not in old_val]
    missing_new = [a for a in req_attrs if a not in new_val]
    
    if missing_old or missing_new:
        return {
            "normal_form": "BQNF",
            "decision": "Invalidate",
            "terminal_route": "Invalidate",
            "obstruction_class": "[NonZero - MissingEvidence]",
            "repair": None,
            "evidence_sufficient": False,
            "certified": False,
            "authorized": False,
            "reason": f"Missing required columns in event. Old missing: {missing_old}, New missing: {missing_new}"
        }
        
    # 2. Check if the update affects boundary attributes
    # Compare old and new values to check if any boundary attribute changed
    boundary_changed = False
    for attr in req_attrs:
        if old_val.get(attr) != new_val.get(attr):
            boundary_changed = True
            break
            
    if not boundary_changed:
        return {
            "normal_form": "BQNF",
            "decision": "Preserve",
            "terminal_route": "Preserve",
            "obstruction_class": "[0]",
            "repair": None,
            "evidence_sufficient": True,
            "certified": True,
            "authorized": False,
            "reason": "No columns tracked by the boundary were modified."
        }

    # 3. Check for supported aggregates
    # SUM is supported, MAX without extremum witness is unsupported (requires full recomputation)
    aggregates = boundary.get("aggregates", [])
    unsupported_aggs = [agg for agg in aggregates if not agg.startswith("SUM")]
    if unsupported_aggs:
        return {
            "normal_form": "BQNF",
            "decision": "Unsupported",
            "terminal_route": "Unsupported",
            "obstruction_class": "[NonZero - LimitOfSubstrate]",
            "repair": None,
            "evidence_sufficient": True,
            "certified": False,
            "authorized": False,
            "reason": f"Aggregate functions {unsupported_aggs} require auxiliary state or full table recomputation."
        }

    # 4. Evaluate BQNF Boundary Predicates (e.g. status = 'paid')
    # For this demo, we parse the simple "status = paid" condition
    def is_paid(record: Dict[str, Any]) -> bool:
        return record.get("status") == "paid"
        
    was_paid = is_paid(old_val)
    is_now_paid = is_paid(new_val)
    
    old_amount = old_val.get("amount", 0)
    new_amount = new_val.get("amount", 0)
    customer_id = new_val.get("customer_id")
    
    delta_revenue = 0
    decision = "Repair"
    terminal_route = "Repair"
    obstruction_class = "[0]"
    
    # Evaluate cochain defect transition
    if was_paid and is_now_paid:
        # Case A: stayed paid, delta is the difference
        delta_revenue = new_amount - old_amount
    elif not was_paid and is_now_paid:
        # Case B: transitioned to paid, full new amount is added
        delta_revenue = new_amount
    elif was_paid and not is_now_paid:
        # Case C: transitioned out of paid, old amount is subtracted
        delta_revenue = -old_amount
    else:
        # Case D: remained unpaid, no change to view
        decision = "Preserve"
        terminal_route = "Preserve"
        delta_revenue = 0

    return {
        "normal_form": "BQNF",
        "decision": decision,
        "terminal_route": terminal_route,
        "obstruction_class": obstruction_class,
        "repair": {
            "customer_id": customer_id,
            "delta_revenue": delta_revenue
        } if decision == "Repair" else None,
        "evidence_sufficient": True,
        "certified": True,
        "authorized": False
    }

def main():
    print("================================================================================")
    print("DEMO 01: BQNF (Boundary Quotient Normal Form) - Change Stream Evaluation")
    print("================================================================================")
    
    if not os.path.exists(DATA_PATH):
        print(f"Error: Data file not found at {DATA_PATH}")
        return
        
    with open(DATA_PATH, "r") as f:
        cases = json.load(f)
        
    for i, case in enumerate(cases, 1):
        print(f"\n--- Running Case {i}: {case.get('description')} ---")
        print("Input Event:")
        print(json.dumps(case.get("event"), indent=2))
        
        result = evaluate_bqnf(case)
        
        print("\nOutput Certificate:")
        print(json.dumps(result, indent=2))
        print("-" * 80)

if __name__ == "__main__":
    main()
