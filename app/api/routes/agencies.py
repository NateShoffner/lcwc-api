import logging
import os
from lcwc.category import IncidentCategory
from typing import Optional
from fastapi import APIRouter, HTTPException
from playhouse.shortcuts import model_to_dict
from app.api.models.agency import AgenciesResponse, Agency as AgencyOutput
from app.database.models.agency import Agency
from fastapi_cache.decorator import cache

agency_router = APIRouter(
    prefix="/agencies",
    tags=["agencies"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)


@agency_router.get("/search")
@cache(expire=os.getenv("CACHE_AGENCIES_EXPIRE"))
async def search_agencies(
    category: Optional[IncidentCategory] = None,
    station_id: Optional[str] = None,
    name: Optional[str] = None,
    url: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None,
    phone: Optional[str] = None,
) -> AgenciesResponse:
    """Search for agencies"""

    agencies = []

    if category:
        agencies = Agency.select().where(Agency.category == category)
    if station_id:
        agencies = Agency.select().where(Agency.station_id == station_id)
    if name:
        agencies = Agency.select().where(Agency.name == name)
    if url:
        agencies = Agency.select().where(Agency.url == url)
    if address:
        agencies = Agency.select().where(Agency.address == address)
    if city:
        agencies = Agency.select().where(Agency.city == city)
    if state:
        agencies = Agency.select().where(Agency.state == state)
    if zip_code:
        agencies = Agency.select().where(Agency.zip_code == zip_code)
    if phone:
        agencies = Agency.select().where(Agency.phone == phone)

    output_agencies = []
    for incident in agencies:
        output_agencies.append(AgencyOutput.from_db_model(incident))
    return AgenciesResponse(count=len(output_agencies), data=output_agencies)


@agency_router.get("/stats")
@cache(expire=os.getenv("CACHE_AGENCIES_EXPIRE"))
async def agency_stats():
    """Get agency stats"""

    stats = {}
    try:
        stats = {
            "total": Agency.select().count(),
            "fire": Agency.select()
            .where(Agency.category == IncidentCategory.FIRE)
            .count(),
            "medical": Agency.select()
            .where(Agency.category == IncidentCategory.MEDICAL)
            .count(),
            "traffic": Agency.select()
            .where(Agency.category == IncidentCategory.TRAFFIC)
            .count(),
        }
    except Agency.DoesNotExist:
        raise HTTPException(status_code=404, detail="Agencies not found")
    return stats


@agency_router.get("/{category}")
@cache(expire=os.getenv("CACHE_AGENCIES_EXPIRE"))
async def agencies(category: IncidentCategory) -> AgenciesResponse:
    """Get all agencies for a given category"""

    agencies = []
    try:
        agencies = Agency.select().where(Agency.category == category)
    except Agency.DoesNotExist:
        raise HTTPException(status_code=404, detail="Agencies not found")

    output_agencies = []
    for incident in agencies:
        output_agencies.append(AgencyOutput.from_db_model(incident))
    return AgenciesResponse(count=len(output_agencies), data=output_agencies)


@agency_router.get("/{category}/{id}")
@cache(expire=os.getenv("CACHE_AGENCIES_EXPIRE"))
async def agency(category: IncidentCategory, id: str):
    """Get a single agency for a given category and ID"""

    agency = None
    try:
        agency = Agency.get(Agency.category == category and Agency.station_id == id)
    except Agency.DoesNotExist:
        raise HTTPException(status_code=404, detail="Agency not found")
    return model_to_dict(agency)
