# Refactored by Copilot
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
import logging

from app.core.logging_config import setup_logging
from app.core.exceptions import unhandled_exception_handler
from app.routers import health, incoming_sms, wallets, payments
from app.routers.admin_geo import router as admin_geo_router
from app.routers.admin_wallets import router as admin_wallets_router
from app.routers.admin_companies import router as admin_companies_router
from app.routers.admin_payment_providers import router as admin_payment_providers_router
from app.routers.admin_payments import router as admin_payments_router
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from app.config import settings

# Configure logging early
setup_logging()

app = FastAPI(title="Payment Gateway API")

# Mount onboarding static files (generated HTML/PDF) so they can be downloaded
onboarding_dir = Path(settings.ONBOARDING_OUTPUT_DIR)
onboarding_dir.mkdir(parents=True, exist_ok=True)

app.mount(
    "/static/onboarding",
    StaticFiles(directory=str(onboarding_dir)),
    name="onboarding_static",
)

# CORS for admin frontend (Vite dev server)
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

# Register global exception handlers
logger = logging.getLogger("payment_gateway")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return await unhandled_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Log a concise validation message
    logger.info("Validation error on %s %s: %s", request.method, request.url.path, exc.errors())
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


app.include_router(health.router)
app.include_router(incoming_sms.router)
app.include_router(wallets.router)
app.include_router(payments.router)
app.include_router(admin_wallets_router)
app.include_router(admin_companies_router)
app.include_router(admin_payment_providers_router)
app.include_router(admin_geo_router)
app.include_router(admin_payments_router)


@app.get("/")
def read_root():
    logger.info("Application startup")
    return {"message": "Welcome to the Payment Gateway API"}
