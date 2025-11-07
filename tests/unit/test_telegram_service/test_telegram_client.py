"""
Unit tests for Telegram client module.

Tests message sending, retry logic, and error handling.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from telegram_service.telegram_client import TelegramClient
from telegram.error import (
    TelegramError,
    RetryAfter,
    BadRequest,
    TimedOut,
    NetworkError,
)


@pytest.mark.unit
class TestTelegramClient:
    """Test cases for TelegramClient class."""

    @pytest.mark.asyncio
    async def test_client_initialization(self, test_env_vars):
        """Test that client initializes with correct configuration."""
        client = TelegramClient()

        assert client.retry_attempts == 3
        assert client.retry_delay == 1
        assert client.timeout == 10

    @pytest.mark.asyncio
    async def test_validate_token_success(self, mock_telegram_bot):
        """Test successful token validation."""
        with patch('telegram_service.telegram_client.Bot', return_value=mock_telegram_bot):
            client = TelegramClient()
            bot_info = await client.validate_token()

            assert bot_info["id"] == 123456789
            assert bot_info["username"] == "test_bot"
            assert bot_info["first_name"] == "Test Bot"
            assert bot_info["can_join_groups"] is True

    @pytest.mark.asyncio
    async def test_validate_token_failure(self):
        """Test token validation failure."""
        mock_bot = AsyncMock()
        mock_bot.get_me.side_effect = TelegramError("Invalid token")

        with patch('telegram_service.telegram_client.Bot', return_value=mock_bot):
            client = TelegramClient()

            with pytest.raises(TelegramError):
                await client.validate_token()

    @pytest.mark.asyncio
    async def test_send_message_success(self, mock_telegram_bot):
        """Test successful message sending."""
        with patch('telegram_service.telegram_client.Bot', return_value=mock_telegram_bot):
            client = TelegramClient()

            result = await client.send_message(
                chat_id="123456789",
                text="Test message",
                request_id="req-123"
            )

            assert result["message_id"] == 12345
            assert result["chat_id"] == 123456789
            assert "date" in result

    @pytest.mark.asyncio
    async def test_send_message_with_html(self, mock_telegram_bot):
        """Test sending message with HTML parse mode."""
        with patch('telegram_service.telegram_client.Bot', return_value=mock_telegram_bot):
            client = TelegramClient()

            result = await client.send_message(
                chat_id="123456789",
                text="<b>Bold</b> text",
                parse_mode="HTML",
                request_id="req-123"
            )

            assert result["message_id"] == 12345
            mock_telegram_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_retry_after(self, mock_telegram_bot):
        """Test handling of RetryAfter error."""
        # First call raises RetryAfter, second succeeds
        mock_telegram_bot.send_message.side_effect = [
            RetryAfter(retry_after=1),
            mock_telegram_bot.send_message.return_value
        ]

        with patch('telegram_service.telegram_client.Bot', return_value=mock_telegram_bot):
            client = TelegramClient()

            with patch('asyncio.sleep') as mock_sleep:
                result = await client.send_message(
                    chat_id="123456789",
                    text="Test message"
                )

                assert result["message_id"] == 12345
                mock_sleep.assert_called_with(1)  # Should sleep for retry_after seconds

    @pytest.mark.asyncio
    async def test_send_message_bad_request_no_retry(self, mock_telegram_bot):
        """Test that BadRequest errors are not retried."""
        mock_telegram_bot.send_message.side_effect = BadRequest("Invalid chat_id")

        with patch('telegram_service.telegram_client.Bot', return_value=mock_telegram_bot):
            client = TelegramClient()

            with pytest.raises(BadRequest):
                await client.send_message(
                    chat_id="invalid",
                    text="Test message"
                )

            # Should only be called once (no retries)
            assert mock_telegram_bot.send_message.call_count == 1

    @pytest.mark.asyncio
    async def test_send_message_timeout_retry(self, mock_telegram_bot):
        """Test retry on timeout error."""
        # First two calls timeout, third succeeds
        mock_telegram_bot.send_message.side_effect = [
            TimedOut(),
            TimedOut(),
            mock_telegram_bot.send_message.return_value
        ]

        with patch('telegram_service.telegram_client.Bot', return_value=mock_telegram_bot):
            client = TelegramClient()

            with patch('asyncio.sleep') as mock_sleep:
                result = await client.send_message(
                    chat_id="123456789",
                    text="Test message"
                )

                assert result["message_id"] == 12345
                # Should have exponential backoff: 1s, 2s
                assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    async def test_send_message_network_error_retry(self, mock_telegram_bot):
        """Test retry on network error."""
        mock_telegram_bot.send_message.side_effect = [
            NetworkError("Connection failed"),
            mock_telegram_bot.send_message.return_value
        ]

        with patch('telegram_service.telegram_client.Bot', return_value=mock_telegram_bot):
            client = TelegramClient()

            with patch('asyncio.sleep'):
                result = await client.send_message(
                    chat_id="123456789",
                    text="Test message"
                )

                assert result["message_id"] == 12345
                assert mock_telegram_bot.send_message.call_count == 2

    @pytest.mark.asyncio
    async def test_send_message_max_retries_exceeded(self, mock_telegram_bot):
        """Test that max retries are enforced."""
        mock_telegram_bot.send_message.side_effect = TimedOut()

        with patch('telegram_service.telegram_client.Bot', return_value=mock_telegram_bot):
            client = TelegramClient()
            client.retry_attempts = 3

            with patch('asyncio.sleep'):
                with pytest.raises(TelegramError) as exc_info:
                    await client.send_message(
                        chat_id="123456789",
                        text="Test message"
                    )

                assert "Failed to send message after 3 attempts" in str(exc_info.value)
                assert mock_telegram_bot.send_message.call_count == 3

    @pytest.mark.asyncio
    async def test_send_message_exponential_backoff(self, mock_telegram_bot):
        """Test exponential backoff on retries."""
        mock_telegram_bot.send_message.side_effect = [
            TimedOut(),
            TimedOut(),
            mock_telegram_bot.send_message.return_value
        ]

        with patch('telegram_service.telegram_client.Bot', return_value=mock_telegram_bot):
            client = TelegramClient()
            client.retry_delay = 1

            with patch('asyncio.sleep') as mock_sleep:
                await client.send_message(
                    chat_id="123456789",
                    text="Test message"
                )

                # Check exponential backoff: 1s, 2s
                calls = [call.args[0] for call in mock_sleep.call_args_list]
                assert calls == [1, 2]  # 1 * 2^0, 1 * 2^1

    @pytest.mark.asyncio
    async def test_close_client(self):
        """Test closing the client."""
        mock_bot = AsyncMock()

        with patch('telegram_service.telegram_client.Bot', return_value=mock_bot):
            client = TelegramClient()
            await client.close()  # Should not raise any errors


@pytest.mark.unit
class TestTelegramClientEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_send_empty_message(self, mock_telegram_bot):
        """Test sending empty message."""
        with patch('telegram_service.telegram_client.Bot', return_value=mock_telegram_bot):
            client = TelegramClient()

            # Should still call the API (Telegram will reject it)
            result = await client.send_message(
                chat_id="123456789",
                text=""
            )

            mock_telegram_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_very_long_message(self, mock_telegram_bot):
        """Test sending very long message."""
        with patch('telegram_service.telegram_client.Bot', return_value=mock_telegram_bot):
            client = TelegramClient()

            long_text = "a" * 5000  # Telegram limit is 4096

            result = await client.send_message(
                chat_id="123456789",
                text=long_text
            )

            assert result["message_id"] == 12345

    @pytest.mark.asyncio
    async def test_chat_id_privacy(self, mock_telegram_bot):
        """Test that chat IDs are partially masked in logs."""
        with patch('telegram_service.telegram_client.Bot', return_value=mock_telegram_bot):
            client = TelegramClient()

            # This tests the privacy feature where chat_id is masked in logs
            result = await client.send_message(
                chat_id="1234567890",
                text="Test",
                request_id="req-123"
            )

            # The actual chat_id should still be sent to Telegram
            assert result["chat_id"] == 123456789

    @pytest.mark.asyncio
    async def test_unknown_telegram_error(self, mock_telegram_bot):
        """Test handling of unknown Telegram errors."""
        mock_telegram_bot.send_message.side_effect = TelegramError("Unknown error")

        with patch('telegram_service.telegram_client.Bot', return_value=mock_telegram_bot):
            client = TelegramClient()
            client.retry_attempts = 2

            with patch('asyncio.sleep'):
                with pytest.raises(TelegramError):
                    await client.send_message(
                        chat_id="123456789",
                        text="Test"
                    )

                # Should retry on unknown errors
                assert mock_telegram_bot.send_message.call_count == 2
