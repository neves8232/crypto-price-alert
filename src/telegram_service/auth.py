"""
Authentication Module

Bearer token authentication for inter-service communication.
Uses constant-time comparison to prevent timing attacks.
"""

import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from .config import settings


async def verify_auth_token(
    authorization: Annotated[str | None, Header()] = None
) -> str:
    """
    Verify Bearer token authentication.

    Args:
        authorization: Authorization header value (e.g., "Bearer <token>")

    Returns:
        The validated token

    Raises:
        HTTPException: If authentication fails

    Security:
        - Uses secrets.compare_digest() for constant-time comparison
        - Prevents timing attacks
        - Never logs the token value
    """

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Parse Authorization header
    parts = authorization.split()

    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, token = parts

    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme. Expected 'Bearer'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate token using constant-time comparison
    expected_token = settings.auth_token

    if not secrets.compare_digest(token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token


# Dependency for protected routes
AuthToken = Annotated[str, Depends(verify_auth_token)]
