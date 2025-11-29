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

## 2) Company Wallets – create & toggle

Steps:
1. Ensure backend & frontend are running:
   - Backend: `.`\dev_start_stack.ps1` from the project root.
   - Frontend: `npm run dev` from `admin-frontend` (Vite on http://localhost:5173/).

2. Open the "Company Wallets" page in the admin UI.

3. Validation checks:
   - Try to submit the wallet form empty:
     - Field-level errors should appear under required fields (label, identifier, daily limit, channel).
   - Enter invalid values (e.g. daily limit = 0 or negative):
     - The form should show a validation error for the daily limit field.
   - While submitting:
     - The "Create" button should be disabled and show a loading text (e.g. "Creating...").

4. Happy path:
   - Create a new wallet with:
     - A clear label and identifier.
     - A positive daily_limit (e.g. 10_000).
     - An active channel selected.
   - The wallet should appear in the table with:
     - Correct label, identifier, daily_limit, and used_today = 0.
   - Click "Toggle Active":
     - The Active column should update accordingly (true/false).

5. Notes:
   - Use this page together with `merchant_demo.py` to verify that a wallet can be picked for a given company/channel and amount.

## 3) Payment Providers – create & validate

Steps:
1. Ensure backend & frontend are running:
   - Backend: `.\dev_start_stack.ps1` from the project root.
   - Frontend: `npm run dev` from `admin-frontend` (Vite on http://localhost:5173/).

2. Open the "Payment Providers" page in the admin UI.

3. Validation checks:
   - Try to submit the provider form empty:
     - Field-level errors should appear under required fields (e.g. `name`, `code`).
   - Enter clearly invalid values if applicable (e.g. whitespace-only `name`):
     - The form should show a validation error for those fields.
   - While submitting:
     - The "Save" button should be disabled and show a loading text (e.g. "Saving...").

4. Happy path:
   - Create a new payment provider with:
     - A clear `name` and unique `code`.
     - A valid country selection and any required fields.
   - The provider should appear in the table with the correct values.

5. Error handling:
   - If the backend returns an error (e.g. duplicate `code`), a general error banner should appear above the form.

## 4) Payments – check & verify

Steps:
1. Ensure backend and admin frontend are running:
  - Backend: `.`\dev_start_stack.ps1` (or `python -m uvicorn app.main:app --reload`)
  - Frontend: from `admin-frontend`: `npm run dev`

2. Open the Payments check page:
  - URL: `http://localhost:5173/`
  - Navigate to: "Payments" in the admin nav.

3. Enter API key:
  - Use the dev channel key from `dev_seed.py` output (default: `dev-channel-key`).
  - Paste into the "API key (X-API-Key)" field.

4. Check a known test payment:
  - From `create_test_payment.py` output, take:
    - `amount`
    - `txn_id`
    - `payer_phone` (if set)
  - Fill the form with matching values.
  - Click "Check payment".
  - Expect result:
    - `found: true`
    - `match: true`
    - `payment` object present.

5. Negative / mismatch scenarios:
  - Change `amount` to a different value and check again.
  - Expect:
    - `found: true`, `match: false`
    - `reason` explains mismatch (e.g. amount mismatch).

6. Error handling:
  - Clear API key and submit.
  - Expect an on-page validation error before the request is sent.
  - Use an invalid key and submit.
  - Expect backend to respond with 401 and error details shown in the result area.
