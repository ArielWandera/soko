from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import UserProfile, FarmerReview, ReviewHelpful, FarmerStats
from app.schemas.schemas import FarmerReviewOut, CreateReviewPayload
from app.helpers.builders import make_initials
import uuid

router = APIRouter(tags=["Reviews"])


@router.get("/{farmer_id}/reviews", response_model=list[FarmerReviewOut])
def get_farmer_reviews(
    farmer_id: str,
    x_user_id: str = Header(default=None),
    db: Session = Depends(get_db)
):
    reviews = db.query(FarmerReview).filter(
        FarmerReview.farmer_id == uuid.UUID(farmer_id)
    ).order_by(FarmerReview.created_at.desc()).all()

    result = []
    for r in reviews:
        is_helpful = None
        if x_user_id:
            is_helpful = db.query(ReviewHelpful).filter(
                ReviewHelpful.review_id == r.id,
                ReviewHelpful.voter_id  == uuid.UUID(x_user_id)
            ).first() is not None
        result.append(FarmerReviewOut(
            id=str(r.id),
            reviewerId=str(r.reviewer_id),
            reviewerName=r.reviewer_name,
            reviewerInitials=r.reviewer_initials,
            rating=r.rating,
            body=r.body,
            createdAt=r.created_at.isoformat(),
            helpful=r.helpful,
            isHelpfulByMe=is_helpful,
        ))
    return result


@router.post("/{farmer_id}/reviews", response_model=FarmerReviewOut, status_code=201)
def add_review(
    farmer_id: str,
    payload: CreateReviewPayload,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    if farmer_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot review yourself")

    if db.query(FarmerReview).filter(
        FarmerReview.farmer_id   == uuid.UUID(farmer_id),
        FarmerReview.reviewer_id == uuid.UUID(user_id)
    ).first():
        raise HTTPException(status_code=409, detail="You have already reviewed this farmer")

    reviewer = db.query(UserProfile).filter(UserProfile.id == uuid.UUID(user_id)).first()
    if not reviewer:
        raise HTTPException(status_code=404, detail="Reviewer profile not found")

    review = FarmerReview(
        farmer_id=uuid.UUID(farmer_id),
        reviewer_id=uuid.UUID(user_id),
        reviewer_name=reviewer.full_name or reviewer.email,
        reviewer_initials=make_initials(reviewer.full_name or reviewer.email),
        rating=payload.rating,
        body=payload.body,
    )
    db.add(review)

    # Recalculate farmer average rating
    fs = db.query(FarmerStats).filter(FarmerStats.user_id == uuid.UUID(farmer_id)).first()
    if fs:
        all_ratings = [r.rating for r in db.query(FarmerReview).filter(
            FarmerReview.farmer_id == uuid.UUID(farmer_id)
        ).all()] + [payload.rating]
        fs.average_rating = round(sum(all_ratings) / len(all_ratings), 2)
        fs.total_reviews  = len(all_ratings)

    db.commit()
    db.refresh(review)
    return FarmerReviewOut(
        id=str(review.id),
        reviewerId=str(review.reviewer_id),
        reviewerName=review.reviewer_name,
        reviewerInitials=review.reviewer_initials,
        rating=review.rating,
        body=review.body,
        createdAt=review.created_at.isoformat(),
        helpful=review.helpful,
        isHelpfulByMe=False,
    )


@router.post("/reviews/{review_id}/helpful")
def mark_helpful(
    review_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    review = db.query(FarmerReview).filter(FarmerReview.id == uuid.UUID(review_id)).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    vote = db.query(ReviewHelpful).filter(
        ReviewHelpful.review_id == uuid.UUID(review_id),
        ReviewHelpful.voter_id  == uuid.UUID(user_id)
    ).first()

    if vote:
        db.delete(vote)
        review.helpful = max(0, review.helpful - 1)
    else:
        db.add(ReviewHelpful(review_id=uuid.UUID(review_id), voter_id=uuid.UUID(user_id)))
        review.helpful += 1

    db.commit()
    return {"helpful": review.helpful}