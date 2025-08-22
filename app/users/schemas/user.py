"""Schemas for user management"""
from enum import Enum

class UserRole(str, Enum):
    """
    Enumeration of user roles for role-based access control.

    Roles:
    - user: Regular user with limited permissions.
    - coordinator: Can create and manage MDT meetings.
    - admin: Full access to all system resources.
    """
    USER = "user"
    COORDINATOR = "coordinator"
    ADMIN = "admin"
