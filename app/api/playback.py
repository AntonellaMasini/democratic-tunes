from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db import get_session
from app.api.deps import get_current_user_id
from app.schemas.tracks import QueueItem, QueueState
from app.api.tracks import _compute_queue
from app.domain.scoring import score_room_track
from app.sql import playback as SQL_PB

router = APIRouter(tags=["playback"])

@router.post("/rooms/{code}/advance", response_model=QueueState)
async def advance_playback(
    code: str,
    session: AsyncSession = Depends(get_session),
    user_id = Depends(get_current_user_id),
):

    # room must be active; also fetch host
    room_row = (await session.execute(text(SQL_PB.GET_ACTIVE_ROOM_WITH_HOST), {"code": code})).mappings().first()
    if not room_row:
        raise HTTPException(404, "Room not found or inactive")
    room_id = room_row["id"]
    host_id = room_row["host_user_id"]
    if str(host_id) != str(user_id):
        raise HTTPException(403, "Only the host can hit next!")

    # mark any current playing as played 
    current_playing = (await session.execute(text(SQL_PB.GET_CURRENT_PLAYING), {"room_id": str(room_id)})).scalar_one_or_none()
    if current_playing:
        await session.execute(text(SQL_PB.MARK_PLAYED), {"room_track_id": str(current_playing)})

    # compute queue
    queue_items = await _compute_queue(session, room_id)

    now_playing: Optional[QueueItem] = None
    if queue_items:
        next_item = queue_items[0]
        # set DB track status to playing
        await session.execute(text(SQL_PB.SET_PLAYING), {"room_track_id": str(next_item.room_track_id)})
        await session.commit()

        # reflect status in response
        now_playing = QueueItem(**next_item.model_dump())
        now_playing.status = "playing"

        #return updated queue
        remaining = queue_items[1:]
        return QueueState(now_playing=now_playing, queue=remaining)

    # nothing left to play
    await session.commit()
    return QueueState(now_playing=None, queue=[])

@router.get("/rooms/{code}/now-playing", response_model=Optional[QueueItem])
async def get_now_playing(
    code: str,
    session: AsyncSession = Depends(get_session),
):
    room_row = (await session.execute(text(SQL_PB.GET_ACTIVE_ROOM_WITH_HOST), {"code": code})).mappings().first()
    if not room_row:
        raise HTTPException(404, "Room not found or inactive")
    room_id = room_row["id"]

    row = (await session.execute(text(SQL_PB.GET_NOW_PLAYING_DETAILS), {"room_id": str(room_id)})).mappings().first()
    if not row:
        return None

    # compute score to be consistent with queue items (host bonus + age)
    is_host_add = str(row["added_by_user_id"]) == str(row["host_user_id"])
    score = score_room_track(row["created_at"], int(row["votes"]), is_host_add=is_host_add, now=datetime.now(timezone.utc))
    return QueueItem(
        room_track_id=str(row["room_track_id"]),
        track_id=row["track_id"],
        title=row["title"],
        artist=row["artist"],
        duration_ms=row["duration_ms"],
        votes=int(row["votes"]),
        score=float(score),
        status=str(row["status"]),
        created_at=row["created_at"],
    )
