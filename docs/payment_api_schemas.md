# Payment API Schemas

This document describes the Pydantic schemas used by the `/payments/check` and
`/payments/confirm` endpoints.

1) PaymentCheckRequest

```json
{
  "order_id": "ORD-1",
  "expected_amount": 150,
  "txn_id": "TXN123",
  "max_age_minutes": 30
}
```

Fields:
- `order_id` (string) – the client order identifier to look up.
- `expected_amount` (int) – expected payment amount (whole units).
- `txn_id` (optional) – provider transaction id, if available.
- `max_age_minutes` (optional, default 30) – maximum age for matched payments.

2) PaymentCheckResponse

When the service checks for a matching payment it responds with a `PaymentCheckResponse`.

Success / match example:

```json
{
  "found": true,
  "match": true,
  "confirm_token": "token-abc",
  "order_id": "ORD-1",
  "payment": {
    "payment_id": 123,
    "txn_id": "TXN123",
    "amount": 150,
    "currency": "AED",
    "created_at": "2025-11-26T12:34:56Z"
  }
}
```

Mismatch example (amount mismatch):

```json
{
  "found": true,
  "match": false,
  "reason": "amount_mismatch",
  "payment": { ... }
}
```

Not found example:

```json
{
  "found": false,
  "match": false
}
```

3) PaymentConfirmRequest

```json
{
  "payment_id": 123,
  "confirm_token": "token-abc"
}
```

4) PaymentConfirmResponse

Successful confirmation (first time):

```json
{
  "success": true,
  "already_used": false,
  "payment_id": 123,
  "status": "used"
}
```

Idempotent repeat of same confirm token:

```json
{
  "success": true,
  "already_used": true,
  "payment_id": 123,
  "status": "used"
}
```
