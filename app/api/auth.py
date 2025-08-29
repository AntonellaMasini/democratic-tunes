from fastapi import APIRouter, Depends,  HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.infra.db import get_session
from app.domain.models import User
from app.schemas.auth import AuthResp, GuestReq
from typing import Optional
import secrets
from sqlalchemy.exc import IntegrityError
import logging

router = APIRouter()

def make_guest_name(requested: Optional[str]) -> str:
    # Trim spaces. If empty, auto-generate a handle.
    base = (requested or "").strip()
    if not base:
        return f"Guest-{secrets.token_hex(2).upper()}"  # like Guest-7F3A
    return base
    
@router.post("/guest", response_model=AuthResp, status_code=status.HTTP_201_CREATED)
async def create_guest(payload: GuestReq, session: AsyncSession = Depends(get_session)):
    name = make_guest_name(payload.display_name)
    
    if len(name) > 64:
        raise HTTPException(status_code=422, detail="display_name too long (max 64).")

    try: 
        u = User(display_name=name)
        session.add(u)
        await session.commit()
        await session.refresh(u)
        return AuthResp(user_id=str(u.id), display_name=u.display_name) 

    except IntegrityError as e:
        await session.rollback()
        # Show the precise PG error (e.g., unique_violation, not_null_violation)
        logging.exception("Integrity error on /auth/guest")
        raise HTTPException(status_code=409, detail=str(e.orig))
    except Exception as e:
        await session.rollback()
        logging.exception("Unexpected DB error on /auth/guest")
        raise HTTPException(status_code=500, detail=str(e))