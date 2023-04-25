import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from playhouse.shortcuts import model_to_dict
from peewee import fn
from pydantic import BaseModel
from app.utils.info import get_lcwc_version
from app.utils.logging import get_custom_logger
from app.models.incident import Incident
from app.models.unit import Unit

router = APIRouter()

logger = get_custom_logger('lcwc-api')

class ResponseModel(BaseModel):
    message: str
    data: Optional[dict] = None

@router.get("/stats")
async def stats():

    """ Returns various statistics about the API """

    total_incidents = Incident.select().count()
    total_active_incidents = Incident.select().where(Incident.resolved_at.is_null()).count()
    total_resolved_incidents = Incident.select().where(Incident.resolved_at.is_null(False)).count()

    data = {
        'total_incidents': total_incidents,
        'total_active_incidents': total_active_incidents,
        'total_resolved_incidents': total_resolved_incidents,
        'lcwc_version': get_lcwc_version(),
    }

    return ResponseModel(status=True, message='Success', data=data)

@router.get("/incidents")
async def incidents(
    guid: str = None,
    category: str = None,
    description: str = None,
    intersection: str = None,
    township: str = None,
    dispacted_at: datetime.date = None,
    show_related: bool = False):

    """ Returns a list of active incidents """

    incidents = Incident.select().where(Incident.resolved_at.is_null())
    
    if guid:
        incidents = incidents.where(Incident.guid == guid)
    if category:
        incidents = incidents.where(Incident.category == category)
    if description:
        incidents = incidents.where(Incident.description.contains(description))
    if intersection:
        incidents = incidents.where(Incident.intersection.contains(intersection))
    if township:
        incidents = incidents.where(Incident.township.contains(township))
    if dispacted_at:
        incidents = incidents.where(Incident.dispatched_at == dispacted_at)
    
    incidents.order_by(Incident.dispatched_at.desc())

    data = {
        'count': len(incidents),
        'incidents': [model_to_dict(item) for item in incidents]
    }

    return ResponseModel(status=True, message='Success', data=data)

@router.get("/incidents/by-date-range/{start}/{end}")
async def incident(start: datetime.date, end: datetime.date):

    #list(Event.select().where(fn.date_trunc('day', Event.event_date) == event_date_dt))
    #incidents = IncidentModel.select().where(IncidentModel.category == IncidentCategory.FIRE)
    #(fn.date('day', Incident.dispacted_at) == date
    incidents = Incident.select().where(Incident.dispatched_at.between(start, end)).order_by(Incident.dispatched_at.desc())

    data = {
        'count': len(incidents),
        'incidents': [model_to_dict(item) for item in incidents]
    }

    return ResponseModel(status=True, message='Success', data=data)

@router.get("/incident/id/{guid}")
async def incident(guid: str):
    try:
        incident = Incident.get_by_id(guid)
    except Incident.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Incident with {guid=} does not exist.")
    return ResponseModel(status=True, message='Success', data=model_to_dict(incident))

@router.get("/incidents/related/{guid}")
async def incident(guid: str):
    #SELECT * FROM incidents WHERE intersection = (SELECT intersection FROM incidents WHERE guid = '862dafa5-9714-4af1-91d9-bf70f066fe91')

    incidents = Incident.select().where(Incident.intersection == (Incident.select(Incident.intersection).where(Incident.guid == guid)))

    incidents.order_by(Incident.dispatched_at.desc())

    data = {
        'intersection': incidents[0].intersection,
        'count': len(incidents),
        'incidents': [model_to_dict(item) for item in incidents]
    }

    return ResponseModel(status=True, message='Success', data=data)

