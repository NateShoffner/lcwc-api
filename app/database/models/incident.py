import datetime
import uuid

from peewee import *

from app.database.models import BaseModel


class Incident(BaseModel):
    id = UUIDField(primary_key=True, default=uuid.uuid4)

    # Incident data
    category = CharField()
    description = CharField()
    intersection = CharField(null=True)
    municipality = CharField()
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
