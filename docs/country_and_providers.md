# Countries and Payment Providers

`Country` تمثّل الدول التي تعمل ضمنها المنصّة.

`PaymentProvider` تمثّل أنواع وسائل الدفع (مثل e& money، محافظ إلكترونية أخرى، الخ).

`CountryPaymentProvider` تربط بينهما لتحديد أي مزوّد متاح في أي دولة.

لوحة التحكم تستخدم `countries` و `payment_providers` لعرض "الوسائل المدعومة في تلك الدولة".

عند إنشاء شركة جديدة وتحديد الدولة، يتم عرض قائمة الـ `PaymentProvider` المرتبطة بهذه الدولة لاختيارها كقنوات للشركة.
