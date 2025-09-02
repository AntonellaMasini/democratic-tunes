from fastapi import Header, Cookie, HTTPException, status
from typing import Optional
from uuid import UUID

async def get_current_user_id(
    x_user_id: Optional[str] = Header(default=None),  # for dev
    uid: Optional[str] = Cookie(default=None),        # cookie set by /auth/guest
    ) -> UUID:

    if uid and x_user_id and uid != x_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conflicting identities: cookie uid and X-User-ID differ",
        )
        
    raw = x_user_id or uid
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing identity")
    try:
        return UUID(raw)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")