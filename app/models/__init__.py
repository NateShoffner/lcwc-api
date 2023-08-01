import uuid
from peewee import *

database_proxy = DatabaseProxy()


class BaseModel(Model):

    id = UUIDField(primary_key=True, default=uuid.uuid4)

    class Meta:
        database = database_proxy
