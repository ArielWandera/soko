import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.helpers.pesapal import get_transaction_status
from app.models.payment import Transaction, PaymentStatus
from app.routers.internal import confirm_order_with_service, fail_order_with_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Webhook"])

# PesaPal status codes
PESAPAL_COMPLETED = "COMPLETED"
PESAPAL_FAILED    = "FAILED"
PESAPAL_REVERSED  = "REVERSED"
PESAPAL_INVALID   = "INVALID"


@router.get("/pesapal/ipn")
async def pesapal_ipn(
    orderTrackingId:  str = Query(...),
    orderMerchantRef: str = Query(...),
    orderNotifyType:  str = Query(...),
    db: Session = Depends(get_db)
):
    """
    PesaPal sends a GET request here when payment status changes.
    We verify the status directly with PesaPal API — never trust the IPN alone.
    """
    logger.info(f"IPN received: tracking_id={orderTrackingId} ref={orderMerchantRef}")

    # ── 1. Find the transaction
    tx = db.query(Transaction).filter(
        Transaction.pesapal_order_tracking_id == orderTrackingId
    ).first()

    if not tx:
        logger.warning(f"IPN for unknown tracking id: {orderTrackingId}")
        # Still return 200 — PesaPal will retry on non-200
        return {"status": "ok", "message": "Transaction not found"}

    # Skip if already finalised
    if tx.status in (PaymentStatus.completed, PaymentStatus.failed, PaymentStatus.refunded):
        return {"status": "ok", "message": "Already processed"}

    # ── 2. Verify status directly with PesaPal — never trust IPN payload alone
    try:
        status_data = await get_transaction_status(orderTrackingId)
    except Exception as e:
        logger.error(f"PesaPal status check failed: {e}")
        raise HTTPException(status_code=502, detail="Could not verify payment status")

    pesapal_status    = status_data.get("payment_status_description", "").upper()
    payment_method    = status_data.get("payment_method")

    logger.info(f"PesaPal status for {orderTrackingId}: {pesapal_status}")

    # ── 3. Update transaction and notify Order Service
    if pesapal_status == PESAPAL_COMPLETED:
        tx.status                = PaymentStatus.completed
        tx.paid_at               = datetime.utcnow()
        tx.pesapal_payment_method = payment_method
        db.commit()

        await confirm_order_with_service(
            order_id=str(tx.order_id),
            transaction_id=str(tx.id),
            payment_reference=orderTrackingId,
        )

    elif pesapal_status in (PESAPAL_FAILED, PESAPAL_INVALID):
        tx.status         = PaymentStatus.failed
        tx.failure_reason = pesapal_status
        db.commit()

        await fail_order_with_service(
            order_id=str(tx.order_id),
            reason=f"PesaPal status: {pesapal_status}"
        )

    elif pesapal_status == PESAPAL_REVERSED:
        tx.status         = PaymentStatus.refunded
        tx.failure_reason = "Payment reversed by PesaPal"
        db.commit()

        await fail_order_with_service(
            order_id=str(tx.order_id),
            reason="Payment reversed"
        )

    else:
        # Still pending — PesaPal will IPN again
        logger.info(f"Payment still pending for order {tx.order_id}")

    # PesaPal expects 200 — anything else triggers retries
    return {"status": "ok", "orderNotificationType": orderNotifyType}


@router.get("/pesapal/callback")
async def pesapal_callback(
    order_id:        str = Query(...),
    OrderTrackingId: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Buyer lands here after completing or cancelling on PesaPal's page.
    We check status and redirect them to the frontend.
    """
    from fastapi.responses import RedirectResponse
    from app.core.config import settings

    tx = db.query(Transaction).filter(
        Transaction.order_id == order_id
    ).first()

    if not tx:
        return RedirectResponse(f"{settings.FRONTEND_URL}/orders?status=error")

    # Check live status
    try:
        status_data    = await get_transaction_status(OrderTrackingId)
        pesapal_status = status_data.get("payment_status_description", "").upper()
    except Exception:
        return RedirectResponse(f"{settings.FRONTEND_URL}/orders/{order_id}?status=error")

    if pesapal_status == PESAPAL_COMPLETED:
        return RedirectResponse(
            f"{settings.FRONTEND_URL}/orders/{order_id}?status=success"
        )
    else:
        return RedirectResponse(
            f"{settings.FRONTEND_URL}/orders/{order_id}?status=pending"
        )