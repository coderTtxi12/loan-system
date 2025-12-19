# 🏦 Loan System - Sistema de Créditos Multipaís

Sistema de gestión de solicitudes de préstamos diseñado para operar en múltiples países (España, México, Colombia, Brasil) con arquitectura escalable, event-driven y preparada para manejar millones de transacciones.

## 📋 Tabla de Contenidos

- [Instalación y Ejecución](#-instalación-y-ejecución)
- [Supuestos](#-supuestos)
- [Modelo de Datos](#-modelo-de-datos)
- [Decisiones Técnicas](#-decisiones-técnicas)
- [Consideraciones de Seguridad](#-consideraciones-de-seguridad)
- [Escalabilidad y Grandes Volúmenes](#-escalabilidad-y-manejo-de-grandes-volúmenes-de-datos)
- [Concurrencia, Colas, Caché y Webhooks](#-estrategia-de-concurrencia-colas-caché-y-webhooks)
- [Arquitectura](#️-arquitectura)
- [API Endpoints](#-api-endpoints)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)

---

## 🚀 Instalación y Ejecución

### Prerrequisitos

#### Para Docker (Opción Recomendada)
- [Docker](https://docs.docker.com/get-docker/) >= 20.10
- [Docker Compose](https://docs.docker.com/compose/install/) >= 2.0

#### Para Desarrollo Local
- [Python](https://www.python.org/downloads/) >= 3.11
- [Node.js](https://nodejs.org/) >= 18.0
- [Make](https://www.gnu.org/software/make/) (incluido en macOS/Linux)
- [Docker](https://docs.docker.com/get-docker/) (para PostgreSQL y Redis)

### Quick Start con Docker (Recomendado)

**Tiempo estimado: < 5 minutos**

#### 1. Clonar el repositorio
```bash
git clone https://github.com/coderTtxi12/loan-system.git
cd loan
```

#### 2. Configurar variables de entorno

**Backend:**
```bash
cp backend/.env.example backend/.env
```

**Frontend:**
```bash
cp frontend/.env.example frontend/.env
```

> 💡 **Nota**: Si no creas los archivos `.env`, Docker Compose usará los valores por defecto definidos en `docker-compose.yml`.

#### 3. Levantar todos los servicios
```bash
docker compose up --build
```

> ⏳ La primera vez tardará unos minutos en construir las imágenes.

#### 4. Ejecutar las migraciones de base de datos

En otra terminal:
```bash
docker compose exec backend alembic upgrade head
```

#### 5. Cargar usuarios de demostración (seed)
```bash
docker compose exec backend python -m app.db.seed
```

#### 6. Acceder a la aplicación

| Servicio | URL |
|----------|-----|
| 🖥️ **Frontend** | http://localhost:3000 |
| 🔧 **API Docs (Swagger)** | http://localhost:8000/docs |
| 📘 **API Docs (ReDoc)** | http://localhost:8000/redoc |
| 🗄️ **pgAdmin** (opcional) | http://localhost:5050 |

**🔐 Credenciales de Demo:**
| Rol | Email | Password |
|-----|-------|----------|
| Admin | `admin@loan.com` | `admin123` |
| Analyst | `analyst@loan.com` | `analyst123` |
| Viewer | `viewer@loan.com` | `viewer123` |

**Credenciales pgAdmin:**
- Email: `admin@admin.com`
- Password: `admin`

#### 7. Detener los servicios
```bash
docker compose down
```

Para eliminar también los volúmenes (datos):
```bash
docker compose down -v
```

### Desarrollo Local

#### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd loan
```

#### 2. Configurar variables de entorno

**Backend:**
```bash
cp backend/.env.example backend/.env
```

**Frontend:**
```bash
cp frontend/.env.example frontend/.env
```

#### 3. Levantar PostgreSQL y Redis
```bash
docker compose up -d postgres redis
```

Espera a que los servicios estén saludables:
```bash
docker compose ps
```

#### 4. Instalar dependencias
```bash
make install
```

Esto instalará:
- Dependencias de Python en un entorno virtual (`backend/.venv`)
- Dependencias de Node.js (`frontend/node_modules`)

#### 5. Ejecutar migraciones de base de datos
```bash
make migrate
```

#### 6. Cargar usuarios de demostración (seed)
```bash
make seed
```

#### 7. Iniciar los servidores de desarrollo
```bash
make dev
```

| Servicio | URL |
|----------|-----|
| 🖥️ **Frontend** | http://localhost:5173 |
| 🔧 **API Docs** | http://localhost:8000/docs |

### Iniciar servicios por separado

```bash
# Solo backend
make dev-backend

# Solo frontend
make dev-frontend

# Workers
make workers
```

### Comandos Make

| Comando | Descripción |
|---------|-------------|
| `make help` | Mostrar ayuda con todos los comandos |
| `make install` | Instalar dependencias (backend + frontend) |
| `make dev` | Iniciar servidores de desarrollo |
| `make dev-backend` | Iniciar solo el backend |
| `make dev-frontend` | Iniciar solo el frontend |
| `make test` | Ejecutar todos los tests |
| `make test-backend` | Ejecutar tests del backend |
| `make test-coverage` | Ejecutar tests con cobertura |
| `make lint` | Ejecutar linters |
| `make migrate` | Ejecutar migraciones de DB |
| `make migrate-create msg="descripcion"` | Crear nueva migración |
| `make seed` | Cargar usuarios de demostración |
| `make workers` | Ejecutar todos los workers |
| `make worker-risk` | Ejecutar worker de riesgo |
| `make worker-audit` | Ejecutar worker de auditoría |
| `make worker-webhook` | Ejecutar worker de webhooks |
| `make docker-build` | Construir imágenes Docker |
| `make docker-up` | Levantar servicios con Docker Compose |
| `make docker-down` | Detener servicios Docker |
| `make clean` | Limpiar archivos generados |

---

## 📝 Supuestos

### Supuestos de Negocio

1. **Países Implementados**: Se implementaron 4 países (ES, MX, CO, BR) de los 6 requeridos. Los países restantes (PT, IT) pueden agregarse fácilmente siguiendo el mismo patrón Strategy.

2. **Proveedores Bancarios**: Los proveedores bancarios están simulados para el MVP. En producción, cada país tendría su propio proveedor real (Equifax España, Buró de Crédito México, etc.).

3. **Validación de Documentos**: Se implementa validación de formato y dígito de control donde aplica (DNI español, CURP mexicano). La validación contra bases de datos gubernamentales se asume como responsabilidad del proveedor bancario.

4. **Estados de Préstamo**: Se definió un flujo de estados estándar que puede variar por país. Las transiciones están validadas para evitar estados inválidos.

5. **Autenticación**: Se implementa JWT con roles básicos (ADMIN, ANALYST, VIEWER). La autorización por país puede agregarse fácilmente.

6. **Real-time Updates**: Se usa Socket.IO para actualizaciones en tiempo real.

7. **Escalabilidad**: El sistema está diseñado para escalar horizontalmente.

### Supuestos Técnicos

1. **Base de Datos**: PostgreSQL 15+ con soporte para particionamiento, triggers y LISTEN/NOTIFY.

2. **Cache**: Redis disponible para caché y sesiones. Si Redis no está disponible, el sistema funciona pero sin caché.

3. **Workers**: Los workers pueden ejecutarse en múltiples instancias sin conflictos gracias a `SELECT FOR UPDATE SKIP LOCKED`.

4. **Timezone**: Se usa UTC para todos los timestamps. La conversión a timezone local se hace en el frontend.

5. **Encriptación PII**: Se usa Fernet (symmetric encryption) derivado de `JWT_SECRET`. En producción, se recomienda usar una clave dedicada almacenada en un key management service.

---

## 🗄️ Modelo de Datos

### Diagrama de Entidad-Relación

```
┌─────────────────────────────────────────────────────────────┐
│                    loan_applications                        │
│  ────────────────────────────────────────────────────────  │
│  id (UUID, PK)                                             │
│  country_code (VARCHAR(2)) - Particionamiento por LIST     │
│  document_type (VARCHAR(20))                               │
│  document_number (VARCHAR(255)) - ENCRIPTADO (PII)         │
│  document_hash (VARCHAR(64)) - SHA256 para búsquedas      │
│  full_name (VARCHAR(255)) - ENCRIPTADO (PII)               │
│  amount_requested (DECIMAL(15,2))                          │
│  monthly_income (DECIMAL(15,2))                             │
│  currency (VARCHAR(3))                                     │
│  status (ENUM) - PENDING, VALIDATING, IN_REVIEW, etc.      │
│  risk_score (INTEGER, nullable) - 0-1000                  │
│  requires_review (BOOLEAN)                                 │
│  banking_info (JSONB) - Respuesta del proveedor            │
│  extra_data (JSONB) - Metadatos y advertencias              │
│  created_at, updated_at, processed_at (TIMESTAMPTZ)        │
│  ────────────────────────────────────────────────────────  │
│  ÍNDICES:                                                   │
│  - idx_loans_country_status (country_code, status)         │
│  - idx_loans_created_at (created_at DESC)                  │
│  - idx_loans_document_hash (document_hash)                 │
│  - idx_loans_pending_review (status, created_at)           │
│    WHERE status IN ('PENDING', 'IN_REVIEW')                │
│  ────────────────────────────────────────────────────────  │
│  PARTICIONAMIENTO: BY LIST (country_code)                   │
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
│  ÍNDICE: idx_status_history_loan_created                   │
│    (loan_id, created_at DESC)                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    audit_logs                              │
│  ────────────────────────────────────────────────────────  │
│  id (BIGSERIAL, PK)                                        │
│  entity_type (VARCHAR(50)) - 'loan_application', 'user'    │
│  entity_id (UUID)                                          │
│  action (VARCHAR(30)) - CREATE, UPDATE, DELETE, etc.       │
│  actor_id (UUID, nullable) - user_id o system              │
│  actor_type (VARCHAR(20)) - USER, SYSTEM, WORKER, WEBHOOK   │
│  changes (JSONB) - {campo: {old: x, new: y}}              │
│  ip_address (INET, nullable)                               │
│  user_agent (TEXT, nullable)                                │
│  created_at (TIMESTAMPTZ)                                   │
│  ────────────────────────────────────────────────────────  │
│  PARTICIONAMIENTO: BY RANGE (created_at) - Mensual          │
│  ÍNDICES:                                                   │
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
│  priority (INTEGER) - Mayor = procesado primero            │
│  attempts (INTEGER)                                        │
│  max_attempts (INTEGER, default: 3)                        │
│  error (TEXT, nullable)                                     │
│  scheduled_at (TIMESTAMPTZ)                                │
│  started_at, completed_at (TIMESTAMPTZ, nullable)          │
│  locked_by (VARCHAR(100), nullable) - worker_id            │
│  locked_at (TIMESTAMPTZ, nullable)                          │
│  created_at (TIMESTAMPTZ)                                   │
│  ────────────────────────────────────────────────────────  │
│  ÍNDICES:                                                   │
│  - idx_jobs_pending_queue (queue_name, priority,            │
│      scheduled_at) WHERE status = 'PENDING'                │
│  - idx_jobs_running (locked_by, locked_at)                 │
│    WHERE status = 'RUNNING'                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  webhook_events                             │
│  ────────────────────────────────────────────────────────  │
│  id (UUID, PK)                                             │
│  source (VARCHAR(50)) - Nombre del proveedor                │
│  event_type (VARCHAR(50)) - status_update, risk_score      │
│  payload (JSONB) - Payload completo                         │
│  signature (VARCHAR(256), nullable) - HMAC para verificación│
│  processed (BOOLEAN)                                        │
│  processed_at (TIMESTAMPTZ, nullable)                      │
│  processing_error (TEXT, nullable)                          │
│  loan_id (UUID, FK → loan_applications.id, SET NULL)        │
│  created_at (TIMESTAMPTZ)                                   │
│  ────────────────────────────────────────────────────────  │
│  ÍNDICES:                                                   │
│  - idx_webhook_unprocessed (processed, created_at)         │
│    WHERE processed = false                                  │
│  - idx_webhook_source_type (source, event_type,            │
│      created_at)                                            │
└─────────────────────────────────────────────────────────────┘
```

### Descripción de Tablas

#### `loan_applications`
Tabla principal que almacena todas las solicitudes de préstamo. **Particionada por `country_code`** para escalabilidad.

**Campos clave:**
- `document_number` y `full_name`: **Encriptados** usando Fernet (PII)
- `document_hash`: SHA256 hash para búsquedas sin desencriptar
- `banking_info`: JSONB con respuesta del proveedor bancario
- `extra_data`: JSONB con metadatos, advertencias y factores de riesgo

**Estados posibles:**
- `PENDING` → `VALIDATING` → `IN_REVIEW` → `APPROVED` → `DISBURSED` → `COMPLETED`
- `PENDING` → `VALIDATING` → `REJECTED` (terminal)
- `PENDING` o `APPROVED` → `CANCELLED` (terminal)

#### `loan_status_history`
Registra todos los cambios de estado para auditoría y trazabilidad.

#### `audit_logs`
Registro completo de auditoría para cumplimiento. **Particionada por mes** para facilitar archivado.

#### `async_jobs`
Cola de trabajos asíncronos almacenada en PostgreSQL. Usa `SELECT FOR UPDATE SKIP LOCKED` para procesamiento concurrente seguro.

#### `webhook_events`
Almacena todos los webhooks recibidos de proveedores bancarios para auditoría y reintentos.

---

## 🎯 Decisiones Técnicas

### 1. Strategy Pattern para Países

**Decisión**: Usar Strategy Pattern en lugar de if/else gigante.

**Por qué es mejor:**
- ✅ **Extensibilidad**: Agregar un país nuevo = 1 archivo nuevo + registro en `StrategyRegistry`
- ✅ **Zero cambios en código existente**: Open/Closed Principle
- ✅ **Testing aislado**: Cada estrategia se testea independientemente
- ✅ **Paralelismo**: Equipos pueden trabajar en paralelo por país
- ✅ **Mantenibilidad**: Cambios en un país no afectan otros

**Implementación:**
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

### 2. Event-Driven con PostgreSQL LISTEN/NOTIFY

**Decisión**: Usar PostgreSQL triggers + `pg_notify()` en lugar de message broker externo (Kafka/RabbitMQ) para MVP.

**Por qué es mejor para MVP:**
- ✅ **Latencia < 50ms**: Notificaciones casi instantáneas
- ✅ **Sin overhead**: No requiere infraestructura adicional
- ✅ **Transaccionalidad garantizada**: El evento se dispara dentro de la misma transacción
- ✅ **Fácil migración**: Puede migrarse a Kafka/RabbitMQ después sin cambiar código de aplicación

**Implementación:**
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

**Backend Python escucha:**
```python
# app/sockets/pg_listener.py
class PostgresListener:
    async def listen(self, channels: list[str]):
        await self.connection.add_listener("loan_changes", self._handle_notification)
        # Broadcast via Socket.IO
```

### 3. Cola de Trabajos en PostgreSQL

**Decisión**: Usar tabla `async_jobs` en PostgreSQL en lugar de Redis Queue o RabbitMQ.

**Por qué es mejor para MVP:**
- ✅ **ACID garantizado**: Los jobs se crean en la misma transacción que el préstamo
- ✅ **Sin infraestructura adicional**: No requiere Redis Queue o RabbitMQ
- ✅ **Consulta directa**: Puedes ver jobs pendientes con SQL
- ✅ **Migración fácil**: Puede migrarse a Redis Queue después

**Procesamiento concurrente seguro:**
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

**Decisión**: Separar lógica de acceso a datos en repositorios.

**Por qué es mejor:**
- ✅ **Testeable**: Puedes mockear repositorios fácilmente
- ✅ **Desacoplado**: Cambiar de PostgreSQL a otro DB = cambiar repository
- ✅ **Reutilizable**: Múltiples servicios pueden usar el mismo repository
- ✅ **Mantenible**: Lógica SQL centralizada

### 5. Encriptación PII con Fernet

**Decisión**: Usar Fernet (symmetric encryption) derivado de `JWT_SECRET`.

**Por qué:**
- ✅ **Simplicidad**: No requiere key management service para MVP
- ✅ **Búsquedas**: `document_hash` permite buscar sin desencriptar
- ✅ **Performance**: Encriptación simétrica es rápida

**En producción se recomienda:**
- Usar AWS KMS, HashiCorp Vault o similar
- Clave dedicada separada de `JWT_SECRET`
- Rotación de claves periódica

### 6. React + Vite en lugar de Next.js

**Decisión**: Usar React + Vite en lugar de Next.js.

**Por qué es mejor para esta aplicación:**
- ✅ **No necesitamos SSR**: La app es privada (requiere login), no necesita SEO
- ✅ **Build más rápido**: Vite usa esbuild (10-100x más rápido que Webpack)
- ✅ **HMR instantáneo**: Hot Module Replacement en < 50ms
- ✅ **Menor overhead**: No necesitamos API routes (backend separado)
- ✅ **Más control**: Routing y estado manejados explícitamente

**Comparación:**
| Métrica | Next.js | React + Vite |
|---------|---------|--------------|
| Build time | 30-60s | 5-10s ✅ |
| HMR | 2-5s | < 50ms ✅ |
| Bundle size | ~250KB | ~150KB ✅ |
| Dev startup | 5-10s | < 1s ✅ |

### 7. Redux Toolkit para Estado Global

**Decisión**: Usar Redux Toolkit en lugar de Context API.

**Por qué:**
- ✅ **Real-time updates**: Middleware para Socket.IO sincroniza estado automáticamente
- ✅ **DevTools**: Time-travel debugging, inspector de acciones
- ✅ **Performance**: Selectores memoizados evitan re-renders innecesarios
- ✅ **Type-safe**: TypeScript support completo

### 8. Socket.IO para Real-time

**Decisión**: Usar Socket.IO en lugar de WebSockets nativos o Server-Sent Events.

**Por qué:**
- ✅ **Fallback automático**: Si WebSocket falla, usa polling
- ✅ **Rooms**: Fácil suscripción por país o préstamo específico
- ✅ **Auto-reconnect**: Maneja desconexiones automáticamente
- ✅ **Integración simple**: Middleware de Redux sincroniza estado

---

## 🔐 Consideraciones de Seguridad

### 1. Encriptación de PII (Personally Identifiable Information)

**Implementación:**
- `document_number` y `full_name` se encriptan usando **Fernet** (AES-128 en modo CBC)
- La clave se deriva de `JWT_SECRET` usando PBKDF2 (100,000 iteraciones)
- `document_hash` (SHA256) permite búsquedas sin desencriptar

**Por qué:**
- ✅ **Cumplimiento**: GDPR, LGPD requieren protección de PII
- ✅ **Búsquedas eficientes**: El hash permite buscar sin desencriptar
- ✅ **Auditoría**: Los cambios se registran en `audit_logs`

**En producción:**
- Usar AWS KMS, HashiCorp Vault o Azure Key Vault
- Rotación de claves periódica
- Clave dedicada separada de `JWT_SECRET`

### 2. Autenticación JWT

**Implementación:**
- Access tokens con expiración de 60 minutos
- Refresh tokens con expiración de 7 días
- Tokens firmados con HS256

**Seguridad:**
- ✅ Tokens almacenados en memoria (no localStorage para evitar XSS)
- ✅ Refresh tokens rotados en cada uso
- ✅ Validación de firma en cada request

**Mejoras futuras:**
- RS256 para verificación sin exponer secreto
- Token blacklist para logout
- Rate limiting por IP/usuario

### 3. Validación de Webhooks

**Implementación:**
- HMAC-SHA256 signature verification
- Comparación constante en tiempo para prevenir timing attacks

```python
def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)  # Constant-time comparison
```

### 4. Autorización por Roles

**Roles implementados:**
- `ADMIN`: Acceso completo
- `ANALYST`: Puede aprobar/rechazar préstamos
- `VIEWER`: Solo lectura

**Mejoras futuras:**
- Autorización por país (ej: analista solo para México)
- Permisos granulares por acción
- RBAC (Role-Based Access Control) completo

### 5. Protección contra SQL Injection

**Implementación:**
- SQLAlchemy ORM con parámetros preparados
- Validación de entrada con Pydantic
- No se usa SQL crudo con interpolación de strings

### 6. CORS Configurado

**Implementación:**
- Solo orígenes permitidos en `CORS_ORIGINS`
- Credenciales solo para orígenes confiables

### 7. Logs sin PII

**Implementación:**
- Los logs nunca incluyen `document_number` o `full_name` encriptados
- Solo se loguean IDs, códigos de país y metadatos

---

## 📊 Escalabilidad y Manejo de Grandes Volúmenes de Datos

### 1. Particionamiento de Tablas

#### `loan_applications` - Particionamiento por País (LIST)

**Por qué:**
- ✅ **Escalabilidad horizontal**: Cada partición puede estar en diferentes servidores
- ✅ **Consultas más rápidas**: Filtros por país solo escanean una partición
- ✅ **Mantenimiento**: Puedes hacer VACUUM/ANALYZE por país
- ✅ **Archivado**: Puedes archivar particiones antiguas fácilmente

**Implementación:**
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

#### `audit_logs` - Particionamiento por Mes (RANGE)

**Por qué:**
- ✅ **Archivado automático**: Particiones antiguas se pueden mover a cold storage
- ✅ **Consultas más rápidas**: Filtros por fecha solo escanean particiones relevantes
- ✅ **Mantenimiento**: VACUUM solo en particiones activas

**Implementación:**
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

### 2. Índices Optimizados

#### Índices Parciales (Partial Indexes)

**Por qué son mejores:**
- ✅ **Menor tamaño**: Solo indexan filas relevantes
- ✅ **Consultas más rápidas**: Menos datos que escanear
- ✅ **Menor overhead**: Menos escrituras en INSERT/UPDATE

**Ejemplos:**
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

#### Índices Compuestos

**Optimizados para consultas frecuentes:**
```sql
-- Consulta: "Préstamos de México con status APPROVED"
CREATE INDEX idx_loans_country_status
    ON loan_applications(country_code, status);

-- Consulta: "Auditoría de un préstamo específico"
CREATE INDEX idx_audit_entity_created
    ON audit_logs(entity_type, entity_id, created_at DESC);
```

### 3. Estrategia de Caché

**Qué se cachea y por qué:**

| Recurso | TTL | Razón |
|---------|-----|-------|
| Préstamo individual (`loan:{id}`) | 5 min | Cambia frecuentemente, pero consultas repetidas |
| Lista de préstamos (`loans:list:{country}`) | 1 min | Alta frecuencia de cambios, pero consultas muy frecuentes |
| Estadísticas (`stats:loans:{country}`) | 15 min | Cálculo costoso, cambios menos frecuentes |
| Información bancaria (`banking:{provider}:{doc}`) | 1 hora | Datos estables, no cambian frecuentemente |

**Invalidación:**
- **Write-through**: Al actualizar un préstamo, se invalida su caché
- **Pattern invalidation**: Al crear/actualizar, se invalida `loans:list:*` del país
- **TTL**: Expiración automática como fallback

**Implementación:**
```python
# app/services/loan_service.py
async def update_status(self, loan_id: UUID, new_status: LoanStatus):
    # ... actualizar préstamo ...
    
    # Invalidar caché
    await cache.delete(f"loan:{loan_id}")
    await cache.delete_pattern(f"loans:list:{loan.country_code}:*")
    await cache.delete(f"stats:loans:{loan.country_code}")
```

### 4. Consultas Optimizadas

#### Paginación con Cursor

**Para listas grandes:**
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

#### Consultas Solo Campos Necesarios

**Evitar SELECT *:**
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

### 5. Archivado de Datos Antiguos

**Estrategia:**
1. **Particiones mensuales** de `audit_logs` → mover a cold storage después de 1 año
2. **Préstamos completados** → mover a tabla de archivado después de 5 años
3. **Comprimir** particiones antiguas con `pg_compress`

**Implementación futura:**
```sql
-- Mover partición antigua a cold storage
ALTER TABLE audit_logs DETACH PARTITION audit_logs_2023_01;
-- Exportar a S3/Glacier
-- Eliminar partición local
```

### 6. Escalabilidad Horizontal

**Backend API:**
- Múltiples pods en Kubernetes con HPA (Horizontal Pod Autoscaler)
- Load balancer distribuye tráfico
- Stateless: cada pod es independiente

**Workers:**
- Múltiples instancias procesan jobs en paralelo
- `SELECT FOR UPDATE SKIP LOCKED` evita conflictos
- Auto-scaling basado en longitud de cola

**Base de Datos:**
- Read replicas para consultas de solo lectura
- Particionamiento permite sharding por país
- Connection pooling (SQLAlchemy pool_size)

---

## ⚙️ Estrategia de Concurrencia, Colas, Caché y Webhooks

### 1. Concurrencia

#### Workers Paralelos

**Implementación:**
- Múltiples instancias de workers pueden ejecutarse simultáneamente
- `SELECT FOR UPDATE SKIP LOCKED` garantiza que cada job sea procesado por un solo worker

**Por qué es seguro:**
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

**SKIP LOCKED** significa:
- Si el job está siendo procesado por otro worker, se omite
- No hay espera (no bloquea)
- Cada worker obtiene un job diferente

**Escalabilidad:**
- 1 worker: ~10 jobs/min
- 10 workers: ~100 jobs/min
- 100 workers: ~1,000 jobs/min

#### Locks de Base de Datos

**Para operaciones críticas:**
```python
# Ejemplo: Actualizar estado de préstamo
async with session.begin():
    loan = await session.get(LoanApplication, loan_id, with_for_update=True)
    # Solo este worker puede modificar este préstamo
    loan.status = new_status
```

### 2. Colas de Trabajos

#### Arquitectura de Colas

**Decisión**: Cola en PostgreSQL (`async_jobs`) en lugar de Redis Queue o RabbitMQ.

**Ventajas:**
- ✅ **ACID**: Jobs se crean en la misma transacción que el préstamo
- ✅ **Consulta directa**: Puedes ver jobs con SQL
- ✅ **Sin infraestructura adicional**: No requiere Redis Queue
- ✅ **Migración fácil**: Puede migrarse a Redis Queue después

**Colas implementadas:**
1. **`risk_evaluation`**: Evaluación de riesgo asíncrona
2. **`audit`**: Registro de auditoría
3. **`notifications`**: Notificaciones a usuarios
4. **`webhooks`**: Webhooks salientes

#### Procesamiento de Jobs

**Flujo:**
```
1. Crear préstamo → INSERT en loan_applications
2. Trigger PostgreSQL → INSERT en async_jobs (queue: 'audit')
3. Worker escucha → SELECT ... FOR UPDATE SKIP LOCKED
4. Worker procesa → UPDATE status = 'RUNNING'
5. Worker completa → UPDATE status = 'COMPLETED'
```

**Retry automático:**
```python
# app/workers/base.py
if job.attempts < job.max_attempts:
    # Reencolar con delay exponencial
    await job_repo.fail(job_id, retry=True, retry_delay=60 * attempts)
```

**Prioridades:**
- `priority = 2`: Alta (notificaciones)
- `priority = 1`: Media (auditoría)
- `priority = 0`: Baja (evaluación de riesgo)

### 3. Caché (Redis)

#### Estrategia de Caché

**Qué se cachea:**

| Clave | TTL | Invalidación |
|-------|-----|--------------|
| `loan:{id}` | 5 min | Al actualizar préstamo |
| `loans:list:{country}:{status}:{page}` | 1 min | Al crear/actualizar préstamo del país |
| `stats:loans:{country}` | 15 min | Al crear/actualizar préstamo del país |
| `banking:{provider}:{doc_hash}` | 1 hora | Manual (datos estables) |

**Implementación:**
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

**Invalidación inteligente:**
```python
# Al actualizar préstamo
await cache.delete(f"loan:{loan_id}")
await cache.delete_pattern(f"loans:list:{country_code}:*")
await cache.delete(f"stats:loans:{country_code}")
await cache.delete("stats:loans:all")
```

**Fallback graceful:**
- Si Redis no está disponible, el sistema funciona sin caché
- No falla la aplicación, solo es más lenta

#### Cache-Aside Pattern

**Implementación:**
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

#### Webhooks Entrantes

**Endpoint:** `POST /api/v1/webhooks/banking/{country_code}`

**Flujo:**
```
1. Proveedor bancario → POST /webhooks/banking/ES
2. Verificar HMAC signature
3. Almacenar en webhook_events
4. Buscar préstamo relacionado (por loan_id o document_hash)
5. Procesar evento (actualizar estado, risk_score, etc.)
6. Encolar job de auditoría
```

**Seguridad:**
```python
def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)  # Constant-time
```

**Reintentos:**
- Si el procesamiento falla, el webhook queda marcado como `processed = false`
- Un worker puede reintentar procesamiento de webhooks fallidos

#### Webhooks Salientes

**Implementación:**
- Worker `webhook_worker` procesa jobs de la cola `webhooks`
- Envía notificaciones a sistemas externos cuando cambia el estado de un préstamo

**Payload ejemplo:**
```json
{
  "event": "loan_status_changed",
  "loan_id": "uuid",
  "old_status": "PENDING",
  "new_status": "APPROVED",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Reintentos:**
- 3 intentos con backoff exponencial
- Si falla, se marca como `FAILED` y se puede reintentar manualmente

### 5. Real-time Updates (Socket.IO + PostgreSQL LISTEN/NOTIFY)

**Arquitectura:**
```
PostgreSQL INSERT/UPDATE
    ↓
Trigger → pg_notify('loan_changes', payload)
    ↓
PostgresListener (Python) → Recibe notificación
    ↓
Socket.IO Server → Emit a rooms
    ↓
Frontend (Socket.IO Client) → Recibe evento
    ↓
Redux Middleware → Dispatch action
    ↓
UI Update automático
```

**Latencia:** < 100ms del evento a la UI

**Rooms:**
- `country:{code}`: Todos los préstamos de un país
- `loan:{id}`: Un préstamo específico
- `all`: Todos los préstamos

**Implementación:**
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

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│              Frontend (React + Vite + Redux + TailwindCSS)  │
│              Socket.IO Client para Real-time                │
└─────────────────────────────┬───────────────────────────────┘
                              │ HTTP / WebSocket
┌─────────────────────────────┴───────────────────────────────┐
│                    Backend (FastAPI + Python)                │
│  ┌───────────┐  ┌───────────┐  ┌─────────────┐  ┌────────┐ │
│  │  API v1   │  │  Services │  │  Strategies │  │ Socket │ │
│  │  (REST)   │  │   Layer   │  │ (per país)  │  │   IO   │ │
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

### Arquitectura

**Backend:**
- **Layered Architecture** (Arquitectura por Capas): Controllers (API Routers) → Services → Domain (Strategies/Models) → Repositories/Infrastructure
- **Event-Driven Architecture**: PostgreSQL LISTEN/NOTIFY + Workers asíncronos para procesamiento en background

**Frontend:**
- **SPA (Single Page Application)** con **Flux/Redux Architecture**: React + Redux Toolkit para estado global unidireccional

### Patrones de Diseño

- **Strategy Pattern**: Lógica de validación específica por país
- **Repository Pattern**: Capa de acceso a datos desacoplada
- **Dependency Injection**: Usando FastAPI Depends
- **Observer Pattern**: PostgreSQL LISTEN/NOTIFY → Socket.IO

---

## 🌍 Países Soportados

| País | Código | Documento | Moneda | Formato Documento |
|------|--------|-----------|--------|-------------------|
| 🇪🇸 España | ES | DNI | EUR | 8 dígitos + letra |
| 🇲🇽 México | MX | CURP | MXN | 18 caracteres alfanuméricos |
| 🇨🇴 Colombia | CO | CC | COP | 6-10 dígitos |
| 🇧🇷 Brasil | BR | CPF | BRL | 11 dígitos |

---

## 🔌 API Endpoints

### Autenticación
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Registrar usuario |
| POST | `/api/v1/auth/login` | Iniciar sesión |
| POST | `/api/v1/auth/refresh` | Refrescar token |
| GET | `/api/v1/auth/me` | Obtener usuario actual |

### Préstamos
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/loans` | Listar préstamos (con filtros) |
| POST | `/api/v1/loans` | Crear préstamo |
| GET | `/api/v1/loans/{id}` | Obtener préstamo |
| PATCH | `/api/v1/loans/{id}/status` | Actualizar estado |
| GET | `/api/v1/loans/{id}/history` | Historial de estados |
| GET | `/api/v1/loans/statistics` | Estadísticas |

### Webhooks
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/webhooks/banking/{country_code}` | Recibir webhook de proveedor bancario |
| GET | `/api/v1/webhooks/events` | Listar eventos webhook |

### Health
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/health` | Estado de la aplicación |
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

### Error: "Connection refused" al conectar a PostgreSQL

**Causa**: PostgreSQL no está listo o el puerto es incorrecto.

**Solución**:
```bash
# Verificar que PostgreSQL esté corriendo
docker compose ps

# Ver logs de PostgreSQL
docker compose logs postgres

# Para desarrollo local, el puerto es 5433
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/loans_db
```

### Error: "No module named 'app'"

**Causa**: El entorno virtual no está activado o PYTHONPATH incorrecto.

**Solución**:
```bash
# Activar entorno virtual
source backend/.venv/bin/activate

# O usar el binario directamente
backend/.venv/bin/python -m app.main
```

### Error: "relation does not exist" (tablas no existen)

**Causa**: Las migraciones no se han ejecutado.

**Solución**:
```bash
# Con Docker
docker compose exec backend alembic upgrade head

# Local
make migrate
```

### Frontend no conecta al backend

**Causa**: CORS o URL incorrecta.

**Solución**:
1. Verificar que el backend esté corriendo
2. Verificar la variable `VITE_API_URL` en `frontend/.env`
3. Verificar `CORS_ORIGINS` en `backend/.env`

### Workers no procesan jobs

**Causa**: Workers no están corriendo o hay error en la conexión a DB.

**Solución**:
```bash
# Verificar workers
make workers

# Ver logs
docker compose logs worker-risk
docker compose logs worker-audit
```

### Redis no disponible

**Causa**: Redis no está corriendo.

**Solución**:
```bash
# Verificar Redis
docker compose logs redis

# Verificar conexión
docker compose exec redis redis-cli ping
```

**Nota**: El sistema funciona sin Redis, pero sin caché (más lento).

---

## 📊 Servicios Docker

| Servicio | Puerto Local | Puerto Container | Descripción |
|----------|-------------|------------------|-------------|
| postgres | 5433 | 5432 | Base de datos PostgreSQL 15 |
| redis | 6379 | 6379 | Cache y cola de mensajes |
| backend | 8000 | 8000 | API FastAPI |
| frontend | 3000 | 80 | App React (Nginx) |
| pgadmin | 5050 | 80 | Administrador de PostgreSQL |
| worker-risk | - | - | Worker de evaluación de riesgo |
| worker-audit | - | - | Worker de auditoría |
| worker-webhook | - | - | Worker de notificaciones |

---

## 🔐 Variables de Entorno

### Backend (`backend/.env`)

| Variable | Descripción | Default |
|----------|-------------|---------|
| `DATABASE_URL` | URL de conexión a PostgreSQL | `postgresql+asyncpg://postgres:postgres@localhost:5433/loans_db` |
| `REDIS_URL` | URL de conexión a Redis | `redis://localhost:6379/0` |
| `JWT_SECRET` | Clave secreta para JWT | `your-super-secret-key-change-in-production` |
| `CORS_ORIGINS` | Orígenes permitidos (separados por coma) | `http://localhost:5173,http://localhost:3000` |
| `DEBUG` | Modo debug | `false` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |
| `WEBHOOK_SECRET` | Secreto para verificar webhooks | `webhook-secret-key` |

### Frontend (`frontend/.env`)

| Variable | Descripción | Default |
|----------|-------------|---------|
| `VITE_API_URL` | URL del backend | `http://localhost:8000` |
| `VITE_WS_URL` | URL WebSocket | `http://localhost:8000` |

---

## 📝 Licencia

Este proyecto es parte de una prueba técnica.

---
