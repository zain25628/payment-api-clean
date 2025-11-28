# Admin Geo / Metadata Schemas

هذه الـ Schemas ستُستخدم لاحقًا في Router Admin (مثلاً `/admin/geo`) لعرض قوائم جغرافية وبيانات وصفية.

المخرجات الرئيسية:

- `AdminCountryOut`: تمثيل مبسّط لدولة (يُستخدم في القوائم وحقول الاختيار).
- `AdminPaymentProviderOut`: تمثيل لمزوّد دفع (id, code, name, description).
- `AdminCountryWithProviders`: تركيبة تحتوي على دولة وقائمة المزوّدين المدعومين في تلك الدولة.

هذه البيانات تُستخدم في واجهة لوحة التحكم عندما يختار الـ Admin دولة لكي تعرض له "الوسائل المدعومة في تلك البلد".

مثال JSON لـ `AdminCountryWithProviders`:

```json
{
  "country": {
    "id": 1,
    "code": "UAE",
    "name": "United Arab Emirates"
  },
  "providers": [
    {
      "id": 10,
      "code": "eand_money",
      "name": "e& money",
      "description": "Wallet provider in UAE"
    }
  ]
}
```
