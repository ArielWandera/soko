import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user_id
from app.db.database import get_db
from app.helpers.pesapal import get_transaction_status
from app.models.payment import Transaction
from app.schemas.payment import TransactionOut

router = APIRouter(tags=["Payments"])


def build_transaction_out(tx: Transaction) -> TransactionOut:
    return TransactionOut(
        id=str(tx.id),
        orderId=str(tx.order_id),
        amount=tx.amount,
        currency=tx.currency,
        status=tx.status.value,
        paymentMethod=tx.payment_method_type.value,
        paidAt=tx.paid_at.isoformat() if tx.paid_at else None,
        createdAt=tx.created_at.isoformat(),
    )


@router.get("/me", response_model=list[TransactionOut])
def get_my_transactions(
    page:    int          = Query(default=1,  ge=1),
    limit:   int          = Query(default=20, le=100),
    user_id: str          = Depends(get_current_user_id),
    db:      Session      = Depends(get_db)
):
    txs = db.query(Transaction).filter(
        Transaction.buyer_id == uuid.UUID(user_id)
    ).order_by(Transaction.created_at.desc()) \
     .offset((page - 1) * limit).limit(limit).all()

    return [build_transaction_out(tx) for tx in txs]


@router.get("/me/{transaction_id}", response_model=TransactionOut)
def get_transaction(
    transaction_id: str,
    user_id:        str     = Depends(get_current_user_id),
    db:             Session = Depends(get_db)
):
    tx = db.query(Transaction).filter(
        Transaction.id       == uuid.UUID(transaction_id),
        Transaction.buyer_id == uuid.UUID(user_id)
    ).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return build_transaction_out(tx)


@router.get("/order/{order_id}/status")
async def check_payment_status(
    order_id: str,
    user_id:  str     = Depends(get_current_user_id),
    db:       Session = Depends(get_db)
):
    """
    Frontend polls this while buyer is on PesaPal page
    to know when payment completes.
    """
    tx = db.query(Transaction).filter(
        Transaction.order_id == uuid.UUID(order_id),
        Transaction.buyer_id == uuid.UUID(user_id)
    ).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # If pending, check live with PesaPal
    if tx.status.value == "pending" and tx.pesapal_order_tracking_id:
        try:
            status_data    = await get_transaction_status(tx.pesapal_order_tracking_id)
            pesapal_status = status_data.get("payment_status_description", "").upper()
            return {
                "status":         tx.status.value,
                "pesapal_status": pesapal_status,
                "payment_url":    tx.pesapal_payment_url,
            }
        except Exception:
            pass

    return {
        "status":      tx.status.value,
        "payment_url": tx.pesapal_payment_url,
    }