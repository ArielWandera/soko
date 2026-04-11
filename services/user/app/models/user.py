import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, Float,
    Integer, Text, ForeignKey, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum


class UserRole(str, enum.Enum):
    farmer = "farmer"
    buyer  = "buyer"
    both   = "both"
    admin  = "admin"


class VerificationStatus(str, enum.Enum):
    unverified = "unverified"
    pending    = "pending"
    verified   = "verified"
    rejected   = "rejected"


# Core profile — mirrors auth_credentials.id
class UserProfile(Base):
    __tablename__ = "user_profiles"

    id     = Column(UUID(as_uuid=True), primary_key=True)   # same UUID as auth
    email  = Column(String, unique=True, nullable=False)     # denormalised copy
    role   = Column(SAEnum(UserRole), nullable=False)

    # Core
    full_name  = Column(String,  nullable=True)
    phone      = Column(String,  unique=True, nullable=True)
    avatar_url = Column(String,  nullable=True)
    district   = Column(String,  nullable=True)
    village    = Column(String,  nullable=True)

    # Farmer-specific
    farm_name   = Column(String, nullable=True)
    farmer_bio  = Column(Text,   nullable=True)
    specialties = Column(String, nullable=True)   # comma-separated, max 3

    # Buyer-specific
    interests = Column(String, nullable=True)     # comma-separated, max 3

    # Verification
    verified             = Column(Boolean,        default=False)
    verification_status  = Column(SAEnum(VerificationStatus),
                                  default=VerificationStatus.unverified)

    # Settings
    theme                = Column(String,  default="system")
    notifications_email  = Column(Boolean, default=True)
    notifications_sms    = Column(Boolean, default=False)
    notifications_push   = Column(Boolean, default=True)
    language             = Column(String,  default="en")
    currency             = Column(String,  default="UGX")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    farmer_stats  = relationship("FarmerStats",  back_populates="user",
                                 uselist=False, cascade="all, delete-orphan")
    buyer_stats   = relationship("BuyerStats",   back_populates="user",
                                 uselist=False, cascade="all, delete-orphan")
    reviews       = relationship("FarmerReview", back_populates="farmer",
                                 foreign_keys="FarmerReview.farmer_id",
                                 cascade="all, delete-orphan")
    settings      = relationship("UserSettings", back_populates="user",
                                 uselist=False, cascade="all, delete-orphan")
    followers     = relationship("FarmerFollow", back_populates="farmer",
                                 foreign_keys="FarmerFollow.farmer_id",
                                 cascade="all, delete-orphan")


# Farmer stats — updated by Order Service
# via internal event / webhook
class FarmerStats(Base):
    __tablename__ = "farmer_stats"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id        = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"),
                            unique=True, nullable=False)
    total_listings = Column(Integer, default=0)
    total_sales    = Column(Integer, default=0)
    total_earned   = Column(Integer, default=0)
    pending_payout = Column(Integer, default=0)
    average_rating = Column(Float,   default=0.0)
    total_reviews  = Column(Integer, default=0)
    response_time  = Column(String,  nullable=True)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserProfile", back_populates="farmer_stats")


# Buyer stats — updated by Order Service
class BuyerStats(Base):
    __tablename__ = "buyer_stats"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id        = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"),
                            unique=True, nullable=False)
    total_orders   = Column(Integer, default=0)
    total_spent    = Column(Integer, default=0)    # UGX
    wishlist_count = Column(Integer, default=0)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserProfile", back_populates="buyer_stats")


# Farmer reviews — written by buyers
class FarmerReview(Base):
    __tablename__ = "farmer_reviews"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id   = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    reviewer_id = Column(UUID(as_uuid=True), nullable=False)   # from buyer/both->role
    reviewer_name     = Column(String, nullable=False)
    reviewer_initials = Column(String, nullable=False)
    rating      = Column(Integer, nullable=False)              # 1–5
    body        = Column(Text,    nullable=False)
    helpful     = Column(Integer, default=0)
    created_at  = Column(DateTime, default=datetime.utcnow)

    farmer      = relationship("UserProfile", back_populates="reviews",
                               foreign_keys=[farmer_id])
    helpful_votes = relationship("ReviewHelpful", back_populates="review",
                                 cascade="all, delete-orphan")


# Helpful votes on reviews
class ReviewHelpful(Base):
    __tablename__ = "review_helpful"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id  = Column(UUID(as_uuid=True), ForeignKey("farmer_reviews.id"), nullable=False)
    voter_id   = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    review = relationship("FarmerReview", back_populates="helpful_votes")


# Farmer follows — buyers follow farmers
class FarmerFollow(Base):
    __tablename__ = "farmer_follows"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id  = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    follower_id = Column(UUID(as_uuid=True), nullable=False)   # buyer id — cross-service
    created_at = Column(DateTime, default=datetime.utcnow)

    farmer = relationship("UserProfile", back_populates="followers",
                          foreign_keys=[farmer_id])


# User settings (split out for clean updates)
class UserSettings(Base):
    __tablename__ = "user_settings"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id             = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"),
                                 unique=True, nullable=False)
    theme               = Column(String,  default="system")
    notifications_email = Column(Boolean, default=True)
    notifications_sms   = Column(Boolean, default=False)
    notifications_push  = Column(Boolean, default=True)
    language            = Column(String,  default="en")
    currency            = Column(String,  default="UGX")
    updated_at          = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserProfile", back_populates="settings")