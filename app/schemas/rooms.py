import uuid
from typing import Optional
from pydantic import BaseModel

class CreateRoomReq(BaseModel):
    host_user_id: uuid.UUID
    name: Optional[str] = None

class RoomResp(BaseModel):
    room_id: str
    code: str
    name: Optional[str] = None

class JoinReq(BaseModel):
    user_id: uuid.UUID
