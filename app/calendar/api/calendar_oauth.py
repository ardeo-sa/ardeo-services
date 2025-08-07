"""
This module provides API routes to handle OAuth2 authentication flows for
Google Calendar and Microsoft Outlook Calendar integrations.

It enables users to:
- Start the OAuth flow for Google and Microsoft calendars
- Handle callbacks and securely exchange authorization codes for access tokens
- Persist calendar tokens in the database for future authenticated requests

Routes:
- GET /google: Redirects user to Google's OAuth2 consent screen
- GET /google/callback: Handles Google's redirect with auth code, exchanges for tokens
- GET /microsoft: Redirects user to Microsoft's OAuth2 consent screen
- GET /microsoft/callback: Handles Microsoft's redirect with auth code, exchanges for tokens

These endpoints support calendar sync functionality, allowing the app to create
or manage events on behalf of authenticated users.

Dependencies:
- FastAPI for routing and dependency injection
- google-auth-oauthlib for managing Google OAuth2 flow
- Microsoft OAuth handled via direct POST to the token endpoint
"""
import logging
import uuid

import requests
from fastapi import APIRouter, Request, Depends, HTTPException
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from google_auth_oauthlib.flow import Flow
# from google.oauth2.credentials import Credentials

from app.config import (
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI,
    MS_CLIENT_ID, MS_CLIENT_SECRET, MS_REDIRECT_URI, MS_TENANT_ID
)
from app.calendar.services.oauth import save_calendar_token
from app.calendar.schemas.oauth import OAuthTokenResponse
from app.core.dependencies import get_current_user
from app.database.services import get_services_db
from app.users.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/calendar/oauth", tags=["Calendar OAuth"])


@router.get("/google")
def start_google_oauth():
    """
    Initiate OAuth2 flow for Google Calendar.

    Redirects the user to Google's consent screen to authorize access to their calendar.
    """
    logger.info("Starting Google OAuth flow")

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=["https://www.googleapis.com/auth/calendar.events"],
        redirect_uri=GOOGLE_REDIRECT_URI,
    )
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline', include_granted_scopes='true')

    logger.debug(f"Google auth URL: {auth_url}")
    return RedirectResponse(auth_url)


@router.get("/google/callback", response_model=OAuthTokenResponse)
def google_callback(
    request: Request,
    db: Session = Depends(get_services_db),
    current_user: User = Depends(get_current_user),
):
    """
    Callback from Google with authorization code.

    Exchanges code for access/refresh tokens. Save securely in your DB in production.
    """
    code = request.query_params.get("code")
    logger.info(f"Google callback received for user {current_user.id}")

    if not code:
        logger.error("Missing authorization code in Google callback")
        raise HTTPException(status_code=400, detail="Missing authorization code.")

    logger.debug("Exchanging code for Google tokens")
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=["https://www.googleapis.com/auth/calendar.events"],
        redirect_uri=GOOGLE_REDIRECT_URI,
    )
    flow.fetch_token(code=code)
    credentials = flow.credentials

    # Save token to DB
    logger.info(f"Saving Google calendar token for user {current_user.id}")
    save_calendar_token(db, current_user, "google", {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "expiry": credentials.expiry.isoformat(),
        "token_type": credentials.token_uri,
        "scopes": credentials.scopes,
    })

    return {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "expiry": credentials.expiry.isoformat(),
        "token_type": credentials.token_uri,
        "scope": " ".join(credentials.scopes),
    }


@router.get("/microsoft")
def start_microsoft_oauth():
    """
    Initiate OAuth2 flow for Microsoft Outlook Calendar.

    Redirects the user to Microsoft's login and consent screen.
    """
    logger.info("Starting Microsoft OAuth flow")

    state = str(uuid.uuid4())
    url = (
        f"https://login.microsoftonline.com/{MS_TENANT_ID}/oauth2/v2.0/authorize"
        f"?client_id={MS_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={MS_REDIRECT_URI}"
        f"&response_mode=query"
        f"&scope=offline_access Calendars.ReadWrite"
        f"&state={state}"
    )
    logger.debug(f"Microsoft auth URL: {url}")
    return RedirectResponse(url)


@router.get("/microsoft/callback", response_model=OAuthTokenResponse)
def microsoft_callback(
    code: str,
    db: Session = Depends(get_services_db),
    current_user: User = Depends(get_current_user),
    ):
    """
    Callback from Microsoft with authorization code.

    Exchanges code for tokens and returns them.
    """
    logger.info(f"Microsoft callback received for user {current_user.id}")

    token_url = f"https://login.microsoftonline.com/{MS_TENANT_ID}/oauth2/v2.0/token"
    data = {
        "client_id": MS_CLIENT_ID,
        "scope": "offline_access Calendars.ReadWrite",
        "code": code,
        "redirect_uri": MS_REDIRECT_URI,
        "grant_type": "authorization_code",
        "client_secret": MS_CLIENT_SECRET,
    }

    logger.debug("Sending request to Microsoft token endpoint")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(token_url, data=data, headers=headers, timeout=15)

    if response.status_code != 200:
        logger.error(f"Failed to exchange Microsoft token: {response.text}")
        raise HTTPException(status_code=500, detail="Failed to exchange token")

    token = response.json()

    logger.info(f"Saving Microsoft calendar token for user {current_user.id}")
    save_calendar_token(db, current_user, "microsoft", {
        "access_token": token["access_token"],
        "refresh_token": token.get("refresh_token"),
        "expires_in": token.get("expires_in"),
        "scope": token.get("scope"),
        "token_type": token.get("token_type"),
    })

    return {
        "access_token": token["access_token"],
        "refresh_token": token.get("refresh_token"),
        "expiry": None,
        "token_type": token.get("token_type"),
        "scope": token.get("scope"),
    }
