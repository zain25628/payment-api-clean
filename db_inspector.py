#!/usr/bin/env python3
"""
db_inspector.py

Fast DB inspection helper for the payment API.
- Prints last 10 Payments (id DESC)
- Shows fields: id, payer_phone, raw_message, channel_id, created_at
- Warns if `raw_message` contains placeholders like %SMSRF or %SMSRB
- Provides `check_latest()` to inspect the most recent payment and comment

Run: `python db_inspector.py`
"""
from typing import Optional
from app.db.session import SessionLocal
from app.models.payment import Payment

def _format_value(v: Optional[object]) -> str:
    if v is None:
        return "<None>"
    return str(v)

def print_last_payments(limit: int = 10) -> None:
    db = SessionLocal()
    try:
        payments = db.query(Payment).order_by(Payment.id.desc()).limit(limit).all()
        if not payments:
            print("لا توجد دفعات في قاعدة البيانات.")
            return

        print(f"آخر {len(payments)} دفعات (مرتّبة تنازلي id DESC):")
        print("=" * 80)
        for p in payments:
            print(f"ID: {p.id} | payer_phone: {_format_value(p.payer_phone)} | channel_id: {_format_value(p.channel_id)} | created_at: {_format_value(p.created_at)}")
            raw = p.raw_message if hasattr(p, "raw_message") else None
            print("raw_message:")
            print(repr(raw))

            # detect strange Tasker placeholders or percent tokens
            if raw:
                if ("%SMSRF" in raw) or ("%SMSRB" in raw):
                    print("⚠️ تحذير: raw_message يحتوي على علامات Tasker مثل %SMSRF أو %SMSRB — تحقق من إعداد Tasker.")
                elif "%" in raw:
                    # generic percent tokens may indicate placeholder usage
                    print("⚠️ تحذير: raw_message يحتوي على رمز '%' — قد توجد placeholders غير مُستبدلة.")

            print("-" * 80)
    finally:
        db.close()


def check_latest() -> None:
    """Print the latest payment and comment whether it looks like it arrived correctly from Tasker.

    Heuristic rules used:
    - If `raw_message` contains `%SMSRF` or `%SMSRB` or other percent placeholders -> likely malformed from Tasker.
    - If `raw_message` is empty or missing payer_phone -> suspicious.
    - Otherwise, assume data arrived correctly.
    """
    db = SessionLocal()
    try:
        p = db.query(Payment).order_by(Payment.id.desc()).first()
        if not p:
            print("لا توجد دفعات لمعاينتها.")
            return

        print("تفاصيل آخر دفعة:")
        print("=" * 60)
        print(f"ID: {p.id}")
        print(f"payer_phone: {_format_value(getattr(p, 'payer_phone', None))}")
        print(f"channel_id: {_format_value(getattr(p, 'channel_id', None))}")
        print(f"created_at: {_format_value(getattr(p, 'created_at', None))}")
        raw = getattr(p, 'raw_message', None)
        print("raw_message:")
        print(repr(raw))
        print("=" * 60)

        issues = []
        if not raw or str(raw).strip() == "":
            issues.append("raw_message فارغة أو None.")
        else:
            s = str(raw)
            if "%SMSRF" in s or "%SMSRB" in s:
                issues.append("يحتوي raw_message على placeholders من Tasker مثل %SMSRF/%SMSRB.")
            elif "%" in s:
                issues.append("يحتوي raw_message على رمز '%' وقد تكون هناك placeholders لم تُستبدل.")

        if getattr(p, 'payer_phone', None) is None:
            issues.append("payer_phone مفقود.")

        if issues:
            print("🔍 تعليق: يبدو أن البيانات قد لا تكون وصلت بشكل صحيح من Tasker:")
            for it in issues:
                print(f" - {it}")
            print("")
            print("نصيحة: تأكد من أن Tasker يستبدل المتغيرات قبل إرسالها (مثال: استخدم Action -> Send HTTP Request مع body مُركب بشكل صحيح).")
        else:
            print("✅ تعليق: تبدو البيانات واردة بشكل صحيح من Tasker — لا توجد علامات placeholders أو حقول مفقودة.")
    finally:
        db.close()


if __name__ == "__main__":
    check_latest()
