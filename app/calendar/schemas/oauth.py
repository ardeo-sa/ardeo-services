"""
Schema definitions for OAuth token responses.

This module provides Pydantic models to serialize and validate the structure
of OAuth token responses returned by external calendar providers such as
Google and Microsoft.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OAuthTokenResponse(BaseModel):
    """
    Response schema for an OAuth token.

    Represents the structure of token data returned after successful
    authentication with an external calendar provider.

    Attributes:
    - `access_token`: The token used to authenticate API requests.
    - `refresh_token`: (Optional) Token used to obtain new access tokens.
    - `expiry`: (Optional) Datetime when the access token expires.
    - `token_type`: (Optional) Type of the token, usually "Bearer".
    - `scope`: (Optional) Scopes granted by the user.
    """
    access_token: str
    refresh_token: Optional[str]
    expiry: Optional[datetime]
    token_type: Optional[str]
    scope: Optional[str]

    class Config:
        orm_mode = True

