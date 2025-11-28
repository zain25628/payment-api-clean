from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.incoming_sms import router as incoming_sms_router
from app.routers.wallets import router as wallets_router
from app.routers.payments import router as payments_router
from app.routers.admin_companies import router as admin_companies_router
from app.routers.admin_geo import router as admin_geo_router


app = FastAPI(title="Payment Gateway API", version="0.1.0")

# CORS to allow the React admin frontend (localhost:5173)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(incoming_sms_router)
app.include_router(wallets_router)
app.include_router(payments_router)
app.include_router(admin_companies_router)
app.include_router(admin_geo_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
