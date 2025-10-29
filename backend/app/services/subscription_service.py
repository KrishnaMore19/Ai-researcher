# app/services/subscription_service.py
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException
from uuid import UUID
import logging

from app.models.subscription import Subscription, Billing
from app.schemas.subscription import (
    SubscriptionResponse,
    BillingHistoryResponse,
    SubscriptionCreate
)

logger = logging.getLogger(__name__)


class SubscriptionService:
    """
    Service to manage user subscriptions and billing.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------
    # Get user's current subscription
    # ------------------------------
    async def get_user_subscription(self, user_id) -> Optional[SubscriptionResponse]:
        """
        Get the active subscription for a user.
        If multiple active subscriptions exist, deactivate old ones and keep the latest.
        """
        # Convert to UUID if string
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        
        query = await self.db.execute(
            select(Subscription).where(
                and_(
                    Subscription.user_id == user_uuid,
                    Subscription.active == True
                )
            ).order_by(Subscription.start_date.desc())  # Get newest first
        )
        subscriptions = query.scalars().all()
        
        # Handle multiple active subscriptions
        if len(subscriptions) > 1:
            logger.warning(f"Found {len(subscriptions)} active subscriptions for user {user_id}. Cleaning up...")
            
            # Keep the most recent subscription, deactivate others
            active_subscription = subscriptions[0]
            for old_sub in subscriptions[1:]:
                old_sub.active = False
                self.db.add(old_sub)
                logger.info(f"Deactivated old subscription {old_sub.id} for user {user_id}")
            
            await self.db.commit()
            subscription = active_subscription
        elif len(subscriptions) == 1:
            subscription = subscriptions[0]
        else:
            logger.info(f"No subscription found for user {user_id}")
            return None

        # Get billing history
        billing_query = await self.db.execute(
            select(Billing).where(
                Billing.subscription_id == subscription.id
            ).order_by(Billing.date.desc())
        )
        billing_records = billing_query.scalars().all()
        
        billing_history = [
            BillingHistoryResponse(
                id=record.id,
                invoice_number=record.invoice_number,
                amount=record.amount,
                status=record.status,
                date=record.date
            ) for record in billing_records
        ]

        return SubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            plan_name=subscription.plan_name,
            price=subscription.price,
            period=subscription.period,
            active=subscription.active,
            documents_used=subscription.documents_used,
            documents_limit=subscription.documents_limit,
            queries_used=subscription.queries_used,
            queries_limit=subscription.queries_limit,
            storage_used=subscription.storage_used,
            storage_limit=subscription.storage_limit,
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            billing_history=billing_history
        )

    # ------------------------------
    # Create a new subscription
    # ------------------------------
    async def create_subscription(
        self,
        user_id,
        plan_name: str,
        price: float,
        period: str = "month"
    ) -> SubscriptionResponse:
        """
        Create a new subscription for a user.
        Deactivates any existing active subscriptions.
        """
        # Convert to UUID if string
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        
        # Deactivate any existing active subscriptions
        existing_query = await self.db.execute(
            select(Subscription).where(
                and_(
                    Subscription.user_id == user_uuid,
                    Subscription.active == True
                )
            )
        )
        existing_subs = existing_query.scalars().all()
        
        if existing_subs:
            logger.info(f"Deactivating {len(existing_subs)} existing subscription(s) for user {user_id}")
            for sub in existing_subs:
                sub.active = False
                self.db.add(sub)
        
        # Set limits based on plan
        plan_limits = self._get_plan_limits(plan_name)
        
        new_subscription = Subscription(
            user_id=user_uuid,
            plan_name=plan_name,
            price=price,
            period=period,
            active=True,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30 if period == "month" else 365),
            **plan_limits
        )
        
        self.db.add(new_subscription)
        await self.db.commit()
        await self.db.refresh(new_subscription)
        
        logger.info(f"Created {plan_name} subscription for user {user_id}")

        return SubscriptionResponse(
            id=new_subscription.id,
            user_id=new_subscription.user_id,
            plan_name=new_subscription.plan_name,
            price=new_subscription.price,
            period=new_subscription.period,
            active=new_subscription.active,
            documents_used=new_subscription.documents_used,
            documents_limit=new_subscription.documents_limit,
            queries_used=new_subscription.queries_used,
            queries_limit=new_subscription.queries_limit,
            storage_used=new_subscription.storage_used,
            storage_limit=new_subscription.storage_limit,
            start_date=new_subscription.start_date,
            end_date=new_subscription.end_date,
            billing_history=[]
        )

    # ------------------------------
    # Upgrade subscription
    # ------------------------------
    async def upgrade_subscription(
        self,
        user_id,
        new_plan: str
    ) -> SubscriptionResponse:
        """
        Upgrade or change user's subscription plan.
        If multiple active subscriptions exist, keeps the latest and updates it.
        """
        # Convert to UUID if string
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        
        query = await self.db.execute(
            select(Subscription).where(
                and_(
                    Subscription.user_id == user_uuid,
                    Subscription.active == True
                )
            ).order_by(Subscription.start_date.desc())
        )
        subscriptions = query.scalars().all()
        
        if not subscriptions:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        # Handle multiple active subscriptions
        if len(subscriptions) > 1:
            logger.warning(f"Found {len(subscriptions)} active subscriptions during upgrade. Cleaning up...")
            subscription = subscriptions[0]  # Keep the newest
            
            # Deactivate old ones
            for old_sub in subscriptions[1:]:
                old_sub.active = False
                self.db.add(old_sub)
        else:
            subscription = subscriptions[0]

        # Update plan and limits
        plan_limits = self._get_plan_limits(new_plan)
        plan_price = self._get_plan_price(new_plan)
        
        subscription.plan_name = new_plan
        subscription.price = plan_price
        subscription.documents_limit = plan_limits["documents_limit"]
        subscription.queries_limit = plan_limits["queries_limit"]
        subscription.storage_limit = plan_limits["storage_limit"]
        
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        
        logger.info(f"Upgraded user {user_id} to {new_plan} plan")

        # Get updated billing history
        billing_query = await self.db.execute(
            select(Billing).where(
                Billing.subscription_id == subscription.id
            ).order_by(Billing.date.desc())
        )
        billing_records = billing_query.scalars().all()
        
        billing_history = [
            BillingHistoryResponse(
                id=record.id,
                invoice_number=record.invoice_number,
                amount=record.amount,
                status=record.status,
                date=record.date
            ) for record in billing_records
        ]

        return SubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            plan_name=subscription.plan_name,
            price=subscription.price,
            period=subscription.period,
            active=subscription.active,
            documents_used=subscription.documents_used,
            documents_limit=subscription.documents_limit,
            queries_used=subscription.queries_used,
            queries_limit=subscription.queries_limit,
            storage_used=subscription.storage_used,
            storage_limit=subscription.storage_limit,
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            billing_history=billing_history
        )

    # ------------------------------
    # Add billing record
    # ------------------------------
    async def add_billing_record(
        self,
        user_id,
        amount: float,
        invoice_number: str,
        status: str = "Paid"
    ) -> BillingHistoryResponse:
        """
        Add a billing record for a user's subscription
        """
        # Convert to UUID if string
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        
        # Get user's subscription (will handle duplicates automatically)
        subscription_response = await self.get_user_subscription(user_uuid)
        
        if not subscription_response:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        # Create billing record
        billing_record = Billing(
            subscription_id=subscription_response.id,
            invoice_number=invoice_number,
            amount=amount,
            status=status,
            date=datetime.utcnow()
        )
        
        self.db.add(billing_record)
        await self.db.commit()
        await self.db.refresh(billing_record)
        
        logger.info(f"Added billing record: {invoice_number} for user {user_id}")
        
        return BillingHistoryResponse(
            id=billing_record.id,
            invoice_number=billing_record.invoice_number,
            amount=billing_record.amount,
            status=billing_record.status,
            date=billing_record.date
        )

    # ------------------------------
    # Get billing history
    # ------------------------------
    async def get_billing_history(self, user_id) -> List[BillingHistoryResponse]:
        """
        Get billing history for a user
        """
        # Convert to UUID if string
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        
        # First get user's subscription
        query = await self.db.execute(
            select(Subscription).where(Subscription.user_id == user_uuid)
            .order_by(Subscription.start_date.desc())
        )
        subscriptions = query.scalars().all()
        
        if not subscriptions:
            logger.warning(f"No subscription found for user {user_id}")
            return []

        # Get billing records from all subscriptions
        all_billing_records = []
        for subscription in subscriptions:
            billing_query = await self.db.execute(
                select(Billing)
                .where(Billing.subscription_id == subscription.id)
                .order_by(Billing.date.desc())
            )
            billing_records = billing_query.scalars().all()
            all_billing_records.extend(billing_records)

        # Sort all records by date
        all_billing_records.sort(key=lambda x: x.date, reverse=True)

        return [
            BillingHistoryResponse(
                id=record.id,
                invoice_number=record.invoice_number,
                amount=record.amount,
                status=record.status,
                date=record.date
            ) for record in all_billing_records
        ]

    # ------------------------------
    # Helper methods
    # ------------------------------
    def _get_plan_limits(self, plan_name: str) -> dict:
        """
        Get limits for a subscription plan
        """
        plans = {
            "Starter": {
                "documents_limit": 10,
                "queries_limit": 100,
                "storage_limit": 1.0  # GB
            },
            "Pro": {
                "documents_limit": 100,
                "queries_limit": 1000,
                "storage_limit": 10.0
            },
            "Enterprise": {
                "documents_limit": 1000,
                "queries_limit": 10000,
                "storage_limit": 100.0
            }
        }
        return plans.get(plan_name, plans["Starter"])

    def _get_plan_price(self, plan_name: str) -> float:
        """
        Get price for a subscription plan
        """
        prices = {
            "Starter": 0.0,      # Free
            "Pro": 29.99,
            "Enterprise": 99.99
        }
        return prices.get(plan_name, 0.0)