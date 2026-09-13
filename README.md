# aegis-urban-data-api

[![CI](https://github.com/your-org/aegis-urban-data-api/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/aegis-urban-data-api/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Package Manager: uv](https://img.shields.io/badge/uv-fast_package_manager-purple)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Benchmark workload for the [Aegis Platform](https://github.com/your-org/aegis-infra)** — a production-grade DevSecOps / GitOps HA platform built as a HUTECH University VJIT Capstone project.

---

## Overview

`aegis-urban-data-api` is a high-performance **Python/FastAPI** service architected as a **Modular Monolith** adhering to **Clean Architecture / Domain-Driven Design (DDD)** principles. It simulates IoT urban data ingestion following [FIWARE NGSI-v2](https://fiware-orion.readthedocs.io/en/master/user/ngsiv2_implementation_notes/) conventions.

It acts as the primary **benchmark workload** running on the Aegis Platform, exercising Kubernetes HA capabilities:
- Zero-downtime rolling updates & progressive delivery (Argo Rollouts)
- Leader election failover resilience (CloudNativePG PostgreSQL)
- Policy enforcement (Kyverno) & secrets injection (External Secrets Operator)
- Autoscaling under stress (HPA on CPU)

---

## Architecture: Modular Monolith + Clean Architecture

The codebase follows the **Dependency Rule**: inner domain layers contain zero external dependencies or framework annotations; outer layers depend inward.

```
app/
├── main.py                           # App factory, ASGI lifespan & Prometheus metrics
├── shared/                           # Cross-cutting concerns (Shared Kernel)
│   ├── infrastructure/
│   │   ├── database.py               # Async SQLAlchemy 2.0 SessionManager & Base
│   │   └── settings.py               # Pydantic-settings v2 (12-factor env configuration)
│   └── logging.py                    # Structlog structured JSON/console logging
│
└── modules/                          # Bounded Contexts (Vertical Slices)
    ├── entities/                     # IoT Entity Ingestion Bounded Context
    │   ├── domain/                   # [Layer 1] Pure Domain (zero external dependencies)
    │   │   ├── models.py             #   Entity aggregate root (dataclass)
    │   │   ├── value_objects.py      #   EntityId, EntityType (invariant enforcement)
    │   │   ├── repository.py         #   IEntityRepository (abstract interface)
    │   │   └── exceptions.py         #   Domain-specific exceptions
    │   │
    │   ├── application/              # [Layer 2] Application & Use Cases
    │   │   ├── dtos.py               #   Commands, Queries & DTOs
    │   │   └── use_cases/            #   Orchestration use cases
    │   │       ├── create_entity.py
    │   │       ├── get_entity.py
    │   │       ├── list_entities.py
    │   │       ├── update_entity.py
    │   │       └── delete_entity.py
    │   │
    │   ├── infrastructure/           # [Layer 3] Data & Adapters
    │   │   ├── orm.py                #   SQLAlchemy ORM table mapping (cross-DB JSON/Uuid)
    │   │   └── pg_repository.py      #   PostgresEntityRepository (implements IEntityRepository)
    │   │
    │   └── presentation/             # [Layer 4] Delivery Mechanism
    │       ├── dependencies.py       #   FastAPI DI providers for repository & use cases
    │       ├── router.py             #   FastAPI endpoints & HTTP status codes
    │       └── schemas.py            #   Pydantic v2 request/response validation schemas
    │
    └── health/                       # Health & Observability Module
        └── presentation/
            └── router.py             # /health (liveness) & /ready (DB connectivity)
```

---

## Tech Stack

| Component | Technology | Rationale |
|---|---|---|
| **Language** | Python 3.12 | Modern syntax, native type hints, async performance |
| **Web Framework** | FastAPI 0.115+ | OpenAPI auto-docs, async-native, dependency injection |
| **Validation** | Pydantic v2 | High-performance Rust core, strict type validation |
| **Settings** | pydantic-settings v2 | 12-factor configuration mapped from env vars |
| **Database ORM** | SQLAlchemy 2.0 async | Fully-typed `mapped_column`, `AsyncSession` |
| **DB Driver** | asyncpg | High-throughput asynchronous PostgreSQL driver |
| **Package Manager**| uv | 10–100× faster than pip/poetry, reproducible virtual environments |
| **Linter / Formatter**| Ruff | High-speed all-in-one linter, formatter, import sorter |
| **Type Checker** | mypy (strict mode) | Full compile-time static type safety |
| **Logging** | structlog | Human-readable in local dev, structured JSON for Loki |
| **Testing** | pytest-asyncio + httpx | Async test suite with in-memory SQLite isolation |
| **Security Scanning** | pip-audit + Semgrep | Supply-chain CVE audit and SAST security gates |

---

## API Endpoints

### Entities (FIWARE NGSI-v2)
| Method | Path | Description | Status Code |
|---|---|---|---|
| `POST` | `/v1/entities` | Ingest IoT sensor entity (triggers webhook notifications) | `201 Created` / `409 Conflict` |
| `GET` | `/v1/entities` | List entities (paginated, optional type filter) | `200 OK` |
| `GET` | `/v1/entities/{id}` | Retrieve entity by FIWARE Entity ID | `200 OK` / `404 Not Found` |
| `PATCH` | `/v1/entities/{id}` | Update entity attributes (triggers webhook notifications) | `200 OK` / `404 Not Found` |
| `DELETE` | `/v1/entities/{id}` | Delete entity by ID | `204 No Content` / `404 Not Found` |

### Subscriptions & Notifications
| Method | Path | Description | Status Code |
|---|---|---|---|
| `POST` | `/v1/subscriptions` | Register webhook subscription for entity changes | `201 Created` / `409 Conflict` |
| `GET` | `/v1/subscriptions` | List subscriptions (filter by active/paused) | `200 OK` |
| `GET` | `/v1/subscriptions/{id}` | Retrieve subscription details & notification count | `200 OK` / `404 Not Found` |
| `DELETE` | `/v1/subscriptions/{id}`| Deregister subscription | `204 No Content` / `404 Not Found` |

### Observations (Time-Series Telemetry)
| Method | Path | Description | Status Code |
|---|---|---|---|
| `POST` | `/v1/observations` | Ingest single sensor metric | `201 Created` |
| `POST` | `/v1/observations/bulk`| High-throughput batch telemetry ingestion | `201 Created` |
| `GET` | `/v1/observations` | Query time-series window (`entity_id`, time range) | `200 OK` |
| `GET` | `/v1/observations/latest` | Get latest reading for each attribute of an entity | `200 OK` |

### IoT Simulation & Stream Generation
| Method | Path | Description | Status Code |
|---|---|---|---|
| `POST` | `/v1/simulation/start` | Start background urban sensor stream simulation | `200 OK` |
| `POST` | `/v1/simulation/stop` | Stop running simulation | `200 OK` |
| `GET` | `/v1/simulation/status`| Get simulation telemetry rate & uptime | `200 OK` |
| `POST` | `/v1/simulation/seed` | Seed default urban sensor fleet (HCM City) | `200 OK` |

### External Ingestion (Open-Meteo Public API)
| Method | Path | Description | Status Code |
|---|---|---|---|
| `GET` | `/v1/external-ingest/stations` | List monitored urban stations in Ho Chi Minh City | `200 OK` |
| `POST` | `/v1/external-ingest/sync` | On-demand sync of live weather & PM2.5/PM10 from Open-Meteo | `200 OK` |
| `POST` | `/v1/external-ingest/schedule/start` | Start periodic background sync (default: 10 mins) | `200 OK` |
| `POST` | `/v1/external-ingest/schedule/stop` | Stop periodic background sync | `200 OK` |
| `GET` | `/v1/external-ingest/status` | Get scheduler status, last sync timestamp & count | `200 OK` |

### Observability & Probes
| Method | Path | Description | Status Code |
|---|---|---|---|
| `GET` | `/health`, `/v1/health` | Liveness probe (returns 200 if process alive) | `200 OK` |
| `GET` | `/ready`, `/v1/ready` | Readiness probe (verifies database connectivity) | `200 OK` / `503 Unavailable` |
| `GET` | `/metrics` | Prometheus metrics scrape endpoint | `200 OK` |
| `GET` | `/docs` | Interactive Swagger UI documentation | `200 OK` |

---

## Local Development

### Prerequisites
- Python 3.12+
- [`uv`](https://github.com/astral-sh/uv): `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Setup Environment
```bash
# Clone the repository
git clone <repo-url>
cd aegis-urban-data-api

# Install dependencies (creates .venv automatically)
uv sync

# Configure environment
cp .env.example .env
```

### Run Tests & Quality Checks
```bash
# Run test suite with coverage
uv run pytest

# Check formatting and linting
uv run ruff check app/ tests/
uv run ruff format app/ tests/ --check

# Run static type analysis
uv run mypy app/

# Run supply-chain security audit
uv run pip-audit
```

### Run Locally
```bash
uv run uvicorn app.main:create_app --factory --reload --port 8080
```
Visit http://localhost:8080/docs for the interactive Swagger documentation.

---

## Container Build

Multi-stage build utilizing `uv` for layer caching and minimal image footprint on `python:3.12-slim`:

```bash
docker build -t aegis/urban-data-api:latest .
```

---

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) enforces rigorous quality gates:
1. **Test Job**: Runs `pytest` with coverage report threshold enforcement (>=80%).
2. **Lint Job**: Runs `ruff` checks and `mypy` strict type checking.
3. **Security Scan**: Supply-chain dependency vulnerability audit (`pip-audit`) + SAST scanning (`Semgrep`).
4. **Build Image**: Docker buildx multi-stage build + Container vulnerability scanning (`Trivy`) + ECR push.
5. **GitOps Auto-Update**: Idempotently commits the new image SHA tag into `aegis-infra` Helm values repository to trigger Argo CD automated synchronization.

---

## Related Repositories

- [aegis-infra](https://github.com/your-org/aegis-infra): Infrastructure repository (Terraform, k3d, Helm, Argo CD).
- [aegis-platform](https://github.com/your-org/aegis-platform): Umbrella repository linking submodules.
