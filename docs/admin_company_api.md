# Admin Company API Schemas

هذه الـ Schemas ستُستخدم لاحقًا في Router خاص بلوحة التحكم (مثل `admin_companies`)، لتمثيل:

- طلب إنشاء شركة (`AdminCompanyCreate`)
- عرض شركة مفصلة (`AdminCompanyOut`)
- عرض شركة في قائمة (`AdminCompanyListItem`)
- تمثيل قناة مرتبطة بشركة (`AdminChannelOut`)

مثال `AdminCompanyOut` مبسّط:

```json
{
  "id": 1,
  "name": "Test Co",
  "api_key": "abcd-1234",
  "country_code": "UAE",
  "channels": [
    {
      "id": 10,
      "name": "E& Money UAE",
      "provider_code": "eand_money",
      "provider_name": "e& money",
      "channel_api_key": "chan-key-123",
      "telegram_group_id": "-1001234567890",
      "is_active": true
    }
  ]
}
```
