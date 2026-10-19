#!/usr/bin/env python3
"""Demo traffic generator: imitates a "day's worth" of refund requests right after deployment.

  scripts/simulate_traffic.py http://127.0.0.1:8100 --count 120

Client mix (like the real service): web 60%, mobile app 3.3 15%, mobile app 3.1 (legacy) 25%.
Mobile app 3.1 does not send the refund reason (reason).
"""

import argparse
import json
import random
import urllib.error
import urllib.request

CLIENTS = [
    ("ShopFlowWeb/2.4", 0.60, True),
    ("ShopFlowMobile/3.3", 0.15, True),
    ("ShopFlowMobile/3.1", 0.25, False),
]
REASONS = [
    "Wrong size",
    "Change of mind",
    "Delivery delay",
    "Defective product",
    "Color differs from photo",
    "Duplicate order",
]


def call(base, method, path, body=None, ua="sim", headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        base + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "User-Agent": ua, **(headers or {})},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            return res.status, json.loads(res.read() or b"{}")
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read() or b"{}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url")
    parser.add_argument("--count", type=int, default=120)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    rnd = random.Random(args.seed)
    _, customers = call(args.base_url, "GET", "/customers")
    summary: dict[str, int] = {}
    for _ in range(args.count):
        ua, _, sends_reason = rnd.choices(CLIENTS, weights=[c[1] for c in CLIENTS])[0]
        customer = rnd.choice(customers)
        amount = rnd.choice(
            [29_000, 59_000, 89_000, 129_000, 349_000, 790_000, 1_000_000, 1_350_000, 2_100_000]
        )
        days_ago = rnd.choice([1, 3, 7, 14, 21, 29, 33, 40, 45, 52, 58, 64])
        from datetime import date, timedelta

        ordered_at = (date.today() - timedelta(days=days_ago)).isoformat()
        status, order = call(
            args.base_url,
            "POST",
            "/orders",
            {
                "customer_id": customer["id"],
                "total_amount": amount,
                "status": "DELIVERED",
                "ordered_at": ordered_at,
            },
            ua=ua,
        )
        if status != 201:
            continue
        body = {"amount": amount}
        if sends_reason:
            body["reason"] = rnd.choice(REASONS)
        status, result = call(args.base_url, "POST", f"/orders/{order['id']}/refund", body, ua=ua)
        key = f"{status}:{result.get('status') or result.get('detail', {}).get('code')}"
        summary[key] = summary.get(key, 0) + 1
    print(f"Simulation complete ({args.count} requests):")
    for key, value in sorted(summary.items(), key=lambda kv: -kv[1]):
        print(f"  {key:<28} {value}")


if __name__ == "__main__":
    main()
