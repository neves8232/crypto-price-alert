"""Initial database schema

Revision ID: 001_initial
Revises:
Create Date: 2025-11-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""
    # Users table
    op.create_table(
        'users',
        sa.Column('user_id', sa.String(64), primary_key=True),
        sa.Column('telegram_chat_id', sa.String(64), nullable=False, unique=True),
        sa.Column('telegram_username', sa.String(64), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('alert_count', sa.Integer(), default=0),
        sa.Column('watchlist_size', sa.Integer(), default=0),
        sa.Column('max_watchlist_size', sa.Integer(), default=25),
        sa.Column('preferences', sa.JSON(), default=dict),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_users_telegram_chat_id', 'users', ['telegram_chat_id'])
    op.create_index('idx_users_last_activity', 'users', ['last_activity_at'])

    # Cryptocurrencies table
    op.create_table(
        'cryptocurrencies',
        sa.Column('crypto_id', sa.String(64), primary_key=True),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('current_price', sa.Numeric(20, 8), nullable=True),
        sa.Column('market_cap', sa.Integer(), nullable=True),
        sa.Column('volume_24h', sa.Integer(), nullable=True),
        sa.Column('price_change_24h', sa.Numeric(20, 8), nullable=True),
        sa.Column('price_change_percentage_24h', sa.Numeric(10, 4), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=True),
        sa.Column('api_data', sa.JSON(), default=dict),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_crypto_symbol', 'cryptocurrencies', ['symbol'])
    op.create_index('idx_crypto_active', 'cryptocurrencies', ['is_active'])
    op.create_index('idx_crypto_last_updated', 'cryptocurrencies', ['last_updated'])

    # Alerts table
    op.create_table(
        'alerts',
        sa.Column('alert_id', sa.String(64), primary_key=True),
        sa.Column('user_id', sa.String(64), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('crypto_id', sa.String(64), sa.ForeignKey('cryptocurrencies.crypto_id'), nullable=False),
        sa.Column('alert_type', sa.String(32), nullable=False),
        sa.Column('threshold', sa.Numeric(20, 8), nullable=False),
        sa.Column('telegram_chat_id', sa.String(64), nullable=False),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_triggered_price', sa.Numeric(20, 8), nullable=True),
        sa.Column('trigger_count', sa.Integer(), default=0),
        sa.Column('metadata', sa.JSON(), default=dict),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint('threshold > 0', name='check_threshold_positive'),
        sa.CheckConstraint(
            "alert_type IN ('PRICE_ABOVE', 'PRICE_BELOW', 'PRICE_CHANGE_PERCENT', 'PRICE_CROSSES_UP', 'PRICE_CROSSES_DOWN')",
            name='check_alert_type'
        ),
    )
    op.create_index('idx_alerts_user_id', 'alerts', ['user_id'])
    op.create_index('idx_alerts_crypto_id', 'alerts', ['crypto_id'])
    op.create_index('idx_alerts_enabled', 'alerts', ['enabled'])
    op.create_index('idx_alerts_last_triggered', 'alerts', ['last_triggered_at'])
    op.create_index('idx_alerts_active_monitors', 'alerts', ['crypto_id', 'enabled'])

    # Price history table
    op.create_table(
        'price_history',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('crypto_id', sa.String(64), sa.ForeignKey('cryptocurrencies.crypto_id'), nullable=False),
        sa.Column('price', sa.Numeric(20, 8), nullable=False),
        sa.Column('volume_24h', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('source', sa.String(32), default='api'),
        sa.CheckConstraint('price > 0', name='check_price_positive'),
    )
    op.create_index('idx_price_history_crypto_time', 'price_history', ['crypto_id', 'timestamp'])
    op.create_index('idx_price_history_timestamp', 'price_history', ['timestamp'])

    # Alert logs table
    op.create_table(
        'alert_logs',
        sa.Column('log_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('alert_id', sa.String(64), sa.ForeignKey('alerts.alert_id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(64), nullable=False),
        sa.Column('crypto_id', sa.String(64), nullable=False),
        sa.Column('trigger_price', sa.Numeric(20, 8), nullable=False),
        sa.Column('threshold', sa.Numeric(20, 8), nullable=False),
        sa.Column('alert_type', sa.String(32), nullable=False),
        sa.Column('message_sent', sa.Text(), nullable=True),
        sa.Column('telegram_message_id', sa.Integer(), nullable=True),
        sa.Column('delivery_status', sa.String(32), nullable=False),
        sa.Column('delivery_time_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', sa.JSON(), default=dict),
    )
    op.create_index('idx_alert_logs_alert_id', 'alert_logs', ['alert_id'])
    op.create_index('idx_alert_logs_user_id', 'alert_logs', ['user_id'])
    op.create_index('idx_alert_logs_triggered_at', 'alert_logs', ['triggered_at'])
    op.create_index('idx_alert_logs_delivery_status', 'alert_logs', ['delivery_status'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('alert_logs')
    op.drop_table('price_history')
    op.drop_table('alerts')
    op.drop_table('cryptocurrencies')
    op.drop_table('users')
