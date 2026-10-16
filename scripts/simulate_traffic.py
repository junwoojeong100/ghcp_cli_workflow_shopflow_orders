#!/usr/bin/env python3
"""시연용 트래픽 생성기: 배포 직후 '하루치' 환불 요청을 흉내 낸다.

  scripts/simulate_traffic.py http://127.0.0.1:8100 --count 120

클라이언트 구성(실제 서비스와 비슷하게): 웹 60%, 모바일 앱 3.3 15%, 모바일 앱 3.1(구버전) 25%.
모바일 앱 3.1 은 환불 사유(reason)를 보내지 않는다.
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
REASONS = ["사이즈가 맞지 않음", "단순 변심", "배송 지연", "상품 불량", "색상이 사진과 다름", "중복 주문"]


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
        amount = rnd.choice([29_000, 59_000, 89_000, 129_000, 349_000, 790_000, 1_000_000, 1_350_000, 2_100_000])
        days_ago = rnd.choice([1, 3, 7, 14, 21, 29, 33, 40, 45, 52, 58, 64])
        from datetime import date, timedelta

        ordered_at = (date.today() - timedelta(days=days_ago)).isoformat()
        status, order = call(
            args.base_url, "POST", "/orders",
            {"customer_id": customer["id"], "total_amount": amount, "status": "DELIVERED", "ordered_at": ordered_at},
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
    print(f"시뮬레이션 완료 ({args.count}건): ")
    for key, value in sorted(summary.items(), key=lambda kv: -kv[1]):
        print(f"  {key:<28} {value}")


if __name__ == "__main__":
    main()
