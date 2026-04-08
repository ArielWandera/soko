from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.buyer import BuyerProfile
from app.schemas import BuyerProfileCreate, BuyerProfileUpdate, BuyerProfileOut
from app.dependencies import require_buyer

router = APIRouter(prefix="/buyers", tags=["Buyer Profile"])


@router.post("/profile", response_model=BuyerProfileOut, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: BuyerProfileCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_buyer)
):
    existing = db.query(BuyerProfile).filter(BuyerProfile.user_id == user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists")

    profile = BuyerProfile(user_id=user_id, **payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/profile", response_model=BuyerProfileOut)
def get_my_profile(
    db: Session = Depends(get_db),
    user_id: str = Depends(require_buyer)
):
    profile = db.query(BuyerProfile).filter(BuyerProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.patch("/profile", response_model=BuyerProfileOut)
def update_profile(
    payload: BuyerProfileUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_buyer)
):
    profile = db.query(BuyerProfile).filter(BuyerProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile
