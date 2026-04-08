from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class OrderStatus(str, enum.Enum):
    pending   = "pending"       # just placed, awaiting produce service confirmation
    confirmed = "confirmed"     # produce service confirmed stock
    rejected  = "rejected"      # produce service rejected — out of stock
    completed = "completed"     # transaction done
    cancelled = "cancelled"     # buyer cancelled


class PaymentStatus(str, enum.Enum):
    unpaid    = "unpaid"
    pending   = "pending"       # payment initiated (Mobile Money hook)
    paid      = "paid"
    failed    = "failed"


class Order(Base):
    __tablename__ = "orders"

    id             = Column(Integer, primary_key=True, index=True)
    buyer_id       = Column(Integer, ForeignKey("buyer_profiles.id"), nullable=False)
    produce_id     = Column(Integer, nullable=False)   # FK to produce_db
    farmer_id      = Column(String, nullable=False)    # auth user UUID of the farmer
    quantity_kg    = Column(Float, nullable=False)
    price_per_kg   = Column(Float, nullable=False)
    total_price    = Column(Float, nullable=False)
    status         = Column(Enum(OrderStatus), default=OrderStatus.pending, nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.unpaid, nullable=False)
    notes          = Column(String, nullable=True)     # optional buyer notes
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    updated_at     = Column(DateTime(timezone=True), onupdate=func.now())

    buyer  = relationship("BuyerProfile", back_populates="orders")
    review = relationship("Review", back_populates="order", uselist=False)
