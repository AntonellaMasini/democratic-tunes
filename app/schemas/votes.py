import uuid
from pydantic import BaseModel

class VoteReq(BaseModel):
    user_id: uuid.UUID
    room_track_id: uuid.UUID
    value: int  # +1 or -1
