import json
import os
from typing import Any, Dict, List

# Load the observers configuration from JSON
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "observers.json")

def evaluate_freshness(scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
    packet = scenario.get("packet", {})
    observers = scenario.get("observers", [])
    
    #value = packet.get("value")
    #read_at = packet.get("read_at")
    lag = packet.get("replica_lag_seconds")
    packet_scope = packet.get("packet_scope", "public") # default to public if not specified
    
    results = []
    
    for observer in observers:
        observer_id = observer.get("observer_id", "unknown")
        max_lag = observer.get("max_lag_seconds", 0)
        auth_scopes = observer.get("authorized_scopes", ["public"]) # default to public scope only
        
        # 1. Scope Authorization Check
        # If the packet has a restricted scope but the observer only has public access
        is_scope_authorized = True
        for scope in [packet_scope]:
            if scope not in auth_scopes:
                is_scope_authorized = False
                break
                
        if not is_scope_authorized:
            results.append({
                "observer_id": observer_id,
                "terminal_route": "Refuse",
                "authorized": False,
                "reason": f"Observer is not authorized for packet scope: '{packet_scope}'."
            })
            continue

        # 2. Freshness Evidence Check
        # If replica lag is missing or null, the system cannot verify freshness
        if lag is None:
            results.append({
                "observer_id": observer_id,
                "terminal_route": "ConservativeInvalidate",
                "authorized": False,
                "reason": "Replica lag is missing or null; unable to verify SLA budget."
            })
            continue
            
        # 3. SLA Budget Check
        if lag <= max_lag:
            results.append({
                "observer_id": observer_id,
                "terminal_route": "AuthorizedFresh",
                "authorized": True,
                "reason": f"Replica lag ({lag}s) is within the observer's max limit ({max_lag}s)."
            })
        else:
            results.append({
                "observer_id": observer_id,
                "terminal_route": "RefreshRequired",
                "authorized": False,
                "reason": f"Replica lag ({lag}s) exceeds the observer's max limit ({max_lag}s)."
            })
            
    return results

def main():
    print("================================================================================")
    print("DEMO 03: Observer-Relative Freshness SLA Bounds")
    print("================================================================================")
    
    if not os.path.exists(DATA_PATH):
        print(f"Error: Data file not found at {DATA_PATH}")
        return
        
    with open(DATA_PATH, "r") as f:
        scenarios = json.load(f)
        
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n--- Running Scenario {i}: {scenario.get('description')} ---")
        print("Input Packet Metadata:")
        print(json.dumps(scenario.get("packet"), indent=2))
        
        results = evaluate_freshness(scenario)
        
        print("\nObserver Resolutions:")
        print(json.dumps(results, indent=2))
        print("-" * 80)

if __name__ == "__main__":
    main()
