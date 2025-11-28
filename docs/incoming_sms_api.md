# Incoming SMS API Schemas

هذه الـ Schemas تمثّل الـ payload الذي يرسله تطبيق الموبايل / Tasker إلى نقطة الدخول `/incoming-sms`.

## IncomingSmsCreate

الحقول المتوقعة:

- `channel_api_key` (string, required)  
  المفتاح السري الخاص بالقناة (Channel) الذي يتيح ربط الرسالة بقناة وشركة معيّنة.

- `provider` (string, optional)  
  اسم مزوّد الدفع (مثلاً `eand_money`) إن كان متاحًا.

- `raw_message` (string, required)  
  النص الخام لرسالة الـ SMS كما هي.

- `amount` (integer, optional)  
  المبلغ المستخرج من الرسالة، إذا قام تطبيق الموبايل بتحليله مسبقًا.

- `currency` (string, optional, default = "AED")  
  عملة العملية.

- `txn_id` (string, optional)  
  رقم العملية كما يظهر في نص الرسالة.

- `payer_phone` (string, optional)  
  رقم هاتف الدافع إن توفّر.

- `receiver_phone` (string, optional)  
  رقم المحفظة / المستلم.

- `timestamp` (datetime, optional)  
  وقت استقبال الرسالة في الجهاز.

## IncomingSmsStored

يمثّل الرد البسيط بعد قبول الرسالة وتخزينها كـ `Payment`:

- `payment_id` – معرّف الدفع الذي تم إنشاؤه.
- `status` – حالة العملية (مثلاً `new`).
