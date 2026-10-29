"""RiskAssessment database model."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Float, Boolean, ForeignKey
from database import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    severity = Column(String(16), nullable=False)
    contributing_factors = Column(Text)  # JSON
    rationale = Column(Text)
    confidence = Column(Float)
    requires_human_review = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "risk_score": self.risk_score,
            "severity": self.severity,
            "contributing_factors": json.loads(self.contributing_factors) if self.contributing_factors else [],
            "rationale": self.rationale,
            "confidence": self.confidence,
            "requires_human_review": self.requires_human_review,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
