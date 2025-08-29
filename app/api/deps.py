from fastapi import Header, HTTPException, status
from typing import Optional
from uuid import UUID

async def get_current_user_id(x_user_id: Optional[str] = Header(default=None)) -> UUID:
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-User-ID header")
    try:
        return UUID(x_user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-User-ID")