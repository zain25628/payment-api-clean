# Admin Companies Router

هذا الـ Router يقدّم واجهات إدارة الشركات في لوحة التحكم:

- `POST /admin/companies` لإنشاء شركة جديدة + قنواتها.
- `GET /admin/companies` لعرض قائمة الشركات.
- `GET /admin/companies/{company_id}` لعرض تفاصيل شركة مفصّلة.

الـ Schemas المستخدمة:

- إدخال: `AdminCompanyCreate` (body لطلب الإنشاء).
- إخراج: `AdminCompanyOut` (تفاصيل الشركة)، `AdminCompanyListItem` (عنصر في القائمة).

مثال مبسّط لطلب إنشاء شركة (body لـ POST /admin/companies):

```json
{
  "name": "Test Co",
  "country_code": "UAE",
  "provider_codes": ["eand_money", "wallet_x"],
  "telegram_bot_token": "123:ABC",
  "telegram_default_group_id": "-1001234567890"
}
```

## Update & Toggle

- `PUT /admin/companies/{company_id}`
  - يحدث بيانات الشركة: `name`, `country_code`, `telegram_bot_token`, `telegram_default_group_id`, ويفسح المجال لاختيار `provider_codes` لتحديد القنوات المرتبطة.
  - يستقبل `AdminCompanyCreate` في الـ body ويعيد `AdminCompanyOut` عند النجاح.
  - يعيد `404 Company not found` إن لم توجد الشركة.

- `POST /admin/companies/{company_id}/toggle`
  - يقلب حالة الشركة `is_active` بين مفعّل/موقوف.
  - لا يحتاج body. يعيد `AdminCompanyOut` بعد التبديل.
  - يعيد `404 Company not found` إن لم توجد الشركة.
