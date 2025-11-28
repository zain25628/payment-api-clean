# تشغيل سريع محليًا (Quickstart)

## مقدمة
هذا المشروع هو API لبوابة دفع بسيطة تتضمّن إدارة شركات، قنوات، محافظ (wallets)، ومعالجة المدفوعات المستخلصة من رسائل SMS واردة. الدليل التالي يشرح كيف تشغّل المشروع محليًا كنسخة "منتج جاهز" للاختبار والتجربة.

> الحالة الحالية: كل الاختبارات تمرّ (`106 passed`) والسيرفر يعمل محليًا عبر Uvicorn عند `http://127.0.0.1:8000` بعد تهيئة البيئة وقاعدة البيانات.

## المتطلبات

- Python 3.11+ وبيئة افتراضية (`venv`).
- PostgreSQL مثبت محليًا أو متاح عبر شبكة.
- أدوات: `alembic` مثبت ضمن المتطلبات في `requirements.txt`.

## خطوات التشغيل المحلية (1 → 5)

1. إعداد ملف `.env` في جذر المشروع (موجود بجانب `requirements.txt`). انسخ من `.env.example` أو أنشئ ملفًا جديدًا وضع القيم الأساسية:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/payment_gateway
SECRET_KEY=ضع_قيمة_سرية_وقوية_هنا
ENVIRONMENT=production
API_LOG_LEVEL=info
```

2. أنشئ قاعدة بيانات PostgreSQL مناسبة (مثال الاسم: `payment_gateway`). يمكنك استخدام `psql` أو `pgAdmin`:

```sql
CREATE DATABASE payment_gateway;
```

3. شغّل Alembic لإنشاء الجداول:

```bash
alembic upgrade head
```

4. شغّل السيرفر عبر Uvicorn باستخدام بايثون من الـ venv:

```powershell
& C:\Users\zaink\OneDrive\Desktop\api\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

5. (اختياري ومهم للـ Demo) طباعة بيانات تجريبية ومفتاح API:

```powershell
& C:\Users\zaink\OneDrive\Desktop\api\.venv\Scripts\python.exe app/seed_dev_data.py
```

بعد التشغيل، سيطبع السكربت `api_key` للشركة التجريبية؛ احفظ هذه القيمة لاستخدامها في هيدر الطلبات `X-API-Key`.

## التحقق السريع

- افتح التوثيق التفاعلي: `http://127.0.0.1:8000/docs`
- تحقق من حالة التطبيق: `GET http://127.0.0.1:8000/health`
- تحقق من اتصال قاعدة البيانات: `GET http://127.0.0.1:8000/health/db`

## ملاحظة عن `X-API-Key`

بعض نقاط النهاية الإدارية أو الخاصة بالشركات تحتاج هيدر `X-API-Key` بقيمة الـ API key الناتجة من تنفيذ `seed_dev_data.py`. ضع الهيدر في طلباتك لاختبار العمليات الخاصة بالشركات والقنوات والمحافظ.

## مشاكل شائعة

- **No module named uvicorn** → ثبت الحزمة داخل الـ venv: `pip install uvicorn` أو استخدم `python -m uvicorn` من مسار الـ venv.
- **Cannot connect to server: Connection refused** → تحقق من أن PostgreSQL يعمل وأن `DATABASE_URL` صحيح.
- **مشكلة Alembic** → تأكد من أن `alembic.ini` يشير إلى `DATABASE_URL` الصحيح وأن المهاجرات موجودة في `alembic/versions`.
- **الـ .env مفقود** → أنشئ `.env` في جذر المشروع واملأ المتغيرات المطلوبة أعلاه.

---

هذا الملف موجّه للبدء السريع المحلي، ويمكنك الاعتماد عليه لتجربة الواجهة أو للإعداد لبيئة staging/production مع تعديلات بسيطة في `.env` وطرق التشغيل.
