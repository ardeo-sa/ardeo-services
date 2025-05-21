from fastapi import Depends, HTTPException, status
from app.users.models.user import User
from app.core.auth import get_current_user  # assumed to exist

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
