#!/usr/bin/env python3
import sys
from pathlib import Path
# ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.models.channel import Channel
from app.models.payment import Payment
import json

key = "m2d-VSqtORULUq32resoBr4-qQos8fQtuoiWIxPvSQg"

if __name__ == '__main__':
    db = SessionLocal()
    try:
        ch = db.query(Channel).filter(Channel.channel_api_key == key).first()
        if not ch:
            print(json.dumps({"error": "channel not found"}, ensure_ascii=False))
        else:
            payments = (
                db.query(Payment)
                .filter(Payment.channel_id == ch.id)
                .order_by(Payment.id.desc())
                .limit(10)
                .all()
            )
            out = []
            for p in payments:
                out.append({
                    "id": p.id,
                    "payer_phone": p.payer_phone,
                    "receiver_phone": p.receiver_phone,
                    "raw_message": p.raw_message,
                    "amount": p.amount,
                    "currency": p.currency,
                    "company_id": p.company_id,
                    "created_at": p.created_at.isoformat() if getattr(p, 'created_at', None) else None,
                })
            print(json.dumps({"channel_id": ch.id, "company_id": ch.company_id, "payments": out}, ensure_ascii=False, indent=2))
    finally:
        db.close()
