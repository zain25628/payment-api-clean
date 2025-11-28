# Incoming SMS Router

يوفّر هذا الـ Router نقطة دخول واحدة لاستقبال رسائل الـ SMS بعد معالجتها من تطبيق الموبايل / Tasker.

## `POST /incoming-sms/`

- **الـ Body**: `IncomingSmsCreate`
  - يحتوي على `channel_api_key`, `raw_message`, والحقول الاختيارية الأخرى (`amount`, `currency`, `txn_id`, `payer_phone`, `receiver_phone`, `timestamp`).
- **الاستعمال**:
  - يُستدعى من تطبيق الموبايل أو Tasker عند وصول SMS جديدة.
  - يبحث النظام عن `Channel` باستخدام `channel_api_key`، ويربط الرسالة بالشركة والقناة (وأحيانًا بمحفظة).
- **الاستجابة**: `IncomingSmsStored`
  - `payment_id`: رقم العملية التي تم إنشاؤها في جدول `payments`.
  - `status`: الحالة الحالية (عادةً `"new"` عند الإنشاء).

أخطاء محتملة:

- `400 Bad Request` مع `{"detail": "Invalid channel_api_key"}` إذا كان المفتاح غير صالح أو لا توجد قناة مرتبطة به.
