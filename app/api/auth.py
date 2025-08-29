from fastapi import APIRouter, Depends,  HTTPException, status, Response
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
async def create_guest(payload: GuestReq, response: Response, session: AsyncSession = Depends(get_session)):
    name = make_guest_name(payload.display_name)
    
    if len(name) > 64:
        raise HTTPException(status_code=422, detail="display_name too long (max 64).")

    try: 
        u = User(display_name=name)
        session.add(u)
        await session.commit()
        await session.refresh(u)

        # Set HttpOnly cookie so the browser remembers the user automatically
        response.set_cookie(
            key="uid",
            value=str(u.id),
            max_age=60 * 60 * 24 * 30,  # 30 days
            httponly=True,
            samesite="lax",
            secure=False,               # set True behind HTTPS in prod
        )

        return AuthResp(user_id=str(u.id), display_name=u.display_name) 

    except IntegrityError as e:
        await session.rollback()
        logging.exception("Integrity error on /auth/guest")
        raise HTTPException(status_code=409, detail=str(e.orig))
    except Exception as e:
        await session.rollback()
        logging.exception("Unexpected DB error on /auth/guest")
        raise HTTPException(status_code=500, detail=str(e))

    
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie(
        key="uid",
        path="/",
        httponly=True,
        samesite="lax",
        secure=False  # True in prod (HTTPS)
    )