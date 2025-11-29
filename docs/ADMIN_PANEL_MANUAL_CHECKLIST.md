# Admin Panel Manual Checklist

## 1) Companies – create & validation

Steps:
1. Start backend & frontend:
   - Backend:
     ```powershell
     cd C:\Users\zaink\OneDrive\Desktop\api
     .\.venv\Scripts\Activate.ps1
     .\dev_start_stack.ps1
     ```
   - Frontend (if not auto-started):
     ```powershell
     cd C:\Users\zaink\OneDrive\Desktop\api\admin-frontend
     $nodeDir = "C:\Program Files\nodejs"
     if (Test-Path "$nodeDir\node.exe") { $env:Path = "$nodeDir;$env:Path" }
     npm run dev
     ```
2. Open the admin UI in the browser:
   - Go to: `http://localhost:5173/`
   - Navigate to the Companies page (route: `/companies`, which renders `CompanyForm` for create/edit in `admin-frontend/src/routes/CompanyForm.tsx`).
3. Validation checks:
   - حاول تضغط "Save" وفورم فاضي:
     - يجب أن تظهر رسائل خطأ تحت الحقول الإلزامية (name, providers, apiKey إذا كانت مطلوبة).
   - املأ الحقول الإلزامية بقيم صحيحة:
     - الحقول الإلزامية يجب أن لا تظهر أخطاء.
     - زر الحفظ يجب أن يتغير إلى "Saving..." أثناء الإرسال ثم يعود لحالته الطبيعية.
   - في حالة خطأ من الـ backend:
     - يجب أن يظهر مربع رسالة خطأ أعلى الفورم.
4. Happy path:
   - أنشئ شركة جديدة ببيانات تجريبية.
   - تأكد من ظهور الشركة في القائمة/الجدول بعد الحفظ أو بعد إعادة تحميل الصفحة (إن كان ذلك مدعومًا).

## Notes
- إذا تغيّرت أسماء الحقول أو المسارات في المستقبل، حدّث هذه التشيك ليست.
- الهدف: خطوة واحدة بسيطة للتأكد أن CompanyForm يعمل بعد أي تعديل على الواجهة أو الـ backend.
