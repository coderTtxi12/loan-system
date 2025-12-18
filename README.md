# 🏦 Loan System - Multipaís

Sistema de gestión de solicitudes de préstamos para España, México, Colombia y Brasil.

## 📋 Tabla de Contenidos

- [Prerrequisitos](#-prerrequisitos)
- [Quick Start con Docker](#-quick-start-con-docker-recomendado)
- [Desarrollo Local](#-desarrollo-local)
- [Comandos Make](#-comandos-make)
- [Arquitectura](#️-arquitectura)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Países Soportados](#-países-soportados)
- [API Endpoints](#-api-endpoints)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)

---

## 📌 Prerrequisitos

### Para Docker (Opción Recomendada)
- [Docker](https://docs.docker.com/get-docker/) >= 20.10
- [Docker Compose](https://docs.docker.com/compose/install/) >= 2.0

### Para Desarrollo Local
- [Python](https://www.python.org/downloads/) >= 3.11
- [Node.js](https://nodejs.org/) >= 18.0
- [Make](https://www.gnu.org/software/make/) (incluido en macOS/Linux)
- [Docker](https://docs.docker.com/get-docker/) (para PostgreSQL y Redis)

---

## 🐳 Quick Start con Docker (Recomendado)

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd loan
```

### 2. Configurar variables de entorno

**Backend:**
```bash
cp backend/.env.example backend/.env
```

**Frontend:**
```bash
cp frontend/.env.example frontend/.env
```

> 📝 **Opcional**: Revisa y ajusta los archivos `.env` según tu configuración si es necesario.
> 
> 💡 **Nota**: Si no creas los archivos `.env`, Docker Compose usará los valores por defecto definidos en `docker-compose.yml`.

### 3. Levantar todos los servicios
```bash
docker compose up --build
```

> ⏳ La primera vez tardará unos minutos en construir las imágenes.

### 4. Ejecutar las migraciones de base de datos

En otra terminal, ejecuta:
```bash
docker compose exec backend alembic upgrade head
```

> ✅ **Nota**: Las migraciones iniciales (`000_initial_schema.py` y `001_add_postgresql_triggers.py`) ya están incluidas en el repositorio, así que solo necesitas ejecutar `upgrade head`.
> 
> Si necesitas crear nuevas migraciones en el futuro (después de modificar modelos), usa:
> ```bash
> docker compose exec backend alembic revision --autogenerate -m "descripción del cambio"
> docker compose exec backend alembic upgrade head
> ```

### 5. Cargar usuarios de demostración (seed)

```bash
docker compose exec backend python -m app.db.seed
```

Esto creará los usuarios de prueba para poder iniciar sesión.

### 6. Acceder a la aplicación

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

### 7. Detener los servicios
```bash
docker compose down
```

Para eliminar también los volúmenes (datos):
```bash
docker compose down -v
```

---

## 💻 Desarrollo Local

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd loan
```

### 2. Configurar variables de entorno

**Backend:**
```bash
cp backend/.env.example backend/.env
```

**Frontend:**
```bash
cp frontend/.env.example frontend/.env
```

> 📝 Revisa y ajusta los archivos `.env` según tu configuración local si es necesario.

### 3. Levantar PostgreSQL y Redis
```bash
docker compose up -d postgres redis
```

Espera a que los servicios estén saludables:
```bash
docker compose ps
```

### 4. Instalar dependencias
```bash
make install
```

Esto instalará:
- Dependencias de Python en un entorno virtual (`backend/.venv`)
- Dependencias de Node.js (`frontend/node_modules`)

### 5. Ejecutar migraciones de base de datos

Primero, si no existen migraciones, genera la migración inicial:
```bash
cd backend
../.venv/bin/alembic revision --autogenerate -m "initial"
cd ..
```

Luego aplica las migraciones:
```bash
make migrate
```

### 6. Cargar usuarios de demostración (seed)
```bash
make seed
```

Esto creará los usuarios de prueba para poder iniciar sesión (ver credenciales en la sección Docker).

### 7. Iniciar los servidores de desarrollo
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
```

---

## 🛠️ Comandos Make

| Comando | Descripción |
|---------|-------------|
| `make help` | Mostrar ayuda con todos los comandos |
| `make install` | Instalar dependencias (backend + frontend) |
| `make dev` | Iniciar servidores de desarrollo |
| `make dev-backend` | Iniciar solo el backend |
| `make dev-frontend` | Iniciar solo el frontend |
| `make test` | Ejecutar todos los tests |
| `make test-backend` | Ejecutar tests del backend |
| `make test-frontend` | Ejecutar tests del frontend |
| `make lint` | Ejecutar linters |
| `make migrate` | Ejecutar migraciones de DB |
| `make migrate-create msg="descripcion"` | Crear nueva migración |
| `make seed` | Cargar usuarios de demostración |
| `make docker-build` | Construir imágenes Docker |
| `make clean` | Limpiar archivos generados |
| `make clean-venv` | Eliminar entorno virtual |

---

## 🌍 Países Soportados

| País | Código | Documento | Moneda | Formato Documento |
|------|--------|-----------|--------|-------------------|
| 🇪🇸 España | ES | DNI | EUR | 8 dígitos + letra |
| 🇲🇽 México | MX | CURP | MXN | 18 caracteres alfanuméricos |
| 🇨🇴 Colombia | CO | CC | COP | 6-10 dígitos |
| 🇧🇷 Brasil | BR | CPF | BRL | 11 dígitos |

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
    └───────────┘       └───────────┘       └───────────┘
```

### Patrones de Diseño

- **Strategy Pattern**: Lógica de validación específica por país
- **Repository Pattern**: Capa de acceso a datos desacoplada
- **Dependency Injection**: Usando FastAPI Depends

---

## 📁 Estructura del Proyecto

```
loan/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # Endpoints REST
│   │   │   ├── auth/         # Autenticación (login, registro)
│   │   │   ├── health/       # Health checks
│   │   │   ├── loans/        # CRUD de préstamos
│   │   │   └── webhooks/     # Webhooks entrantes
│   │   ├── core/             # Config, security, exceptions
│   │   ├── db/               # Configuración de base de datos
│   │   ├── models/           # SQLAlchemy models
│   │   ├── repositories/     # Capa de acceso a datos
│   │   ├── services/         # Lógica de negocio
│   │   ├── sockets/          # WebSocket handlers
│   │   ├── strategies/       # Estrategias por país
│   │   └── workers/          # Workers asíncronos
│   ├── alembic/              # Migraciones de DB
│   ├── tests/                # Tests unitarios e integración
│   ├── Dockerfile
│   ├── Dockerfile.workers
│   ├── requirements.txt
│   └── requirements-dev.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/       # Componentes React
│   │   │   ├── layout/       # Layout, Navbar, Sidebar
│   │   │   ├── loans/        # Componentes de préstamos
│   │   │   └── ui/           # Componentes UI reutilizables
│   │   ├── pages/            # Páginas de la aplicación
│   │   ├── store/            # Redux store y slices
│   │   ├── services/         # API client y Socket
│   │   ├── hooks/            # Custom hooks
│   │   ├── types/            # TypeScript types
│   │   └── utils/            # Utilidades y validadores
│   ├── __tests__/            # Tests del frontend
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
│
├── k8s/                      # Kubernetes manifests
│   ├── base/                 # Configuración base
│   └── overlays/             # Configuración por ambiente
│       ├── development/
│       ├── staging/
│       └── production/
│
├── docker-compose.yml        # Orquestación de servicios
├── Makefile                  # Comandos de automatización
└── README.md
```

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
| GET | `/api/v1/loans` | Listar préstamos |
| POST | `/api/v1/loans` | Crear préstamo |
| GET | `/api/v1/loans/{id}` | Obtener préstamo |
| PUT | `/api/v1/loans/{id}/status` | Actualizar estado |
| GET | `/api/v1/loans/{id}/history` | Historial de estados |

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
cd backend && ../.venv/bin/pytest -v --cov=app --cov-report=html
```

### Frontend
```bash
# Ejecutar tests
make test-frontend

# O directamente
cd frontend && npm test
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

**Causa**: Redis no está disponible.

**Solución**:
```bash
# Verificar Redis
docker compose logs redis

# Verificar conexión
docker compose exec redis redis-cli ping
```

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

### Frontend (`frontend/.env`)

| Variable | Descripción | Default |
|----------|-------------|---------|
| `VITE_API_URL` | URL del backend | `http://localhost:8000` |
| `VITE_WS_URL` | URL WebSocket | `http://localhost:8000` |

---

## 📝 Licencia

Este proyecto es parte de una prueba técnica.
