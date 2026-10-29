"""Resource database models."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Float, Integer, ForeignKey
from database import Base


class ResourceRecommendation(Base):
    __tablename__ = "resource_recommendations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False)
    recommended_quantity = Column(Integer, nullable=False)
    reason = Column(Text)
    availability_status = Column(String(32), default="UNKNOWN")
    source_of_availability_data = Column(String(128))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "resource_type": self.resource_type,
            "recommended_quantity": self.recommended_quantity,
            "reason": self.reason,
            "availability_status": self.availability_status,
            "source_of_availability_data": self.source_of_availability_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ResourceInventory(Base):
    __tablename__ = "resource_inventory"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_type = Column(String(64), nullable=False, index=True)
    name = Column(String(128))
    base_location = Column(String(256))
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    total_quantity = Column(Integer, default=0)
    available_quantity = Column(Integer, default=0)
    data_provenance = Column(String(64), default="DEMO_DATA")
    notes = Column(Text)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "resource_type": self.resource_type,
            "name": self.name,
            "base_location": self.base_location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "total_quantity": self.total_quantity,
            "available_quantity": self.available_quantity,
            "data_provenance": self.data_provenance,
            "notes": self.notes,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
