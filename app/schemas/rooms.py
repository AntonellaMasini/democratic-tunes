
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class RoomCreate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)

class RoomResp(BaseModel):
    id: UUID
    code: str
    name: Optional[str]
    host_user_id: UUID
    is_active: bool
    created_at: datetime

class JoinRoomReq(BaseModel):
    code: str = Field(min_length=4, max_length=12)

class JoinRoomResp(BaseModel):
    room_id: UUID
    user_id: UUID

class RoomMemberResp(BaseModel):
    room_id: UUID
    user_id: UUID
    role: str
    joined_at: datetime
