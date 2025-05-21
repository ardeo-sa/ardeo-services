
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.users.models.user import User


def get_current_user(request: Request) -> User:
    """
    Dependency that returns the currently authenticated user.

    Assumes the user has already been authenticated and attached to the request,
    e.g., via middleware or upstream authentication system.

    Raises:
        HTTPException: If user is not found in request.
    """
    user: User = request.state.user  # Assumes middleware sets this

    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")

    return user


def get_db() -> Session:
    """
    Provides a database session for dependency injection.

    Yields:
        Session: SQLAlchemy DB session.

    Closes:
        Ensures the session is closed after request lifecycle.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_role(role: str):
    """
        Dependency factory that ensures the current user has the required role.

        Args:
            role (str): The required role (e.g., "coordinator").

        Returns:
            function: Dependency that raises HTTP 403 if role mismatch occurs.

        Raises:
            HTTPException: If current user does not match the required role.
        """
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Only users with role '{role}' can perform this action."
            )
        return current_user
    return role_checker


__all__ = ["get_db", "get_current_user", "require_role"]
