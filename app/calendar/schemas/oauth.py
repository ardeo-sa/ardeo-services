from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OAuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str]
    expiry: Optional[datetime]
    token_type: Optional[str]
    scope: Optional[str]

    class Config:
        orm_mode = True

