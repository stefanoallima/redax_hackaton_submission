"""
Subscription model
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base
import uuid
from datetime import datetime


class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    stripe_subscription_id = Column(String(255), unique=True, nullable=True, index=True)
    plan_tier = Column(String(50), nullable=False)  # free, premium, professional, enterprise
    status = Column(String(50), nullable=False)  # active, canceled, past_due, trialing, incomplete
    current_period_end = Column(DateTime, nullable=False)
    usage_limit_docs = Column(Integer, nullable=True)  # Null = unlimited
    usage_limit_searches = Column(Integer, nullable=True)  # Null = unlimited
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Subscription {self.plan_tier} - {self.status}>"
