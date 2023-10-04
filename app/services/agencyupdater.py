import logging
import aiohttp
import time
import datetime
import peewee
import redis

from lcwc.category import IncidentCategory
from app.database.models.agency import Agency as AgencyModel
from lcwc.agencies.agencyclient import AgencyClient


class AgencyUpdater:
    """Updates the agency list from the LCWC website"""

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
                categories = [
                    IncidentCategory.FIRE,
                    IncidentCategory.MEDICAL,
                    IncidentCategory.TRAFFIC,
                ]
                agencies = await self.agency_client.get_agencies(session, categories)
                fetch_end = time.perf_counter()
                self.logger.info(
                    f"Found {len(agencies)} live agencies in {fetch_end - fetch_start:0.2f} seconds"
                )
            except Exception as e:
                self.logger.error(f"Error fetching agencies: {e}")
                return

        try:
            with self.db.atomic():
                for agency in agencies:
                    r = (
                        AgencyModel.insert(
                            category=agency.category,
                            station_id=agency.station_number,
                            name=agency.name,
                            url=agency.url,
                            address=agency.address,
                            city=agency.city,
                            state=agency.state,
                            zip_code=agency.zip_code,
                            phone=agency.phone,
                        )
                        .on_conflict(
                            conflict_target=[
                                AgencyModel.category,
                                AgencyModel.station_id,
                            ],
                            update={
                                AgencyModel.name: agency.name,
                                AgencyModel.url: agency.url,
                                AgencyModel.address: agency.address,
                                AgencyModel.city: agency.city,
                                AgencyModel.state: agency.state,
                                AgencyModel.zip_code: agency.zip_code,
                                AgencyModel.phone: agency.phone,
                                AgencyModel.updated_at: datetime.datetime.utcnow(),
                            },
                        )
                        .execute()
                    )

        except Exception as e:
            self.logger.error(f"Error saving agencies: {e}")
            return

        self.update_count += 1
        self.last_update = datetime.datetime.utcnow()
