from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.domain.scoring import score_room_track
from app.infra.db import get_session
from app.schemas.tracks import AddTrackReq, QueueItem, TrackOut
from app.sql import tracks as SQL

router = APIRouter(tags=["tracks"])

@router.get("/search", response_model=list[TrackOut])
async def search_tracks(artist_or_title: str, session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(text(SQL.SEARCH_TRACKS), {"q": f"%{artist_or_title}%"})).mappings().all()
    return [TrackOut(**row) for row in rows] #returns list of trackout objects
    

@router.get("/rooms/{code}/queue", response_model=list[QueueItem])
async def get_queue(code: str, session: AsyncSession = Depends(get_session)):
    room_row = (await session.execute(text(SQL.GET_ACTIVE_ROOM_BY_CODE), {"code": code})).mappings().first()
    if not room_row:
        raise HTTPException(404, "Room not found or inactive")
    return await _compute_queue(session, room_row["id"])


@router.post("/rooms/{code}/tracks", response_model=list[QueueItem])
async def add_track_to_room(
    code: str, 
    payload: AddTrackReq,
    session: AsyncSession = Depends(get_session),
    user_id = Depends(get_current_user_id)
    ):

    room_row = (await session.execute(text(SQL.GET_ACTIVE_ROOM_BY_CODE), {"code": code})).mappings().first()
    if not room_row:
        raise HTTPException(404, "Room not found or inactive")
    room_id = room_row["id"]

    exists = await session.execute(text(SQL.TRACK_EXISTS), {"track_id": payload.track_id})
    if exists.scalar_one_or_none() is None:
        raise HTTPException(404, "Track not found")

    rt_id = uuid.uuid4()
    try:
        await session.execute(
            text(SQL.INSERT_ROOM_TRACK_IF_NOT_EXISTS),
            {
                "id": rt_id,
                "room_id": room_id,                 
                "track_id_ins": payload.track_id,   
                "track_id_chk": payload.track_id,
                "user_id": user_id,
            },
        )
        await session.commit()
    except IntegrityError:
        # If two inserts raced, the partial unique index will reject one.
        # Roll back and continue; the track is already queued.
        await session.rollback()

    return await _compute_queue(session, room_id)


async def _compute_queue(session: AsyncSession, room_id):
    rows = (await session.execute(text(SQL.COMPUTE_QUEUE), {"room_id": str(room_id)})).mappings().all()
    now = datetime.now(timezone.utc)
    items: list[QueueItem] = []
    created_at_by_id: dict[str, datetime] = {}

    for row in rows:
        is_host_add = str(row["added_by_user_id"]) == str(row["host_user_id"])
        score = score_room_track(row["created_at"], int(row["votes"]), is_host_add=is_host_add, now=now)
        item = QueueItem(
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
        items.append(item)
        created_at_by_id[item.room_track_id] = row["created_at"]

    # created_at ASC, then score DESC 
    items.sort(key=lambda i: created_at_by_id[i.room_track_id])
    items.sort(key=lambda i: i.score, reverse=True)
    return items