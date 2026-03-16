from fastapi import APIRouter, Query
from app.http_client import get_produce_listing, search_produce

router = APIRouter(prefix="/produce", tags=["Browse Produce"])


@router.get("/")
async def browse_produce(
    name: str | None = Query(default=None, description="Search by produce name"),
    district: str | None = Query(default=None, description="Filter by district"),
    min_price: float | None = Query(default=None, description="Minimum price per kg"),
    max_price: float | None = Query(default=None, description="Maximum price per kg"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
):
    """
    Search produce listings. Proxies to Produce service.
    Buyers use this to find what's available before placing an order.
    """
    return await search_produce(
        name=name,
        district=district,
        min_price=min_price,
        max_price=max_price,
        page=page,
        page_size=page_size,
    )


@router.get("/{produce_id}")
async def get_produce(produce_id: int):
    """Get a single produce listing by ID."""
    listing = await get_produce_listing(produce_id)
    if not listing:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Produce listing not found")
    return listing
