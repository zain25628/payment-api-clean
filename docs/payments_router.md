# Payments Router

يوفر هذا الـ Router واجهتين للتحقق من عمليات الدفع وتأكيدها:

## `POST /payments/check`

- **الهيدر**: `X-API-Key` لمصادقة الشركة (يتم حله عبر `get_current_company`).
- **الـ Body**: `PaymentCheckRequest`:

```json
{
  "order_id": "ORD-1",
  "expected_amount": 150,
  "txn_id": "TXN123",
  "max_age_minutes": 30
}
```

السلوك:

يبحث عن عملية دفع (Payment) تابعة للشركة الحالية (من الـ API Key).

يطبّق حدًا زمنيًا `max_age_minutes` على `created_at`.

يتجاهل العمليات ذات الحالة `used`.

في حال:

- عدم وجود عملية مطابقة:

  `found=false, match=false`.

- وجود عملية لكن المبلغ مختلف:

  `found=true, match=false, reason="amount_mismatch"`.

- تطابق كامل:

  يحدّث العملية إلى `pending_confirmation`.
  يعيّن `order_id`.
  يولّد `confirm_token`.

  يعيد `PaymentCheckResponse` مع الحقول الخاصة بالمطابقة.

## `POST /payments/confirm`

**الهيدر**: `X-API-Key` لنفس الشركة المالكة للعملية.

**الـ Body**: `PaymentConfirmRequest`:

```json
{
  "payment_id": 123,
  "confirm_token": "token-abc"
}
```

السلوك:

يتحقق من أن العملية تتبع لنفس الشركة (`company_id`) وأن `confirm_token` يطابق القيمة المخزّنة.

في حال خطأ:

يعيد `400 Bad Request` مع `{ "detail": "Invalid payment_id or confirm_token" }`.

في حال نجاح أول تأكيد:

- يعيد `PaymentConfirmResponse` مع:

  `success=true`

  `already_used=false`

  `status="used"`.

في حال استدعاء تأكيد لعملية سبق وأن أصبحت `used` بنفس التوكن:

- يعيد ردًا Idempotent:

  `success=true`

  `already_used=true`

  `status="used"`.
