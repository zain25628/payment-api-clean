# Project README

Current version: **0.1.0**

## تشغيل بيئة التطوير على ويندوز (زر واحد)

الطريقة المدعومة لبدء كامل بيئة التطوير (PostgreSQL + migrations + seed + API) هي تشغيل السكрипت `dev_start_stack.ps1` من PowerShell داخل مجلد المشروع.

نفّذ الأوامر التالية بالضبط في نافذة PowerShell:

```powershell
cd "C:\Users\zaink\OneDrive\Desktop\api"
.\venv\Scripts\Activate.ps1
.\dev_start_stack.ps1
```

ماذا يفعل السكрипت:
- يشغّل PostgreSQL باستخدام `pg_ctl` (وليس خدمة ويندوز)
- ينفّذ هجرات Alembic: `alembic upgrade head`
- يشغّل الـ seeder التطويري: `python -m app.seed_dev_data` (يضمن وجود شركة تجريبية، قناة، ومحفظة اختبار)
- يشغّل الخادم: `uvicorn app.main:app --reload` على `http://127.0.0.1:8000`

> ملاحظة: قد تحتاج لتشغيل PowerShell بامتيازات المدير (Run as Administrator) إن تطلب تشغيل `pg_ctl` صلاحيات أعلى للوصول إلى دليل البيانات.

### اختبار سريع

- افتح المتصفح وتوجّه إلى:

```
http://127.0.0.1:8000/docs
```

- مثال لاستدعاء endpoint للحصول على محفظة متاحة (`POST /wallets/request`):

Headers:

```
X-API-Key: test-key-123
Content-Type: application/json
```

JSON body:

```json
{
  "amount": 25.0
}
```

الاستجابة المتوقعة في حالة وجود محفظة:

```json
{
  "wallet_id": 45,
  "wallet_identifier": "+15557654321",
  "channel_id": 3
}
```

### Multiple payment buttons per provider

You can implement multiple payment buttons (one per payment provider) using the same `MERCHANT_API_KEY` for all buttons. Each button sends the same `/wallets/request` request but with an optional field `"preferred_payment_method": "slug"` (e.g., `"eand_money"`, `"stripe"`, `"ui-test"`).

**How it works:**
- If `preferred_payment_method` is provided, the system will **only** select wallets associated with that specific provider.
- If no matching wallet is found, the endpoint returns `404` with the message: `"No wallet available for this company / amount"`.
- If `preferred_payment_method` is omitted, the system selects from all available wallets (default behavior).

**Example JSON request:**

```json
{
  "amount": 100,
  "currency": "AED",
  "txn_id": "ORDER-123",
  "payer_phone": "+971500000000",
  "preferred_payment_method": "eand_money"
}
```

**Example JavaScript implementation:**

```javascript
function requestWallet(preferredPaymentMethod) {
  return fetch("http://localhost:8000/wallets/request", {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': '<YOUR_MERCHANT_API_KEY>',
    },
    body: JSON.stringify({
      amount: 100,
      currency: 'AED',
      txn_id: 'ORDER-123',
      payer_phone: '+971500000000',
      preferred_payment_method: preferredPaymentMethod,
    }),
  }).then(r => r.json());
}

// Usage with buttons:
// <button onclick="requestWallet('eand_money')">Pay with e& money</button>
// <button onclick="requestWallet('stripe')">Pay with Stripe</button>
// <button onclick="requestWallet('ui-test')">Pay with UI Test</button>
```

**Use case:** This feature is ideal for checkout pages where you want to display separate payment buttons for different providers (e.g., "Pay with e& money", "Pay with Stripe"), while using a single merchant API key.

### Provider-specific endpoints

In addition to using `preferred_payment_method` in the request body, you can also use **provider-specific endpoints** for even cleaner integration:

- **`POST /wallets/request`** — Automatic selection from all available wallets (default behavior)
- **`POST /wallets/request/{provider_code}`** — Strict selection for a specific payment provider only

**Examples:**
```
POST /wallets/request/stripe
POST /wallets/request/eand_money
POST /wallets/request/ui-test
```

**How it works:**
- The `{provider_code}` in the URL path forces wallet selection to that specific provider.
- If no wallet is available for the specified provider, the endpoint returns `404` with `"No wallet available for this company / amount"`.
- The request body is the same as the standard `/wallets/request` endpoint (no need to include `preferred_payment_method` in the JSON).

**Example usage:**
```javascript
// Direct fetch to provider-specific endpoint
fetch("https://your-gateway.example.com/wallets/request/stripe", {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': '<YOUR_MERCHANT_API_KEY>',
  },
  body: JSON.stringify({
    amount: 100,
    currency: 'AED',
    txn_id: 'ORDER-123',
    payer_phone: '+971500000000',
  }),
}).then(r => r.json());
```

**Comparison:**
- **Body-based**: `POST /wallets/request` with `"preferred_payment_method": "stripe"` in JSON
- **Path-based**: `POST /wallets/request/stripe` (cleaner, more RESTful)

Both approaches achieve the same result — choose whichever fits your integration style better.

--------------------------------------------------

If you need the script to run without elevation or using Docker instead, let me know and I can add alternative instructions.
## Project Overview

- This project is a **Payment Gateway API** built with FastAPI.
- Core domain concepts:
  - **Company / Channel**: who is calling the API and through which integration.
  - **Wallet**: account/number used to receive payments with daily usage limits.
  - **Payment**: normalized representation of an incoming payment (e.g. via SMS).
- Key API endpoints:
  - `GET /health`  health check.
  - `POST /incoming-sms`  receive and normalize inbound payment SMS.
  - `POST /wallets/request`  request an available wallet for a given amount.
  - `POST /payments/match` and `POST /payments/{id}/confirm-usage`  payment matching/confirmation flows.

## Project Structure (high level)

```
app/
  routers/         # FastAPI endpoints (health, incoming-sms, wallets, payments)
  services/        # Domain services (payment_service, wallet_service, sms_service)
  repositories/    # Data access (payment_repository, wallet_repository)
  models/          # SQLAlchemy ORM models (Company, Channel, Wallet, Payment)
  db/              # DB base + session
  dependencies/    # Authentication helpers (X-API-Key, channel_api_key)
docs/
  INDEX.md         # Documentation index
  ARCHITECTURE.md  # System architecture overview
  ...              # API and domain-specific docs
tests/
  ...              # Unit tests for routers, services, repositories, deps
```

## Getting Started

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
## Admin panel manual checks

Before changing the admin frontend, run through the manual checklist:

- [Admin panel manual checklist (CompanyForm)](docs/ADMIN_PANEL_MANUAL_CHECKLIST.md)
```

3. Apply database migrations (example):

```bash
alembic upgrade head
```

4. Run the API in development mode:

```bash
uvicorn app.main:app --reload
```

## Quickstart (API & Telegram Bot)

- To run the API locally (development quickstart), see `docs/QUICKSTART_AR.md` for step-by-step instructions.

- To deploy to Production (Docker / systemd / Linux), see `docs/DEPLOY_PRODUCTION.md`.

- To run the Telegram Bot (simple demo over the API, supports `/start` and `/ping`), see `docs/TELEGRAM_BOT_QUICKSTART_AR.md`.

  The Telegram bot is intended as a demo interface on top of the API (not a full production bot).

## Running Tests

To run the full test suite:

```bash
pytest -q
```

## Merchant onboarding PDFs

You can generate a PDF onboarding package for a merchant using the provided
Markdown template and helper script. Example (PowerShell):

```powershell
cd "C:\Users\zaink\OneDrive\Desktop\api"
& .\.venv\Scripts\Activate.ps1

python .\generate_onboarding_pdf.py `
  --merchant-name "UI Test Shop" `
  --api-key "<PASTE-COMPANY-API-KEY>" `
  --base-url "http://localhost:8000" `
  --environment "dev"
```

The template file is `docs/MERCHANT_ONBOARDING_TEMPLATE.md`. The generated PDF
will be written to `docs/<slug>-onboarding-YYYY-MM-DD.pdf` by default.

## Developer utilities

Short pointers for local testing:

- Dev seed script: `docs/dev_seed.md` (creates a sample country, provider, company and channel)
- Manual flow: `docs/manual_flow.md` (example requests for incoming-sms, payments/check and payments/confirm)

> Note: The local SQLite database file `dev.db` is ignored by Git and should not be committed.
> Each developer can safely recreate it locally using `python dev_seed.py`.


## Local end-to-end demo (merchant_demo.py)

You can run a small end-to-end demo against the local dev stack using the seeded dev channel key.

Steps:

1. Start the dev stack (backend + admin):
  - From the project root:
    ```powershell
    .\dev_start_stack.ps1
    ```
  - Backend runs on `http://localhost:8000`
  - Admin frontend (if running) is on `http://localhost:5173/`.

2. Seed the dev database (creates Dev Co, a dev channel, and a dev wallet):
  ```powershell
  cd C:\Users\zaink\OneDrive\Desktop\api
  & .\.venv\Scripts\Activate.ps1
  python dev_seed.py
  ```

Run the merchant demo using the seeded dev channel key:

```powershell
cd C:\Users\zaink\OneDrive\Desktop\api
& .\.venv\Scripts\Activate.ps1
$env:MERCHANT_API_KEY = "dev-channel-key"
python .\examples\merchant_demo.py
```

Expected behavior:

GET /health → 200 OK.

POST /wallets/request → 200 OK with "WALLET-DEV-001" and "Dev Test Wallet".

POST /payments/check → 200 OK with "found": false (no payment created yet in this demo).

### Creating a matching test payment

To have `/payments/check` return `found: true` in the demo:

```powershell
cd C:\Users\zaink\OneDrive\Desktop\api
& .\.venv\Scripts\Activate.ps1
python create_test_payment.py

$env:MERCHANT_API_KEY = "dev-channel-key"
python .\examples\merchant_demo.py
```

`create_test_payment.py` will insert a dev `Payment` for the seeded
`Dev Co` / `dev-channel-key` / `WALLET-DEV-001` so that the demo
`check_payment` call can match it.


## Documentation

* See `docs/INDEX.md` for a list of more detailed documents:

  * API flows
  * Integration scenarios
  * Services and repositories
  * Architecture overview
