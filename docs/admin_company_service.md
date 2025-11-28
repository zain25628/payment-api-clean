# AdminCompanyService

هذه الخدمة مسؤولة عن إنشاء شركات جديدة وقنواتها انطلاقًا من بيانات لوحة التحكم (`AdminCompanyCreate`).

وظيفة `create_company_with_channels`:

- توليد `api_key` للشركة.
- إنشاء سجل جديد في جدول `companies`.
- جلب `PaymentProvider` من قاعدة البيانات باستخدام `provider_codes` المرسلة.
- إنشاء `Channel` لكل مزوّد متاح مع `channel_api_key` جديد.
- إرجاع كائن `Company` بعد `commit` و `refresh` لاستخدامه في الـ Router لاحقًا.

- `update_company_and_channels(db, company_id, data)`: تقوم بتحديث بيانات شركة موجودة وتعديل قنواتها بناءً على `provider_codes` المرسلة. تفعل التالي:
	- تحدث الحقول الأساسية: `name`, `country_code`, `telegram_bot_token`, `telegram_default_group_id`.
	- تجلب القنوات الحالية للشركة وتبني قنوات جديدة للمزوّدين المطلوبين (مع `channel_api_key` جديد عند الإنشاء).
	- تعيد تفعيل القنوات المطابقة للمزوّدين المختارين.
	- تُعطّل (لا تحذف) القنوات المرتبطة بمزوّدين لم يعدوا ضمن القائمة.
	- تتجاهل أكواد المزوّدين غير المعروفة.

- `toggle_company_active(db, company_id)`: تقلب العلم `is_active` للشركة وتُرجع الكائن المحدّث، أو `None` إن لم توجد الشركة.

```
