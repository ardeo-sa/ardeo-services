from typing import Callable

from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session


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


def require_role(*roles: str) -> Callable:
    """
    Dependency factory that ensures the current user has one of the required roles.

    Args:
        *roles (str): Allowed roles (e.g., "admin", "coordinator").

    Returns:
        function: Dependency that raises HTTP 403 if role mismatch occurs.

    Raises:
        HTTPException: If current user does not have one of the required roles.
    """
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Only users with role(s) {roles} can perform this action."
            )
        return current_user
    return role_checker

__all__ = ["get_current_user", "require_role"]

