import uuid
from pydantic import BaseModel

class TrackOut(BaseModel):
    id: str
    title: str
    artist: str
    duration_ms: int

class AddTrackReq(BaseModel):
    user_id: uuid.UUID
    track_id: str

class QueueItem(BaseModel):
    room_track_id: str
    track_id: str
    title: str
    artist: str
    duration_ms: int
    votes: int
    score: float
    status: str
