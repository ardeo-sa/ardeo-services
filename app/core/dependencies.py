from fastapi import Depends
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    role: str

def get_current_user():
    """
    Simulates user retrieval in place of actual authentication logic.
    """
    # This would usually come from a token
    return User(id=1, name="Test User", role="coordinator")
