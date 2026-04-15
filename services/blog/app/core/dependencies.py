from fastapi import Header, HTTPException
from app.core.config import settings


def get_current_user_id(x_user_id: str = Header(...)) -> str:
    """Extracts user id injected by the Gateway after token verification."""
    return x_user_id


def get_current_user_role(x_user_role: str = Header(...)) -> str:
    return x_user_role


def internal_only(x_internal_secret: str = Header(...)):
    """Protects routes that should only be called by other services."""
    if x_internal_secret != settings.INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")