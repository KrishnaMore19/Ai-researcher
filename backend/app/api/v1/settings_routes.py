# app/api/v1/settings_routes.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import json

from app.schemas import subscription as subscription_schema
from app.services.subscription_service import SubscriptionService
from app.services.payment_service import PaymentService
from app.services.auth_service import AuthService
from app.db.session import get_db

router = APIRouter(prefix="/settings", tags=["Settings"])
logger = logging.getLogger(__name__)

# ------------------------------
# Get current user's subscription
# ------------------------------
@router.get("/subscription", response_model=subscription_schema.SubscriptionResponse)
async def get_current_subscription(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """
    Get the current user's active subscription.
    If no subscription exists, creates a free Starter plan automatically.
    """
    subscription_service = SubscriptionService(db)

    # Try to get existing subscription
    subscription = await subscription_service.get_user_subscription(user_id=current_user.id)

    # If not found, automatically create a free "Starter" plan
    if not subscription:
        logger.info(f"Creating default Starter subscription for user {current_user.id}")
        subscription = await subscription_service.create_subscription(
            user_id=current_user.id,
            plan_name="Starter",
            price=0.0,
            period="month"
        )
        logger.info(f"✓ Created Starter subscription for user {current_user.id}")

    return subscription


# ------------------------------
# Upgrade subscription
# ------------------------------
@router.post("/subscription/upgrade")
async def upgrade_subscription(
    subscription_request: subscription_schema.SubscriptionUpgradeRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """
    Upgrade subscription plan.
    - Starter (free): Upgrades directly
    - Pro/Enterprise (paid): Creates payment order and returns payment details
    """
    subscription_service = SubscriptionService(db)
    payment_service = PaymentService()
    plan_name = subscription_request.plan_name.strip()
    
    # Validate plan name
    valid_plans = ["Starter", "Pro", "Enterprise"]
    if plan_name not in valid_plans:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan. Choose one of: {', '.join(valid_plans)}"
        )
    
    # Get or create current subscription
    current_subscription = await subscription_service.get_user_subscription(user_id=current_user.id)
    
    if not current_subscription:
        logger.info(f"No subscription found, creating Starter for user {current_user.id}")
        current_subscription = await subscription_service.create_subscription(
            user_id=current_user.id,
            plan_name="Starter",
            price=0.0,
            period="month"
        )
    
    if current_subscription and current_subscription.plan_name == plan_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You are already on the {plan_name} plan"
        )
    
    # If upgrading to Starter (free plan), do it directly
    if plan_name == "Starter":
        try:
            updated_subscription = await subscription_service.upgrade_subscription(
                user_id=current_user.id,
                new_plan=plan_name
            )
            return {
                "success": True,
                "requires_payment": False,
                "message": f"Successfully switched to {plan_name} plan",
                "subscription": updated_subscription
            }
        except Exception as e:
            logger.error(f"Error upgrading to Starter: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error upgrading subscription: {str(e)}"
            )
    
    # For paid plans (Pro/Enterprise), create payment order
    plan_price = subscription_service._get_plan_price(plan_name)
    
    # Get user phone (required by Razorpay)
    user_phone = getattr(current_user, 'phone', None)
    if not user_phone or len(str(user_phone).strip()) < 10:
        user_phone = "9999999999"  # Default for testing
    
    try:
        logger.info(f"Creating payment order for user {current_user.id}, plan {plan_name}")
        
        # Create payment order
        payment_details = await payment_service.create_payment_order(
            user_id=str(current_user.id),
            user_email=current_user.email,
            user_phone=str(user_phone),
            plan_name=plan_name,
            amount=plan_price
        )
        
        logger.info(f"Payment order created: {payment_details['order_id']}")
        
        return {
            "success": True,
            "requires_payment": True,
            "message": "Complete payment to upgrade your plan",
            "order_id": payment_details["order_id"],
            "amount": payment_details["amount"],
            "amount_in_paise": payment_details["amount_in_paise"],
            "currency": payment_details["currency"],
            "plan_name": plan_name,
            "key_id": payment_details["key_id"],  # Frontend needs this for Razorpay checkout
            "user_email": current_user.email,
            "user_phone": str(user_phone),
            "user_id": str(current_user.id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating payment order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment order: {str(e)}"
        )


# ------------------------------
# Verify Payment (Frontend calls this after successful payment)
# ------------------------------
@router.post("/subscription/verify-payment")
async def verify_payment(
    payment_data: subscription_schema.PaymentVerificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """
    Verify payment signature and process successful payment.
    Called by frontend after Razorpay checkout is completed.
    """
    payment_service = PaymentService()
    
    try:
        logger.info(f"Verifying payment: order_id={payment_data.order_id}, payment_id={payment_data.payment_id}")
        
        # Verify payment signature
        is_valid = payment_service.verify_payment_signature(
            order_id=payment_data.order_id,
            payment_id=payment_data.payment_id,
            signature=payment_data.signature
        )
        
        if not is_valid:
            logger.error(f"Invalid payment signature for order {payment_data.order_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment verification failed: Invalid signature"
            )
        
        # Verify payment status
        payment_verified = await payment_service.verify_payment(
            order_id=payment_data.order_id,
            payment_id=payment_data.payment_id,
            signature=payment_data.signature
        )
        
        if not payment_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment verification failed: Payment not completed"
            )
        
        # Get order details to extract plan name
        order_details = await payment_service.get_payment_status(payment_data.order_id)
        plan_name = order_details.get("notes", {}).get("plan_name", "Pro")
        amount = order_details.get("amount", 0)
        
        # Process successful payment
        result = await payment_service.process_successful_payment(
            db=db,
            order_id=payment_data.order_id,
            payment_id=payment_data.payment_id,
            user_id=str(current_user.id),
            plan_name=plan_name,
            amount=amount
        )
        
        logger.info(f"✓ Payment verified and processed: {payment_data.order_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment verification error: {str(e)}"
        )


# ------------------------------
# Webhook (Optional - for server-to-server notifications)
# ------------------------------
@router.post("/subscription/webhook")
async def payment_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Razorpay webhook - optional server-to-server notification.
    This is a backup in case the payment is completed but frontend doesn't call verify.
    
    NOTE: In test mode, you need to configure webhooks in Razorpay Dashboard.
    """
    payment_service = PaymentService()
    
    try:
        # Get raw body
        body = await request.body()
        
        # Check if body is empty
        if not body:
            logger.warning("Webhook received empty body")
            return {"status": "error", "message": "Empty webhook body"}
        
        # Parse JSON
        try:
            webhook_data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Webhook JSON decode error: {str(e)}")
            logger.error(f"Raw body: {body[:200]}")  # Log first 200 chars
            return {"status": "error", "message": "Invalid JSON in webhook"}
        
        logger.info(f"Received webhook event: {webhook_data.get('event', 'unknown')}")
        
        # Razorpay webhook format
        event = webhook_data.get("event")
        payload = webhook_data.get("payload", {})
        
        if event == "payment.authorized" or event == "payment.captured":
            payment = payload.get("payment", {}).get("entity", {})
            order_id = payment.get("order_id")
            payment_id = payment.get("id")
            
            if not order_id or not payment_id:
                logger.error("Missing order_id or payment_id in webhook")
                return {"status": "error", "message": "Invalid webhook data"}
            
            logger.info(f"Processing webhook payment: order={order_id}, payment={payment_id}")
            
            # Get order details to extract user info and plan
            try:
                order_details = await payment_service.get_payment_status(order_id)
                user_id = order_details.get("notes", {}).get("user_id")
                plan_name = order_details.get("notes", {}).get("plan_name", "Pro")
                amount = order_details.get("amount", 0)
                
                if user_id:
                    result = await payment_service.process_successful_payment(
                        db=db,
                        order_id=order_id,
                        payment_id=payment_id,
                        user_id=user_id,
                        plan_name=plan_name,
                        amount=amount
                    )
                    logger.info(f"✓ Webhook processed payment: {order_id}")
                    return {"status": "success", "result": result}
                else:
                    logger.error("No user_id found in order notes")
                    return {"status": "error", "message": "User ID not found"}
            except Exception as e:
                logger.error(f"Failed to process webhook payment: {str(e)}")
                return {"status": "error", "message": str(e)}
        
        logger.info(f"Webhook event acknowledged: {event}")
        return {"status": "success", "message": f"Event {event} acknowledged"}
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}


# ------------------------------
# Billing history
# ------------------------------
@router.get("/billing-history", response_model=List[subscription_schema.BillingHistoryResponse])
async def get_billing_history(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """
    Get billing history for the current user.
    Returns all invoices and payment records.
    """
    subscription_service = SubscriptionService(db)
    
    # Ensure user has a subscription first
    subscription = await subscription_service.get_user_subscription(user_id=current_user.id)
    if not subscription:
        logger.info(f"Creating default subscription for billing history - user {current_user.id}")
        await subscription_service.create_subscription(
            user_id=current_user.id,
            plan_name="Starter",
            price=0.0,
            period="month"
        )
    
    history = await subscription_service.get_billing_history(user_id=current_user.id)
    logger.info(f"Retrieved {len(history)} billing records for user {current_user.id}")
    return history


# ------------------------------
# Add billing record (testing only)
# ------------------------------
@router.post("/billing/add-record", response_model=subscription_schema.BillingHistoryResponse)
async def add_billing_record(
    amount: float,
    invoice_number: str,
    status: str = "Paid",
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user)
):
    """
    Add a billing record (for testing or manual billing).
    """
    subscription_service = SubscriptionService(db)
    
    try:
        # Ensure user has a subscription
        subscription = await subscription_service.get_user_subscription(user_id=current_user.id)
        if not subscription:
            subscription = await subscription_service.create_subscription(
                user_id=current_user.id,
                plan_name="Starter",
                price=0.0,
                period="month"
            )
        
        record = await subscription_service.add_billing_record(
            user_id=current_user.id,
            amount=amount,
            invoice_number=invoice_number,
            status=status
        )
        logger.info(f"✓ Added billing record: {invoice_number} for user {current_user.id}")
        return record
    except Exception as e:
        logger.error(f"Error adding billing record: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding billing record: {str(e)}"
        )