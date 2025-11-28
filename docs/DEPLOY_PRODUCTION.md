# Production Deployment Guide

## 1. Overview
- هذا المشروع عبارة عن بوابة دفع بسيطة تتضمن إدارة الشركات والقنوات والمحافظ (wallets) واستقبال الرسائل النصية الواردة لمعالجة المدفوعات (incoming SMS).
- الكود مستقر: كل الاختبارات `106 passed`، والمشروع مبني على FastAPI + SQLAlchemy + Alembic + PostgreSQL.
- هذا الدليل يشرح طريقتين رئيسيتين للنشر:
  - تشغيل محلي (Local Demo) كما استخدمناه على Windows.
  - نشر على سيرفر Linux (Ubuntu) في وضع Production، مع أو بدون Docker.

## 2. Project Components
- **API:** تطبيق FastAPI في `app/main.py` (Uvicorn ASGI app).
- **Database:** PostgreSQL (تُستخدم قيمة `DATABASE_URL` من `.env`).
- **Migrations:** Alembic (`alembic.ini` و `alembic/versions`).
- **Seed script:** `app/seed_dev_data.py` لتهيئة بيانات وشركة Demo + API key.
- **Health endpoints:**
  - `GET /health` – فحص أساسي.
  - `GET /health/db` – فحص اتصال قاعدة البيانات.

## 3. Environment Variables (.env)
ملف `.env` يجب أن يكون في جذر المشروع ويحتوي على المتغيرات التالية كمثال:

```env
DATABASE_URL=postgresql://<USER>:<PASSWORD>@<HOST>:5432/<DB_NAME>
SECRET_KEY=استبدل_بهذه_قيمة_عشوائية_قوية
ENVIRONMENT=production
API_LOG_LEVEL=info
```

- **ملاحظة:** `app.config.Settings` يقرأ هذه المتغيرات تلقائيًا.

ملاحظات أمنية:

- لا ترفع ملف `.env` إلى Git أو أي نظام تحكم بالمصدر العام.
- غيّر كلمات المرور الافتراضية إلى سلاسل قوية وفريدة لكل بيئة.
- استخدم قيم مختلفة بين `staging` و `production` وقيّم منطق الوصول والمفاتيح السرية.

## 4. Local Demo (Windows, without Docker)
هذا القسم يشرح الخطوات التي اتُّبعت محليًا أثناء التطوير.

**المتطلبات**

- Python 3.11+ مع `venv`.
- PostgreSQL مثبت محليًا أو متاح على شبكة محلية.

**خطوات مختصرة**

1. إنشاء وتفعيل virtualenv.

2. تثبيت المتطلبات:

```bash
pip install -r requirements.txt
```

3. إعداد `.env` كما في القسم السابق.

4. إنشاء قاعدة بيانات Postgres (مثال اسمها `payment_gateway`).

5. تشغيل migrations:

```bash
alembic upgrade head
```

6. تشغيل السيرفر:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

7. تهيئة بيانات تجريبية:

```bash
python app/seed_dev_data.py
```

8. احفظ الـ API key الناتج من السكربت واستخدمه في Header: `X-API-Key`.

## 5. Production Deployment on Linux (Ubuntu) with Docker
هذا القسم يشرح نشرًا نموذجيًا باستخدام Docker و docker-compose.

### 5.1. Prerequisites

- Ubuntu 22.04 LTS.
- Docker Engine مثبت.
- اختيارياً: Docker Compose v2 (أو استخدام `docker compose`).

### 5.2. Directory Layout

- انسخ ملفات المشروع إلى مجلد مثل: `/opt/payment-api`.
- ضع ملف `.env` داخل نفس المجلد `/opt/payment-api/.env`.

### 5.3. Configure Environment

- حرّر `.env` على السيرفر بقيم Production (قاعدة بيانات على نفس السيرفر أو خدمة مُدارة).
- تأكد من أن `DATABASE_URL` يستخدم مستخدمًا وكلمة مرور قويين وخادمًا آمنًا.

### 5.4. Database Setup

- ثبّت PostgreSQL على السيرفر أو استخدم خدمة خارجية (RDS مثلاً).
- أنشئ قاعدة البيانات والمستخدم المناسب (أوامر مختصرة):

```sql
-- Example (run in psql as postgres user)
CREATE USER payment_user WITH PASSWORD 'strong_password';
CREATE DATABASE payment_gateway OWNER payment_user;
```

- شغّل Alembic migrations داخل الحاوية أو على نفس السيرفر:

```bash
docker compose run --rm api alembic upgrade head
```

> ملاحظة: اسم الخدمة `api` مأخوذ من `docker-compose.yml` بالمشروع.

### 5.5. Running the API with Docker Compose

- بناء وتشغيل الخدمات:

```bash
docker compose up -d --build
```

- تحقق من الحالة واللوجات:

```bash
docker compose ps
docker compose logs --tail=50 api
```

- تأكد من الوصول إلى:

```
http://SERVER_IP:8000/health
http://SERVER_IP:8000/docs
```

### 5.6. Seeding Demo Data in Production/Staging

- شغّل السكربت داخل الحاوية مرة واحدة:

```bash
docker compose run --rm api python app/seed_dev_data.py
```

- احفظ الـ API key الناتج واستخدمه للاختبارات.

## 6. Production Deployment on Linux (Ubuntu) without Docker
هذا القسم يصف نشرًا تقليديًا على خادم Ubuntu بدون حاويات.

### 6.1. Prerequisites

- Python 3.11+ مع virtualenv.
- PostgreSQL.
- حساب مستخدم غير root لتشغيل الخدمة.
- Nginx أو أي reverse proxy لرفع الأمان وتوفير SSL.

### 6.2. Setup Steps

1. انسخ المشروع إلى `/opt/payment-api`.

2. أنشئ virtualenv داخل المشروع:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. إعداد `.env`.

4. تشغيل Alembic:

```bash
.venv/bin/alembic upgrade head
```

5. اختبار تشغيل السيرفر يدويًا:

```bash
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 6.3. systemd Service

مثال مختصر لخدمة `systemd`:

```
[Unit]
Description=Payment API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/payment-api
ExecStart=/opt/payment-api/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

أوامر التفعيل:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now payment-api
sudo systemctl status payment-api
```

### 6.4. Nginx Reverse Proxy (Overview Only)

- فكرة عامة: Nginx يستمع على المنافذ 80/443 ويُعيد توجيه الطلبات إلى `http://127.0.0.1:8000` خلف الـ proxy.
- إعداد SSL وLet's Encrypt خارج نطاق هذا الدليل، لكن يُنصح بشدة باستخدام HTTPS في الإنتاج.

## 7. Health Checks and Monitoring

- استخدم `GET /health` في Load Balancer أو أدوات مراقبة مثل UptimeRobot.
- استخدم `GET /health/db` للتحقق من توفر قاعدة البيانات.
- راجع لوجات `uvicorn` أو لوجات الحاويات لرسائل الخطأ، واضبط سياسة تدوير لوجات (log rotation).

## 8. Security & Hardening Checklist

- غيّر `SECRET_KEY` في كل بيئة.
- لا تفتح منفذ PostgreSQL (5432) للعالم، واستخدم قواعد جدار ناري مناسبة.
- قيد الوصول إلى لوحة الإدارة وواجهة التوثيق إن لزم (مثلاً عبر IP allowlist أو auth middleware).
- تعطيل `--reload` في بيئة production.
- حافظ على تحديث النظام والحزم (Ubuntu, Docker, Python dependencies).

## 9. Troubleshooting

- `cannot connect to server: Connection refused` → تحقق من `DATABASE_URL` وتشغيل خدمة PostgreSQL.
- مشاكل Alembic → تأكد من أن الجداول غير موجودة جزئيًا وفحص ملف `alembic.ini` وبيانات الاتصال.
- أخطاء 500 → راجع لوجات Uvicorn/Containers: `docker compose logs api` أو `journalctl -u payment-api`.

---

هذا المستند يوفّر خارطة طريق عملية للنشر المحلي والانتقال إلى بيئة إنتاجية. إذا رغبت، أستطيع إضافة مقاطع عملية مفصّلة أكثر (ملفات systemd كاملة، إعداد Nginx مع SSL، أو سكربتات تشغيل/نسخ احتياطي للقاعدة).
