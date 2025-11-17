"""Role definitions for RBAC."""

import enum


class Role(str, enum.Enum):
    """User roles for role-based access control."""

    ADMIN = "admin"
    SUPPLIER = "supplier"
    CONSUMER = "consumer"
    MANAGER = "manager"
