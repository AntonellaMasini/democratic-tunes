import uuid
from pydantic import BaseModel

class VoteReq(BaseModel):
    room_track_id: uuid.UUID
    value: int  # +1 or -1
