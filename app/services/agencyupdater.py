import logging
import aiohttp
import time
import datetime
import fastapi
import peewee
import redis
from fastapi_utils.tasks import repeat_every
from lcwc.category import IncidentCategory
from app.models.unit import Unit as UnitModel
from app.services.geocoder import IncidentGeocoder
from lcwc.agencyclient import AgencyClient
from app.utils.info import get_lcwc_dist, get_lcwc_version
from app.models.incident import Incident as IncidentModel


class AgencyUpdater:
    """ Updates the agency list from the LCWC website """

    def __init__(
        self,
        app: fastapi.FastAPI,
        db: peewee.Database,
        update_interval: datetime.timedelta,
        redis: redis.Redis,
    ):
        self.app = app
        self.db = db
        self.redis = redis
        self.agency_client = AgencyClient()
        self.last_update = None
        self.logger = logging.getLogger(__name__)

        self.update_count = 0

        @app.on_event("startup")
        @repeat_every(seconds=update_interval.total_seconds())
        async def update_repeater():
            await self.update_agencies()

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
