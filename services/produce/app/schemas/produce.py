from pydantic import BaseModel, field_validator
from typing import List, Optional
from enum import Enum


class ProductUnit(str, Enum):
    kg      = "kg"
    litre   = "litre"
    bag     = "bag"
    crate   = "crate"
    bunch   = "bunch"
    piece   = "piece"
    tonne   = "tonne"


class ProductCategory(str, Enum):
    grains    = "Grains"
    vegeta    = "Vegetables"
    fruits    = "Fruits"
    herbs     = "Herbs"
    dairy     = "Dairy"
    poultry   = "Poultry"
    livestock = "Livestock"
    fish      = "Fish"
    other     = "Other"


class ListingStatus(str, Enum):
    draft    = "draft"
    active   = "active"
    sold_out = "sold_out"
    archived = "archived"


# ── Price tier
class PriceTierIn(BaseModel):
    minQty: float
    price:  float
    label:  str


class PriceTierOut(BaseModel):
    id:     str
    minQty: float
    price:  float
    label:  str


# ── Farmer snapshot (matches ProductFarmer in frontend)
class ProductFarmerOut(BaseModel):
    name:         str
    district:     str
    verified:     bool
    phone:        Optional[str]
    responseTime: Optional[str]
    totalSales:   Optional[int]
    memberSince:  Optional[str]


# ── Product review
class ProductReviewOut(BaseModel):
    id:               str
    reviewer:         str
    reviewerInitials: str
    rating:           int
    body:             str
    createdAt:        str
    helpful:          int
    isHelpfulByMe:    Optional[bool] = None


class CreateProductReviewPayload(BaseModel):
    rating: int
    body:   str

    @field_validator("rating")
    @classmethod
    def valid_rating(cls, v):
        if not 0 <= v <= 5:
            raise ValueError("Rating must be between 0 and 5")
        return v


# ── Full listing out — matches Product interface in frontend exactly
class ListingOut(BaseModel):
    # Flat fields used by card components
    id:           str
    slug:         str
    farmerId:     str
    name:         str
    category:     str
    image:        str           # first image — card fallback
    img:          str           # alias — frontend uses both
    badge:        Optional[str]
    farmer:       str           # flat farmer name for cards
    district:     str           # flat district for cards
    verified:     bool          # flat verified for cards
    price:        float
    priceValue:   float         # alias of price
    unit:         str
    qty:          float         # availableQty alias
    qtyDisplay:   str           # "42 kg available"
    rating:       float
    fresh:        bool
    status:       str

    # Detail page fields
    description:  Optional[str]
    images:       List[str]
    minimumOrder: float
    harvestDate:  Optional[str]
    storage:      Optional[str]
    tags:         List[str]
    priceTiers:   List[PriceTierOut]
    reviewCount:  int
    isWishlisted: Optional[bool]       = None
    farmerDetail: Optional[ProductFarmerOut] = None
    posted:       Optional[str]        = None
    createdAt:    str
    updatedAt:    str


# ── Create listing payload
class CreateListingPayload(BaseModel):
    name:         str
    category:     ProductCategory
    district:     str
    village:      Optional[str]        = None
    description:  Optional[str]        = None
    tags:         List[str]            = []
    price:        float
    unit:         ProductUnit
    totalQty:     float
    minimumOrder: float                = 1.0
    fresh:        bool                 = True
    harvestDate:  Optional[str]        = None   # ISO string
    storage:      Optional[str]        = None
    priceTiers:   Optional[List[PriceTierIn]] = None

    @field_validator("price", "totalQty", "minimumOrder")
    @classmethod
    def must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Must be greater than 0")
        return v

    @field_validator("tags")
    @classmethod
    def max_tags(cls, v):
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        return v


# ── Update listing payload
class UpdateListingPayload(BaseModel):
    name:         Optional[str]             = None
    category:     Optional[ProductCategory] = None
    district:     Optional[str]             = None
    village:      Optional[str]             = None
    description:  Optional[str]             = None
    tags:         Optional[List[str]]       = None
    price:        Optional[float]           = None
    unit:         Optional[ProductUnit]     = None
    totalQty:     Optional[float]           = None
    minimumOrder: Optional[float]           = None
    fresh:        Optional[bool]            = None
    harvestDate:  Optional[str]             = None
    storage:      Optional[str]             = None
    priceTiers:   Optional[List[PriceTierIn]] = None
    status:       Optional[ListingStatus]   = None


# ── Create listing response
class CreateListingResponse(BaseModel):
    id:        str
    slug:      str
    imageUrls: List[str]
    message:   str


# ── AI price suggestion (matches AiPriceSuggestion in frontend)
class AiPriceSuggestion(BaseModel):
    min:       float
    max:       float
    suggested: float
    basis:     str


# ── Internal stock update
class StockUpdatePayload(BaseModel):
    listing_id: str
    quantity:   float