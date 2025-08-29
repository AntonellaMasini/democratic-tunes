from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.infra.db import get_session
from app.domain.models import User

router = APIRouter()

class GuestReq(BaseModel):
    display_name: str | None = None

class AuthResp(BaseModel):
    user_id: str
    display_name: str

@router.post("/guest", response_model=AuthResp)
async def create_guest(req: GuestReq, session: AsyncSession = Depends(get_session)):
    u = User(display_name=req.display_name or "Guest")
    session.add(u)
    await session.commit()
    await session.refresh(u)
    return AuthResp(user_id=str(u.id), display_name=u.display_name)