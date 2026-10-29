"""Incident database model."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Float, Integer
from database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    correlation_id = Column(String(36), unique=True, nullable=False, index=True,
                            default=lambda: str(uuid.uuid4()))
    raw_report = Column(Text, nullable=False)
    incident_type = Column(String(64))
    location_text = Column(String(256))
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    reported_time = Column(String(64))
    affected_population = Column(Integer, nullable=True)
    injuries_reported = Column(Integer, nullable=True)
    missing_persons_reported = Column(Integer, nullable=True)
    immediate_threats = Column(Text)        # JSON array stored as text
    extracted_facts = Column(Text)          # JSON array
    missing_information = Column(Text)      # JSON array
    confidence = Column(Float, default=0.5)
    processing_source = Column(String(32))  # "gemini" | "fallback"
    status = Column(String(32), default="NEW", index=True)
    risk_score = Column(Float, nullable=True)
    severity = Column(String(16), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    is_demo = Column(String(5), default="false")  # "true" | "false"

    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "correlation_id": self.correlation_id,
            "raw_report": self.raw_report,
            "incident_type": self.incident_type,
            "location_text": self.location_text,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "reported_time": self.reported_time,
            "affected_population": self.affected_population,
            "injuries_reported": self.injuries_reported,
            "missing_persons_reported": self.missing_persons_reported,
            "immediate_threats": json.loads(self.immediate_threats) if self.immediate_threats else [],
            "extracted_facts": json.loads(self.extracted_facts) if self.extracted_facts else [],
            "missing_information": json.loads(self.missing_information) if self.missing_information else [],
            "confidence": self.confidence,
            "processing_source": self.processing_source,
            "status": self.status,
            "risk_score": self.risk_score,
            "severity": self.severity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_demo": self.is_demo,
        }
