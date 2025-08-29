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

router = APIRouter(tags=["rooms"])

ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no O/0/I/1
def make_room_code(n: int = 8) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(n))

@router.post("", response_model=RoomResp, status_code=status.HTTP_201_CREATED)
async def create_room(
    payload: RoomCreate,
    session: AsyncSession = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    # retry a few times if the randomly generated code collides with UNIQUE(rooms.code)
    for _ in range(5):
        code = make_room_code()  # "X8F2K9QJ"
        try:
            async with session.begin():  # one atomic transaction
                room = Room(code=code, name=(payload.name or None), host_user_id=user_id, is_active=True)
                session.add(room)
                # flush to hit the UNIQUE constraint early (if it’s a collision)
                await session.flush()

                # host auto-joins to the room when they create it
                session.add(RoomMember(room_id=room.id, user_id=user_id, role="host"))

            # committed successfully
            return RoomResp(
                id=room.id,
                code=room.code,
                name=room.name,
                host_user_id=room.host_user_id,
                is_active=room.is_active,
                created_at=room.created_at,
            )

        except IntegrityError as e:
            # probably due to code collision; rollback handled by session.begin()
            # try again with a new code
            continue

        except Exception:
            raise HTTPException(status_code=500, detail="Failed to create room")

    raise HTTPException(status_code=500, detail="Could not generate unique room code after retries")


@router.post("/join", response_model=JoinRoomResp)
async def join_room(
    payload: JoinRoomReq,
    session: AsyncSession = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    code = (payload.code or "").strip().upper()
    if not code:
        raise HTTPException(status_code=422, detail="code required")

    room = (await session.execute(select(Room).where(Room.code == code, Room.is_active.is_(True)))).scalar_one_or_none()

    if not room or not room.is_active:
        raise HTTPException(status_code=404, detail="Room not found or inactive")

    try:
        session.add(RoomMember(room_id=room.id, user_id=user_id, role="guest"))
        await session.commit()
    except IntegrityError:
        # already a member
        await session.rollback()
    
    return JoinRoomResp(room_id=room.id, user_id=user_id)

@router.post("/{room_id}/close", status_code=status.HTTP_204_NO_CONTENT)
async def close_room(
    room_id: UUID,
    session: AsyncSession = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id),
):
    room = (await session.execute(select(Room).where(Room.id == room_id))).scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.host_user_id != user_id:
        raise HTTPException(status_code=403, detail="Only the host can close the room")

    async with session.begin():
        room.is_active = False