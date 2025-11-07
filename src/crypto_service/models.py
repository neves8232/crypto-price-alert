"""
SQLAlchemy ORM models for the crypto price alert system.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    String, Integer, Numeric, Boolean, DateTime, Text, Index, ForeignKey, CheckConstraint, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from crypto_service.database import Base


class User(Base):
    """User model for managing users and their preferences."""

    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    telegram_chat_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    telegram_username: Mapped[Optional[str]] = mapped_column(String(64))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    alert_count: Mapped[int] = mapped_column(Integer, default=0)
    watchlist_size: Mapped[int] = mapped_column(Integer, default=0)
    max_watchlist_size: Mapped[int] = mapped_column(Integer, default=25)
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_users_telegram_chat_id", "telegram_chat_id"),
        Index("idx_users_last_activity", "last_activity_at"),
    )


class Cryptocurrency(Base):
    """Cryptocurrency model for tracked assets."""

    __tablename__ = "cryptocurrencies"

    crypto_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    current_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8))
    market_cap: Mapped[Optional[int]] = mapped_column(Integer)
    volume_24h: Mapped[Optional[int]] = mapped_column(Integer)
    price_change_24h: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8))
    price_change_percentage_24h: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    api_data: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="cryptocurrency")
    price_history: Mapped[list["PriceHistory"]] = relationship(
        "PriceHistory", back_populates="cryptocurrency", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_crypto_symbol", "symbol"),
        Index("idx_crypto_active", "is_active"),
        Index("idx_crypto_last_updated", "last_updated"),
    )


class Alert(Base):
    """Alert model for user-defined price alerts."""

    __tablename__ = "alerts"

    alert_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.user_id", ondelete="CASCADE"))
    crypto_id: Mapped[str] = mapped_column(String(64), ForeignKey("cryptocurrencies.crypto_id"))
    alert_type: Mapped[str] = mapped_column(String(32), nullable=False)
    threshold: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    telegram_chat_id: Mapped[str] = mapped_column(String(64), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_triggered_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8))
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="alerts")
    cryptocurrency: Mapped["Cryptocurrency"] = relationship("Cryptocurrency", back_populates="alerts")
    alert_logs: Mapped[list["AlertLog"]] = relationship(
        "AlertLog", back_populates="alert", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("threshold > 0", name="check_threshold_positive"),
        CheckConstraint(
            "alert_type IN ('PRICE_ABOVE', 'PRICE_BELOW', 'PRICE_CHANGE_PERCENT', 'PRICE_CROSSES_UP', 'PRICE_CROSSES_DOWN')",
            name="check_alert_type"
        ),
        Index("idx_alerts_user_id", "user_id"),
        Index("idx_alerts_crypto_id", "crypto_id"),
        Index("idx_alerts_enabled", "enabled", postgresql_where="enabled = true"),
        Index("idx_alerts_last_triggered", "last_triggered_at"),
        Index("idx_alerts_active_monitors", "crypto_id", "enabled", postgresql_where="enabled = true"),
    )


class PriceHistory(Base):
    """Price history model for storing historical price data."""

    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crypto_id: Mapped[str] = mapped_column(String(64), ForeignKey("cryptocurrencies.crypto_id"))
    price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    volume_24h: Mapped[Optional[int]] = mapped_column(Integer)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    source: Mapped[str] = mapped_column(String(32), default="api")

    # Relationships
    cryptocurrency: Mapped["Cryptocurrency"] = relationship("Cryptocurrency", back_populates="price_history")

    __table_args__ = (
        CheckConstraint("price > 0", name="check_price_positive"),
        Index("idx_price_history_crypto_time", "crypto_id", "timestamp"),
        Index("idx_price_history_timestamp", "timestamp"),
    )


class AlertLog(Base):
    """Alert log model for tracking triggered alerts."""

    __tablename__ = "alert_logs"

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_id: Mapped[str] = mapped_column(String(64), ForeignKey("alerts.alert_id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    crypto_id: Mapped[str] = mapped_column(String(64), nullable=False)
    trigger_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    threshold: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(32), nullable=False)
    message_sent: Mapped[Optional[str]] = mapped_column(Text)
    telegram_message_id: Mapped[Optional[int]] = mapped_column(Integer)
    delivery_status: Mapped[str] = mapped_column(String(32), nullable=False)
    delivery_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    alert: Mapped["Alert"] = relationship("Alert", back_populates="alert_logs")

    __table_args__ = (
        Index("idx_alert_logs_alert_id", "alert_id"),
        Index("idx_alert_logs_user_id", "user_id"),
        Index("idx_alert_logs_triggered_at", "triggered_at"),
        Index("idx_alert_logs_delivery_status", "delivery_status"),
    )
