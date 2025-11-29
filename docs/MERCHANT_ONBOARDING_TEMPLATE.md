# Merchant Onboarding Guide

> This document is a generic template for merchants integrating with the Payment Gateway.
> Fill the placeholders with the values provided in your Admin Dashboard or using the
> `generate_onboarding_pdf.py` helper which replaces the placeholders automatically.

---

## {{MERCHANT_NAME}}

**Environment:** `{{ENVIRONMENT}}`

---

## Credentials & Environment

### API key

Keep this key secret. Store it in an environment variable (for example: `MERCHANT_API_KEY`).

```
{{API_KEY}}
```

### Base URL

Use this base URL to call the merchant API (replace `{{BASE_URL}}` when running in a different environment):

```
{{BASE_URL}}
```

---

## Quick checklist

1) Plug the API key into your server environment (e.g. `MERCHANT_API_KEY`).
2) Call `POST {{BASE_URL}}/wallets/request` to obtain a payment destination for an order.
3) Display instructions to the customer and wait for payment to arrive.
4) Optionally call `POST {{BASE_URL}}/payments/check` and then `POST {{BASE_URL}}/payments/confirm`.

If `{{ENVIRONMENT}}` is not `production`, this document is intended for development/staging purposes only.

---

## JavaScript (Node / backend) example

```js
const BASE_URL = process.env.PAYMENT_GATEWAY_BASE_URL || "{{BASE_URL}}";
const MERCHANT_API_KEY = process.env.MERCHANT_API_KEY || "{{API_KEY}}";

async function requestWallet() {
  const res = await fetch(`${BASE_URL}/wallets/request`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": MERCHANT_API_KEY,
    },
    body: JSON.stringify({
      amount: 100,
      currency: "AED",
      txn_id: "ORDER-123",
      payer_phone: "+971500000000",
    }),
  });

  const data = await res.json();
  console.log("Wallet request result:", data);
}

requestWallet().catch(console.error);
```

## Python (requests) example

```py
import os
import requests

BASE_URL = os.getenv("PAYMENT_GATEWAY_BASE_URL", "{{BASE_URL}}")
API_KEY = os.getenv("MERCHANT_API_KEY", "{{API_KEY}}")

resp = requests.post(
    f"{BASE_URL}/wallets/request",
    headers={"X-API-Key": API_KEY},
    json={
        "amount": 100,
        "currency": "AED",
        "txn_id": "ORDER-123",
        "payer_phone": "+971500000000",
    },
)
print(resp.status_code, resp.json())
```

---

## Notes

- This file is a template — it intentionally contains placeholders (the `{{...}}` tokens).
- Use `generate_onboarding_pdf.py` to substitute the placeholders and emit a PDF.


---

## 1. Overview

Welcome! This guide explains how to integrate your system with the Payment Gateway
using a simple, step-by-step flow:

1. Request a wallet / payment destination.
2. Receive a payment from your customer.
3. Let the gateway match the payment.
4. (Optionally) Confirm the payment and mark it as used.

You will mainly talk to the **public merchant API** using your **merchant API key**.

---

## 2. Credentials & Environment

### 2.1. API key

Your merchant API key is visible in the Admin Dashboard under **Companies → Edit Company**.

- Keep this key **secret**.
- Store it in an environment variable (for example: `MERCHANT_API_KEY`).
- Do **not** hard-code it in your frontend code shipped to browsers.

Example (.env):

```env
MERCHANT_API_KEY=<YOUR_MERCHANT_API_KEY>
PAYMENT_GATEWAY_BASE_URL=<BASE_URL>
```

### 2.2. Base URL
You will call the API using a base URL. Typical examples:

Sandbox / Dev: https://sandbox.your-gateway.com

Production: https://api.your-gateway.com

In local development (if you run the gateway yourself):

http://localhost:8000

We will refer to this as <BASE_URL> in the rest of this document.

## 3. Core Flow

### Step 1 – Request a wallet
You first request a wallet / payment destination for a specific order.

**Endpoint**

POST /wallets/request

**Headers**

X-API-Key: <YOUR_MERCHANT_API_KEY>

Content-Type: application/json

**Request body (example)**

```json
{
  "amount": 10,
  "currency": "AED",
  "txn_id": "ORDER-123",
  "payer_phone": "+971500000000"
}
```

**Response (simplified example)**

```json
{
  "wallet_identifier": "WALLET-DEV-001",
  "wallet_label": "Dev Test Wallet",
  "channel_id": 1,
  "channel_api_key": "********",
  "wallet_id": 1
}
```

You typically use this response to show payment instructions to your customer
(e.g. which account / wallet to pay to).

### Step 2 – Customer pays
This step is done by your customer through their banking / wallet app.
From the gateway’s perspective, payments arrive asynchronously and will be linked later.

You don’t need to call any API in this step.

### Step 3 – Check payment (optional from your backend)
You can ask the gateway to check if a payment matching your order has been seen.

**Endpoint**

POST /payments/check

**Headers**

X-API-Key: <YOUR_MERCHANT_API_KEY>

Content-Type: application/json

**Request body (example)**

```json
{
  "order_id": "ORDER-123",
  "expected_amount": 10,
  "txn_id": "ORDER-123",
  "payer_phone": "+971500000000"
}
```

**Response (simplified)**

```json
{
  "found": true,
  "match": true,
  "reason": null,
  "confirm_token": "SOME-CONFIRM-TOKEN",
  "order_id": "ORDER-123",
  "payment": {
    "payment_id": 6,
    "txn_id": "ORDER-123",
    "amount": 10,
    "currency": "AED",
    "created_at": "2025-11-29T12:24:02.710524"
  }
}
```

If found and match are true, you may confirm the payment (next step).

Keep confirm_token safe; it’s required to mark the payment as used.

### Step 4 – Confirm payment (mark as used)
Once you are satisfied that the payment is genuine and should be consumed,
you can mark it as used.

**Endpoint**

POST /payments/confirm

**Headers**

X-API-Key: <YOUR_MERCHANT_API_KEY>

Content-Type: application/json

**Request body**

```json
{
  "payment_id": 6,
  "confirm_token": "SOME-CONFIRM-TOKEN"
}
```

**Response**

```json
{
  "success": true,
  "already_used": false,
  "payment_id": 6,
  "status": "used"
}
```

Subsequent checks for the same payment will usually show that it has been used.

## 4. Code Examples

### 4.1. JavaScript (Node / backend)

```js
const BASE_URL = process.env.PAYMENT_GATEWAY_BASE_URL || "<BASE_URL>";
const MERCHANT_API_KEY = process.env.MERCHANT_API_KEY || "<YOUR_MERCHANT_API_KEY>";

async function requestWallet() {
  const res = await fetch(`${BASE_URL}/wallets/request`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": MERCHANT_API_KEY,
    },
    body: JSON.stringify({
      amount: 10,
      currency: "AED",
      txn_id: "ORDER-123",
      payer_phone: "+971500000000",
    }),
  });

  const data = await res.json();
  console.log("Wallet request result:", data);
}

requestWallet().catch(console.error);
```

### 4.2. Python

```python
import os
import requests

BASE_URL = os.getenv("PAYMENT_GATEWAY_BASE_URL", "<BASE_URL>")
MERCHANT_API_KEY = os.getenv("MERCHANT_API_KEY", "<YOUR_MERCHANT_API_KEY>")

payload = {
    "amount": 10,
    "currency": "AED",
    "txn_id": "ORDER-123",
    "payer_phone": "+971500000000",
}

resp = requests.post(
    f"{BASE_URL}/wallets/request",
    json=payload,
    headers={"X-API-Key": MERCHANT_API_KEY},
    timeout=10,
)
print(resp.status_code, resp.json())
```

### 4.3. curl (for quick testing)

```bash
curl -X POST "<BASE_URL>/wallets/request" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <YOUR_MERCHANT_API_KEY>" \
  -d '{
    "amount": 10,
    "currency": "AED",
    "txn_id": "ORDER-123",
    "payer_phone": "+971500000000"
  }'
```

## 5. Admin Tools (optional)
The Admin Dashboard provides:

- Payments — Check & Confirm: Check if a payment has been seen and confirm it.
- Payments history: Search and review payments by amount, status, date, or transaction ID.

These tools are primarily for operations and support, not for your public integration.

## 6. Support
If you have any questions about this integration or need help debugging a payment:

Contact the support team with:

- Your company name.
- The transaction ID (txn_id) and amount.
- Approximate payment time and currency.

We’re happy to help you get your integration running smoothly.
