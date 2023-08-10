import datetime
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from playhouse.shortcuts import model_to_dict
from peewee import fn
from pydantic import BaseModel
from app.utils.info import get_lcwc_version
from app.api.models.incident import Incident
from app.api.models.unit import Unit

router = APIRouter()

logger = logging.getLogger(__name__)


class ResponseModel(BaseModel):
    message: Optional[str] = None
    data: Optional[dict] = None


@router.get("/stats")
async def stats():
    """Returns various statistics about the API"""

    total_incidents = Incident.select().count()
    total_active_incidents = (
        Incident.select().where(Incident.resolved_at.is_null()).count()
    )
    total_resolved_incidents = (
        Incident.select().where(Incident.resolved_at.is_null(False)).count()
    )

    data = {
        "total_incidents": total_incidents,
        "total_active_incidents": total_active_incidents,
        "total_resolved_incidents": total_resolved_incidents,
        "lcwc_version": get_lcwc_version(),
    }

    return ResponseModel(status=True, data=data)


@router.get("/incidents/active")
async def incidents(
    category: str = None,
    description: str = None,
    intersection: str = None,
    municipality: str = None,
):
    """Returns a list of active incidents"""

    incidents = Incident.select().join(Unit).where(Incident.resolved_at.is_null())

    if category:
        incidents = incidents.where(Incident.category == category)
    if description:
        incidents = incidents.where(Incident.description.contains(description))
    if intersection:
        incidents = incidents.where(Incident.intersection.contains(intersection))
    if municipality:
        incidents = incidents.where(Incident.municipality.contains(municipality))

    incidents.order_by(Incident.dispatched_at.desc())

    data = {
        "count": len(incidents),
        "incidents": [model_to_dict(item, backrefs=True) for item in incidents],
    }

    return ResponseModel(status=True, data=data)


@router.get("/incidents/by-date-range/{start}/{end}")
async def incident(start: datetime.date, end: datetime.date):
    # list(Event.select().where(fn.date_trunc('day', Event.event_date) == event_date_dt))
    # incidents = IncidentModel.select().where(IncidentModel.category == IncidentCategory.FIRE)
    # (fn.date('day', Incident.dispacted_at) == date
    incidents = (
        Incident.select()
        .where(Incident.dispatched_at.between(start, end))
        .order_by(Incident.dispatched_at.desc())
    )

    data = {
        "count": len(incidents),
        "incidents": [model_to_dict(item) for item in incidents],
    }

    return ResponseModel(status=True, data=data)


@router.get("/incident/id/{id}")
async def incident(id: int):
    try:
        incident = Incident.get_by_id(int)
    except Incident.DoesNotExist:
        raise HTTPException(
            status_code=404, detail=f"Incident with {id=} does not exist."
        )
    return ResponseModel(status=True, data=model_to_dict(incident))


@router.get("/incidents/related/{id}")
async def incident(id: int):
    incidents = Incident.select().where(
        Incident.intersection
        == (Incident.select(Incident.intersection).where(Incident.id == id))
    )

    incidents.order_by(Incident.dispatched_at.desc())

    data = {
        "intersection": incidents[0].intersection,
        "count": len(incidents),
        "incidents": [model_to_dict(item) for item in incidents],
    }

    return ResponseModel(status=True, data=data)
