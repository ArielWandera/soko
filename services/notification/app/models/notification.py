import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean,
    DateTime, Text, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base
import enum


class NotificationType(str, enum.Enum):
    order_placed       = "order_placed"
    payment_confirmed  = "payment_confirmed"
    payment_failed     = "payment_failed"
    order_dispatched   = "order_dispatched"
    order_delivered    = "order_delivered"
    order_cancelled    = "order_cancelled"
    new_message        = "new_message"
    new_review         = "new_review"
    new_follower       = "new_follower"
    system             = "system"


class NotificationChannel(str, enum.Enum):
    in_app = "in_app"
    sms    = "sms"
    push   = "push"


class Notification(Base):
    __tablename__ = "notifications"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id     = Column(UUID(as_uuid=True), nullable=False, index=True)

    type        = Column(SAEnum(NotificationType), nullable=False)
    channel     = Column(SAEnum(NotificationChannel), nullable=False)

    title       = Column(String, nullable=False)
    body        = Column(Text,   nullable=False)

    # Optional deep-link data — frontend uses to navigate on tap
    entity_type = Column(String, nullable=True)   # "order" | "message" | "listing"
    entity_id   = Column(String, nullable=True)   # the id to navigate to

    is_read     = Column(Boolean, default=False)
    sent        = Column(Boolean, default=False)   # whether SMS/push was sent
    sent_at     = Column(DateTime, nullable=True)

    created_at  = Column(DateTime, default=datetime.utcnow)