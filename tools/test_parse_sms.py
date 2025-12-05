from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.sms_service import parse_incoming_sms

payload = {
    "payer_phone": "eandmoney",
    "raw_message": "Good news! AED 1.00 from MAHMOUD RAED HASSOUN landed in your account. \nCheck your new balance: 48.42\nTransaction ID: 242833601 ",
}

print(parse_incoming_sms(payload))
