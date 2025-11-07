# Docker Setup - Quick Reference

Quick reference guide for Docker deployment of the Crypto Price Alert System.

## Quick Start

### 1. Automated Setup (Recommended)

```bash
# Run the quick start script
./scripts/quickstart.sh
```

This script will:
- Check prerequisites (Docker, Docker Compose)
- Create `.env` file from template
- Validate configuration
- Start services in your chosen mode

### 2. Manual Setup

```bash
# 1. Create environment file
cp .env.example .env

# 2. Edit .env with your values
nano .env

# 3a. Start development mode
make dev

# OR

# 3b. Start production mode
make prod
```

## Essential Commands

```bash
# Start services
make dev              # Development with SQLite
make prod             # Production with PostgreSQL
make monitoring-up    # With Prometheus + Grafana

# Check status
make status           # Service status
make health           # Health checks
make logs             # View all logs

# Stop services
make down             # Stop all services
make clean            # Stop and remove volumes (⚠️  data loss!)

# Database
make db-backup        # Backup database
make db-restore       # Restore from backup
make db-shell         # PostgreSQL shell

# Help
make help             # Show all commands
```

## Required Environment Variables

Edit `.env` and set these **required** values:

| Variable | How to Get | Example |
|----------|-----------|---------|
| `TELEGRAM_BOT_TOKEN` | Message @BotFather on Telegram | `123456789:ABCdef...` |
| `AUTH_TOKEN` | Run: `openssl rand -hex 32` | (32+ characters) |
| `POSTGRES_PASSWORD` | Set strong password | (16+ characters) |

## Access Points

Once running, access your services at:

| Service | URL | Description |
|---------|-----|-------------|
| **Web UI** | http://localhost:52000 | Main dashboard |
| **API Docs** | http://localhost:52000/docs | Interactive API documentation |
| **Health** | http://localhost:52000/health | System health status |
| **Grafana** | http://localhost:3000 | Metrics (with monitoring profile) |
| **Prometheus** | http://localhost:9090 | Raw metrics (with monitoring profile) |

## Common Issues

### Services won't start

```bash
# Check if ports are in use
sudo netstat -tulpn | grep 52000

# Check Docker is running
systemctl status docker

# Validate environment
make validate-env
```

### Health check failures

```bash
# View logs
make logs-crypto
make logs-telegram

# Restart specific service
docker-compose restart crypto-service
```

### Database connection errors

```bash
# Check PostgreSQL
docker-compose ps postgres

# Test connection
docker exec crypto-postgres pg_isready -U crypto_user

# Restart database
docker-compose restart postgres
```

## File Structure

```
crypto-price-alert/
├── docker-compose.yml           # Main compose file
├── docker-compose.dev.yml       # Development overrides
├── docker-compose.prod.yml      # Production overrides
├── .env.example                 # Environment template
├── .env                         # Your config (create from .env.example)
├── Makefile                     # Convenience commands
├── scripts/
│   └── quickstart.sh           # Automated setup script
├── config/
│   ├── prometheus/             # Prometheus config
│   └── grafana/                # Grafana dashboards
└── docs/
    └── deployment/
        └── DOCKER_GUIDE.md     # Complete documentation
```

## Deployment Modes

### Development Mode

- **Database**: SQLite (file-based)
- **Logging**: DEBUG level
- **Features**: Hot reload, relaxed rate limits
- **Data**: Stored in `./data/` directory

```bash
make dev
```

### Production Mode

- **Database**: PostgreSQL (container)
- **Logging**: INFO level
- **Features**: Resource limits, auto-restart
- **Data**: Persistent Docker volumes

```bash
make prod
```

### With Monitoring

Adds Prometheus and Grafana:

```bash
make monitoring-up
```

## Security Checklist

- [ ] Change default `POSTGRES_PASSWORD`
- [ ] Generate strong `AUTH_TOKEN` (32+ chars)
- [ ] Never commit `.env` file
- [ ] Use firewall to restrict port access
- [ ] Enable SSL/TLS for production (via reverse proxy)
- [ ] Regularly backup database
- [ ] Keep Docker images updated

## Backup Strategy

```bash
# Manual backup
make db-backup

# Automated backups (add to crontab)
0 2 * * * cd /home/user/crypto-price-alert && make db-backup
```

Backups are saved to `backups/` directory.

## Updating the System

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
make prod-build
make prod-restart

# Verify
make status
make health
```

## Getting Help

1. **Check logs**: `make logs`
2. **Verify environment**: `make validate-env`
3. **Test health**: `make health`
4. **Read full docs**: `docs/deployment/DOCKER_GUIDE.md`
5. **Service docs**:
   - Telegram Service: `src/telegram_service/README.md`
   - Crypto Service: `src/crypto_service/README.md`

## Additional Resources

- **Complete Docker Guide**: [docs/deployment/DOCKER_GUIDE.md](docs/deployment/DOCKER_GUIDE.md)
- **Project Overview**: [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md)
- **Main README**: [README.md](README.md)

---

**Need more help?** Run `make help` for all available commands.
