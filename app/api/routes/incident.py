import datetime
import logging
import os
from typing import Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.api.models.incident import (
    Incident as IncidentOutput,
    IncidentResponse,
)
from app.database.models.incident import Incident
from app.database.models.unit import Unit
from fastapi_cache.decorator import cache

router = APIRouter(
    prefix="/incident",
    tags=["incident"],
    responses={404: {"description": "Incident not found"}},
)

logger = logging.getLogger(__name__)


@router.get("/number/{incident_number}")
@cache(expire=os.getenv("CACHE_INCIDENTS_EXPIRE"))
async def incident(incident_number: int) -> IncidentResponse:
    try:
        incident = Incident.select().where(Incident.number == incident_number).get()
    except Incident.DoesNotExist:
        raise HTTPException(
            status_code=404, detail=f"Incident with {incident_number=} does not exist."
        )
    return IncidentResponse(data=IncidentOutput.from_db_model(incident))


@router.get("/{incident_id}")
@cache(expire=os.getenv("CACHE_INCIDENTS_EXPIRE"))
async def incident(incident_id: str) -> IncidentResponse:
    try:
        incident = Incident.get(incident_id)
    except Incident.DoesNotExist:
        raise HTTPException(
            status_code=404, detail=f"Incident with {incident_id=} does not exist."
        )
    return IncidentResponse(data=IncidentOutput.from_db_model(incident))
