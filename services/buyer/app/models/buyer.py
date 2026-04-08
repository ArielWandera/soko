from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class BuyerProfile(Base):
    __tablename__ = "buyer_profiles"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(String, unique=True, nullable=False, index=True)   # FK to auth_db (UUID)
    full_name   = Column(String, nullable=False)
    phone       = Column(String, nullable=True)
    district    = Column(String, nullable=True)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    orders  = relationship("Order", back_populates="buyer", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="buyer", cascade="all, delete-orphan")
