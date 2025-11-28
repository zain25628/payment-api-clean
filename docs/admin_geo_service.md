# AdminGeoService

هذه الخدمة مسؤولة عن توفير بيانات جغرافية وبيانات وصفية للوحة التحكم.

الدوال الأساسية:

- `list_countries(db)`: إرجاع قائمة الدول (`AdminCountryOut`) مرتبة حسب الاسم.
- `list_payment_providers(db)`: إرجاع قائمة مزوّدي الدفع (`AdminPaymentProviderOut`) مرتبة حسب الاسم.
- `get_country_with_providers(db, country_code)`: إرجاع دولة مع قائمة المزوّدين المدعومين فيها (يأخذ بالاعتبار `CountryPaymentProvider.is_supported`).

ملاحظة: هذه الدوال قراءة فقط (read-only) وستُستخدم لاحقًا في Router Admin (مثلاً `/admin/geo`) لتغذية واجهة لوحة التحكم بقوائم الدول والمزوّدين المدعومين لكل دولة.
