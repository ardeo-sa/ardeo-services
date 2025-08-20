"""Load env variables and set up all necessary configuration"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file (useful for local dev)
load_dotenv()

def get_services_db_uri(async_mode: bool = True) -> str:
    """
        Returns the full DB URI from environment.

        Tries SERVICES_DB_URI first; if not set, builds from individual components.

        Raises:
            ValueError: if neither full URI nor all components are set.
        """
    full_uri = os.getenv("SERVICES_DB_URI")
    if full_uri:
        # normalize driver based on mode
        if async_mode and full_uri.startswith("postgresql+psycopg2"):
            return full_uri.replace("psycopg2", "asyncpg")
        if not async_mode and full_uri.startswith("postgresql+asyncpg"):
            return full_uri.replace("asyncpg", "psycopg2")
        return full_uri

    # fallback to components
    user = os.getenv("SERVICES_DB_USER")
    password = os.getenv("SERVICES_DB_PASSWORD")
    host = os.getenv("SERVICES_DB_HOST")
    name = os.getenv("SERVICES_DB_NAME")
    port = os.getenv("SERVICES_DB_PORT")

    if not all([user, password, host, port, name]):
        raise ValueError("Missing one or more required DB environment variables")

    if async_mode:
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
    else:
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"

try:
    ASYNC_SERVICES_DB_URI = get_services_db_uri(async_mode=True)
    SYNC_SERVICES_DB_URI = get_services_db_uri(async_mode=False)
except ValueError as e:
    ASYNC_SERVICES_DB_URI = None
    SYNC_SERVICES_DB_URI = None

# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Microsoft OAuth
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")

# Optional: Redirect URIs (if used in OAuth logic)
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
MICROSOFT_REDIRECT_URI = os.getenv("MICROSOFT_REDIRECT_URI")

# Microsoft OAuth
MS_CLIENT_ID = os.getenv("MS_CLIENT_ID")
MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET")
MS_REDIRECT_URI = os.getenv("MS_REDIRECT_URI")
MS_TENANT_ID = os.getenv("MS_TENANT_ID")

# Email SMTP
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@yourdomain.com")

# Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
