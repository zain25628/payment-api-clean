# Manual Payment Flow (End-to-End)

Below is a concise manual flow demonstrating the end-to-end payment processing using the API endpoints. You can follow these steps manually or use the `scripts/dev_seed.py` to populate a development company and channel.

## Create company via /admin/companies

This step can be skipped if you used `dev_seed.py`.

http
```http
POST http://localhost:8000/admin/companies
Content-Type: application/json

{
  "name": "Flow Co",
  "country_code": "UAE",
  "provider_codes": ["eand_money"],
  "telegram_bot_token": null,
  "telegram_default_group_id": null
}
```

The response will include `api_key` and `channels` (each channel contains `channel_api_key`).

## Incoming SMS via /incoming-sms/

Example:

http
```http
POST http://localhost:8000/incoming-sms/
X-API-Key: dev-api-key
Content-Type: application/json

{
  "channel_api_key": "dev-channel-key",
  "raw_message": "تم تحويل 150 درهم",
  "amount": 150,
  "currency": "AED",
  "txn_id": "TXN123",
  "payer_phone": "0500000000",
  "receiver_phone": "0511111111"
}
```

The response typically contains `payment_id` and `status` (likely `new`).

## /payments/check

Example:

http
```http
POST http://localhost:8000/payments/check
X-API-Key: dev-api-key
Content-Type: application/json

{
  "order_id": "ORD-123",
  "expected_amount": 150,
  "txn_id": "TXN123",
  "max_age_minutes": 30
}
```

Expected successful match response includes:

- `found = true`
- `match = true`
- `confirm_token = <token>`
- `payment.payment_id` equals the `payment_id` from incoming-sms response

## /payments/confirm

Example:

http
```http
POST http://localhost:8000/payments/confirm
X-API-Key: dev-api-key
Content-Type: application/json

{
  "payment_id": 1,
  "confirm_token": "token-from-check"
}
```

Notes:
- First call with valid token: `success=true`, `already_used=false`, `status="used"`.
- Second call with same data: `success=true`, `already_used=true`, `status="used"`.
