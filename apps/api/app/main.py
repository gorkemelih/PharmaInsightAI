"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import get_settings
from app.core.security import hash_password
from app.db.session import DBSession, SessionLocal
from app.logging_config import configure_logging, get_logger
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.routers import auth, users, projects, runs, dashboard, documents, paper_summaries

settings = get_settings()
logger = get_logger(__name__)


def seed_admin_user() -> None:
    """Create initial admin user and tenant if they don't exist."""
    db = SessionLocal()
    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.email == settings.admin_email).first()
        if existing_admin:
            logger.info("Admin user already exists", email=settings.admin_email)
            return

        # Create tenant
        tenant = db.query(Tenant).filter(Tenant.name == settings.tenant_name).first()
        if not tenant:
            tenant = Tenant(name=settings.tenant_name)
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
            logger.info("Created default tenant", name=settings.tenant_name)

        # Create admin user
        admin = User(
            tenant_id=tenant.id,
            email=settings.admin_email,
            password_hash=hash_password(settings.admin_password),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        logger.info("Created admin user", email=settings.admin_email)
    except Exception as e:
        logger.error("Failed to seed admin user", error=str(e))
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    configure_logging()
    logger.info("Starting PharmaInsightAI API", environment=settings.environment)

    # Seed admin user on startup
    seed_admin_user()

    yield
    logger.info("Shutting down PharmaInsightAI API")


app = FastAPI(
    title="PharmaInsightAI API",
    description="B2B pharmaceutical insights platform API",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS with credentials support
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(dashboard.router)  # Must be before runs for /runs/recent
app.include_router(runs.router)
app.include_router(documents.router)
app.include_router(paper_summaries.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Welcome to PharmaInsightAI API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/db/ping")
def db_ping(db: DBSession) -> dict[str, str]:
    """Database connectivity check endpoint.

    Opens a session and executes SELECT 1 to verify database is reachable.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        logger.error("Database ping failed", error=str(e))
        return {"status": "error", "message": str(e)}
