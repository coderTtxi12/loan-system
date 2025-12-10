# 🏦 Loan System - Multipaís

Sistema de gestión de solicitudes de préstamos

## 🌍 Países Soportados

| País | Código | Documento | Moneda |
|------|--------|-----------|--------|
| 🇪🇸 España | ES | DNI | EUR |
| 🇲🇽 México | MX | CURP | MXN |
| 🇨🇴 Colombia | CO | CC | COP |
| 🇧🇷 Brasil | BR | CPF | BRL |

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────┐
│           Frontend (React + Vite + Redux)    │
└─────────────────────┬───────────────────────┘
                      │
┌─────────────────────┴───────────────────────┐
│           Backend (FastAPI + Python)         │
│  ┌─────────┐ ┌─────────┐ ┌─────────────┐   │
│  │ API     │ │ Services│ │  Strategies  │   │
│  │ Layer   │ │  Layer  │ │  (per país)  │   │
│  └─────────┘ └─────────┘ └─────────────┘   │
└─────────────────────┬───────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
   PostgreSQL      Redis       Workers
```

## 🚀 Quick Start

### Prerrequisitos

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Make

### Instalación

```bash
# 1. Clonar repositorio
git clone https://github.com/coderTtxi12/loan-system.git
cd loan-system

# 2. Instalar dependencias
make install

# 3. Levantar servicios (PostgreSQL, Redis)
docker compose up -d

# 4. Iniciar desarrollo
make dev
```

### Acceso

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000

## 📁 Estructura del Proyecto

```
loan/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Endpoints REST
│   │   ├── core/            # Config, security
│   │   ├── models/          # SQLAlchemy models
│   │   ├── repositories/    # Data access layer
│   │   ├── services/        # Business logic
│   │   └── strategies/      # Country strategies
│   ├── tests/
│   ├── alembic/             # Migrations
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── store/           # Redux store
│   │   ├── services/        # API client
│   │   └── hooks/           # Custom hooks
│   └── package.json
│
├── k8s/                     # Kubernetes manifests
├── docker-compose.yml
├── Makefile
└── README.md
```

## 🛠️ Comandos Disponibles

```bash
make install     # Instalar dependencias
make dev         # Iniciar desarrollo
make test        # Ejecutar tests
make lint        # Linting
make migrate     # Ejecutar migraciones
make docker-build # Construir imágenes Docker
```

## 📋 Funcionalidades

- [x] Estructura del proyecto
- [ ] Health endpoint
- [ ] Conexión a base de datos
- [ ] Modelo de préstamos
- [ ] Strategy pattern por país
- [ ] API CRUD de préstamos
- [ ] Autenticación JWT
- [ ] Cache con Redis
- [ ] Real-time con Socket.IO
- [ ] Workers asíncronos
- [ ] Frontend completo
- [ ] Kubernetes deployment

