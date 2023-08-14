import datetime
from typing import Optional
import uuid

from pydantic import BaseModel


class Unit(BaseModel):
    id: uuid.UUID
    name: Optional[str]
    short_name: str
    added_at: datetime.datetime
    removed_at: Optional[datetime.datetime]
    last_seen: datetime.datetime
    automatically_removed: bool
