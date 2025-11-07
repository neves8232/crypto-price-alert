# ADR 003: Use SQLite for Development, PostgreSQL for Production

## Status

**Accepted** - November 7, 2025

## Context

We needed to choose a database system for storing alerts, cryptocurrency data, and price history. Requirements include:

- Support for both development and production environments
- ACID compliance for alert state management
- Support for concurrent read/write operations
- Ability to handle time-series data (price history)
- JSON/object storage for metadata
- Database migration support

### Alternatives Considered

1. **SQLite (Development) + PostgreSQL (Production)** - Dual database strategy
2. **PostgreSQL Only** - Single database for all environments
3. **MongoDB** - NoSQL document database
4. **MySQL/MariaDB** - Alternative relational database

## Decision

We chose to use **SQLite for development** and **PostgreSQL for production**, with **SQLAlchemy 2.0** as the ORM to abstract differences.

## Rationale

### Why Dual Database Strategy?

**Development Benefits (SQLite)**:
- Zero configuration required
- No separate database server needed
- Single-file database (easy to reset)
- Fast for single-user development
- Built into Python standard library
- Perfect for local testing

**Production Benefits (PostgreSQL)**:
- ACID compliance with concurrent users
- Advanced features (JSONB, CTEs, window functions)
- Proven scalability
- Excellent performance under load
- Strong ecosystem and tooling
- Industry standard

### SQLAlchemy as Abstraction Layer

SQLAlchemy 2.0 provides database-agnostic code:
```python
# Same code works with both databases
DATABASE_URL = os.getenv("DATABASE_URL")
# Development: sqlite+aiosqlite:///./data/alerts.db
# Production: postgresql+asyncpg://user:pass@host/db

engine = create_async_engine(DATABASE_URL)
```

### PostgreSQL Advantages Over Alternatives

**vs MySQL/MariaDB**:
- Better JSON support (JSONB vs JSON type)
- More SQL standard compliant
- Superior performance for complex queries
- Better open-source licensing

**vs MongoDB**:
- ACID compliance for critical alert state
- Structured schema with migrations
- Better support for relational queries
- SQL standard (widely known)
- SQLAlchemy ORM support

### SQLite Advantages for Development

- **Instant Setup**: No installation, no configuration
- **Portable**: Database is a single file
- **Fast Iteration**: Quick resets with `rm data/alerts.db`
- **No Resource Overhead**: No database server process
- **Deterministic**: Consistent behavior across machines

### PostgreSQL Advantages for Production

- **Concurrency**: Multiple workers can safely access database
- **JSONB**: Efficient storage and indexing of metadata
- **Partial Indexes**: Efficient queries on active alerts
- **Table Partitioning**: Can partition price_history by time
- **Connection Pooling**: Efficient connection management
- **Backup Tools**: pg_dump, pg_basebackup, point-in-time recovery

## Consequences

### Positive

1. **Developer Experience**: Fast setup for new developers
2. **Cost Efficiency**: No database costs in development
3. **Production Ready**: PostgreSQL proven at scale
4. **Flexibility**: Easy to switch databases via SQLAlchemy
5. **Standard Tools**: Well-supported by Python ecosystem

### Negative

1. **Dual Maintenance**: Must test against both databases
2. **Feature Differences**: Some PostgreSQL features not in SQLite
3. **Bug Differences**: Edge cases may differ between databases
4. **Complexity**: Environment-specific configuration needed

### Neutral

1. **SQLAlchemy Dependency**: Tightly coupled to ORM
2. **Migration Complexity**: Alembic migrations must work with both

## Implementation Details

### Configuration

**Environment Variables**:
```bash
# Development (.env.dev)
DATABASE_URL=sqlite+aiosqlite:///./data/crypto_alerts.db

# Production (.env.prod)
DATABASE_URL=postgresql+asyncpg://crypto_user:password@postgres:5432/crypto_alerts
```

### Database Setup

**SQLAlchemy Engine**:
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Create engine based on environment
engine = create_async_engine(
    DATABASE_URL,
    echo=LOG_LEVEL == "DEBUG",
    pool_pre_ping=True,  # PostgreSQL only
    pool_size=10,  # PostgreSQL only
    max_overflow=20  # PostgreSQL only
)

# Create session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency for FastAPI
async def get_db():
    async with async_session() as session:
        yield session
```

### Schema Compatibility

**Design for Both Databases**:
```python
# Use compatible column types
class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(String(64), primary_key=True)  # Works in both
    threshold = Column(Numeric(20, 8))  # Works in both
    metadata = Column(JSON)  # Works in both (PostgreSQL uses JSONB)
    created_at = Column(DateTime(timezone=True))  # Works in both
```

**Avoid Database-Specific Features in Core Code**:
```python
# Bad: PostgreSQL-specific
query = text("SELECT * FROM alerts WHERE metadata->>'priority' = 'high'")

# Good: Works with both
query = select(Alert).where(Alert.priority == "high")
```

### Migrations

**Alembic Configuration**:
```ini
# alembic.ini
[alembic]
script_location = alembic
sqlalchemy.url = %(DATABASE_URL)s

# Use environment variable
prepend_sys_path = .
version_path_separator = os  # Cross-platform
```

**Migration Script**:
```python
# alembic/env.py
import os
from sqlalchemy import engine_from_config

# Read from environment
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

# Auto-generate migrations
def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    ...
```

### Docker Configuration

**Development (docker-compose.dev.yml)**:
```yaml
services:
  crypto-service:
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/crypto_alerts.db
    volumes:
      - ./data:/app/data
```

**Production (docker-compose.prod.yml)**:
```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: crypto_alerts
      POSTGRES_USER: crypto_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  crypto-service:
    environment:
      - DATABASE_URL=postgresql+asyncpg://crypto_user:${POSTGRES_PASSWORD}@postgres:5432/crypto_alerts
    depends_on:
      - postgres
```

## Testing Strategy

### Unit Tests

Use SQLite for fast unit tests:
```python
@pytest.fixture
async def db():
    """Test database fixture"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession)
    async with async_session() as session:
        yield session
```

### Integration Tests

Test against PostgreSQL in CI:
```yaml
# .github/workflows/test.yml
jobs:
  test:
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://test_user:test_password@localhost/test_db
        run: pytest
```

## Data Migration Strategy

### SQLite to PostgreSQL Migration

For users migrating from dev to production:

```bash
# 1. Dump SQLite data
sqlite3 data/crypto_alerts.db .dump > data_dump.sql

# 2. Convert to PostgreSQL format
# (using migration script)
python scripts/sqlite_to_postgres.py data_dump.sql > postgres_dump.sql

# 3. Import to PostgreSQL
psql -U crypto_user -d crypto_alerts -f postgres_dump.sql
```

## Risk Mitigation

### Risk 1: Schema Incompatibility

**Mitigation**:
- Use SQLAlchemy ORM for all database access
- Avoid database-specific SQL
- Test migrations on both databases
- CI pipeline tests against PostgreSQL

### Risk 2: Performance Differences

**Mitigation**:
- Performance testing on production-like environment
- Query optimization for PostgreSQL
- Monitor query performance with metrics
- Use explain analyze for slow queries

### Risk 3: Data Loss on SQLite

**Mitigation**:
- SQLite only for development (no production data)
- Regular backups of PostgreSQL
- Database health checks
- Automated backup schedule

## Performance Considerations

### SQLite Limitations

- Single writer at a time
- No network access
- Limited concurrent readers
- Not suitable for production with multiple workers

### PostgreSQL Optimizations

```python
# Connection pooling
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,  # Base connections
    max_overflow=20,  # Additional connections
    pool_pre_ping=True,  # Verify connections
    pool_recycle=3600,  # Recycle after 1 hour
)

# Query optimization
query = select(Alert).where(
    Alert.enabled == True,
    Alert.crypto_id == "bitcoin"
).options(
    selectinload(Alert.user)  # Eager load relationships
)
```

### Indexing Strategy

```python
# Indexes for both databases
class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(String(64), primary_key=True)
    user_id = Column(String(64), index=True)  # Index for user queries
    crypto_id = Column(String(64), index=True)  # Index for crypto queries
    enabled = Column(Boolean, index=True)  # Index for active alert queries
    last_triggered_at = Column(DateTime(timezone=True), index=True)
```

## Alternatives Reconsidered

We will reconsider this decision if:
- SQLite proves inadequate for development
- PostgreSQL costs become prohibitive
- Performance issues at scale
- Team expertise changes
- Better alternatives emerge

## Future Enhancements

**Version 0.2.0**:
- Add TimescaleDB extension for time-series data
- Implement read replicas for scalability
- Add database connection pooling optimizations

**Version 0.3.0**:
- Evaluate CockroachDB for distributed deployment
- Consider Redis for caching layer
- Implement database sharding if needed

## References

- **SQLite Documentation**: https://www.sqlite.org/docs.html
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **SQLAlchemy 2.0 Docs**: https://docs.sqlalchemy.org/
- **Alembic Documentation**: https://alembic.sqlalchemy.org/

## Related Decisions

- [ADR 001: Use FastAPI](001-use-fastapi.md) - FastAPI supports async database operations
- [ADR 004: Microservices Architecture](004-microservices.md) - Each service can have its own database

## Review Date

**Next Review**: November 2026 (1 year from decision)

**Review Triggers**:
- Performance issues in production
- Database costs exceed budget
- SQLite limitations in development
- Team requests database change

---

**Decision made by**: Backend Architecture Team
**Date**: November 7, 2025
**Approved by**: Technical Lead
