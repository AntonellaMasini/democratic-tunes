from pydantic import BaseModel
from typing import Optional

class GuestReq(BaseModel):
    display_name: Optional[str] = None

class AuthResp(BaseModel):
    user_id: str
    display_name: str