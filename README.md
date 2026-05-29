# 🏦 Loan System - Multi-Country Credit System

Loan application management system designed to operate across multiple countries (Spain, Mexico, Colombia, Brazil) with a scalable, event-driven architecture ready to handle millions of transactions.

## 📋 Table of Contents

- [Installation and Setup](#-installation-and-setup)
- [Assumptions](#-assumptions)
- [Data Model](#-data-model)
- [Technical Decisions](#-technical-decisions)
- [Security Considerations](#-security-considerations)
- [Scalability and Large-Volume Data Handling](#-scalability-and-large-volume-data-handling)
- [Concurrency, Queues, Cache and Webhooks Strategy](#-concurrency-queues-cache-and-webhooks-strategy)
- [Architecture](#️-architecture)
- [API Endpoints](#-api-endpoints)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)

---

## 🚀 Installation and Setup

### Prerequisites

#### For Docker (Recommended Option)
- [Docker](https://docs.docker.com/get-docker/) >= 20.10
- [Docker Compose](https://docs.docker.com/compose/install/) >= 2.0

#### For Local Development
- [Python](https://www.python.org/downloads/) >= 3.11
- [Node.js](https://nodejs.org/) >= 18.0
- [Make](https://www.gnu.org/software/make/) (included on macOS/Linux)
- [Docker](https://docs.docker.com/get-docker/) (for PostgreSQL and Redis)

### Quick Start with Docker (Recommended)

**Estimated time: < 5 minutes**

#### 1. Clone the repository
```bash
git clone https://github.com/coderTtxi12/loan-system.git
cd loan-system
```

#### 2. Configure environment variables

**Backend:**
```bash
cp backend/.env.example backend/.env
```

**Frontend:**
```bash
cp frontend/.env.example frontend/.env
```

> 💡 **Note**: If you do not create the `.env` files, Docker Compose will use the default values defined in `docker-compose.yml`.

#### 3. Start all services
```bash
docker compose up --build
```

> ⏳ The first run will take a few minutes to build the images.

#### 4. Run database migrations

In another terminal:
```bash
docker compose exec backend alembic upgrade head
```

#### 5. Load demo users (seed)
```bash
docker compose exec backend python -m app.db.seed
```

#### 6. Access the application

| Service | URL |
|----------|-----|
| 🖥️ **Frontend** | http://localhost:3000 |
| 🔧 **API Docs (Swagger)** | http://localhost:8000/docs |
| 📘 **API Docs (ReDoc)** | http://localhost:8000/redoc |
| 🗄️ **pgAdmin** (optional) | http://localhost:5050 |

**🔐 Demo Credentials:**
| Role | Email | Password |
|-----|-------|----------|
| Admin | `admin@loan.com` | `admin123` |
| Analyst | `analyst@loan.com` | `analyst123` |
| Viewer | `viewer@loan.com` | `viewer123` |

**pgAdmin credentials:**
- Email: `admin@admin.com`
- Password: `admin`

#### 7. Stop the services
```bash
docker compose down
```

To also remove volumes (data):
```bash
docker compose down -v
```

### Local Development

#### 1. Clone the repository
```bash
git clone https://github.com/coderTtxi12/loan-system.git
cd loan-system
```

#### 2. Configure environment variables

**Backend:**
```bash
cp backend/.env.example backend/.env
```

**Frontend:**
```bash
cp frontend/.env.example frontend/.env
```

#### 3. Start PostgreSQL and Redis
```bash
docker compose up -d postgres redis
```

Wait for the services to become healthy:
```bash
docker compose ps
```

#### 4. Install dependencies
```bash
make install
```

This will install:
- Python dependencies in a virtual environment (`backend/.venv`)
- Node.js dependencies (`frontend/node_modules`)

#### 5. Run database migrations
```bash
make migrate
```

#### 6. Load demo users (seed)
```bash
make seed
```

#### 7. Start the development servers
```bash
make dev
```

| Service | URL |
|----------|-----|
| 🖥️ **Frontend** | http://localhost:5173 |
| 🔧 **API Docs** | http://localhost:8000/docs |

### Start services separately

```bash
# Backend only
make dev-backend

# Frontend only
make dev-frontend

# Workers
make workers
```

### Make Commands

| Command | Description |
|---------|-------------|
| `make help` | Show help with all commands |
| `make install` | Install dependencies (backend + frontend) |
| `make dev` | Start development servers |
| `make dev-backend` | Start backend only |
| `make dev-frontend` | Start frontend only |
| `make test` | Run all tests |
| `make test-backend` | Run backend tests |
| `make test-coverage` | Run tests with coverage |
| `make lint` | Run linters |
| `make migrate` | Run DB migrations |
| `make migrate-create msg="descripcion"` | Create a new migration |
| `make seed` | Load demo users |
| `make workers` | Run all workers |
| `make worker-risk` | Run risk worker |
| `make worker-audit` | Run audit worker |
| `make worker-webhook` | Run webhook worker |
| `make docker-build` | Build Docker images |
| `make docker-up` | Start services with Docker Compose |
| `make docker-down` | Stop Docker services |
| `make clean` | Clean generated files |

---

## 📝 Assumptions

### Business Assumptions

1. **Implemented Countries**: 4 countries (ES, MX, CO, BR) were implemented out of the 6 required. The remaining countries (PT, IT) can be added easily by following the same Strategy pattern.

2. **Banking Providers**: Banking providers are simulated for the MVP. In production, each country would have its own real provider (Equifax Spain, Buró de Crédito Mexico, etc.).

3. **Document Validation**: Format and check-digit validation is implemented where applicable (Spanish DNI, Mexican CURP). Validation against government databases is assumed to be the responsibility of the banking provider.

4. **Loan States**: A standard state flow was defined that may vary by country. Transitions are validated to prevent invalid states.

5. **Authentication**: JWT is implemented with basic roles (ADMIN, ANALYST, VIEWER). Country-based authorization can be added easily.

6. **Real-time Updates**: Socket.IO is used for real-time updates.

7. **Scalability**: The system is designed to scale horizontally.

### Technical Assumptions

1. **Database**: PostgreSQL 15+ with support for partitioning, triggers, and LISTEN/NOTIFY.

2. **Cache**: Redis available for cache and sessions. If Redis is unavailable, the system works but without caching.

3. **Workers**: Workers can run on multiple instances without conflicts thanks to `SELECT FOR UPDATE SKIP LOCKED`.

4. **Timezone**: UTC is used for all timestamps. Conversion to local timezone is done on the frontend.

5. **PII Encryption**: Fernet (symmetric encryption) derived from `JWT_SECRET` is used. In production, a dedicated key stored in a key management service is recommended.

---

## 🗄️ Data Model

### Entity-Relationship Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    loan_applications                        │
│  ────────────────────────────────────────────────────────  │
│  id (UUID, PK)                                             │
│  country_code (VARCHAR(2)) - Partitioning by LIST          │
│  document_type (VARCHAR(20))                               │
│  document_number (VARCHAR(255)) - ENCRYPTED (PII)          │
│  document_hash (VARCHAR(64)) - SHA256 for lookups          │
│  full_name (VARCHAR(255)) - ENCRYPTED (PII)                │
│  amount_requested (DECIMAL(15,2))                          │
│  monthly_income (DECIMAL(15,2))                             │
│  currency (VARCHAR(3))                                     │
│  status (ENUM) - PENDING, VALIDATING, IN_REVIEW, etc.      │
│  risk_score (INTEGER, nullable) - 0-1000                  │
│  requires_review (BOOLEAN)                                 │
│  banking_info (JSONB) - Provider response                  │
│  extra_data (JSONB) - Metadata and warnings                │
│  created_at, updated_at, processed_at (TIMESTAMPTZ)        │
│  ────────────────────────────────────────────────────────  │
│  INDEXES:                                                   │
│  - idx_loans_country_status (country_code, status)         │
│  - idx_loans_created_at (created_at DESC)                  │
│  - idx_loans_document_hash (document_hash)                 │
│  - idx_loans_pending_review (status, created_at)           │
│    WHERE status IN ('PENDING', 'IN_REVIEW')                │
│  ────────────────────────────────────────────────────────  │
│  PARTITIONING: BY LIST (country_code)                      │
│  - loan_applications_es FOR VALUES IN ('ES')                │
│  - loan_applications_mx FOR VALUES IN ('MX')                │
│  - loan_applications_co FOR VALUES IN ('CO')                │
│  - loan_applications_br FOR VALUES IN ('BR')                │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ 1:N
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              loan_status_history                            │
│  ────────────────────────────────────────────────────────  │
│  id (UUID, PK)                                             │
│  loan_id (UUID, FK → loan_applications.id, CASCADE)        │
│  previous_status (VARCHAR(30), nullable)                  │
│  new_status (VARCHAR(30))                                  │
│  changed_by (UUID, nullable) - user_id                      │
│  reason (TEXT, nullable)                                    │
│  extra_data (JSONB, nullable)                               │
│  created_at (TIMESTAMPTZ)                                   │
│  ────────────────────────────────────────────────────────  │
│  INDEX: idx_status_history_loan_created                   │
│    (loan_id, created_at DESC)                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    audit_logs                              │
│  ────────────────────────────────────────────────────────  │
│  id (BIGSERIAL, PK)                                        │
│  entity_type (VARCHAR(50)) - 'loan_application', 'user'    │
│  entity_id (UUID)                                          │
│  action (VARCHAR(30)) - CREATE, UPDATE, DELETE, etc.       │
│  actor_id (UUID, nullable) - user_id or system              │
│  actor_type (VARCHAR(20)) - USER, SYSTEM, WORKER, WEBHOOK   │
│  changes (JSONB) - {field: {old: x, new: y}}              │
│  ip_address (INET, nullable)                               │
│  user_agent (TEXT, nullable)                                │
│  created_at (TIMESTAMPTZ)                                   │
│  ────────────────────────────────────────────────────────  │
│  PARTITIONING: BY RANGE (created_at) - Monthly              │
│  INDEXES:                                                   │
│  - idx_audit_entity_created (entity_type, entity_id,       │
│      created_at DESC)                                       │
│  - idx_audit_actor_created (actor_id, created_at)           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    async_jobs                              │
│  ────────────────────────────────────────────────────────  │
│  id (BIGSERIAL, PK)                                        │
│  queue_name (VARCHAR(50)) - risk_evaluation, audit, etc.   │
│  payload (JSONB)                                            │
│  status (ENUM) - PENDING, RUNNING, COMPLETED, FAILED         │
│  priority (INTEGER) - Higher = processed first             │
│  attempts (INTEGER)                                        │
│  max_attempts (INTEGER, default: 3)                        │
│  error (TEXT, nullable)                                     │
│  scheduled_at (TIMESTAMPTZ)                                │
│  started_at, completed_at (TIMESTAMPTZ, nullable)          │
│  locked_by (VARCHAR(100), nullable) - worker_id            │
│  locked_at (TIMESTAMPTZ, nullable)                          │
│  created_at (TIMESTAMPTZ)                                   │
│  ────────────────────────────────────────────────────────  │
│  INDEXES:                                                   │
│  - idx_jobs_pending_queue (queue_name, priority,            │
│      scheduled_at) WHERE status = 'PENDING'                │
│  - idx_jobs_running (locked_by, locked_at)                 │
│    WHERE status = 'RUNNING'                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  webhook_events                             │
│  ────────────────────────────────────────────────────────  │
│  id (UUID, PK)                                             │
│  source (VARCHAR(50)) - Provider name                       │
│  event_type (VARCHAR(50)) - status_update, risk_score      │
│  payload (JSONB) - Full payload                             │
│  signature (VARCHAR(256), nullable) - HMAC for verification│
│  processed (BOOLEAN)                                        │
│  processed_at (TIMESTAMPTZ, nullable)                      │
│  processing_error (TEXT, nullable)                          │
│  loan_id (UUID, FK → loan_applications.id, SET NULL)        │
│  created_at (TIMESTAMPTZ)                                   │
│  ────────────────────────────────────────────────────────  │
│  INDEXES:                                                   │
│  - idx_webhook_unprocessed (processed, created_at)         │
│    WHERE processed = false                                  │
│  - idx_webhook_source_type (source, event_type,            │
│      created_at)                                            │
└─────────────────────────────────────────────────────────────┘
```

### Table Descriptions

#### `loan_applications`
Main table storing all loan applications. **Partitioned by `country_code`** for scalability.

**Key fields:**
- `document_number` and `full_name`: **Encrypted** using Fernet (PII)
- `document_hash`: SHA256 hash for lookups without decryption
- `banking_info`: JSONB with banking provider response
- `extra_data`: JSONB with metadata, warnings, and risk factors

**Possible states:**
- `PENDING` → `VALIDATING` → `IN_REVIEW` → `APPROVED` → `DISBURSED` → `COMPLETED`
- `PENDING` → `VALIDATING` → `REJECTED` (terminal)
- `PENDING` or `APPROVED` → `CANCELLED` (terminal)

#### `loan_status_history`
Records all status changes for audit and traceability.

#### `audit_logs`
Complete audit log for compliance. **Partitioned by month** to facilitate archiving.

#### `async_jobs`
Asynchronous job queue stored in PostgreSQL. Uses `SELECT FOR UPDATE SKIP LOCKED` for safe concurrent processing.

#### `webhook_events`
Stores all webhooks received from banking providers for audit and retries.

---

## 🎯 Technical Decisions

### 1. Strategy Pattern for Countries

**Decision**: Use the Strategy Pattern instead of a giant if/else.

**Why it is better:**
- ✅ **Extensibility**: Adding a new country = 1 new file + registration in `StrategyRegistry`
- ✅ **Zero changes to existing code**: Open/Closed Principle
- ✅ **Isolated testing**: Each strategy is tested independently
- ✅ **Parallelism**: Teams can work in parallel by country
- ✅ **Maintainability**: Changes in one country do not affect others

**Implementation:**
```python
# app/strategies/base.py
class CountryStrategy(ABC):
    @abstractmethod
    def validate_document(self, document_number: str) -> ValidationResult:
        pass
    
    @abstractmethod
    def apply_business_rules(self, ...) -> ValidationResult:
        pass
    
    @abstractmethod
    async def fetch_banking_info(self, ...) -> BankingInfo:
        pass

# app/strategies/spain.py
class SpainStrategy(CountryStrategy):
    country_code = "ES"
    # Implementación específica para España

# app/strategies/registry.py
StrategyRegistry.register(SpainStrategy())
StrategyRegistry.register(MexicoStrategy())
# ...
```

### 2. Event-Driven with PostgreSQL LISTEN/NOTIFY

**Decision**: Use PostgreSQL triggers + `pg_notify()` instead of an external message broker (Kafka/RabbitMQ) for the MVP.

**Why it is better for the MVP:**
- ✅ **Latency < 50ms**: Near-instant notifications
- ✅ **No overhead**: Does not require additional infrastructure
- ✅ **Guaranteed transactional consistency**: The event fires within the same transaction
- ✅ **Easy migration**: Can migrate to Kafka/RabbitMQ later without changing application code

**Implementation:**
```sql
-- Trigger que dispara pg_notify() en cada INSERT/UPDATE
CREATE TRIGGER trigger_notify_loan_change
    AFTER INSERT OR UPDATE ON loan_applications
    FOR EACH ROW
    EXECUTE FUNCTION notify_loan_change();

-- Función que envía notificación
CREATE FUNCTION notify_loan_change() RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('loan_changes', json_build_object(...)::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

**Python backend listens:**
```python
# app/sockets/pg_listener.py
class PostgresListener:
    async def listen(self, channels: list[str]):
        await self.connection.add_listener("loan_changes", self._handle_notification)
        # Broadcast via Socket.IO
```

### 3. Job Queue in PostgreSQL

**Decision**: Use the `async_jobs` table in PostgreSQL instead of Redis Queue or RabbitMQ.

**Why it is better for the MVP:**
- ✅ **Guaranteed ACID**: Jobs are created in the same transaction as the loan
- ✅ **No additional infrastructure**: Does not require Redis Queue or RabbitMQ
- ✅ **Direct querying**: You can view pending jobs with SQL
- ✅ **Easy migration**: Can migrate to Redis Queue later

**Safe concurrent processing:**
```python
# app/repositories/job_repository.py
async def dequeue(self, queue_name: str, worker_id: str):
    query = (
        select(AsyncJob)
        .where(AsyncJob.queue_name == queue_name, AsyncJob.status == 'PENDING')
        .order_by(AsyncJob.priority.desc(), AsyncJob.scheduled_at.asc())
        .limit(1)
        .with_for_update(skip_locked=True)  # ← Clave para concurrencia
    )
    # SKIP LOCKED evita que múltiples workers procesen el mismo job
```

### 4. Repository Pattern

**Decision**: Separate data access logic into repositories.

**Why it is better:**
- ✅ **Testable**: You can mock repositories easily
- ✅ **Decoupled**: Switching from PostgreSQL to another DB = change the repository
- ✅ **Reusable**: Multiple services can use the same repository
- ✅ **Maintainable**: SQL logic centralized

### 5. PII Encryption with Fernet

**Decision**: Use Fernet (symmetric encryption) derived from `JWT_SECRET`.

**Why:**
- ✅ **Simplicity**: Does not require a key management service for the MVP
- ✅ **Lookups**: `document_hash` allows searching without decryption
- ✅ **Performance**: Symmetric encryption is fast

**Recommended in production:**
- Use AWS KMS, HashiCorp Vault, or similar
- Dedicated key separate from `JWT_SECRET`
- Periodic key rotation

### 6. React + Vite instead of Next.js

**Decision**: Use React + Vite instead of Next.js.

**Why it is better for this application:**
- ✅ **No SSR needed**: The app is private (requires login), no SEO needed
- ✅ **Faster build**: Vite uses esbuild (10-100x faster than Webpack)
- ✅ **Instant HMR**: Hot Module Replacement in < 50ms
- ✅ **Lower overhead**: No API routes needed (separate backend)
- ✅ **More control**: Routing and state managed explicitly

**Comparison:**
| Metric | Next.js | React + Vite |
|---------|---------|--------------|
| Build time | 30-60s | 5-10s ✅ |
| HMR | 2-5s | < 50ms ✅ |
| Bundle size | ~250KB | ~150KB ✅ |
| Dev startup | 5-10s | < 1s ✅ |

### 7. Redux Toolkit for Global State

**Decision**: Use Redux Toolkit instead of Context API.

**Why:**
- ✅ **Real-time updates**: Middleware for Socket.IO synchronizes state automatically
- ✅ **DevTools**: Time-travel debugging, action inspector
- ✅ **Performance**: Memoized selectors avoid unnecessary re-renders
- ✅ **Type-safe**: Full TypeScript support

### 8. Socket.IO for Real-time

**Decision**: Use Socket.IO instead of native WebSockets or Server-Sent Events.

**Why:**
- ✅ **Automatic fallback**: If WebSocket fails, uses polling
- ✅ **Rooms**: Easy subscription by country or specific loan
- ✅ **Auto-reconnect**: Handles disconnections automatically
- ✅ **Simple integration**: Redux middleware synchronizes state

---

## 🔐 Security Considerations

### 1. PII Encryption (Personally Identifiable Information)

**Implementation:**
- `document_number` and `full_name` are encrypted using **Fernet** (AES-128 in CBC mode)
- The key is derived from `JWT_SECRET` using PBKDF2 (100,000 iterations)
- `document_hash` (SHA256) allows lookups without decryption

**Why:**
- ✅ **Compliance**: GDPR, LGPD require PII protection
- ✅ **Efficient lookups**: The hash allows searching without decryption
- ✅ **Audit**: Changes are recorded in `audit_logs`

**In production:**
- Use AWS KMS, HashiCorp Vault, or Azure Key Vault
- Periodic key rotation
- Dedicated key separate from `JWT_SECRET`

### 2. JWT Authentication

**Implementation:**
- Access tokens with 60-minute expiration
- Refresh tokens with 7-day expiration
- Tokens signed with HS256

**Security:**
- ✅ Tokens stored in memory (not localStorage to avoid XSS)
- ✅ Refresh tokens rotated on each use
- ✅ Signature validation on every request

**Future improvements:**
- RS256 for verification without exposing the secret
- Token blacklist for logout
- Rate limiting by IP/user

### 3. Webhook Validation

**Implementation:**
- HMAC-SHA256 signature verification
- Constant-time comparison to prevent timing attacks

```python
def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)  # Constant-time comparison
```

### 4. Role-Based Authorization

**Implemented roles:**
- `ADMIN`: Full access
- `ANALYST`: Can approve/reject loans
- `VIEWER`: Read-only

**Future improvements:**
- Country-based authorization (e.g., analyst for Mexico only)
- Granular permissions per action
- Full RBAC (Role-Based Access Control)

### 5. SQL Injection Protection

**Implementation:**
- SQLAlchemy ORM with prepared parameters
- Input validation with Pydantic
- No raw SQL with string interpolation

### 6. CORS Configuration

**Implementation:**
- Only allowed origins in `CORS_ORIGINS`
- Credentials only for trusted origins

### 7. Logs Without PII

**Implementation:**
- Logs never include encrypted `document_number` or `full_name`
- Only IDs, country codes, and metadata are logged

---

## 📊 Scalability and Large-Volume Data Handling

### 1. Table Partitioning

#### `loan_applications` - Partitioning by Country (LIST)

**Why:**
- ✅ **Horizontal scalability**: Each partition can be on different servers
- ✅ **Faster queries**: Country filters only scan one partition
- ✅ **Maintenance**: You can run VACUUM/ANALYZE per country
- ✅ **Archiving**: You can archive old partitions easily

**Implementation:**
```sql
CREATE TABLE loan_applications (
    ...
) PARTITION BY LIST (country_code);

CREATE TABLE loan_applications_es PARTITION OF loan_applications
    FOR VALUES IN ('ES');
CREATE TABLE loan_applications_mx PARTITION OF loan_applications
    FOR VALUES IN ('MX');
-- ...
```

#### `audit_logs` - Partitioning by Month (RANGE)

**Why:**
- ✅ **Automatic archiving**: Old partitions can be moved to cold storage
- ✅ **Faster queries**: Date filters only scan relevant partitions
- ✅ **Maintenance**: VACUUM only on active partitions

**Implementation:**
```sql
CREATE TABLE audit_logs (
    ...
) PARTITION BY RANGE (created_at);

-- Crear particiones mensuales automáticamente
CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS void AS $$
BEGIN
    -- Crea partición para el próximo mes
    -- ...
END;
$$ LANGUAGE plpgsql;
```

### 2. Optimized Indexes

#### Partial Indexes

**Why they are better:**
- ✅ **Smaller size**: Only index relevant rows
- ✅ **Faster queries**: Less data to scan
- ✅ **Lower overhead**: Fewer writes on INSERT/UPDATE

**Examples:**
```sql
-- Solo indexa préstamos pendientes (los más consultados)
CREATE INDEX idx_loans_pending_review
    ON loan_applications(status, created_at)
    WHERE status IN ('PENDING', 'IN_REVIEW', 'VALIDATING');

-- Solo indexa jobs pendientes
CREATE INDEX idx_jobs_pending_queue
    ON async_jobs(queue_name, priority, scheduled_at)
    WHERE status = 'PENDING';
```

#### Composite Indexes

**Optimized for frequent queries:**
```sql
-- Consulta: "Préstamos de México con status APPROVED"
CREATE INDEX idx_loans_country_status
    ON loan_applications(country_code, status);

-- Consulta: "Auditoría de un préstamo específico"
CREATE INDEX idx_audit_entity_created
    ON audit_logs(entity_type, entity_id, created_at DESC);
```

### 3. Caching Strategy

**What is cached and why:**

| Resource | TTL | Reason |
|---------|-----|-------|
| Individual loan (`loan:{id}`) | 5 min | Changes frequently, but repeated queries |
| Loan list (`loans:list:{country}`) | 1 min | High change frequency, but very frequent queries |
| Statistics (`stats:loans:{country}`) | 15 min | Expensive calculation, less frequent changes |
| Banking info (`banking:{provider}:{doc}`) | 1 hour | Stable data, does not change frequently |

**Invalidation:**
- **Write-through**: When updating a loan, its cache is invalidated
- **Pattern invalidation**: On create/update, `loans:list:*` for the country is invalidated
- **TTL**: Automatic expiration as fallback

**Implementation:**
```python
# app/services/loan_service.py
async def update_status(self, loan_id: UUID, new_status: LoanStatus):
    # ... actualizar préstamo ...
    
    # Invalidar caché
    await cache.delete(f"loan:{loan_id}")
    await cache.delete_pattern(f"loans:list:{loan.country_code}:*")
    await cache.delete(f"stats:loans:{loan.country_code}")
```

### 4. Optimized Queries

#### Cursor-Based Pagination

**For large lists:**
```python
# En lugar de OFFSET (lento con millones de registros)
# Usar cursor-based pagination
query = (
    select(LoanApplication)
    .where(LoanApplication.id > last_id)  # Cursor
    .order_by(LoanApplication.id)
    .limit(page_size)
)
```

#### Queries With Only Required Fields

**Avoid SELECT *:**
```python
# Solo campos necesarios para listado
query = select(
    LoanApplication.id,
    LoanApplication.country_code,
    LoanApplication.status,
    LoanApplication.amount_requested,
    LoanApplication.created_at
)
```

### 5. Archiving Old Data

**Strategy:**
1. **Monthly partitions** of `audit_logs` → move to cold storage after 1 year
2. **Completed loans** → move to archive table after 5 years
3. **Compress** old partitions with `pg_compress`

**Future implementation:**
```sql
-- Mover partición antigua a cold storage
ALTER TABLE audit_logs DETACH PARTITION audit_logs_2023_01;
-- Exportar a S3/Glacier
-- Eliminar partición local
```

### 6. Horizontal Scalability

**Backend API:**
- Multiple pods in Kubernetes with HPA (Horizontal Pod Autoscaler)
- Load balancer distributes traffic
- Stateless: each pod is independent

**Workers:**
- Multiple instances process jobs in parallel
- `SELECT FOR UPDATE SKIP LOCKED` avoids conflicts
- Auto-scaling based on queue length

**Database:**
- Read replicas for read-only queries
- Partitioning enables sharding by country
- Connection pooling (SQLAlchemy pool_size)

---

## ⚙️ Concurrency, Queues, Cache and Webhooks Strategy

### 1. Concurrency

#### Parallel Workers

**Implementation:**
- Multiple worker instances can run simultaneously
- `SELECT FOR UPDATE SKIP LOCKED` ensures each job is processed by a single worker

**Why it is safe:**
```python
# app/repositories/job_repository.py
query = (
    select(AsyncJob)
    .where(AsyncJob.status == 'PENDING')
    .order_by(AsyncJob.priority.desc())
    .limit(1)
    .with_for_update(skip_locked=True)  # ← Clave
)
```

**SKIP LOCKED means:**
- If the job is being processed by another worker, it is skipped
- No waiting (does not block)
- Each worker gets a different job

**Scalability:**
- 1 worker: ~10 jobs/min
- 10 workers: ~100 jobs/min
- 100 workers: ~1,000 jobs/min

#### Database Locks

**For critical operations:**
```python
# Ejemplo: Actualizar estado de préstamo
async with session.begin():
    loan = await session.get(LoanApplication, loan_id, with_for_update=True)
    # Solo este worker puede modificar este préstamo
    loan.status = new_status
```

### 2. Job Queues

#### Queue Architecture

**Decision**: Queue in PostgreSQL (`async_jobs`) instead of Redis Queue or RabbitMQ.

**Advantages:**
- ✅ **ACID**: Jobs are created in the same transaction as the loan
- ✅ **Direct querying**: You can view jobs with SQL
- ✅ **No additional infrastructure**: Does not require Redis Queue
- ✅ **Easy migration**: Can migrate to Redis Queue later

**Implemented queues:**
1. **`risk_evaluation`**: Asynchronous risk evaluation
2. **`audit`**: Audit logging
3. **`notifications`**: User notifications
4. **`webhooks`**: Outbound webhooks

#### Job Processing

**Flow:**
```
1. Create loan → INSERT into loan_applications
2. PostgreSQL trigger → INSERT into async_jobs (queue: 'audit')
3. Worker listens → SELECT ... FOR UPDATE SKIP LOCKED
4. Worker processes → UPDATE status = 'RUNNING'
5. Worker completes → UPDATE status = 'COMPLETED'
```

**Automatic retry:**
```python
# app/workers/base.py
if job.attempts < job.max_attempts:
    # Reencolar con delay exponencial
    await job_repo.fail(job_id, retry=True, retry_delay=60 * attempts)
```

**Priorities:**
- `priority = 2`: High (notifications)
- `priority = 1`: Medium (audit)
- `priority = 0`: Low (risk evaluation)

### 3. Cache (Redis)

#### Caching Strategy

**What is cached:**

| Key | TTL | Invalidation |
|-------|-----|--------------|
| `loan:{id}` | 5 min | On loan update |
| `loans:list:{country}:{status}:{page}` | 1 min | On create/update loan in country |
| `stats:loans:{country}` | 15 min | On create/update loan in country |
| `banking:{provider}:{doc_hash}` | 1 hour | Manual (stable data) |

**Implementation:**
```python
# app/core/cache.py
class RedisCache:
    async def get(self, key: str) -> Optional[Any]:
        # JSON deserialization automática
    
    async def set(self, key: str, value: Any, ttl_seconds: int):
        # JSON serialization automática
    
    async def delete_pattern(self, pattern: str):
        # Invalida múltiples claves con patrón
```

**Smart invalidation:**
```python
# Al actualizar préstamo
await cache.delete(f"loan:{loan_id}")
await cache.delete_pattern(f"loans:list:{country_code}:*")
await cache.delete(f"stats:loans:{country_code}")
await cache.delete("stats:loans:all")
```

**Graceful fallback:**
- If Redis is unavailable, the system works without cache
- The application does not fail, it is just slower

#### Cache-Aside Pattern

**Implementation:**
```python
async def get_loan_by_id(self, loan_id: UUID):
    # 1. Intentar cache
    cached = await cache.get(f"loan:{loan_id}")
    if cached:
        return cached
    
    # 2. Si no está en cache, consultar DB
    loan = await self.loan_repo.get_by_id(loan_id)
    
    # 3. Guardar en cache
    await cache.set(f"loan:{loan_id}", loan, ttl_seconds=300)
    
    return loan
```

### 4. Webhooks

#### Inbound Webhooks

**Endpoint:** `POST /api/v1/webhooks/banking/{country_code}`

**Flow:**
```
1. Banking provider → POST /webhooks/banking/ES
2. Verify HMAC signature
3. Store in webhook_events
4. Find related loan (by loan_id or document_hash)
5. Process event (update status, risk_score, etc.)
6. Enqueue audit job
```

**Security:**
```python
def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)  # Constant-time
```

**Retries:**
- If processing fails, the webhook remains marked as `processed = false`
- A worker can retry processing failed webhooks

#### Outbound Webhooks

**Implementation:**
- Worker `webhook_worker` processes jobs from the `webhooks` queue
- Sends notifications to external systems when a loan status changes

**Example payload:**
```json
{
  "event": "loan_status_changed",
  "loan_id": "uuid",
  "old_status": "PENDING",
  "new_status": "APPROVED",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Retries:**
- 3 attempts with exponential backoff
- If it fails, marked as `FAILED` and can be retried manually

### 5. Real-time Updates (Socket.IO + PostgreSQL LISTEN/NOTIFY)

**Architecture:**
```
PostgreSQL INSERT/UPDATE
    ↓
Trigger → pg_notify('loan_changes', payload)
    ↓
PostgresListener (Python) → Receives notification
    ↓
Socket.IO Server → Emit to rooms
    ↓
Frontend (Socket.IO Client) → Receives event
    ↓
Redux Middleware → Dispatch action
    ↓
Automatic UI update
```

**Latency:** < 100ms from event to UI

**Rooms:**
- `country:{code}`: All loans in a country
- `loan:{id}`: A specific loan
- `all`: All loans

**Implementation:**
```python
# app/sockets/pg_listener.py
class PostgresListener:
    async def _handle_loan_change(self, data: dict):
        loan_id = data.get("loan_id")
        country_code = data.get("country_code")
        
        # Emit a room del país
        await emit_loan_updated(loan_id, country_code)
        
        # Emit a room del préstamo
        await emit_to_room(f"loan:{loan_id}", "loan_updated", data)
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Frontend (React + Vite + Redux + TailwindCSS)  │
│              Socket.IO Client for Real-time                  │
└─────────────────────────────┬───────────────────────────────┘
                              │ HTTP / WebSocket
┌─────────────────────────────┴───────────────────────────────┐
│                    Backend (FastAPI + Python)                │
│  ┌───────────┐  ┌───────────┐  ┌─────────────┐  ┌────────┐ │
│  │  API v1   │  │  Services │  │  Strategies │  │ Socket │ │
│  │  (REST)   │  │   Layer   │  │ (per country)│  │   IO   │ │
│  └───────────┘  └───────────┘  └─────────────┘  └────────┘ │
│  ┌───────────┐  ┌───────────────────────────────────────┐  │
│  │ Repos     │  │            Workers (Async)            │  │
│  │  (DAL)    │  │  Risk │ Audit │ Webhook/Notifications │  │
│  └───────────┘  └───────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
    ┌─────┴─────┐       ┌─────┴─────┐       ┌─────┴─────┐
    │ PostgreSQL│       │   Redis   │       │  Workers  │
    │   (Data)  │       │  (Cache)  │       │  (Queue)  │
    │           │       │           │       │           │
    │ TRIGGERS  │       │           │       │           │
    │ pg_notify │       │           │       │           │
    └───────────┘       └───────────┘       └───────────┘
```

### Architecture

**Backend:**
- **Layered Architecture**: Controllers (API Routers) → Services → Domain (Strategies/Models) → Repositories/Infrastructure
- **Event-Driven Architecture**: PostgreSQL LISTEN/NOTIFY + async workers for background processing

**Frontend:**
- **SPA (Single Page Application)** with **Flux/Redux Architecture**: React + Redux Toolkit for unidirectional global state

### Design Patterns

- **Strategy Pattern**: Country-specific validation logic
- **Repository Pattern**: Decoupled data access layer
- **Dependency Injection**: Using FastAPI Depends
- **Observer Pattern**: PostgreSQL LISTEN/NOTIFY → Socket.IO

---

## 🌍 Supported Countries

| Country | Code | Document | Currency | Document Format |
|------|--------|-----------|--------|-------------------|
| 🇪🇸 Spain | ES | DNI | EUR | 8 digits + letter |
| 🇲🇽 Mexico | MX | CURP | MXN | 18 alphanumeric characters |
| 🇨🇴 Colombia | CO | CC | COP | 6-10 digits |
| 🇧🇷 Brazil | BR | CPF | BRL | 11 digits |

---

## 🔌 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register user |
| POST | `/api/v1/auth/login` | Log in |
| POST | `/api/v1/auth/refresh` | Refresh token |
| GET | `/api/v1/auth/me` | Get current user |

### Loans
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/loans` | List loans (with filters) |
| POST | `/api/v1/loans` | Create loan |
| GET | `/api/v1/loans/{id}` | Get loan |
| PATCH | `/api/v1/loans/{id}/status` | Update status |
| GET | `/api/v1/loans/{id}/history` | Status history |
| GET | `/api/v1/loans/statistics` | Statistics |

### Webhooks
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/webhooks/banking/{country_code}` | Receive banking provider webhook |
| GET | `/api/v1/webhooks/events` | List webhook events |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Application status |
| GET | `/api/v1/health/ready` | Readiness check |

---

## 🧪 Testing

### Backend
```bash
# Ejecutar todos los tests
make test-backend

# Con cobertura
make test-coverage

# O directamente
cd backend && pytest -v --cov=app --cov-report=html
```
---

## ❓ Troubleshooting

### Error: "Connection refused" when connecting to PostgreSQL

**Cause**: PostgreSQL is not ready or the port is incorrect.

**Solution**:
```bash
# Verificar que PostgreSQL esté corriendo
docker compose ps

# Ver logs de PostgreSQL
docker compose logs postgres

# Para desarrollo local, el puerto es 5433
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/loans_db
```

### Error: "No module named 'app'"

**Cause**: The virtual environment is not activated or PYTHONPATH is incorrect.

**Solution**:
```bash
# Activar entorno virtual
source backend/.venv/bin/activate

# O usar el binario directamente
backend/.venv/bin/python -m app.main
```

### Error: "relation does not exist" (tables do not exist)

**Cause**: Migrations have not been run.

**Solution**:
```bash
# Con Docker
docker compose exec backend alembic upgrade head

# Local
make migrate
```

### Frontend does not connect to backend

**Cause**: CORS or incorrect URL.

**Solution**:
1. Verify that the backend is running
2. Verify the `VITE_API_URL` variable in `frontend/.env`
3. Verify `CORS_ORIGINS` in `backend/.env`

### Workers do not process jobs

**Cause**: Workers are not running or there is a DB connection error.

**Solution**:
```bash
# Verificar workers
make workers

# Ver logs
docker compose logs worker-risk
docker compose logs worker-audit
```

### Redis unavailable

**Cause**: Redis is not running.

**Solution**:
```bash
# Verificar Redis
docker compose logs redis

# Verificar conexión
docker compose exec redis redis-cli ping
```

**Note**: The system works without Redis, but without cache (slower).

---

## 📊 Docker Services

| Service | Local Port | Container Port | Description |
|----------|-------------|------------------|-------------|
| postgres | 5433 | 5432 | PostgreSQL 15 database |
| redis | 6379 | 6379 | Cache and message queue |
| backend | 8000 | 8000 | FastAPI API |
| frontend | 3000 | 80 | React app (Nginx) |
| pgadmin | 5050 | 80 | PostgreSQL administrator |
| worker-risk | - | - | Risk evaluation worker |
| worker-audit | - | - | Audit worker |
| worker-webhook | - | - | Notifications worker |

---

## 🔐 Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql+asyncpg://postgres:postgres@localhost:5433/loans_db` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `JWT_SECRET` | Secret key for JWT | `your-super-secret-key-change-in-production` |
| `CORS_ORIGINS` | Allowed origins (comma-separated) | `http://localhost:5173,http://localhost:3000` |
| `DEBUG` | Debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `WEBHOOK_SECRET` | Secret for webhook verification | `webhook-secret-key` |

### Frontend (`frontend/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend URL | `http://localhost:8000` |
| `VITE_WS_URL` | WebSocket URL | `http://localhost:8000` |
