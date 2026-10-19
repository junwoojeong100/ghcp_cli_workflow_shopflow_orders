#!/usr/bin/env python3
"""Post-deployment smoke test: checks that the key paths are alive."""

import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8101"
HEADERS = {"Content-Type": "application/json", "User-Agent": "smoke-test/1.0"}


def call(method: str, path: str, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, method=method, headers={**HEADERS, **(headers or {})}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            return res.status, json.loads(res.read() or b"{}")
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read() or b"{}")


def check(name: str, condition: bool, detail: str = "") -> bool:
    print(f"  {'✔' if condition else '✘'} {name}{(' — ' + detail) if detail else ''}")
    return condition


def main() -> int:
    print("Smoke test")
    results = []
    status, body = call("GET", "/health")
    results.append(
        check(
            "GET /health", status == 200 and body.get("status") == "ok", f"v{body.get('version')}"
        )
    )
    status, body = call("GET", "/customers")
    results.append(
        check("GET /customers", status == 200 and len(body) > 0, f"{len(body)} customers")
    )
    status, body = call("GET", "/customers/11/orders")
    results.append(check("GET /customers/11/orders", status == 200 and len(body) > 0))
    status, _ = call(
        "GET", "/admin/refunds?status=REQUESTED", headers={"X-Admin-Token": "demo-admin-token"}
    )
    results.append(check("GET /admin/refunds (admin auth)", status == 200))
    status, order = call("POST", "/orders", {"customer_id": 11, "total_amount": 1000})
    results.append(check("POST /orders (smoke-test order)", status == 201))
    if status == 201:
        status, refund = call(
            "POST", f"/orders/{order['id']}/refund", {"amount": 1000, "reason": "Smoke test"}
        )
        results.append(
            check("POST /orders/{id}/refund", status == 201, f"status {refund.get('status')}")
        )
    ok = all(results)
    print(
        ("✔ Smoke test passed" if ok else "✘ Smoke test failed")
        + f" ({sum(results)}/{len(results)})"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
