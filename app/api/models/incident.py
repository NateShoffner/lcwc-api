import datetime
from app.api.models import BaseModel
from peewee import *


class Incident(BaseModel):
    # Incident data
    category = CharField()
    description = CharField()
    intersection = CharField(null=True)
    township = CharField()
    dispatched_at = DateTimeField()
    number = IntegerField(unique=True)
    priority = IntegerField(null=True)
    agency = CharField()

    # coordinates
    # TODO Use Point data type
    latitude = DecimalField(null=True)
    longitude = DecimalField(null=True)

    # meta data
    added_at = DateTimeField()
    updated_at = DateTimeField(default=datetime.datetime.utcnow())
    resolved_at = DateTimeField(null=True)

    client = CharField(null=True)
    automatically_resolved = BooleanField(default=False)

    class Meta:
        table_name = "incidents"
