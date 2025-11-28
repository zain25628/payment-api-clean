# Merchant Quickstart

Overview
-	Merchants receive an API key from the Admin Panel. Include this API key in every request using the `X-API-Key` HTTP header. The server uses the `X-API-Key` header to resolve the calling Company (via the `get_current_company` dependency).

Authentication
-	Example: a simple health check request showing how to provide the API key header.

curl example:

```bash
curl -v \
  -H "X-API-Key: <YOUR_API_KEY>" \
  http://localhost:8000/health
```

Basic Payment Flow

These examples assume a local server running at `http://localhost:8000` and that you include your `X-API-Key` header with each request.

Step 1 — Request a Wallet
-	Endpoint: `POST /wallets/request`
-	Request model (Pydantic): `WalletRequestPayload` with fields:
  - `amount` (integer, required)
  - `currency` (string, default "AED")
  - `order_id` (optional string)
  - `provider_code` (optional string)

Example curl:

```bash
curl -X POST http://localhost:8000/wallets/request \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <YOUR_API_KEY>" \
  -d '{
    "amount": 100,
    "currency": "AED",
    "order_id": "order-1234"
  }'
```

A successful response returns a JSON object containing fields such as `wallet_id`, `wallet_identifier`, `wallet_label`, `channel_api_key`, and `channel_id`.

Step 2 — Check for a Matching Payment
-	Endpoint: `POST /payments/check`
-	Request model (Pydantic): `PaymentCheckRequest` with fields:
  - `order_id` (string, required)
  - `expected_amount` (integer, required)
  - `txn_id` (optional string)
  - `max_age_minutes` (optional integer, default 30)

Example curl:

```bash
curl -X POST http://localhost:8000/payments/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <YOUR_API_KEY>" \
  -d '{
    "order_id": "order-1234",
    "expected_amount": 100
  }'
```

The response indicates whether a payment was found and whether it matches the expected amount. If a match is found, the response may include a `payment_id` and a `confirm_token` you will use in the next step.

Step 3 — Confirm a Payment
-	Endpoint: `POST /payments/confirm`
-	Request model (Pydantic): `PaymentConfirmRequest` with fields:
  - `payment_id` (integer, required)
  - `confirm_token` (string, required)

Example curl:

```bash
curl -X POST http://localhost:8000/payments/confirm \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <YOUR_API_KEY>" \
  -d '{
    "payment_id": 42,
    "confirm_token": "<CONFIRM_TOKEN_FROM_CHECK_RESPONSE>"
  }'
```

Notes
-	These examples are for local development and testing: `http://localhost:8000`.
-	Always keep your API key secret. Store it in a secure environment variable on your server (e.g. `MERCHANT_API_KEY`) and never embed it in client-side code or public repositories.
-	The server resolves the calling company using the `X-API-Key` header via the `get_current_company` dependency.

If you need more detailed examples (language SDK snippets, webhook examples, or error handling patterns), ask and we can extend this quickstart with concrete code samples.

## Local Testing Checklist (for Zain)

- Start the backend locally:

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Open the Admin UI, create a company, and copy its API key.

- In PowerShell set the key into an environment variable (paste the key between the quotes):

```powershell
$env:MERCHANT_API_KEY = "<PASTE_API_KEY_HERE>"
```

- Re-run the three example requests from this file but replace `<YOUR_API_KEY>` with `$env:MERCHANT_API_KEY`. Example (health):

```powershell
curl -v -H "X-API-Key: $env:MERCHANT_API_KEY" http://localhost:8000/health
```

Example (wallet request):

```powershell
curl -X POST http://localhost:8000/wallets/request \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $env:MERCHANT_API_KEY" \
  -d '{"amount":100, "currency":"AED", "order_id":"order-1234"}'
```

Example (payments check):

```powershell
curl -X POST http://localhost:8000/payments/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $env:MERCHANT_API_KEY" \
  -d '{"order_id":"order-1234", "expected_amount":100}'
```

- If any request returns an unexpected status (not `200`/`201`), copy the response JSON and the HTTP status code and paste them here for debugging.

- Do not store the API key in frontend code. Use an environment variable on your server (e.g. `MERCHANT_API_KEY`) and keep it secret.
