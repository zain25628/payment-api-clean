# PaymentService

تقدّم هذه الخدمة منطق التحقق والتأكيد لعمليات الدفع المخزّنة في جدول `payments`.

## check_payment_for_company(db, company_id, req: PaymentCheckRequest) -> PaymentCheckResponse

- تبحث عن عملية دفع تابعة لشركة معيّنة (`company_id`).
- تطبّق حدًا زمنيًا (`max_age_minutes`, افتراضيًا 30 دقيقة) على `created_at`.
- تتجاهل العمليات ذات الحالة `used`.
- إذا تم تمرير `txn_id` في الطلب، تُفلتر النتائج بناءً عليه.
- الحالات المحتملة:
  - لا توجد عملية:
    - `found=false`, `match=false`
  - توجد عملية لكن `amount` لا يطابق `expected_amount`:
    - `found=true`, `match=false`, `reason="amount_mismatch"`
  - تطابق كامل:
    - تُحدّث العملية إلى:
      - `status="pending_confirmation"`
      - `order_id` من الطلب
      - توليد `confirm_token` وتخزينه في `payment.confirm_token`
    - تُعيد `PaymentCheckResponse` مع:
      - `found=true`, `match=true`, `confirm_token=<token>`, و `payment` من نوع `PaymentMatchInfo`.

## confirm_payment_for_company(db, company_id, req: PaymentConfirmRequest) -> PaymentConfirmResponse

- تبحث عن عملية دفع بـ:
  - `id = payment_id`
  - `company_id = company_id`
- تتحقق من تطابق `confirm_token`.
- إذا لم توجد العملية أو لم يطابق التوكن:
  - ترفع `ValueError("Invalid payment_id or confirm_token")`.
- إذا كانت العملية بحالة `used` مسبقًا:
  - تُعيد ردًا Idempotent:
    - `success=true`, `already_used=true`, `status="used"`.
- إذا كانت العملية بحالة `pending_confirmation` (أو حالة غير `used`) مع توكن صحيح:
  - تُحدّث:
    - `status="used"`
    - `used_at` إلى الوقت الحالي.
  - تُعيد:
    - `success=true`, `already_used=false`, `status="used"`.
# Payment Service

## Responsibility

The Payment Service contains domain logic for creating and managing `Payment` records. It is responsible for:

- Creating `Payment` records from normalized SMS payloads.
- Attempting to match incoming payments to orders/transactions.
- Marking payments as `pending_confirmation` and generating confirmation tokens.
- Confirming payment usage and triggering wallet usage updates.

## Key Functions

- `create_payment_from_sms(db, payment_data)`
  - Description: Construct a `Payment` model from `payment_data`, persist it, and return the refreshed object.
  - Important inputs: `db: Session`, `payment_data: dict` (fields such as `company_id`, `channel_id`, `amount`, `payer_phone`, `receiver_phone`, `raw_message`).
  - Output: `Payment` instance.

- `match_payment_for_order(db, company_id, amount, currency, payer_phone=None, max_age_minutes=None)`
  - Description: Query recent payments for the company and attempt to find the most-recent candidate that is `new` or `pending_confirmation` and matches currency (optionally narrowed by payer phone and age).
  - Important inputs: `db: Session`, `company_id: int`, `amount: float`, `currency: str`, optional `payer_phone`, `max_age_minutes` to limit age.
  - Output: `Payment` or `None`.

- `mark_payment_pending_confirmation(db, payment)`
  - Description: Mutates `payment` to set it to `pending_confirmation`, generates and stores a `confirm_token`, persists and returns the refreshed `Payment`.
  - Important inputs: `db: Session`, `payment: Payment`.
  - Output: `Payment`.

- `confirm_payment_usage(db, payment)`
  - Description: Marks the `payment` as `used`, sets `used_at`, persists, and if a `wallet_id` exists calls `wallet_service.update_wallet_usage(db, wallet_id, amount)` to adjust wallet usage.
  - Important inputs: `db: Session`, `payment: Payment`.
  - Output: `Payment`.

## Interaction with Other Components

- `models.Payment`: Primary data model persisted by this service.
- `wallet_service.update_wallet_usage`: Invoked when a confirmed payment is associated with a wallet; the implementation of wallet usage accounting lives in `wallet_service`.
- `routers/payments`: Exposes endpoints that call into this service (matching, pending confirmation, confirm usage).

## Notes

- This module intentionally keeps behavior minimal and delegates persistence to SQLAlchemy sessions.
- Tests targeting this service should focus on business logic and can stub or fake the `db` session to avoid a real database.
