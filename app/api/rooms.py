import secrets
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db import get_session
from app.api.deps import get_current_user_id
from app.domain.models import Room, RoomMember
from app.schemas.rooms import (
    RoomCreate, RoomResp, JoinRoomReq, JoinRoomResp, RoomMemberResp
)

router = APIRouter(prefix="/rooms", tags=["rooms"])

def make_room_code() -> str:
    return secrets.token_hex(3).upper()  #'A3F91B'

@router.post("", response_model=RoomResp, status_code=status.HTTP_201_CREATED)
async def create_room(
    payload: RoomCreate,
    session: AsyncSession = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    # Try a few times in case of unique collisions on code
    for _ in range(5):
        code = make_room_code()
        room = Room(code=code, name=(payload.name or None), host_user_id=user_id, is_active=True)
        session.add(room)
        try:
            await session.commit()
            await session.refresh(room)
            # Host auto-joins as member with role 'host'
            session.add(RoomMember(room_id=room.id, user_id=user_id, role="host"))
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
            return RoomResp(
                id=room.id,
                code=room.code,
                name=room.name,
                host_user_id=room.host_user_id,
                is_active=room.is_active,
                created_at=room.created_at,
            )
        except IntegrityError:
            await session.rollback() # likely code unique conflict—retry
            continue
        except Exception:
            await session.rollback()
            raise HTTPException(status_code=500, detail="Failed to create room")
    raise HTTPException(status_code=500, detail="Could not generate unique room code")
