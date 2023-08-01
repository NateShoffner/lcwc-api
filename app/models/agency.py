import datetime
import uuid
from app.models import BaseModel
from peewee import *


class Agency(BaseModel):
    id = UUIDField(default=uuid.uuid4)
    category = CharField()
    station_id = CharField()
    name = CharField()
    url = CharField(null=True)
    address = CharField(null=True)
    city = CharField(null=True)
    state = CharField(null=True)
    zip_code = CharField(null=True)
    phone = CharField(null=True)

    updated_at = DateTimeField(default=datetime.datetime.utcnow())

    class Meta:
        table_name = "agencies"
        primary_key = CompositeKey("category", "station_id")
