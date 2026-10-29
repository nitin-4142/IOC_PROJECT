"""ResponsePlan database model."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from database import Base


class ResponsePlan(Base):
    __tablename__ = "response_plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=False, index=True)
    summary = Column(Text)
    priority_actions = Column(Text)       # JSON list
    logistics_notes = Column(Text)
    resource_conflicts = Column(Text)     # JSON list
    missing_data_flags = Column(Text)     # JSON list
    follow_up_questions = Column(Text)    # JSON list
    approval_status = Column(String(32), default="PENDING")
    approved_by = Column(String(128), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "summary": self.summary,
            "priority_actions": json.loads(self.priority_actions) if self.priority_actions else [],
            "logistics_notes": self.logistics_notes,
            "resource_conflicts": json.loads(self.resource_conflicts) if self.resource_conflicts else [],
            "missing_data_flags": json.loads(self.missing_data_flags) if self.missing_data_flags else [],
            "follow_up_questions": json.loads(self.follow_up_questions) if self.follow_up_questions else [],
            "approval_status": self.approval_status,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
