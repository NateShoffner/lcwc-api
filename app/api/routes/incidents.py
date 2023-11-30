import datetime
import logging
import os
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.api.models.incident import (
    Incident as IncidentOutput,
    IncidentResponse,
    IncidentStats,
    IncidentsResponse,
)
from app.database.models.incident import Incident
from app.database.models.unit import Unit
from fastapi_cache.decorator import cache

router = APIRouter(
    prefix="/incidents",
    tags=["incidents"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)


class ResponseModel(BaseModel):
    data: Optional[dict] = None


@router.get("/stats")
@cache(expire=os.getenv("CACHE_INCIDENTS_EXPIRE"))
async def stats() -> IncidentStats:
    """Returns various statistics about the API"""

    total_incidents = Incident.select().count()
    total_active_incidents = (
        Incident.select().where(Incident.resolved_at.is_null()).count()
    )
    total_resolved_incidents = (
        Incident.select().where(Incident.resolved_at.is_null(False)).count()
    )

    return IncidentStats(
        total_incidents=total_incidents,
        total_active_incidents=total_active_incidents,
        total_resolved_incidents=total_resolved_incidents,
    )


@router.get("/active")
@cache(expire=os.getenv("CACHE_ACTIVE_INCIDENTS_EXPIRE"))
async def incidents(
    category: str = None,
    description: str = None,
    intersection: str = None,
    municipality: str = None,
) -> IncidentsResponse:
    """Returns a list of active incidents"""

    incidents = Incident.select().where(Incident.resolved_at.is_null())

    if category:
        incidents = incidents.where(Incident.category == category)
    if description:
        incidents = incidents.where(Incident.description.contains(description))
    if intersection:
        incidents = incidents.where(Incident.intersection.contains(intersection))
    if municipality:
        incidents = incidents.where(Incident.municipality.contains(municipality))

    incidents.order_by(Incident.dispatched_at.desc())

    output_incidents = []

    for incident in incidents:
        output_incidents.append(IncidentOutput.from_db_model(incident))

    return IncidentsResponse(count=len(output_incidents), data=output_incidents)


@router.get("/related/{incident_id}")
@cache(expire=os.getenv("CACHE_INCIDENTS_EXPIRE"))
async def related(incident_id: str, delta_minutes: int = 60):
    try:
        incident = Incident.select().where(Incident.id == incident_id).limit(1).get()
    except Incident.DoesNotExist:
        raise HTTPException(
            status_code=404, detail=f"Incident with {incident_id=} does not exist."
        )

    related = Incident.select().where(
        Incident.intersection == incident.intersection,
        Incident.id != incident.id,
        Incident.added_at.between(
            incident.added_at - datetime.timedelta(minutes=delta_minutes),
            incident.added_at + datetime.timedelta(minutes=delta_minutes),
        ),
    )

    data = {
        "count": len(related),
        "incidents": [IncidentOutput.from_db_model(item) for item in related],
    }

    return ResponseModel(data=data)


@router.get("/by-date-range/{start}/{end}")
@cache(expire=os.getenv("CACHE_INCIDENTS_EXPIRE"))
async def incident(start: datetime.date, end: datetime.date):
    incidents = (
        Incident.select()
        .where(Incident.dispatched_at.between(start, end))
        .order_by(Incident.dispatched_at.desc())
    )

    data = {
        "count": len(incidents),
        "incidents": [IncidentOutput.from_db_model(item) for item in incidents],
    }

    return ResponseModel(data=data)


@router.get("/search")
@cache(expire=os.getenv("CACHE_INCIDENT_SEARCH_EXPIRE"))
async def incident(
    category: str = None,
    description: str = None,
    intersection: str = None,
    municipality: str = None,
    agency: str = None,
) -> IncidentsResponse:
    """Returns a list of incidents matching the query parameters"""

    incidents = Incident.select()

    if category:
        incidents = incidents.where(Incident.category == category)
    if description:
        incidents = incidents.where(Incident.description.contains(description))
    if intersection:
        incidents = incidents.where(Incident.intersection.contains(intersection))
    if municipality:
        incidents = incidents.where(Incident.municipality.contains(municipality))
    if agency:
        incidents = incidents.where(Incident.agency.contains(agency))

    incidents.order_by(Incident.dispatched_at.desc())

    output_incidents = []

    for incident in incidents:
        output_incidents.append(IncidentOutput.from_db_model(incident))

    return IncidentsResponse(count=len(output_incidents), data=output_incidents)
