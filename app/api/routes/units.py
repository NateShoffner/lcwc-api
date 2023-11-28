import datetime
import logging
import os
from fastapi.encoders import jsonable_encoder
from lcwc.category import IncidentCategory
from typing import Optional
from fastapi import APIRouter, HTTPException
from playhouse.shortcuts import model_to_dict
from peewee import fn
from pydantic import BaseModel
from app.api.models.incident import Incident
from app.database.models.agency import Agency
from fastapi_cache.decorator import cache

units_router = APIRouter(
    prefix="/units",
    tags=["units"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)

@units_router.get("/info/{name}")
@cache(expire=os.getenv("CACHE_UNITS_EXPIRE"))
async def unit_info(name: str):
    """Gets unit information for the Unit via its shortname """

    from lcwc.utils.unitparser import UnitParser
    u = UnitParser.parse_unit(name, IncidentCategory.MEDICAL)
    u = jsonable_encoder(u)
    return u
    