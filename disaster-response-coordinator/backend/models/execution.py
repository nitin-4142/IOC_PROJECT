"""Agent execution tracking models."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Float, Boolean, ForeignKey
from database import Base


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=False, index=True)
    agent_name = Column(String(64), nullable=False)
    status = Column(String(32), default="PENDING")  # PENDING|SUCCESS|FAILED|FALLBACK
    used_fallback = Column(Boolean, default=False)
    duration_ms = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "agent_name": self.agent_name,
            "status": self.status,
            "used_fallback": self.used_fallback,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class IncidentEvent(Base):
    __tablename__ = "incident_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    description = Column(Text)
    actor = Column(String(128), default="system")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "event_type": self.event_type,
            "description": self.description,
            "actor": self.actor,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class OperatorApproval(Base):
    __tablename__ = "operator_approvals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=False, index=True)
    plan_id = Column(String(36), ForeignKey("response_plans.id"), nullable=True)
    operator_name = Column(String(128), nullable=False)
    decision = Column(String(32), nullable=False)  # APPROVED | REJECTED | MODIFIED
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "plan_id": self.plan_id,
            "operator_name": self.operator_name,
            "decision": self.decision,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
