"""Exercise a running Studio over HTTP; no checkout imports or extra packages.

HTTPS uses normal certificate/hostname validation. HTTP is allowed only for
loopback development. Results describe this bounded run, not a load benchmark.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


CASES = (
    ("relational", "ecommerce", "/api/relational/normalize"),
    ("relational", "lossy_decomposition", "/api/relational/normalize"),
    ("bqnf", "financial_ledger", "/api/bqnf/simulate"),
    ("compiler", "employee_bcnf", "/api/compiler/lower"),
    ("ai", "rag_research_context", "/api/ai/lossledger"),
)


def request(base, path, payload=None, timeout=30):
    encoded = None if payload is None else json.dumps(payload).encode("utf-8")
    req = Request(base + path, data=encoded, headers={"Content-Type": "application/json"})
    receipt = {"method": req.get_method(), "path": path}
    if encoded is not None:
        receipt["request_sha256"] = hashlib.sha256(encoded).hexdigest()
    start = time.perf_counter()
    try:
        with urlopen(req, timeout=timeout) as response:
            receipt["status"] = response.status
            receipt["final_url"] = response.url
            body = response.read()
            receipt["response_sha256"] = hashlib.sha256(body).hexdigest()
            receipt["passed"] = response.status == 200 and response.url == base + path
            if "application/json" in response.headers.get("Content-Type", ""):
                data = json.loads(body)
            else:
                data = body.decode("utf-8")
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        receipt.update(passed=False, error=str(exc))
        if isinstance(exc, HTTPError):
            receipt["status"] = exc.code
        data = None
    receipt["elapsed_ms"] = round((time.perf_counter() - start) * 1000, 2)
    return receipt, data


def validate_case(family, name, data):
    if family == "relational":
        if name == "lossy_decomposition":
            return (data["chase"]["is_implied"] is False
                    and data["chase"]["spurious_tuple_witness"] is not None)
        return data["chase"]["is_implied"] is True and bool(data["candidate_keys"])
    if family == "bqnf":
        north = data["final_cache"]["North"]
        return north["total_sales"] == 280 and north["sale_count"] == 4
    if family == "compiler":
        return (data["sqlite_verification"]["verified"] is True
                and "CREATE TRIGGER" in data["sqlite_ddl"]["before_insert_trigger_sql"]
                and bool(data["synthesized_counterexamples"]))
    return (data["admitted"] is True
            and data["token_accounting"]["token_conservation_commutes"] is True
            and data["loss_ledger_integrity_verified"] is True)


def run(base, workers=1, repeats=1, timeout=30):
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": base, "workers": workers, "repeats": repeats,
        "tls_certificate_validation": "enabled" if base.startswith("https:") else "not applicable (loopback)",
        "checks": [],
        "scope": "HTTP and semantic smoke only; deployment commit and browser UX require separate verification.",
    }
    checks = report["checks"]
    health, data = request(base, "/healthz", timeout=timeout)
    health["passed"] &= isinstance(data, dict) and data.get("status") == "ok" and data.get("service") == "smplxnf-studio"
    checks.append(health)
    if not health["passed"]:
        report.update(passed=False, remaining_checks="skipped: health check failed")
        return report
    for path, marker in (("/", "Simplex-NF Studio"), ("/static/app.js", "/api/"), ("/static/style.css", "{")):
        receipt, data = request(base, path, timeout=timeout)
        receipt["passed"] &= isinstance(data, str) and marker in data
        checks.append(receipt)
    receipt, presets = request(base, "/api/presets", timeout=timeout)
    receipt["passed"] &= isinstance(presets, dict) and all(
        isinstance(presets.get(family), dict) and name in presets[family]
        for family, name, _ in CASES
    )
    checks.append(receipt)
    if not receipt["passed"]:
        report.update(passed=False, remaining_checks="skipped: preset catalog invalid")
        return report

    def exercise(case):
        family, name, path = case
        receipt, data = request(base, path, presets[family][name], timeout)
        receipt["preset"] = name
        try:
            receipt["passed"] &= validate_case(family, name, data)
        except (KeyError, TypeError, ValueError) as exc:
            receipt.update(passed=False, error="Unexpected response schema: " + str(exc))
        return receipt

    with ThreadPoolExecutor(max_workers=workers) as pool:
        checks.extend(pool.map(exercise, CASES * repeats))
    report["passed"] = all(check["passed"] for check in checks)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url")
    parser.add_argument("--workers", type=int, choices=range(1, 5), default=1)
    parser.add_argument("--repeats", type=int, choices=range(1, 11), default=1)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    url = urlsplit(base)
    if (url.scheme not in ("http", "https") or not url.hostname or url.username or url.password
            or url.query or url.fragment or url.path
            or (url.scheme == "http" and url.hostname not in ("localhost", "127.0.0.1", "::1"))):
        parser.error("Use an HTTPS origin (or an HTTP loopback origin), without credentials, path, or query.")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    report = run(base, args.workers, args.repeats, args.timeout)
    serialized = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
