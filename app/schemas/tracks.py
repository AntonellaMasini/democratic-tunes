from pydantic import BaseModel
from datetime import datetime

class TrackOut(BaseModel):
    id: str
    title: str
    artist: str
    duration_ms: int

class AddTrackReq(BaseModel):
    track_id: str  # user comes from cookie/header

class QueueItem(BaseModel):
    room_track_id: str
    track_id: str
    title: str
    artist: str
    duration_ms: int
    votes: int
    score: float
    status: str
    created_at: datetime