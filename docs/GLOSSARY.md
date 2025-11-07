# Glossary

Definitions of technical terms, concepts, and acronyms used in the Crypto Price Alert System.

## A

**ADR (Architecture Decision Record)**
: A document that captures an important architectural decision along with its context and consequences.

**Alert**
: A notification triggered when a cryptocurrency price meets specific conditions defined by the user.

**Alert Debouncing**
: A mechanism to prevent the same alert from triggering too frequently by enforcing a minimum time period between triggers.

**Alert Engine**
: The component responsible for evaluating alert conditions and determining when to trigger notifications.

**Alert Type**
: The condition that triggers an alert (e.g., PRICE_ABOVE, PRICE_BELOW, PRICE_CROSSES_UP).

**API (Application Programming Interface)**
: A set of protocols and tools for building software and applications, allowing different software systems to communicate.

**API Key**
: A unique identifier used to authenticate requests to an API service.

**APScheduler**
: Advanced Python Scheduler, a task scheduling library used for running background jobs.

**Async/Await**
: Python keywords for writing asynchronous code that doesn't block execution.

**Authentication**
: The process of verifying the identity of a user or service.

**Authorization**
: The process of verifying what resources a user or service has permission to access.

## B

**Bearer Token**
: An access token used in HTTP authentication, included in the Authorization header.

**Background Task**
: A process that runs independently of user requests, such as periodic price polling.

## C

**CoinGecko**
: A cryptocurrency data aggregator providing price, market cap, and other cryptocurrency information via API.

**Container**
: A lightweight, standalone package that includes everything needed to run a piece of software (using Docker).

**CORS (Cross-Origin Resource Sharing)**
: A security feature that controls which domains can access a web API.

**Cryptocurrency**
: A digital or virtual currency that uses cryptography for security and operates on blockchain technology.

**Crypto ID**
: A unique identifier for a cryptocurrency (e.g., "bitcoin" for Bitcoin on CoinGecko).

## D

**Database Migration**
: A script that makes changes to a database schema in a controlled, versioned way.

**Debounce Period**
: The minimum time that must pass between alert triggers for the same alert.

**Deployment**
: The process of making an application available for use.

**Docker**
: A platform for developing, shipping, and running applications in containers.

**Docker Compose**
: A tool for defining and running multi-container Docker applications.

**Docker Network**
: An isolated network that allows Docker containers to communicate with each other.

**Docker Volume**
: A persistent data storage mechanism for Docker containers.

## E

**Endpoint**
: A specific URL path where an API can be accessed (e.g., /api/alerts).

**Environment Variable**
: A dynamic value that can affect the way running processes behave on a computer.

## F

**FastAPI**
: A modern, fast Python web framework for building APIs with automatic documentation.

**Firewall**
: A network security system that monitors and controls incoming and outgoing network traffic.

## H

**Health Check**
: An endpoint that reports the operational status of a service.

**HTTP (Hypertext Transfer Protocol)**
: The foundational protocol used for transmitting data over the web.

**HTTPS (HTTP Secure)**
: An encrypted version of HTTP using TLS/SSL for security.

**httpx**
: A modern async HTTP client library for Python.

## I

**Inter-Service Communication**
: Communication between different services in a microservices architecture.

## J

**JSON (JavaScript Object Notation)**
: A lightweight data-interchange format that's easy for humans to read and write.

**JWT (JSON Web Token)**
: A compact, URL-safe means of representing claims to be transferred between two parties.

## M

**Metadata**
: Additional information associated with an alert or other entity.

**Metrics**
: Quantitative measurements used to track and assess system performance.

**Microservice**
: An architectural style where an application is built as a collection of small, independent services.

**Migration**
: See Database Migration.

## O

**ORM (Object-Relational Mapping)**
: A technique that lets you query and manipulate data using an object-oriented paradigm.

## P

**Polling Interval**
: The time period between successive requests to fetch updated data.

**PostgreSQL**
: An advanced open-source relational database system.

**Price Threshold**
: The price level at which an alert should trigger.

**Prometheus**
: An open-source systems monitoring and alerting toolkit.

**Pydantic**
: A Python library for data validation using Python type annotations.

## R

**Rate Limiting**
: A technique to control the amount of incoming requests or outgoing messages.

**REST (Representational State Transfer)**
: An architectural style for designing networked applications.

**RESTful API**
: An API that follows REST architectural constraints.

## S

**Schema**
: A definition of the structure of data, including fields and types.

**Secret**
: Sensitive information like passwords, tokens, or API keys that must be protected.

**Service**
: An independent component of the application (e.g., crypto-service, telegram-service).

**SQLAlchemy**
: The Python SQL toolkit and Object-Relational Mapping library.

**SQLite**
: A lightweight, file-based relational database management system.

**structlog**
: A Python library for structured logging.

**Swagger UI**
: An interactive documentation interface for REST APIs.

## T

**Telegram Bot**
: An automated Telegram account that can send messages and perform actions.

**Telegram Bot API**
: The HTTP-based interface for interacting with Telegram bots.

**Telegram Bot Token**
: A unique authentication token provided by BotFather to control a bot.

**Telegram Chat ID**
: A unique identifier for a Telegram user or group chat.

**Threshold**
: The price level that triggers an alert when crossed or exceeded.

**TLS (Transport Layer Security)**
: A cryptographic protocol providing secure communication over a network.

**Token Bucket**
: A rate-limiting algorithm that uses tokens to control message flow.

## U

**uvicorn**
: A lightning-fast ASGI server implementation for Python.

## V

**Validation**
: The process of checking that data meets certain requirements.

**Volume**
: See Docker Volume.

## W

**Watchlist**
: The list of cryptocurrencies being monitored by the system.

**WebSocket**
: A protocol providing full-duplex communication channels over a single TCP connection.

## Alert Type Definitions

### PRICE_ABOVE
An alert type that triggers when the current price is above the specified threshold. Continues triggering at each price update while the condition is met (respecting debounce period).

**Example**: Alert when Bitcoin is above $50,000

### PRICE_BELOW
An alert type that triggers when the current price is below the specified threshold. Continues triggering at each price update while the condition is met (respecting debounce period).

**Example**: Alert when Ethereum is below $2,000

### PRICE_CROSSES_UP
An alert type that triggers exactly once when the price crosses from below to above the threshold. Resets when price drops below threshold again.

**Example**: Alert once when Bitcoin crosses $45,000 upward

### PRICE_CROSSES_DOWN
An alert type that triggers exactly once when the price crosses from above to below the threshold. Resets when price rises above threshold again.

**Example**: Alert once when Ethereum crosses $3,000 downward

### PRICE_CHANGE_PERCENT
An alert type that triggers when the price changes by a specified percentage from a reference point.

**Example**: Alert on 5% price change

## Component Definitions

### Crypto Service
The main application service responsible for:
- Monitoring cryptocurrency prices
- Evaluating alert conditions
- Managing configurations
- Serving the web UI and REST API

### Telegram Service
A dedicated microservice responsible for:
- Delivering alert notifications via Telegram
- Rate limiting message sending
- Managing message queue
- Handling delivery retries

### Alert Dispatcher
A component within the crypto service that sends alert requests to the Telegram service.

### Price Collector
A component that periodically fetches cryptocurrency price data from external APIs (like CoinGecko).

### Rate Limiter
A component that controls the rate of message sending to comply with Telegram's API limits (30 messages/second).

## Technical Acronyms

| Acronym | Full Form | Description |
|---------|-----------|-------------|
| **API** | Application Programming Interface | Interface for software communication |
| **ASGI** | Asynchronous Server Gateway Interface | Standard for Python async web servers |
| **CORS** | Cross-Origin Resource Sharing | Browser security feature |
| **CPU** | Central Processing Unit | Computer's main processor |
| **CRUD** | Create, Read, Update, Delete | Basic database operations |
| **CSV** | Comma-Separated Values | Data file format |
| **DB** | Database | Data storage system |
| **DNS** | Domain Name System | Internet naming system |
| **HTTP** | Hypertext Transfer Protocol | Web communication protocol |
| **HTTPS** | HTTP Secure | Encrypted HTTP |
| **I/O** | Input/Output | Data transfer operations |
| **IP** | Internet Protocol | Network addressing protocol |
| **JSON** | JavaScript Object Notation | Data interchange format |
| **JWT** | JSON Web Token | Authentication token format |
| **ORM** | Object-Relational Mapping | Database abstraction technique |
| **OS** | Operating System | System software |
| **RAM** | Random Access Memory | Computer memory |
| **REST** | Representational State Transfer | API architectural style |
| **SQL** | Structured Query Language | Database query language |
| **SSL** | Secure Sockets Layer | Encryption protocol (deprecated) |
| **TCP** | Transmission Control Protocol | Network protocol |
| **TLS** | Transport Layer Security | Encryption protocol |
| **UI** | User Interface | User interaction layer |
| **URL** | Uniform Resource Locator | Web address |
| **UUID** | Universally Unique Identifier | Unique ID format |
| **WSGI** | Web Server Gateway Interface | Standard for Python web servers |
| **XSS** | Cross-Site Scripting | Security vulnerability |

## Configuration Terms

### Environment File (.env)
A file containing environment variables for configuration, not committed to version control.

### Docker Compose File
A YAML file (docker-compose.yml) that defines services, networks, and volumes for a multi-container application.

### Dockerfile
A text file containing instructions for building a Docker image.

### Alembic
A database migration tool for SQLAlchemy.

### Makefile
A file containing a set of directives used to automate common tasks.

## Performance Terms

### Latency
The time delay between a request and its response.

### Throughput
The number of operations or transactions processed in a given time period.

### P95 (95th Percentile)
A value below which 95% of measurements fall; used for performance metrics.

### Resource Limit
A constraint on the amount of CPU, memory, or other resources a container can use.

## Security Terms

### Secret Redaction
The process of removing or masking sensitive information from logs and outputs.

### Bearer Token Authentication
An authentication scheme where the client includes a token in the Authorization header.

### Network Isolation
Separating network traffic to prevent unauthorized access between services.

### Input Validation
Checking user-provided data to ensure it meets requirements and prevent injection attacks.

### SQL Injection
A security vulnerability where malicious SQL code is inserted into queries.

### Defense in Depth
A security strategy using multiple layers of protection.

---

## See Also

- **[User Guide](USER_GUIDE.md)**: For user-focused documentation
- **[Developer Guide](development/DEVELOPER_GUIDE.md)**: For development terms
- **[API Reference](API_REFERENCE.md)**: For API-specific terms
- **[System Architecture](architecture/SYSTEM_ARCHITECTURE.md)**: For architectural concepts

---

**Last Updated**: November 7, 2025
