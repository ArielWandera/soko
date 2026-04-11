from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import FarmerFollow
import uuid

router = APIRouter(tags=["Follows"])


@router.post("/{farmer_id}/follow")
def toggle_follow(
    farmer_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    if farmer_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    existing = db.query(FarmerFollow).filter(
        FarmerFollow.farmer_id   == uuid.UUID(farmer_id),
        FarmerFollow.follower_id == uuid.UUID(user_id)
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {"following": False}

    db.add(FarmerFollow(farmer_id=uuid.UUID(farmer_id), follower_id=uuid.UUID(user_id)))
    db.commit()
    return {"following": True}