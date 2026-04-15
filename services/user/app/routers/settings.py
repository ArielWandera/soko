from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import UserSettings
from app.schemas.schemas import UserSettingsOut, UpdateSettings
import uuid

router = APIRouter(tags=["Settings"])


@router.get("/me/settings", response_model=UserSettingsOut)
def get_settings(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    s = db.query(UserSettings).filter(UserSettings.user_id == uuid.UUID(user_id)).first()
    if not s:
        raise HTTPException(status_code=404, detail="Settings not found")
    return UserSettingsOut(
        theme=s.theme,
        notificationsEmail=s.notifications_email,
        notificationsSms=s.notifications_sms,
        notificationsPush=s.notifications_push,
        language=s.language,
        currency=s.currency,
    )


@router.put("/me/settings", response_model=UserSettingsOut)
def update_settings(
    payload: UpdateSettings,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    s = db.query(UserSettings).filter(UserSettings.user_id == uuid.UUID(user_id)).first()
    if not s:
        raise HTTPException(status_code=404, detail="Settings not found")

    if payload.theme              is not None: s.theme               = payload.theme
    if payload.notificationsEmail is not None: s.notifications_email = payload.notificationsEmail
    if payload.notificationsSms   is not None: s.notifications_sms   = payload.notificationsSms
    if payload.notificationsPush  is not None: s.notifications_push  = payload.notificationsPush
    if payload.language           is not None: s.language            = payload.language
    if payload.currency           is not None: s.currency            = payload.currency

    db.commit()
    return UserSettingsOut(
        theme=s.theme,
        notificationsEmail=s.notifications_email,
        notificationsSms=s.notifications_sms,
        notificationsPush=s.notifications_push,
        language=s.language,
        currency=s.currency,
    )