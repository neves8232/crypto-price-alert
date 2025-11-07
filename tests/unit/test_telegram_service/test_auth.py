"""
Unit tests for authentication module.

Tests Bearer token authentication and security features.
"""

import pytest
from fastapi import HTTPException

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from telegram_service.auth import verify_auth_token


@pytest.mark.unit
class TestAuthVerification:
    """Test cases for authentication verification."""

    @pytest.mark.asyncio
    async def test_valid_token(self, test_env_vars):
        """Test that valid token passes authentication."""
        valid_token = test_env_vars["SERVICE_AUTH_TOKEN"]
        auth_header = f"Bearer {valid_token}"

        result = await verify_auth_token(authorization=auth_header)

        assert result == valid_token

    @pytest.mark.asyncio
    async def test_missing_authorization_header(self):
        """Test that missing authorization header raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_auth_token(authorization=None)

        assert exc_info.value.status_code == 401
        assert "Missing authorization header" in exc_info.value.detail
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    @pytest.mark.asyncio
    async def test_invalid_header_format_no_space(self):
        """Test that malformed header (no space) raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_auth_token(authorization="Bearertoken123")

        assert exc_info.value.status_code == 401
        assert "Invalid authorization header format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_invalid_header_format_too_many_parts(self):
        """Test that header with too many parts raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_auth_token(authorization="Bearer token extra")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_scheme(self):
        """Test that non-Bearer scheme raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_auth_token(authorization="Basic token123")

        assert exc_info.value.status_code == 401
        assert "Invalid authentication scheme" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_invalid_token(self, test_env_vars):
        """Test that invalid token raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_auth_token(authorization="Bearer wrong-token")

        assert exc_info.value.status_code == 401
        assert "Invalid authentication token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_case_insensitive_scheme(self, test_env_vars):
        """Test that scheme is case-insensitive."""
        valid_token = test_env_vars["SERVICE_AUTH_TOKEN"]

        # Test lowercase
        result = await verify_auth_token(authorization=f"bearer {valid_token}")
        assert result == valid_token

        # Test uppercase
        result = await verify_auth_token(authorization=f"BEARER {valid_token}")
        assert result == valid_token

        # Test mixed case
        result = await verify_auth_token(authorization=f"BeArEr {valid_token}")
        assert result == valid_token

    @pytest.mark.asyncio
    async def test_token_with_special_characters(self, monkeypatch):
        """Test token with special characters."""
        special_token = "tok3n-with_special.chars!@#$%^&*()"
        monkeypatch.setenv("SERVICE_AUTH_TOKEN", special_token)

        # Re-import to pick up new env var
        import importlib
        import telegram_service.config as config_module
        importlib.reload(config_module)

        result = await verify_auth_token(authorization=f"Bearer {special_token}")
        assert result == special_token

    @pytest.mark.asyncio
    async def test_empty_token(self):
        """Test that empty token raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_auth_token(authorization="Bearer ")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_timing_attack_resistance(self, test_env_vars):
        """Test that constant-time comparison is used (basic test)."""
        valid_token = test_env_vars["SERVICE_AUTH_TOKEN"]

        # Create tokens that differ at different positions
        wrong_token_start = "x" + valid_token[1:]
        wrong_token_end = valid_token[:-1] + "x"

        # Both should fail with same exception type
        with pytest.raises(HTTPException) as exc1:
            await verify_auth_token(authorization=f"Bearer {wrong_token_start}")

        with pytest.raises(HTTPException) as exc2:
            await verify_auth_token(authorization=f"Bearer {wrong_token_end}")

        assert exc1.value.status_code == exc2.value.status_code
        assert exc1.value.detail == exc2.value.detail


@pytest.mark.unit
class TestAuthEdgeCases:
    """Test edge cases and security concerns."""

    @pytest.mark.asyncio
    async def test_whitespace_in_header(self, test_env_vars):
        """Test handling of whitespace in authorization header."""
        valid_token = test_env_vars["SERVICE_AUTH_TOKEN"]

        # Leading/trailing whitespace should fail
        with pytest.raises(HTTPException):
            await verify_auth_token(authorization=f" Bearer {valid_token}")

        with pytest.raises(HTTPException):
            await verify_auth_token(authorization=f"Bearer {valid_token} ")

    @pytest.mark.asyncio
    async def test_sql_injection_attempt(self):
        """Test that SQL injection attempts are handled safely."""
        sql_injection = "token' OR '1'='1"

        with pytest.raises(HTTPException) as exc_info:
            await verify_auth_token(authorization=f"Bearer {sql_injection}")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_very_long_token(self):
        """Test handling of very long token."""
        very_long_token = "a" * 10000

        with pytest.raises(HTTPException) as exc_info:
            await verify_auth_token(authorization=f"Bearer {very_long_token}")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_unicode_in_token(self):
        """Test handling of unicode characters in token."""
        unicode_token = "token-with-émojis-🚀"

        with pytest.raises(HTTPException) as exc_info:
            await verify_auth_token(authorization=f"Bearer {unicode_token}")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_null_bytes_in_token(self):
        """Test handling of null bytes in token."""
        null_token = "token\x00malicious"

        with pytest.raises(HTTPException) as exc_info:
            await verify_auth_token(authorization=f"Bearer {null_token}")

        assert exc_info.value.status_code == 401
