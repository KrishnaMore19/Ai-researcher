# app/services/payment_service.py
import hashlib
import hmac
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

import httpx
import razorpay
from razorpay.errors import BadRequestError, SignatureVerificationError
from fastapi import HTTPException, status

from app.core.config import settings
from app.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Service to handle Razorpay payment gateway integration
    """

    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        
        # Initialize Razorpay client
        self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
        
        logger.info(f"Payment Service initialized in {'TEST' if 'test' in self.key_id else 'LIVE'} mode")

    # ------------------------------
    # Create Payment Order
    # ------------------------------
    async def create_payment_order(
        self,
        user_id: str,
        user_email: str,
        user_phone: str,
        plan_name: str,
        amount: float
    ) -> Dict[str, Any]:
        """
        Create a payment order with Razorpay
        """
        try:
            # Generate SHORT unique receipt ID (max 40 chars for Razorpay)
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            random_suffix = uuid.uuid4().hex[:6]
            receipt_id = f"RCP_{timestamp}_{random_suffix}"  # ~26 chars
            
            # Razorpay amount is in paise (multiply by 100 for INR)
            amount_in_paise = int(float(amount) * 100)
            
            # Prepare order data for Razorpay
            order_data = {
                "amount": amount_in_paise,
                "currency": settings.CURRENCY or "INR",
                "receipt": receipt_id,
                "notes": {
                    "user_id": str(user_id),
                    "plan_name": plan_name,
                    "user_email": user_email,
                    "user_phone": user_phone
                }
            }
            
            logger.info(f"Creating Razorpay order with receipt: {receipt_id}")
            logger.info(f"Order data: amount={amount_in_paise} paise (₹{amount}), plan={plan_name}")
            
            # Create order via Razorpay API
            order = self.client.order.create(data=order_data)
            
            logger.info(f"✓ Razorpay order created successfully: {order['id']}")
            logger.info(f"Order status: {order.get('status')}")
            
            if not order or 'id' not in order:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create payment order"
                )
            
            return {
                "order_id": order['id'],
                "receipt_id": receipt_id,
                "amount": amount,
                "amount_in_paise": amount_in_paise,
                "currency": settings.CURRENCY or "INR",
                "plan_name": plan_name,
                "key_id": self.key_id  # Frontend needs this for checkout
            }
                
        except BadRequestError as e:
            logger.error(f"Razorpay BadRequest error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error creating payment order: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create payment: {str(e)}"
            )

    # ------------------------------
    # Get Payment Status
    # ------------------------------
    async def get_payment_status(self, order_id: str) -> Dict[str, Any]:
        """
        Check payment status from Razorpay
        """
        try:
            logger.info(f"Fetching order status: {order_id}")
            
            # Get order details from Razorpay
            order = self.client.order.fetch(order_id)
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            logger.info(f"Order {order_id} status: {order.get('status')}")
            
            return {
                "order_id": order.get("id"),
                "order_status": order.get("status"),  # created, attempted, paid, etc.
                "amount": order.get("amount") / 100,  # Convert from paise to rupees
                "currency": order.get("currency"),
                "notes": order.get("notes", {})
            }
                
        except BadRequestError as e:
            logger.error(f"Failed to get payment status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        except Exception as e:
            logger.error(f"Error checking payment status: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to check payment status: {str(e)}"
            )

    # ------------------------------
    # Verify Payment Signature
    # ------------------------------
    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str
    ) -> bool:
        """
        Verify Razorpay payment signature for security
        Razorpay uses: SHA256(order_id + "|" + payment_id, key_secret)
        """
        try:
            # Create signature string: order_id|payment_id
            signature_data = f"{order_id}|{payment_id}"
            
            # Generate expected signature using HMAC SHA256
            expected_signature = hmac.new(
                self.key_secret.encode('utf-8'),
                signature_data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            is_valid = hmac.compare_digest(expected_signature, signature)
            
            if not is_valid:
                logger.warning(f"❌ Invalid signature for order {order_id}, payment {payment_id}")
                logger.warning(f"Expected: {expected_signature[:20]}... Got: {signature[:20]}...")
            else:
                logger.info(f"✓ Signature verified for order {order_id}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying signature: {str(e)}", exc_info=True)
            return False

    # ------------------------------
    # Verify Payment (Full verification)
    # ------------------------------
    async def verify_payment(
        self,
        order_id: str,
        payment_id: str,
        signature: str
    ) -> bool:
        """
        Verify payment was successful using Razorpay's verification
        """
        try:
            logger.info(f"Verifying payment: order={order_id}, payment={payment_id}")
            
            # Step 1: Verify signature
            if not self.verify_payment_signature(order_id, payment_id, signature):
                logger.error(f"❌ Signature verification failed for {order_id}")
                return False
            
            # Step 2: Fetch payment to verify it's actually completed
            payment = self.client.payment.fetch(payment_id)
            payment_status = payment.get("status")
            
            logger.info(f"Payment {payment_id} status: {payment_status}")
            
            # In test mode, 'authorized' is also acceptable (you need to capture manually in dashboard)
            # In live mode, we want 'captured'
            if payment_status in ["captured", "authorized"]:
                logger.info(f"✓ Payment verified: {payment_id} ({payment_status})")
                return True
            else:
                logger.warning(f"❌ Payment not completed: {payment_id}, status: {payment_status}")
                return False
                
        except BadRequestError as e:
            logger.error(f"Error verifying payment - BadRequest: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}", exc_info=True)
            return False

    # ------------------------------
    # Process Successful Payment
    # ------------------------------
    async def process_successful_payment(
        self,
        db,
        order_id: str,
        payment_id: str,
        user_id: str,
        plan_name: str,
        amount: float
    ) -> Dict[str, Any]:
        """
        Process successful payment and upgrade subscription
        """
        try:
            subscription_service = SubscriptionService(db)
            
            # Convert amount from paise to rupees if needed
            if amount > 1000:  # If amount is in paise
                amount = amount / 100
            
            logger.info(f"Processing payment: user={user_id}, plan={plan_name}, amount=₹{amount}")
            
            # Upgrade the subscription
            logger.info(f"Upgrading user {user_id} to {plan_name} plan")
            updated_subscription = await subscription_service.upgrade_subscription(
                user_id=user_id,
                new_plan=plan_name
            )
            
            # Add billing record
            invoice_number = f"INV_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
            
            logger.info(f"Creating billing record: {invoice_number}")
            await subscription_service.add_billing_record(
                user_id=user_id,
                amount=amount,
                invoice_number=invoice_number,
                status="Paid"
            )
            
            logger.info(f"✓ Successfully processed payment for user {user_id}, upgraded to {plan_name}")
            
            return {
                "success": True,
                "message": f"Successfully upgraded to {plan_name} plan",
                "subscription": updated_subscription,
                "invoice_number": invoice_number,
                "order_id": order_id,
                "payment_id": payment_id
            }
            
        except Exception as e:
            logger.error(f"Error processing successful payment: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment successful but subscription upgrade failed: {str(e)}"
            )

    # ------------------------------
    # Handle Failed Payment
    # ------------------------------
    async def handle_failed_payment(
        self,
        order_id: str,
        user_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle failed payment
        """
        logger.warning(f"❌ Payment failed for user {user_id}, order {order_id}: {reason}")
        
        return {
            "success": False,
            "message": "Payment failed",
            "order_id": order_id,
            "reason": reason or "Payment was not completed"
        }