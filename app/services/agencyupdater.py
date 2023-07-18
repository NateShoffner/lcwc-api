import logging
import aiohttp
import time
import datetime
import peewee
import redis

from lcwc.category import IncidentCategory
from app.models.unit import Unit as UnitModel
from lcwc.agencyclient import AgencyClient
from app.models.incident import Incident as IncidentModel


class AgencyUpdater:
    """ Updates the agency list from the LCWC website """

    def __init__(
        self,
        db: peewee.Database,
        redis: redis.Redis,
    ):
        self.db = db
        self.redis = redis
        self.agency_client = AgencyClient()
        self.last_update = None
        self.logger = logging.getLogger(__name__)

        self.update_count = 0


    @property
    def last_updated(self) -> datetime.datetime:
        return self.last_update
    
    async def update_agencies(self) -> None:
        self.logger.info("Updating agencies...")

        agencies = []

        async with aiohttp.ClientSession() as session:
            fetch_start = time.perf_counter()
            try:
                categories = [IncidentCategory.FIRE, IncidentCategory.MEDICAL, IncidentCategory.TRAFFIC]
                agencies = await self.agency_client.get_agencies(session, categories)
                fetch_end = time.perf_counter()
                self.logger.info(
                    f"Found {len(agencies)} live agencies in {fetch_end - fetch_start:0.2f} seconds"
                )
            except Exception as e:
                self.logger.error(f"Error fetching agencies: {e}")
                return
            
        self.update_count += 1
            
        self.last_update = datetime.datetime.utcnow()
