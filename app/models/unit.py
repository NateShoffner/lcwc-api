import datetime
from app.models import BaseModel
from app.models.incident import Incident
from peewee import *


class Unit(BaseModel):
    incident = ForeignKeyField(Incident, backref="units")
    name = CharField()
    added_at = DateTimeField(default=datetime.datetime.utcnow())
    removed_at = DateTimeField()

    class Meta:
        table_name = "units"
