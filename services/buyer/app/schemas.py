from pydantic import BaseModel, field_validator
from datetime import datetime
from app.models.order import OrderStatus, PaymentStatus


# ── Buyer Profile ─────────────────────────────────────────────────────
class BuyerProfileCreate(BaseModel):
    full_name: str
    phone: str | None = None
    district: str | None = None


class BuyerProfileUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    district: str | None = None


class BuyerProfileOut(BaseModel):
    id: int
    user_id: str
    full_name: str
    phone: str | None
    district: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Orders ────────────────────────────────────────────────────────────
class OrderCreate(BaseModel):
    produce_id: int
    quantity_kg: float

    @field_validator("quantity_kg")
    @classmethod
    def quantity_must_be_positive(cls, v):
        if v < 0.1:
            raise ValueError("Quantity must be at least 0.1")
        return v


class OrderOut(BaseModel):
    id: int
    produce_id: int
    farmer_id: str
    quantity_kg: float
    price_per_kg: float
    total_price: float
    status: OrderStatus
    payment_status: PaymentStatus
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderListOut(BaseModel):
    total: int
    page: int
    page_size: int
    results: list[OrderOut]


# ── Reviews ───────────────────────────────────────────────────────────
class ReviewCreate(BaseModel):
    stars: int
    comment: str | None = None

    @field_validator("stars")
    @classmethod
    def stars_must_be_valid(cls, v):
        if v < 1 or v > 5:
            raise ValueError("Stars must be between 1 and 5")
        return v


class ReviewOut(BaseModel):
    id: int
    produce_id: int
    order_id: int
    stars: int
    comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
