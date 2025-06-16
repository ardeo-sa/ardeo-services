import os
from dotenv import load_dotenv

# Load environment variables from .env file (useful for local dev)
load_dotenv()

# Database
services_db_user = os.getenv("SERVICES_DB_USER")
services_db_password = os.getenv("SERVICES_DB_PASSWORD")
services_db_host = os.getenv("SERVICES_DB_HOST")
services_db_name = os.getenv("SERVICES_DB_NAME")
services_db_port = os.getenv("SERVICES_DB_PORT")

SERVICES_DB_URI = (
    f"postgresql+psycopg2://{services_db_user}:{services_db_password}@{services_db_host}:{services_db_port}/{services_db_name}"
)


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