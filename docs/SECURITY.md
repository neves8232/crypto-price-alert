# Security Documentation

Security model, best practices, and vulnerability reporting for the Crypto Price Alert System.

## Table of Contents

1. [Security Model Overview](#security-model-overview)
2. [Threat Model](#threat-model)
3. [Secret Management](#secret-management)
4. [Authentication & Authorization](#authentication--authorization)
5. [Network Security](#network-security)
6. [Data Security](#data-security)
7. [API Security](#api-security)
8. [Dependency Management](#dependency-management)
9. [Security Best Practices](#security-best-practices)
10. [Reporting Vulnerabilities](#reporting-vulnerabilities)

---

## Security Model Overview

The Crypto Price Alert System implements a defense-in-depth security strategy with multiple layers of protection:

```
┌─────────────────────────────────────────────────┐
│ Layer 1: Network (Firewall, Docker networks)   │
├─────────────────────────────────────────────────┤
│ Layer 2: Service (Auth tokens, rate limiting)  │
├─────────────────────────────────────────────────┤
│ Layer 3: Application (Input validation, ORM)   │
├─────────────────────────────────────────────────┤
│ Layer 4: Data (Encryption, access control)     │
└─────────────────────────────────────────────────┘
```

### Security Principles

1. **Least Privilege**: Services run with minimal required permissions
2. **Defense in Depth**: Multiple layers of security controls
3. **Fail Secure**: System fails to a secure state
4. **Secure by Default**: Security enabled out of the box
5. **Separation of Concerns**: Microservices architecture isolates components

---

## Threat Model

### Assets

| Asset | Value | Threats |
|-------|-------|---------|
| Telegram Bot Token | Critical | Unauthorized bot control |
| User Data | High | Data breach, privacy violation |
| Service Authentication | High | Unauthorized access |
| API Keys | Medium | Rate limit exhaustion, cost |
| Database | High | Data loss, corruption |

### Attack Vectors

1. **Network Attacks**:
   - DDoS on exposed ports
   - Man-in-the-middle attacks
   - Port scanning

2. **Application Attacks**:
   - SQL injection
   - Cross-site scripting (XSS)
   - API abuse

3. **Authentication Attacks**:
   - Token theft
   - Brute force
   - Replay attacks

4. **Data Attacks**:
   - Database breach
   - Log file exposure
   - Backup theft

### Mitigations

| Threat | Mitigation | Status |
|--------|-----------|--------|
| SQL Injection | SQLAlchemy ORM with parameterized queries | ✅ Implemented |
| Token Theft | Environment variables, no commits to git | ✅ Implemented |
| DDoS | Rate limiting, firewall rules | ✅ Implemented |
| Data Breach | Network isolation, minimal exposed ports | ✅ Implemented |
| XSS | Input validation, output encoding | ✅ Implemented |
| Log Exposure | Secret redaction in logs | ✅ Implemented |

---

## Secret Management

### Secret Types

**Critical Secrets**:
- `TELEGRAM_BOT_TOKEN`: Controls Telegram bot
- `AUTH_TOKEN`: Inter-service authentication
- `POSTGRES_PASSWORD`: Database access

**Sensitive Data**:
- User Telegram Chat IDs
- API keys (CoinGecko)
- Database connection strings

### Storage

**Environment Variables** (12-Factor App):
```bash
# .env file (never commit to git)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
AUTH_TOKEN=your_secure_random_token_here
POSTGRES_PASSWORD=your_database_password
```

**Verification**:
```bash
# Check .gitignore includes .env
grep ".env" .gitignore

# Verify .env is not tracked
git status --ignored
```

### Secret Generation

**Generate secure tokens**:
```bash
# 32-byte hex string (64 characters)
openssl rand -hex 32

# 32-byte base64 string
openssl rand -base64 32

# UUID
python3 -c "import uuid; print(uuid.uuid4())"
```

### Secret Rotation

**Schedule**:
- **AUTH_TOKEN**: Rotate monthly
- **POSTGRES_PASSWORD**: Rotate quarterly
- **TELEGRAM_BOT_TOKEN**: Rotate on suspected compromise

**Rotation Process**:
1. Generate new secret
2. Update `.env` file
3. Restart services: `make restart`
4. Verify health: `make health`
5. Revoke old secret

### Secret Redaction

**Logs automatically redact**:
```python
# Logged
logger.info("request_received", endpoint="/api/alerts")

# Redacted
logger.info("authentication", token="***REDACTED***")
```

**Redacted fields**:
- `authorization`
- `token`
- `password`
- `api_key`
- `telegram_bot_token`
- `session_id`

---

## Authentication & Authorization

### Inter-Service Authentication

**Bearer Token Authentication**:
```http
POST /api/v1/alerts/send HTTP/1.1
Host: telegram-service:52001
Authorization: Bearer {AUTH_TOKEN}
Content-Type: application/json
```

**Implementation**:
```python
async def verify_auth_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    scheme, token = authorization.split()
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")

    expected_token = os.getenv("AUTH_TOKEN")
    if not secrets.compare_digest(token, expected_token):
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    return token
```

**Security Features**:
- Constant-time comparison (`secrets.compare_digest`)
- No token in logs
- Single token per service pair

### User Authentication

**Current**: No user authentication (single-user system)

**Planned (v0.2.0)**:
- JWT-based authentication
- Role-based access control (RBAC)
- API key management

---

## Network Security

### Docker Network Isolation

**Configuration**:
```yaml
networks:
  crypto-alert-net:
    driver: bridge
    internal: false  # Needs external access for APIs
```

**Access Control**:
- `crypto-service`: Port 52000 exposed (public)
- `telegram-service`: Port 52001 internal only
- `postgres`: Port 5432 internal only
- All services on isolated network

### Firewall Rules

**Recommended iptables rules**:
```bash
# Allow web UI
iptables -A INPUT -p tcp --dport 52000 -j ACCEPT

# Block Telegram service port (internal only)
iptables -A INPUT -p tcp --dport 52001 -j DROP

# Block PostgreSQL port (internal only)
iptables -A INPUT -p tcp --dport 5432 -j DROP

# Drop all other inbound
iptables -A INPUT -j DROP
```

**Using UFW**:
```bash
# Allow only web UI port
sudo ufw allow 52000/tcp
sudo ufw deny 52001/tcp
sudo ufw deny 5432/tcp
sudo ufw enable
```

### TLS/HTTPS

**Development**: HTTP (localhost only)

**Production**: Use reverse proxy for TLS:

**NGINX Example**:
```nginx
server {
    listen 443 ssl http2;
    server_name crypto-alerts.example.com;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;

    location / {
        proxy_pass http://localhost:52000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Data Security

### Database Security

**Access Control**:
```yaml
# PostgreSQL configuration
postgres:
  environment:
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  volumes:
    - postgres_data:/var/lib/postgresql/data
  networks:
    - crypto-alert-net  # Internal only
```

**Connection Security**:
- Password authentication required
- No remote access (Docker network only)
- Encrypted at rest (optional, via volume encryption)

**Backup Security**:
```bash
# Encrypt backups with GPG
make db-backup
gpg -c backups/backup_20231107.sql

# Decrypt backup
gpg -d backups/backup_20231107.sql.gpg > backup.sql
```

### Data Encryption

**At Rest**:
- Database: Volume encryption (optional)
- Backups: GPG encryption (recommended)
- Secrets: Environment variables only

**In Transit**:
- External APIs: HTTPS (CoinGecko, Telegram)
- Inter-service: HTTP (internal Docker network)
- Web UI: HTTPS (via reverse proxy)

### Data Minimization

**Only store necessary data**:
- User IDs and Chat IDs (required)
- Alert configurations (required)
- Price history (90 days retention)
- Alert logs (30 days retention)

**Do NOT store**:
- Personal identifying information
- Financial data beyond prices
- Telegram usernames (optional only)

---

## API Security

### Input Validation

**Pydantic Schemas**:
```python
class AlertCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    crypto_id: str = Field(..., min_length=1, max_length=64)
    threshold: Decimal = Field(..., gt=0)

    @field_validator("alert_type")
    @classmethod
    def validate_alert_type(cls, v: str) -> str:
        allowed_types = {"PRICE_ABOVE", "PRICE_BELOW", ...}
        if v not in allowed_types:
            raise ValueError(f"alert_type must be one of {allowed_types}")
        return v
```

### Rate Limiting

**API Rate Limits**:
| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Read Operations | 100 req | 1 minute |
| Write Operations | 20 req | 1 minute |
| Telegram Delivery | 25 msg | 1 second |

**Implementation**:
```python
from fastapi import Request
from fastapi.responses import JSONResponse
import time

# Simple rate limiter (production: use Redis)
rate_limit_store = {}

async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    now = time.time()

    # Clean old entries
    rate_limit_store[client_ip] = [
        t for t in rate_limit_store.get(client_ip, [])
        if now - t < 60
    ]

    # Check limit
    if len(rate_limit_store.get(client_ip, [])) >= 100:
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded"},
            headers={"Retry-After": "60"}
        )

    # Add request
    rate_limit_store.setdefault(client_ip, []).append(now)

    return await call_next(request)
```

### CORS Configuration

**Development**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://crypto-alerts.example.com"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
```

---

## Dependency Management

### Vulnerability Scanning

**Scan dependencies regularly**:
```bash
# Using pip-audit
pip install pip-audit
pip-audit

# Using safety
pip install safety
safety check

# Using Snyk
snyk test
```

### Dependency Updates

**Update schedule**:
- Security patches: Immediately
- Minor updates: Monthly
- Major updates: Quarterly (with testing)

**Update process**:
```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package_name

# Update all packages (test first!)
pip install --upgrade -r requirements.txt

# Lock dependencies
pip freeze > requirements.txt
```

### Supply Chain Security

**Verify package integrity**:
```bash
# Use hash verification
pip install --require-hashes -r requirements.txt

# Verify package signatures
pip install --trusted-host pypi.org package_name
```

---

## Security Best Practices

### Development

1. **Never commit secrets**:
   - Use `.gitignore` for `.env`
   - Use git-secrets or pre-commit hooks
   - Scan commits with tools like truffleHog

2. **Use virtual environments**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Keep dependencies updated**:
   ```bash
   pip list --outdated
   pip install --upgrade package_name
   ```

### Deployment

1. **Use strong passwords**:
   ```bash
   openssl rand -base64 24
   ```

2. **Enable firewall**:
   ```bash
   sudo ufw enable
   sudo ufw allow 52000/tcp
   ```

3. **Regular backups**:
   ```bash
   # Daily backup cron job
   0 2 * * * /path/to/backup.sh
   ```

4. **Monitor logs**:
   ```bash
   make logs | grep -i error
   ```

### Operations

1. **Principle of least privilege**:
   - Run containers as non-root user
   - Minimal file permissions
   - Read-only filesystems where possible

2. **Regular updates**:
   ```bash
   docker pull postgres:16-alpine
   docker-compose up -d
   ```

3. **Security audits**:
   - Monthly: Review logs
   - Quarterly: Dependency updates
   - Annually: Full security audit

---

## Reporting Vulnerabilities

### Responsible Disclosure

We take security seriously. If you discover a vulnerability:

**DO**:
- Email security@crypto-price-alert.com
- Provide detailed information
- Allow 90 days for fix before public disclosure
- Work with us to verify the fix

**DON'T**:
- Publicly disclose before fix
- Exploit the vulnerability
- Test against production systems without permission

### Report Template

```markdown
**Vulnerability Type**: [e.g., SQL Injection, XSS]

**Affected Component**: [e.g., /api/alerts endpoint]

**Severity**: [Critical / High / Medium / Low]

**Description**:
Detailed description of the vulnerability.

**Steps to Reproduce**:
1. Step 1
2. Step 2
3. Step 3

**Impact**:
What an attacker could do with this vulnerability.

**Proof of Concept**:
Code or commands demonstrating the vulnerability.

**Suggested Fix**:
Your recommendation for fixing the issue.

**Contact Information**:
Your name and email for follow-up.
```

### Response Timeline

- **Initial response**: Within 24 hours
- **Triage**: Within 72 hours
- **Fix**: Within 30 days (critical), 90 days (others)
- **Disclosure**: Coordinated with reporter

### Rewards

We currently don't have a bug bounty program, but we recognize all security researchers in our SECURITY_HALL_OF_FAME.md file.

---

## Security Checklist

### Development

- [ ] No secrets in code
- [ ] Input validation on all endpoints
- [ ] SQL parameterized queries only
- [ ] Output encoding for XSS prevention
- [ ] Error messages don't leak information
- [ ] Tests include security test cases

### Deployment

- [ ] Unique, strong passwords
- [ ] Secrets in environment variables only
- [ ] .env not committed to git
- [ ] Firewall configured
- [ ] Only necessary ports exposed
- [ ] TLS/HTTPS configured (production)
- [ ] Regular backup schedule
- [ ] Log rotation configured

### Operations

- [ ] Regular dependency updates
- [ ] Security patches applied
- [ ] Logs monitored for suspicious activity
- [ ] Access logs reviewed
- [ ] Backups tested
- [ ] Incident response plan documented

---

## Security Resources

### Tools

- **pip-audit**: Python dependency vulnerability scanner
- **safety**: Check Python dependencies for known vulnerabilities
- **bandit**: Security linter for Python
- **git-secrets**: Prevent secrets in git commits
- **truffleHog**: Find secrets in git history

### Learning

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **OWASP API Security**: https://owasp.org/www-project-api-security/
- **CWE Top 25**: https://cwe.mitre.org/top25/
- **NIST Cybersecurity Framework**: https://www.nist.gov/cyberframework

---

## Contact

**Security Email**: security@crypto-price-alert.com

**PGP Key**: [Available on request]

**Response Time**: Within 24 hours

---

**Last Updated**: November 7, 2025
