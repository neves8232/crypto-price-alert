"""
Telegram Client

Wrapper around python-telegram-bot for sending messages with:
- Retry logic with exponential backoff
- Error handling
- Logging
- Metrics
"""

import asyncio
from typing import Any, Dict, Optional

import structlog
from telegram import Bot
from telegram.error import (
    BadRequest,
    NetworkError,
    RetryAfter,
    TelegramError,
    TimedOut,
)

from .config import settings

logger = structlog.get_logger(__name__)


class TelegramClient:
    """
    Telegram Bot API client with retry logic and error handling.

    Handles all interactions with the Telegram Bot API including:
    - Sending messages
    - Handling rate limits
    - Retrying failed requests
    - Validating bot token
    """

    def __init__(self):
        """Initialize Telegram bot client."""
        self.bot = Bot(token=settings.telegram_bot_token)
        self.retry_attempts = settings.telegram_retry_attempts
        self.retry_delay = settings.telegram_retry_delay_seconds
        self.timeout = settings.telegram_api_timeout_seconds

        logger.info("telegram_client_initialized")

    async def validate_token(self) -> Dict[str, Any]:
        """
        Validate bot token and get bot information.

        Returns:
            Bot information from Telegram API

        Raises:
            TelegramError: If token is invalid
        """
        try:
            bot_info = await self.bot.get_me()

            bot_data = {
                "id": bot_info.id,
                "username": bot_info.username,
                "first_name": bot_info.first_name,
                "can_join_groups": bot_info.can_join_groups,
                "can_read_all_group_messages": bot_info.can_read_all_group_messages,
            }

            logger.info(
                "telegram_bot_validated",
                bot_username=bot_info.username,
                bot_id=bot_info.id
            )

            return bot_data

        except TelegramError as e:
            logger.error(
                "telegram_token_validation_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a message via Telegram with retry logic.

        Args:
            chat_id: Telegram chat ID
            text: Message text
            parse_mode: HTML or Markdown
            request_id: Request ID for tracking

        Returns:
            Dictionary with message_id and response data

        Raises:
            TelegramError: If message delivery fails after retries
        """
        attempt = 0
        last_error = None

        log_context = {
            "request_id": request_id,
            "chat_id_prefix": chat_id[:3] + "***" if len(chat_id) > 6 else "***",
            "message_length": len(text),
            "parse_mode": parse_mode,
        }

        while attempt < self.retry_attempts:
            try:
                logger.info(
                    "sending_telegram_message",
                    attempt=attempt + 1,
                    max_attempts=self.retry_attempts,
                    **log_context
                )

                # Send message
                message = await self.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=parse_mode,
                    read_timeout=self.timeout,
                    write_timeout=self.timeout,
                    connect_timeout=self.timeout,
                    pool_timeout=self.timeout,
                )

                result = {
                    "message_id": message.message_id,
                    "date": message.date.isoformat() if message.date else None,
                    "chat_id": message.chat.id,
                }

                logger.info(
                    "telegram_message_sent",
                    message_id=message.message_id,
                    **log_context
                )

                return result

            except RetryAfter as e:
                # Telegram rate limit - wait and retry
                retry_after = e.retry_after
                logger.warning(
                    "telegram_rate_limit_exceeded",
                    retry_after_seconds=retry_after,
                    attempt=attempt + 1,
                    **log_context
                )

                await asyncio.sleep(retry_after)
                last_error = e

            except BadRequest as e:
                # Client error - don't retry
                logger.error(
                    "telegram_bad_request",
                    error=str(e),
                    error_type=type(e).__name__,
                    **log_context
                )
                raise

            except TimedOut as e:
                # Timeout - retry with exponential backoff
                delay = self.retry_delay * (2 ** attempt)
                logger.warning(
                    "telegram_request_timeout",
                    error=str(e),
                    attempt=attempt + 1,
                    retry_delay_seconds=delay,
                    **log_context
                )

                await asyncio.sleep(delay)
                last_error = e

            except NetworkError as e:
                # Network error - retry with exponential backoff
                delay = self.retry_delay * (2 ** attempt)
                logger.warning(
                    "telegram_network_error",
                    error=str(e),
                    attempt=attempt + 1,
                    retry_delay_seconds=delay,
                    **log_context
                )

                await asyncio.sleep(delay)
                last_error = e

            except TelegramError as e:
                # Other Telegram errors
                logger.error(
                    "telegram_error",
                    error=str(e),
                    error_type=type(e).__name__,
                    attempt=attempt + 1,
                    **log_context
                )

                # For unknown errors, retry with exponential backoff
                delay = self.retry_delay * (2 ** attempt)
                await asyncio.sleep(delay)
                last_error = e

            attempt += 1

        # All retries exhausted
        logger.error(
            "telegram_message_failed",
            max_attempts_exceeded=True,
            final_error=str(last_error),
            **log_context
        )

        raise TelegramError(
            f"Failed to send message after {self.retry_attempts} attempts: {last_error}"
        )

    async def close(self) -> None:
        """Close bot session and cleanup resources."""
        try:
            # The Bot object doesn't need explicit cleanup in newer versions
            # but we log for tracking
            logger.info("telegram_client_closed")
        except Exception as e:
            logger.warning("telegram_client_close_error", error=str(e))
