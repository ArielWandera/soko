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


class ProductUnit(str, enum.Enum):
    kg      = "kg"
    litre   = "litre"
    bag     = "bag"
    crate   = "crate"
    bunch   = "bunch"
    piece   = "piece"
    tonne   = "tonne"


class ProductCategory(str, enum.Enum):
    grains    = "Grains"
    vegeta    = "Vegetables"
    fruits    = "Fruits"
    herbs     = "Herbs"
    dairy     = "Dairy"
    poultry   = "Poultry"
    livestock = "Livestock"
    fish      = "Fish"
    other     = "Other"


class ListingStatus(str, enum.Enum):
    draft    = "draft"
    active   = "active"
    sold_out = "sold_out"
    archived = "archived"


class Listing(Base):
    __tablename__ = "listings"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id     = Column(UUID(as_uuid=True), nullable=False, index=True)
    slug          = Column(String, unique=True, nullable=False, index=True)

    # Core info
    name          = Column(String,  nullable=False)
    category      = Column(SAEnum(ProductCategory), nullable=False)
    description   = Column(Text,    nullable=True)
    tags          = Column(String,  nullable=True)    # comma-separated
    district      = Column(String,  nullable=False)
    village       = Column(String,  nullable=True)

    # Pricing
    price         = Column(Float,   nullable=False)
    unit          = Column(SAEnum(ProductUnit), nullable=False)
    total_qty     = Column(Float,   nullable=False)
    available_qty = Column(Float,   nullable=False)
    minimum_order = Column(Float,   default=1.0)
    fresh         = Column(Boolean, default=True)

    # Extra detail fields
    harvest_date   = Column(DateTime, nullable=True)
    storage_notes  = Column(String,   nullable=True)

    # Denormalised review stats
    review_count   = Column(Integer, default=0)
    average_rating = Column(Float,   default=0.0)

    # Farmer snapshot — captured at listing creation
    farmer_name          = Column(String,  nullable=True)
    farmer_district      = Column(String,  nullable=True)
    farmer_verified      = Column(Boolean, default=False)
    farmer_phone         = Column(String,  nullable=True)
    farmer_response_time = Column(String,  nullable=True)
    farmer_member_since  = Column(String,  nullable=True)
    farmer_total_sales   = Column(Integer, default=0)

    # Status
    status        = Column(SAEnum(ListingStatus), default=ListingStatus.draft)

    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    images          = relationship("ListingImage",   back_populates="listing",
                                   cascade="all, delete-orphan")
    price_tiers     = relationship("PriceTier",      back_populates="listing",
                                   cascade="all, delete-orphan")
    product_reviews = relationship("ProductReview",  back_populates="listing",
                                   cascade="all, delete-orphan")


class ListingImage(Base):
    __tablename__ = "listing_images"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id"), nullable=False)
    url        = Column(String,  nullable=False)    # Cloudinary CDN URL
    public_id  = Column(String,  nullable=True)     # Cloudinary public_id for deletion
    order      = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    listing = relationship("Listing", back_populates="images")


class PriceTier(Base):
    __tablename__ = "price_tiers"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id"), nullable=False)
    min_qty    = Column(Float,  nullable=False)
    price      = Column(Float,  nullable=False)
    label      = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    listing = relationship("Listing", back_populates="price_tiers")


class ProductReview(Base):
    __tablename__ = "product_reviews"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id        = Column(UUID(as_uuid=True), ForeignKey("listings.id"), nullable=False)
    reviewer_id       = Column(UUID(as_uuid=True), nullable=False)
    reviewer_name     = Column(String,  nullable=False)
    reviewer_initials = Column(String,  nullable=False)
    rating            = Column(Integer, nullable=False)
    body              = Column(Text,    nullable=False)
    helpful           = Column(Integer, default=0)
    created_at        = Column(DateTime, default=datetime.utcnow)

    listing       = relationship("Listing", back_populates="product_reviews")
    helpful_votes = relationship("ProductReviewHelpful", back_populates="review",
                                 cascade="all, delete-orphan")


class ProductReviewHelpful(Base):
    __tablename__ = "product_review_helpful"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id  = Column(UUID(as_uuid=True), ForeignKey("product_reviews.id"), nullable=False)
    voter_id   = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    review = relationship("ProductReview", back_populates="helpful_votes")