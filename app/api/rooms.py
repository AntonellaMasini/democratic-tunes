import secrets, uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infra.db import get_session
from app.domain.models import Room, RoomMember

router = APIRouter()

def gen_code(n=6):
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no 0/O/I/1 confusion
    return "".join(secrets.choice(alphabet) for _ in range(n))

class CreateRoomReq(BaseModel):
    host_user_id: uuid.UUID
    name: str | None = None

class RoomResp(BaseModel):
    room_id: str
    code: str
    name: str | None = None

@router.post("", response_model=RoomResp)
async def create_room(req: CreateRoomReq, session: AsyncSession = Depends(get_session)):
    r = Room(code=gen_code(), host_user_id=req.host_user_id, name=req.name)
    session.add(r)
    await session.flush()  # get r.id without full commit
    session.add(RoomMember(room_id=r.id, user_id=req.host_user_id, role="host"))
    await session.commit()
    await session.refresh(r)
    return RoomResp(room_id=str(r.id), code=r.code, name=r.name)

class JoinReq(BaseModel):
    user_id: uuid.UUID

@router.post("/{code}/join", response_model=RoomResp)
async def join_room(code: str, req: JoinReq, session: AsyncSession = Depends(get_session)):
    r = (await session.execute(select(Room).where(Room.code == code))).scalar_one_or_none()
    if not r or not r.is_active:
        raise HTTPException(404, "Room not found")
    session.add(RoomMember(room_id=r.id, user_id=req.user_id, role="guest"))
    await session.commit()
    return RoomResp(room_id=str(r.id), code=r.code, name=r.name)
