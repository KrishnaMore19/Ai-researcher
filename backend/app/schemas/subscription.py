# app/schemas/subscription.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from uuid import UUID

# ============================================
# Billing Schemas
# ============================================
class BillingBase(BaseModel):
    invoice_number: str
    amount: float
    status: str = "Paid"
    date: Optional[datetime] = None

class BillingCreate(BillingBase):
    pass

class BillingResponse(BillingBase):
    id: int
    date: datetime

    class Config:
        from_attributes = True

# Alias for backward compatibility
BillingHistoryResponse = BillingResponse

# ============================================
# Subscription Schemas
# ============================================
class SubscriptionBase(BaseModel):
    plan_name: str
    price: float
    period: str
    active: bool = True

    documents_used: int = 0
    documents_limit: int = 0
    queries_used: int = 0
    queries_limit: int = 0
    storage_used: float = 0.0
    storage_limit: float = 0.0

class SubscriptionCreate(SubscriptionBase):
    user_id: UUID

class SubscriptionUpdate(BaseModel):
    plan_name: Optional[str] = None
    active: Optional[bool] = None
    documents_used: Optional[int] = None
    queries_used: Optional[int] = None
    storage_used: Optional[float] = None

class SubscriptionResponse(SubscriptionBase):
    id: int
    user_id: UUID
    start_date: datetime
    end_date: Optional[datetime] = None
    billing_history: List[BillingResponse] = []

    class Config:
        from_attributes = True

# ============================================
# Payment & Upgrade Schemas
# ============================================
class SubscriptionUpgradeRequest(BaseModel):
    """Request to upgrade subscription plan"""
    plan_name: str = Field(..., example="Pro", description="Plan name: Starter, Pro, or Enterprise")

    class Config:
        json_schema_extra = {
            "example": {
                "plan_name": "Pro"
            }
        }

class PaymentVerificationRequest(BaseModel):
    """
    Schema for verifying Razorpay payment after checkout.
    Frontend sends these fields after successful payment.
    """
    order_id: str = Field(..., description="Razorpay Order ID")
    payment_id: str = Field(..., description="Razorpay Payment ID")
    signature: str = Field(..., description="Razorpay Payment Signature for verification")

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "order_MhVSeNGfT5u87Q",
                "payment_id": "pay_MhVSfP3h8wK9zT",
                "signature": "9d3b8c5f6e4a7b2c1d0e9f8g7h6i5j4k3l2m1n0o9p8q7r6s5t4u3v2w1x0y9z"
            }
        }

class PaymentOrderResponse(BaseModel):
    """Response after creating payment order"""
    success: bool
    requires_payment: bool
    message: str
    order_id: Optional[str] = None
    amount: Optional[float] = None
    amount_in_paise: Optional[int] = None
    currency: Optional[str] = None
    plan_name: Optional[str] = None
    key_id: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None
    user_id: Optional[str] = None
    subscription: Optional[SubscriptionResponse] = None

class PaymentVerificationResponse(BaseModel):
    """Response after payment verification"""
    success: bool
    message: str
    subscription: Optional[SubscriptionResponse] = None
    invoice_number: Optional[str] = None
    order_id: Optional[str] = None
    payment_id: Optional[str] = None