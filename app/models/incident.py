import datetime
from app.models import BaseModel
from peewee import *

class Incident(BaseModel):
    guid = CharField(primary_key=True)
    category = CharField()
    description = CharField()
    intersection = CharField(null=True)
    township = CharField()
    dispatched_at = DateTimeField()
    added_at = DateTimeField()
    updated_at = DateTimeField(default=datetime.datetime.utcnow())
    resolved_at = DateTimeField(null=True)
    automatically_resolved = BooleanField(default=False)

    class Meta:
        table_name = 'incidents'