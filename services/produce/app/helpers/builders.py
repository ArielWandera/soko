from datetime import datetime
from app.models.produce import Listing
from app.schemas.produce import ListingOut, PriceTierOut, ProductFarmerOut


def time_ago(dt: datetime) -> str:
    delta = datetime.utcnow() - dt
    if delta.days >= 365:
        n = delta.days // 365
        return f"{n} year{'s' if n > 1 else ''} ago"
    if delta.days >= 30:
        n = delta.days // 30
        return f"{n} month{'s' if n > 1 else ''} ago"
    if delta.days >= 1:
        return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
    hours = delta.seconds // 3600
    if hours >= 1:
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    return "Just now"


def get_badge(listing: Listing) -> str | None:
    if listing.fresh:
        return "Fresh"
    return None


def generate_slug(name: str, farmer_id: str) -> str:
    base   = name.lower().strip().replace(" ", "-")
    base   = "".join(c for c in base if c.isalnum() or c == "-")
    suffix = str(farmer_id).replace("-", "")[:8]
    return f"{base}-{suffix}"


def build_listing_out(
    listing: Listing,
    viewer_id: str = None
) -> ListingOut:

    images     = sorted(listing.images, key=lambda i: i.order)
    image_urls = [img.url for img in images]
    first      = image_urls[0] if image_urls else ""

    farmer_detail = ProductFarmerOut(
        name=listing.farmer_name         or "",
        district=listing.farmer_district or "",
        verified=listing.farmer_verified or False,
        phone=listing.farmer_phone,
        responseTime=listing.farmer_response_time,
        totalSales=listing.farmer_total_sales,
        memberSince=listing.farmer_member_since,
    ) if listing.farmer_name else None

    return ListingOut(
        id=str(listing.id),
        slug=listing.slug,
        farmerId=str(listing.farmer_id),
        name=listing.name,
        category=listing.category.value,
        # Flat card fields
        image=first,
        img=first,
        badge=get_badge(listing),
        farmer=listing.farmer_name   or "",
        district=listing.district,
        verified=listing.farmer_verified or False,
        price=listing.price,
        priceValue=listing.price,
        unit=listing.unit.value,
        qty=listing.available_qty,
        qtyDisplay=f"{listing.available_qty} {listing.unit.value} available",
        rating=listing.average_rating or 0.0,
        fresh=listing.fresh,
        status=listing.status.value,
        # Detail fields
        description=listing.description,
        images=image_urls,
        minimumOrder=listing.minimum_order,
        harvestDate=listing.harvest_date.isoformat() if listing.harvest_date else None,
        storage=listing.storage_notes,
        tags=listing.tags.split(",") if listing.tags else [],
        priceTiers=[
            PriceTierOut(
                id=str(t.id),
                minQty=t.min_qty,
                price=t.price,
                label=t.label or ""
            )
            for t in listing.price_tiers
        ],
        reviewCount=listing.review_count   or 0,
        isWishlisted=None,
        farmerDetail=farmer_detail,
        posted=time_ago(listing.created_at),
        createdAt=listing.created_at.isoformat(),
        updatedAt=listing.updated_at.isoformat(),
    )