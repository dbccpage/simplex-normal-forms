import json
import os
from typing import Any, Dict

# Load the transport certificates from JSON
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "transport_certificates.json")

def evaluate_certificate(cert: Dict[str, Any]) -> Dict[str, Any]:
    cert_id = cert.get("certificate_id", "unknown")
    outcome = cert.get("verifier_outcome")
    
    # Evaluate the status of the verifier
    if outcome == "verified":
        return {
            "certificate_id": cert_id,
            "decision": "Authorized",
            "terminal_route": "Accept",
            "reason": "Morphism certificate successfully validated by active verifier policy",
            "certified": True,
            "authorized": True
        }
    elif outcome == "pending":
        return {
            "certificate_id": cert_id,
            "decision": "NotAuthorized",
            "terminal_route": "AuthorityLaundering",
            "reason": "Certificate row exists but active verifier has not completed verification",
            "certified": True,
            "authorized": False
        }
    else:
        return {
            "certificate_id": cert_id,
            "decision": "NotAuthorized",
            "terminal_route": "MissingVerifier",
            "reason": "No policy verifier is associated with this certificate schema",
            "certified": False,
            "authorized": False
        }

def main():
    print("================================================================================")
    print("DEMO 02: Certificate Validation and Authority Verification")
    print("================================================================================")
    
    if not os.path.exists(DATA_PATH):
        print(f"Error: Data file not found at {DATA_PATH}")
        return
        
    with open(DATA_PATH, "r") as f:
        certs = json.load(f)
        
    for i, cert in enumerate(certs, 1):
        print(f"\n--- Running Case {i}: {cert.get('description')} ---")
        print("Input Certificate:")
        print(json.dumps({k: v for k, v in cert.items() if k != "description"}, indent=2))
        
        result = evaluate_certificate(cert)
        
        print("\nOutput Decision:")
        print(json.dumps(result, indent=2))
        print("-" * 80)

if __name__ == "__main__":
    main()
