"""Simple merchant demo script (development only)

This script acts like a merchant client calling the local API at http://localhost:8000.
It does NOT modify the database directly — it only issues HTTP requests using the
`MERCHANT_API_KEY` environment variable. Intended for local testing and examples
only; do NOT copy verbatim into production code.
"""

import os
import sys
import json
import requests

MERCHANT_API_KEY = os.getenv("MERCHANT_API_KEY")
if not MERCHANT_API_KEY:
    print("Error: MERCHANT_API_KEY environment variable is not set. Set it and retry.")
    sys.exit(1)

# Allow overriding the base URL via env for flexibility during testing
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Standard headers sent with each request (ensure header name is exactly X-API-Key)
HEADERS = {"X-API-Key": MERCHANT_API_KEY, "Content-Type": "application/json"}


def check_health():
    """Call GET /health and print status and body."""
    try:
        r = requests.get(f"{BASE_URL}/health", headers=HEADERS, timeout=5)
        print(f"Health check: status={r.status_code}")
        print(r.text)
    except Exception as exc:
        print("Health check failed:", exc)


def request_wallet():
    """POST /wallets/request with a sample payload. Return parsed JSON or None."""
    payload = {"amount": 100, "currency": "AED", "order_id": "order-1234"}
    try:
        r = requests.post(f"{BASE_URL}/wallets/request", headers=HEADERS, json=payload, timeout=10)
        print(f"request_wallet: status={r.status_code}")
        try:
            data = r.json()
            print("Response JSON:")
            print(json.dumps(data, indent=2))
            return data
        except ValueError:
            print("Non-JSON response:", r.text)
            return None
    except Exception as exc:
        print("request_wallet failed:", exc)
        return None


def check_payment(order_id, expected_amount):
    """POST /payments/check with order_id and expected_amount and return parsed JSON."""
    payload = {"order_id": order_id, "expected_amount": expected_amount}
    try:
        r = requests.post(f"{BASE_URL}/payments/check", headers=HEADERS, json=payload, timeout=10)
        print(f"check_payment: status={r.status_code}")
        try:
            return r.json()
        except ValueError:
            print("Non-JSON response:", r.text)
            return None
    except Exception as exc:
        print("check_payment failed:", exc)
        return None


if __name__ == "__main__":
    print("merchant_demo: using MERCHANT_API_KEY from environment")

    # 1) health
    check_health()

    # 2) request wallet
    wallet_resp = request_wallet()

    # We used order_id "order-1234" in request_wallet above. Use same for check.
    order_id = "order-1234"

    # 3) check payment
    check_resp = check_payment(order_id, 100)
    if check_resp is None:
        print("check_payment returned no data")
    else:
        # print a short summary
        found = check_resp.get("found") if isinstance(check_resp, dict) else None
        confirm_token = check_resp.get("confirm_token") if isinstance(check_resp, dict) else None
        payment = check_resp.get("payment") if isinstance(check_resp, dict) else None
        if found:
            print("Payment matched. Payment info:")
            print(json.dumps(payment, indent=2) if payment else payment)
            if confirm_token:
                print(f"confirm_token: {confirm_token}")
        else:
            print("No matching payment found. Full response:")
            print(json.dumps(check_resp, indent=2))
