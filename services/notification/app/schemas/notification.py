from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class NotificationType(str, Enum):
    order_placed      = "order_placed"
    payment_confirmed = "payment_confirmed"
    payment_failed    = "payment_failed"
    order_dispatched  = "order_dispatched"
    order_delivered   = "order_delivered"
    order_cancelled   = "order_cancelled"
    new_message       = "new_message"
    new_review        = "new_review"
    new_follower      = "new_follower"
    system            = "system"


# ── Internal event payload — any service sends this
class NotifyPayload(BaseModel):
    event:      str                   # matches NotificationType values
    order_id:   Optional[str] = None
    buyer_id:   Optional[str] = None
    farmer_id:  Optional[str] = None
    message_id: Optional[str] = None
    actor_id:   Optional[str] = None  # who triggered (e.g. reviewer, follower)
    actor_name: Optional[str] = None
    meta:       Optional[dict] = None  # any extra data the template needs


# ── Notification out — frontend reads these
class NotificationOut(BaseModel):
    id:          str
    type:        str
    channel:     str
    title:       str
    body:        str
    entityType:  Optional[str]
    entityId:    Optional[str]
    isRead:      bool
    createdAt:   str


# ── Mark read payload
class MarkReadPayload(BaseModel):
    notification_ids: List[str]