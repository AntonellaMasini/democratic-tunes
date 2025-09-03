import logging
import os
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import User
from app.infra.db import get_session
from app.schemas.auth import AuthResp, GuestReq 

router = APIRouter()

def make_guest_name(requested: Optional[str]) -> str:
    # Trim spaces. If empty, auto-generate a handle.
    base = (requested or "").strip()
    if not base:
        return f"Guest-{secrets.token_hex(2).upper()}"  # like Guest-7F3A
    return base
    
@router.post("/guest", response_model=AuthResp, status_code=status.HTTP_201_CREATED)
async def create_guest(payload: GuestReq, request: Request, response: Response, session: AsyncSession = Depends(get_session)):
    name = make_guest_name(payload.display_name)
    
    if len(name) > 64:
        raise HTTPException(status_code=422, detail="display_name too long (max 64).")

    try: 
        u = User(display_name=name)
        session.add(u)
        await session.commit()
        await session.refresh(u)


        is_prod = os.getenv("ENV") == "prod"
        # Set this to true in prod when your frontend is on a different origin (e.g. Vercel)
        cross_site = os.getenv("CROSS_SITE_COOKIES", "false").lower() == "true"

        # In prod on Fly --> HTTPS, so secure can be True.
        # Locally (http://localhost) set CROSS_SITE_COOKIES=false so samesite=lax + secure=False works.
        samesite = "none" if cross_site else "lax"
        secure   = True if (is_prod and cross_site) else (request.url.scheme == "https")

        response.set_cookie(
            key="uid",
            value=str(u.id),
            max_age=60 * 60 * 24 * 30,  # 30 days
            httponly=True,
            # SameSite rules:
            # - same-site (API + UI same origin): "lax"
            # - cross-site (UI on another domain): must be "none" (+ Secure=True)
            samesite=samesite,
            secure=secure,
            path="/",                   # include so delete_cookie matches
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
async def logout(response: Response, request: Request):
    is_prod    = os.getenv("ENV") == "prod"
    cross_site = os.getenv("CROSS_SITE_COOKIES", "false").lower() == "true"
    samesite   = "none" if cross_site else "lax"
    secure     = True if (is_prod and cross_site) else (request.url.scheme == "https")

    response.delete_cookie(
        key="uid",
        path="/",
        httponly=True,
        samesite=samesite,
        secure=secure,
    )