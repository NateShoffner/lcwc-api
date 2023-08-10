import datetime
import uuid
from app.api.models import BaseModel
from app.api.models.incident import Incident
from peewee import *


class Unit(BaseModel):
    id = UUIDField(default=uuid.uuid4)
    incident = ForeignKeyField(Incident, backref="units")
    name = CharField(null=True)
    short_name = CharField()  # ArcGIS uses shorthand names for units
    added_at = DateTimeField(default=datetime.datetime.utcnow())
    removed_at = DateTimeField(null=True)
    last_seen = DateTimeField()
    automatically_removed = BooleanField(default=False)

    class Meta:
        table_name = "units"
        primary_key = CompositeKey("incident", "short_name")
