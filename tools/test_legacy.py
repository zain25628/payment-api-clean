from app.db.session import SessionLocal
import app.services.sms_service as sms_service
import traceback

db = SessionLocal()
try:
    api_key = 'm2d-VSqtORULUq32resoBr4-qQos8fQtuoiWIxPvSQg'
    channel = sms_service.validate_channel_api_key(db, api_key)
    print('channel', channel and channel.id, 'company_id', channel and channel.company_id)
    payload = { 'payer_phone': '+971500000001', 'raw_message': 'TEST MESSAGE' }
    parsed = sms_service.parse_incoming_sms(payload)
    print('parsed', parsed)
    payment = sms_service.store_payment(db, channel.id, channel.company_id, parsed)
    print('OK', payment.id)
except Exception:
    traceback.print_exc()
finally:
    db.close()
