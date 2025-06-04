import os
from dotenv import load_dotenv

# Load environment variables from .env file (useful for local dev)
load_dotenv()

# Database
SERVICES_DB_URI = os.getenv("SERVICES_DB_URI")

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
MS_CLIENT_ID = os.getenv("MS_CLIENT_ID")  # <--- This was missing
MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET")
MS_REDIRECT_URI = os.getenv("MS_REDIRECT_URI")
