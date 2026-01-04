# PharmaInsightAI

Production-grade B2B pharmaceutical insights platform.

## Stack

- **Frontend**: Next.js 14 (App Router) + TypeScript + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI + Pydantic v2 + SQLAlchemy 2.0 + Alembic
- **Worker**: Celery + Redis
- **Database**: PostgreSQL 16
- **Cache/Broker**: Redis 7

## Quick Start

```bash
# Copy environment file
cp .env.example .env

# Start all services
make dev

# Or with docker compose directly
docker compose up --build
```

## Services

| Service | URL | Description |
|---------|-----|-------------|
| Web | http://localhost:3000 | Next.js frontend |
| API | http://localhost:8000 | FastAPI backend |
| API Docs | http://localhost:8000/docs | Swagger UI |

## Development Commands

```bash
make dev          # Start all services
make test         # Run all tests
make lint         # Run linters
make format       # Format code
make clean        # Clean up
```

## Project Structure

```
pharmainsightai/
├── apps/
│   ├── web/      # Next.js frontend
│   ├── api/      # FastAPI backend
│   └── worker/   # Celery worker
├── packages/
│   └── shared/   # Shared types/contracts
└── docker-compose.yml
```

## Environment Variables

See `.env.example` for all required environment variables.

## License

Proprietary - All rights reserved.
