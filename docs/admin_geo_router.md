# Admin Geo Router

هذا الـ Router يقدّم واجهات قراءة (read-only) لبيانات الدول ومزوّدي الدفع لاستخدامها في لوحة التحكم.

المسارات:

- `GET /admin/geo/countries`
  - يعيد قائمة من `AdminCountryOut` (كل الدول المتاحة).

- `GET /admin/geo/providers`
  - يعيد قائمة من `AdminPaymentProviderOut` (كل مزوّدي الدفع المتاحين).

- `GET /admin/geo/countries/{country_code}/providers`
  - يعيد `AdminCountryWithProviders` لدولة معيّنة مع قائمة المزوّدين المدعومين فيها.
  - يعيد 404 مع `{"detail": "Country not found"}` إذا لم توجد الدولة.

هذه الواجهات تُستخدم من واجهة لوحة التحكم لعرض الدول المدعومة والوسائل المتاحة في كل دولة عند إعداد حساب/شركة جديدة.
