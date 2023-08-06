import datetime
from app.api.models import BaseModel
from app.api.models.incident import Incident
from peewee import *


class Unit(BaseModel):
    incident = ForeignKeyField(Incident, backref="units")
    name = CharField()
    short_name = CharField(null=True)
    added_at = DateTimeField(default=datetime.datetime.utcnow())
    removed_at = DateTimeField(null=True)
    last_seen = DateTimeField()

    class Meta:
        table_name = "units"
