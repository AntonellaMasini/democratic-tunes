from pydantic import BaseModel, Field
from typing import Optional

class GuestReq(BaseModel):
    display_name: Optional[str] = Field(default=None, max_length=64)

class AuthResp(BaseModel):
    user_id: str
    display_name: str