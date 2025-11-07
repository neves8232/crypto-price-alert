-- PostgreSQL Initialization Script
-- This script runs automatically when the database is first created
-- ================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search optimization

-- Create additional indexes for performance (after tables are created by Alembic)
-- Note: Main schema is managed by Alembic migrations

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE crypto_alerts TO crypto_user;

-- Set timezone
SET timezone = 'UTC';

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'PostgreSQL initialization complete for crypto_alerts database';
END $$;
