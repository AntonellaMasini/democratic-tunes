import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db import get_session
from app.api.deps import get_current_user_id
from app.schemas.votes import VoteReq
from app.schemas.tracks import QueueItem
from app.api.tracks import _compute_queue
from app.sql import votes as SQLV
from app.sql import tracks as SQLT  #reuse GET_ACTIVE_ROOM_BY_CODE

router = APIRouter(tags=["votes"])

@router.post("/rooms/{code}/votes", response_model=list[QueueItem])
async def cast_vote(
    code: str,
    payload: VoteReq,
    session: AsyncSession = Depends(get_session),
    user_id = Depends(get_current_user_id),
):
    code = (code or "").strip().upper()
    if payload.value not in (-1, 1):
        raise HTTPException(422, "value must be +1 or -1")

    # 1) active room?
    room_row = (
        await session.execute(text(SQLT.GET_ACTIVE_ROOM_BY_CODE), {"code": code})
    ).mappings().first()
    if not room_row:
        raise HTTPException(404, "Room not found or inactive")
    room_id = room_row["id"]

    # 2) room_track belongs to this room and is queued?
    rt_ok = (
        await session.execute(
            text(SQLV.GET_ROOM_TRACK_IN_ROOM),
            {"room_track_id": str(payload.room_track_id), "room_id": str(room_id)},
        )
    ).scalar_one_or_none()
    if rt_ok is None:
        raise HTTPException(404, "Track not in this room (or not queueable)")

    # 3) upsert the vote
    await session.execute(
        text(SQLV.UPSERT_VOTE),
        {
            "id": str(uuid.uuid4()),
            "room_track_id": str(payload.room_track_id),
            "user_id": str(user_id),
            "value": int(payload.value),
        },
    )
    await session.commit()

    # 4) return updated queue
    return await _compute_queue(session, room_id)