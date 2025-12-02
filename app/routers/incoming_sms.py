from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.incoming_sms import IncomingSmsCreate, IncomingSmsStored
from app.services.incoming_sms_service import IncomingSmsService


router = APIRouter(
    prefix="/incoming-sms",
    tags=["incoming-sms"],
)


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
    payload = await request.json()

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
    payment = sms_service.store_payment(
        db,
        channel.id,
        channel.company_id,
        parsed_data
    )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"payment_id": payment.id}
    )

