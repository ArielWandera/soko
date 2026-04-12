from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.core.dependencies import farmer_only
from app.models.produce import Listing, ListingStatus
from app.schemas.produce import AiPriceSuggestion
from typing import Optional

router = APIRouter(tags=["Pricing"])


@router.get("/price-suggestion", response_model=AiPriceSuggestion,
            dependencies=[Depends(farmer_only)])
def get_price_suggestion(
    category: str          = Query(...),
    district: Optional[str] = Query(default=None),
    unit:     str          = Query(...),
    db: Session = Depends(get_db)
):
    """
    Returns a price suggestion based on existing active listings
    for the same category, unit and optionally district.
    """
    q = db.query(Listing).filter(
        Listing.category == category,
        Listing.unit     == unit,
        Listing.status   == ListingStatus.active,
    )
    if district:
        q = q.filter(Listing.district == district)

    prices = [l.price for l in q.all()]

    if not prices:
        # Fallback — no data yet, return zeros with honest basis
        return AiPriceSuggestion(
            min=0, max=0, suggested=0,
            basis=f"No listings found yet for {category} in {district or 'Uganda'}"
        )

    avg       = sum(prices) / len(prices)
    suggested = round(avg, -2)        # round to nearest 100 UGX
    basis_loc = district or "Uganda"

    return AiPriceSuggestion(
        min=round(min(prices)),
        max=round(max(prices)),
        suggested=suggested,
        basis=f"Based on {len(prices)} active listings in {basis_loc}"
    )