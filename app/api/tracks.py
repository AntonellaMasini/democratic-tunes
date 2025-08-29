import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db import get_session
from app.domain.models import Track, Room, RoomTrack, Vote, TrackStatus
from app.domain.scoring import score_room_track
from app.schemas.tracks import TrackOut, AddTrackReq, QueueItem

router = APIRouter()



@router.get("/search", response_model=list[TrackOut])
async def search_tracks(q: str, session: AsyncSession = Depends(get_session)):
    stmt = select(Track).where(
        or_(Track.title.ilike(f"%{q}%"), Track.artist.ilike(f"%{q}%"))
    ).limit(20)
    rows = (await session.execute(stmt)).scalars().all()
    return [TrackOut(id=t.id, title=t.title, artist=t.artist, duration_ms=t.duration_ms) for t in rows]

@router.post("/rooms/{code}/tracks", response_model=list[QueueItem])
async def add_track_to_room(code: str, req: AddTrackReq, session: AsyncSession = Depends(get_session)):
    room = (await session.execute(select(Room).where(Room.code == code))).scalar_one_or_none()
    if not room:
        raise HTTPException(404, "Room not found")

    track = await session.get(Track, req.track_id)
    if not track:
        raise HTTPException(404, "Track not found")

    rt = RoomTrack(room_id=room.id, track_id=track.id, added_by_user_id=req.user_id, status=TrackStatus.queued)
    session.add(rt)
    await session.commit()
    await session.refresh(rt)

    return await _compute_queue(session, room.id)

@router.get("/rooms/{code}/queue", response_model=list[QueueItem])
async def get_queue(code: str, session: AsyncSession = Depends(get_session)):
    room = (await session.execute(select(Room).where(Room.code == code))).scalar_one_or_none()
    if not room:
        raise HTTPException(404, "Room not found")
    return await _compute_queue(session, room.id)

async def _compute_queue(session: AsyncSession, room_id):
    votes_sum_cte = select(
        Vote.room_track_id,
        func.coalesce(func.sum(Vote.value), 0).label("votes_sum")
    ).group_by(Vote.room_track_id).cte("votes_sum")

    stmt = (
        select(RoomTrack, Track, func.coalesce(votes_sum_cte.c.votes_sum, 0))
        .join(Track, Track.id == RoomTrack.track_id)
        .join(votes_sum_cte, votes_sum_cte.c.room_track_id == RoomTrack.id, isouter=True)
        .where(RoomTrack.room_id == room_id, RoomTrack.status == TrackStatus.queued)
    )

    rows = (await session.execute(stmt)).all()
    items = []
    for rt, t, votes_sum in rows:
        score = score_room_track(rt.created_at, int(votes_sum or 0), is_host_add=False)
        items.append(QueueItem(
            room_track_id=str(rt.id),
            track_id=t.id,
            title=t.title,
            artist=t.artist,
            duration_ms=t.duration_ms,
            votes=int(votes_sum or 0),
            score=float(score),
            status=rt.status.value,
        ))

    items.sort(key=lambda x: (-x.score, x.room_track_id))
    return items
