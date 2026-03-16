from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id         = Column(Integer, primary_key=True, index=True)
    buyer_id   = Column(Integer, ForeignKey("buyer_profiles.id"), nullable=False)
    produce_id = Column(Integer, nullable=False)    # FK to produce_db
    order_id   = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)
    stars      = Column(Integer, nullable=False)    # 1-5, enforced by constraint below
    comment    = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Database level enforcement — stars must be between 1 and 5
    __table_args__ = (
        CheckConstraint("stars >= 1 AND stars <= 5", name="valid_star_rating"),
    )

    buyer = relationship("BuyerProfile", back_populates="reviews")
    order = relationship("Order", back_populates="review")
