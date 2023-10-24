import datetime
from typing import Optional
import uuid

from pydantic import BaseModel
from lcwc.category import IncidentCategory


from app.api.models.unit import Unit
from app.database.models.incident import Incident


class Coordinates(BaseModel):
    latitude: float
    longitude: float


class IncidentStats(BaseModel):
    total_incidents: int
    total_active_incidents: int
    total_resolved_incidents: int


class IncidentMeta(BaseModel):
    added_at: datetime.datetime
    updated_at: datetime.datetime
    resolved_at: Optional[datetime.datetime]
    client: str
    automatically_resolved: bool


class Incident(BaseModel):
    id: uuid.UUID
    category: IncidentCategory
    description: str
    intersection: Optional[str]
    municipality: str
    dispatched_at: datetime.datetime

    number: int
    priority: Optional[int]
    agency: str

    coordinates: Coordinates
    meta: IncidentMeta
    units: list[Unit]

    @staticmethod
    def from_db_model(incident: Incident):
        return Incident(
            id=incident.id,
            category=incident.category,
            description=incident.description,
            intersection=incident.intersection,
            municipality=incident.municipality,
            dispatched_at=incident.dispatched_at,
            number=incident.number,
            priority=incident.priority,
            agency=incident.agency,
            meta=IncidentMeta(
                added_at=incident.added_at,
                updated_at=incident.updated_at,
                resolved_at=incident.resolved_at,
                client=incident.client,
                automatically_resolved=incident.automatically_resolved,
            ),
            coordinates=Coordinates(
                latitude=incident.latitude,
                longitude=incident.longitude,
            ),
            units=[
                Unit(
                    id=unit.id,
                    name=unit.name,
                    short_name=unit.short_name,
                    added_at=unit.added_at,
                    removed_at=unit.removed_at,
                    last_seen=unit.last_seen,
                    automatically_removed=unit.automatically_removed,
                )
                for unit in incident.units
            ],
        )


class IncidentResponse(BaseModel):
    data: Incident


class IncidentsResponse(BaseModel):
    count: int
    data: list[Incident]
    # TODO pagination
