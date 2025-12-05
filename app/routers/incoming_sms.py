import json
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from app.db.session import get_db
from app.schemas.incoming_sms import IncomingSmsCreate, IncomingSmsStored
from app.services.incoming_sms_service import IncomingSmsService


router = APIRouter(
    prefix="/incoming-sms",
    tags=["incoming-sms"],
)


logger = logging.getLogger("payment_gateway")


@router.post("/", response_model=IncomingSmsStored, status_code=status.HTTP_201_CREATED)
async def receive_incoming_sms(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Receive an incoming SMS payload (from Tasker/mobile) and store it as a Payment.

    This endpoint is backward-compatible: if the incoming JSON contains a
    `channel_api_key` key we treat it as the new normalized payload and use
    `IncomingSmsService.store_incoming_sms`. If `channel_api_key` is absent
    we fall back to the legacy `sms_service.store_payment` flow (kept for
    compatibility with older callers/tests).
    """
    # Safely read and parse the raw body to avoid uncaught JSON decode errors
    body_bytes = await request.body()
    logger.info("incoming-sms raw body: %r", body_bytes)
    # Log masked API key for security
    logger.info("incoming-sms X-API-Key received (masked)")

    body_text = body_bytes.decode("utf-8", errors="replace")
    try:
        payload = json.loads(body_text)
    except json.JSONDecodeError:
        # Try a tolerant fallback: escape literal newlines/carriage-returns inside the raw body
        # Many clients (Tasker/phones) sometimes send unescaped literal newlines inside JSON strings.
        logger.warning("incoming-sms: initial JSON parse failed, attempting sanitized parse")
        sanitized = body_text.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")
        try:
            payload = json.loads(sanitized)
        except json.JSONDecodeError as exc2:
            logger.exception("Invalid JSON body for /incoming-sms/ after sanitization")
            raise HTTPException(status_code=400, detail="Invalid JSON body") from exc2

    # Minimal content filter: accept only e& money deposit messages.
    # If raw_message is present, enforce pattern: contains "good news" AND "aed" AND ("landed" OR "from").
    if "raw_message" in payload:
        raw_msg = str(payload.get("raw_message") or "")
        low = raw_msg.lower()
        is_deposit = ("good news" in low) and ("aed" in low) and (("landed" in low) or ("from" in low))
        if not is_deposit:
            logger.info("SMS ignored (not a deposit): %s", raw_msg)
            # New normalized path expects IncomingSmsStored response_model; return a safe stored-like response
            if "channel_api_key" in payload:
                return IncomingSmsStored(payment_id=0, status="ignored - not a deposit")
            # Legacy path: return a simple JSON response and do not store
            return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ignored - not a deposit"})

    # New path: expects channel_api_key in payload
    if "channel_api_key" in payload:
        try:
            data = IncomingSmsCreate(**payload)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

        try:
            payment = IncomingSmsService.store_incoming_sms(db, data)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        except IntegrityError as exc:
            # DB constraint violation — rollback and return 400 with safe message
            db.rollback()
            logger.exception("IntegrityError while storing incoming SMS (channel_api_key path)")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment data") from exc
        except Exception:
            db.rollback()
            logger.exception("Unexpected error while storing incoming SMS (channel_api_key path)")
            raise HTTPException(status_code=500, detail="Internal server error")

        return IncomingSmsStored(payment_id=payment.id, status=payment.status)

    # Legacy path: validate X-API-Key header
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header"
        )

    import app.services.sms_service as sms_service
    channel = sms_service.validate_channel_api_key(db, api_key)
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive channel API key"
        )

    # Validate payload and parse
    if "raw_message" not in payload:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="field required: raw_message")

    parsed_data = sms_service.parse_incoming_sms(payload)

    # Store using REAL channel & company IDs
    try:
        payment = sms_service.store_payment(
            db,
            channel.id,
            channel.company_id,
            parsed_data
        )
    except IntegrityError as exc:
        db.rollback()
        logger.exception("IntegrityError while storing payment (legacy path)")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment data") from exc
    except Exception:
        db.rollback()
        logger.exception("Unexpected error while storing payment (legacy path)")
        raise HTTPException(status_code=500, detail="Internal server error")

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"payment_id": payment.id}
    )

