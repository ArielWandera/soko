from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.buyer import BuyerProfile
from app.models.order import Order, OrderStatus
from app.models.review import Review
from app.schemas import ReviewCreate, ReviewOut
from app.dependencies import require_buyer
from app.messaging import publish_event

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/{order_id}", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def leave_review(
    order_id: int,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_buyer)
):
    profile = db.query(BuyerProfile).filter(BuyerProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Order must exist and belong to this buyer
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.buyer_id == profile.id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Can only review a completed order
    if order.status != OrderStatus.completed:
        raise HTTPException(
            status_code=400,
            detail="You can only review a completed order"
        )

    # Write once — check if review already exists
    existing = db.query(Review).filter(Review.order_id == order_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already reviewed this order")

    review = Review(
        buyer_id=profile.id,
        produce_id=order.produce_id,
        order_id=order_id,
        stars=payload.stars,
        comment=payload.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    # Publish so Recommendation service can factor in ratings
    await publish_event("quality.scored", {
        "produce_id": order.produce_id,
        "farmer_id": order.farmer_id,
        "stars": payload.stars,
        "buyer_id": profile.id,
    })

    return review


@router.get("/produce/{produce_id}", response_model=list[ReviewOut])
def get_produce_reviews(produce_id: int, db: Session = Depends(get_db)):
    """Public endpoint — anyone can see reviews for a produce listing."""
    reviews = db.query(Review).filter(Review.produce_id == produce_id).all()
    return reviews
