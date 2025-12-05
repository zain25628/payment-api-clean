from app.db.session import SessionLocal
from app.services.incoming_sms_service import IncomingSmsService
from app.schemas.incoming_sms import IncomingSmsCreate
import traceback

db = SessionLocal()
try:
    data = IncomingSmsCreate(channel_api_key='m2d-VSqtORULUq32resoBr4-qQos8fQtuoiWIxPvSQg', payer_phone='+971500000001', raw_message='TEST MESSAGE')
    p = IncomingSmsService.store_incoming_sms(db, data)
    print('OK', p.id)
except Exception:
    traceback.print_exc()
finally:
    db.close()
