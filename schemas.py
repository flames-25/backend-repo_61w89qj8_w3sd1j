"""
Database Schemas for Pikalba

Define MongoDB collection schemas using Pydantic models.
Each Pydantic model represents a collection (lowercased class name).
"""
from __future__ import annotations
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal, Dict
from datetime import datetime

# ---------- Core Domain Schemas ----------

class Product(BaseModel):
    sku: str = Field(..., description="Stock keeping unit, unique")
    title: str
    description: Optional[str] = None
    category: Literal["pickleball", "padel", "beach", "apparel"]
    brand: str
    price: float = Field(..., ge=0)
    currency: str = Field(default="USD")
    images: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    variants: List[Dict] = Field(default_factory=list, description="Size/Color variations")
    stock: int = Field(default=0, ge=0)
    fulfillment: Literal["self", "third_party"] = Field(default="self")
    eco_score: Optional[int] = Field(None, ge=1, le=5)
    active: bool = Field(default=True)

class CartItem(BaseModel):
    sku: str
    quantity: int = Field(..., ge=1)
    price: float = Field(..., ge=0)
    title: Optional[str] = None
    image: Optional[str] = None

class ShippingAddress(BaseModel):
    name: str
    line1: str
    line2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str
    phone: Optional[str] = None

class Order(BaseModel):
    user_id: Optional[str] = None
    email: Optional[EmailStr] = None
    items: List[CartItem]
    subtotal: float
    shipping_cost: float
    discount: float = 0
    total: float
    currency: str = "USD"
    shipping_address: ShippingAddress
    shipping_method: Literal["standard", "express"] = "standard"
    payment_method: Literal["paypal"] = "paypal"
    status: Literal["pending", "paid", "shipped", "delivered", "cancelled"] = "pending"
    paypal_order_id: Optional[str] = None
    tracking_number: Optional[str] = None
    created_at: Optional[datetime] = None

class Wishlist(BaseModel):
    user_id: str
    skus: List[str] = Field(default_factory=list)

class PromoCode(BaseModel):
    code: str
    description: Optional[str] = None
    percent_off: Optional[int] = Field(None, ge=1, le=90)
    amount_off: Optional[float] = Field(None, ge=0)
    active: bool = True

class BlogPost(BaseModel):
    title: str
    slug: str
    content: str
    cover_image: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    published: bool = True
    created_at: Optional[datetime] = None

class Event(BaseModel):
    title: str
    date: datetime
    location: str
    description: Optional[str] = None
    link: Optional[str] = None

class Newsletter(BaseModel):
    email: EmailStr
    source: Optional[str] = None

class RecommendationFeedback(BaseModel):
    user_id: Optional[str] = None
    sku: str
    liked: bool

class User(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    locale: Literal["en", "es"] = "en"
    marketing_opt_in: bool = False
