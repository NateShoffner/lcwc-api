import datetime
import uuid

from pydantic import BaseModel
from lcwc.category import IncidentCategory
from app.database.models.agency import Agency


class Agency(BaseModel):
    id: uuid.UUID
    category: IncidentCategory
    station_id: str
    name: str
    url: str
    address: str
    city: str
    state: str
    zip_code: str
    phone: str
    updated_at: datetime.datetime

    @staticmethod
    def from_db_model(agency: Agency):
        return Agency(
            id=agency.id,
            category=agency.category,
            station_id=agency.station_id,
            name=agency.name,
            url=agency.url,
            address=agency.address,
            city=agency.city,
            state=agency.state,
            zip_code=agency.zip_code,
            phone=agency.phone,
            updated_at=agency.updated_at,
        )


class AgencyResponse(BaseModel):
    data: Agency


class AgenciesResponse(BaseModel):
    count: int
    data: list[Agency]
    # TODO pagination
