import datetime
import logging
from lcwc.category import IncidentCategory
from typing import Optional
from fastapi import APIRouter, HTTPException
from playhouse.shortcuts import model_to_dict
from peewee import fn
from pydantic import BaseModel
from app.models.agency import Agency

agency_router = APIRouter(
    prefix="/agency",
    tags=["agency"],
    responses={404: {"description": "Not found"}},
)

agencies_router = APIRouter(
    prefix="/agencies",
    tags=["agencies"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)


@agencies_router.get("/{category}")
async def agencies(category: IncidentCategory):
    """Get all agencies for a given category"""

    agencies = []
    try:
        agencies = Agency.select().where(Agency.category == category)
    except Agency.DoesNotExist:
        raise HTTPException(status_code=404, detail="Agencies not found")
    return [model_to_dict(agency) for agency in agencies]


@agency_router.get("/{category}/{id}")
async def agency(category: IncidentCategory, id: str):
    """Get a single agency for a given category and id"""

    agency = None
    try:
        agency = Agency.get(Agency.category == category and Agency.station_id == id)
    except Agency.DoesNotExist:
        raise HTTPException(status_code=404, detail="Agency not found")
    return model_to_dict(agency)
