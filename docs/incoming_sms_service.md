# IncomingSmsService

هذه الخدمة مسؤولة عن استقبال بيانات رسائل الـ SMS (القادمة من تطبيق الموبايل / Tasker) وتخزينها كـ `Payment`.

الدالة الأساسية:

## `store_incoming_sms(db, data: IncomingSmsCreate) -> Payment`

- تبحث عن `Channel` باستخدام `channel_api_key` الموجود في الـ payload.
- تستخدم `channel.company` لتحديد مالك العملية (`company_id`).
- تحاول ربط العملية بمحفظة (`Wallet`) إذا توفّر `receiver_phone` يطابق `wallet_identifier` لنفس الشركة.
- تنشئ سجل `Payment` جديد بالحقل:
  - `amount`, `currency`, `txn_id`, `payer_phone`, `receiver_phone`, `raw_message`.
  - حالة `status` تبقى افتراضيًا `"new"` في هذه المرحلة.
- تعيد كائن `Payment` بعد `commit` و `refresh`.

في حال كان `channel_api_key` غير صحيح ولا يمكن إيجاد قناة:
- ترفع الدالة `ValueError("Invalid channel_api_key")`، ليتم التعامل معها في طبقة الـ Router لاحقًا.
