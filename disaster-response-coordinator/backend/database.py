"""
SQLAlchemy database setup for AI Disaster Response Coordinator.
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import DATABASE_URL

logger = logging.getLogger(__name__)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Create all tables and seed resource inventory if empty."""
    from models.incident import Incident  # noqa: F401
    from models.assessment import RiskAssessment  # noqa: F401
    from models.resource import ResourceRecommendation, ResourceInventory  # noqa: F401
    from models.plan import ResponsePlan  # noqa: F401
    from models.execution import AgentExecution, IncidentEvent, OperatorApproval  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created / verified.")
    _seed_inventory_if_empty()


def _seed_inventory_if_empty() -> None:
    """Populate demo resource inventory on first run."""
    from models.resource import ResourceInventory
    from services.resource_service import DEMO_INVENTORY

    db = SessionLocal()
    try:
        if db.query(ResourceInventory).count() == 0:
            for item in DEMO_INVENTORY:
                db.add(ResourceInventory(**item))
            db.commit()
            logger.info("Demo resource inventory seeded.")
    finally:
        db.close()


def get_db():
    """Yield a database session (use in Flask request context)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
