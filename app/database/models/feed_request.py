

import datetime
import uuid
from app.database.models import BaseModel
from peewee import *

class FeedRequest(BaseModel):
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    date = DateTimeField(default=datetime.datetime.utcnow())
    execution_time = FloatField(null=True)
    success = BooleanField(default=False)
    parser = CharField(null=True)
    incidents: IntegerField(null=True)
    msg = CharField(null=True)