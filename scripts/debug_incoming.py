from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.base import Base
import importlib

importlib.import_module('app.models.company')
importlib.import_module('app.models.channel')
importlib.import_module('app.models.wallet')
importlib.import_module('app.models.payment')
importlib.import_module('app.models.country')

engine = create_engine('sqlite:///:memory:', future=True, connect_args={'check_same_thread': False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

from app.routers.incoming_sms import router as incoming_sms_router
app = FastAPI()
app.include_router(incoming_sms_router)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

from app.db.session import get_db
app.dependency_overrides[get_db] = override_get_db

# create company and channel
from app.models.company import Company
from app.models.channel import Channel

db = TestingSessionLocal()
company = Company(name='Test Co', api_key='test-key')
db.add(company)
db.flush()
channel = Channel(company_id=company.id, name='Test Channel', channel_api_key='chan-key-123')
db.add(channel)
db.commit()
db.close()

client = TestClient(app)
resp = client.post('/incoming-sms/', json={'channel_api_key':'chan-key-123','raw_message':'تم تحويل 150 درهم','amount':150,'currency':'AED','txn_id':'TXN123','payer_phone':'0500000000','receiver_phone':'0511111111'})
print('status', resp.status_code)
print('body', resp.text)
