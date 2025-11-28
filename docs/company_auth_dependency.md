# Company Auth Dependency (X-API-Key)

هذه الـ Dependency تُستخدم لحماية واجهات الـ API العامة الخاصة بالعملاء
(مثل `/payments/check` و `/payments/confirm`) باستخدام مفتاح `X-API-Key`.

## get_company_by_api_key(db, api_key) -> Company

- تبحث عن `Company` بالاعتماد على الحقل `api_key` في قاعدة البيانات.
- في حال:
  - عدم وجود مفتاح → ترفع `HTTP 401 Missing X-API-Key`.
  - المفتاح غير صالح → ترفع `HTTP 401 Invalid X-API-Key`.
  - الشركة غير مفعّلة (`is_active = False`) → ترفع `HTTP 403 Company is inactive`.

## get_current_company(...)

Dependency من FastAPI:

```python
def get_current_company(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> Company:
    ...
```

* تُستخدم في الـ Routers بالشكل:

```python
from fastapi import Depends
from app.dependencies.company_auth import get_current_company
from app.models.company import Company

@router.post("/payments/check")
def check_payment(
    payload: PaymentCheckRequest,
    current_company: Company = Depends(get_current_company),
):
    ...
```

* أي طلب بدون هيدر صحيح `X-API-Key` لن يصل إلى الـ Endpoint، بل سيرجع استجابة خطأ HTTP مباشرة من الـ Dependency.
