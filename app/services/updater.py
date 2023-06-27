import logging
import aiohttp
import time
import datetime
import fastapi
import peewee
from fastapi_utils.tasks import repeat_every
from lcwc.category import IncidentCategory
from lcwc.arcgis import Client, Incident
from app.utils.info import get_lcwc_dist, get_lcwc_version
from app.models.incident import Incident

""" Updates the list of active incidents from the LCWC feed """


class IncidentUpdater:
    def __init__(
        self,
        app: fastapi.FastAPI,
        db: peewee.Database,
        update_interval: datetime.timedelta,
    ):
        """Initializes the incident updater

        Args:
            app (FastAPI): The FastAPI application
            db (peewee.Database): The database connection
            update_interval (datetime.timedelta): The interval at which to update incidents
        """

        self.app = app
        self.db = db
        self.incident_client = Client()
        self.active_incidents = {}
        self.last_update = None
        self.logger = logging.getLogger(__name__)

        @app.on_event("startup")
        @repeat_every(seconds=update_interval.total_seconds())
        async def update_repeater():
            await self.update_incidents()

    @property
    def last_updated(self) -> datetime.datetime:
        return self.last_update

    async def update_incidents(self) -> None:
        self.logger.info("Updating incidents...")

        live_incidents = []

        lcwc_dist = get_lcwc_dist()

        # TODO properly identify client handler
        client_str = f"python-lcwc-arcgis-{lcwc_dist.version}"

        async with aiohttp.ClientSession() as session:
            fetch_start = time.perf_counter()
            try:
                live_incidents = await self.incident_client.get_incidents(session)
                fetch_end = time.perf_counter()
                self.logger.info(
                    f"Found {len(live_incidents)} live incidents in {fetch_end - fetch_start:0.2f} seconds via {client_str}"
                )
            except Exception as e:
                self.logger.error(f"Error fetching incidents: {e}")
                return

        # organize the incidents into known, new, and resolved
        resolved_incidents = []
        known_incidents = []
        new_incidents = []

        for incident in live_incidents:
            if incident.number in self.active_incidents:
                known_incidents.append(incident)
            else:
                new_incidents.append(incident)

            if incident.category == IncidentCategory.UNKNOWN:
                self.logger.warning(
                    f"Unknown incident: {incident.number} - {incident.description} - {incident.intersection} - {incident.township} - {incident.date} - {incident.units}"
                )

        # compare the live incidents to the active incidents and find the ones that are resolved
        self.logger.debug("Checking for resolved incidents...")

        # we're going to track the units that are unassigned from existing incidents
        unassigned_units = {}

        try:
            for number, incident in self.active_incidents.items():
                existing_incident = next(
                    (x for x in live_incidents if x.number == number), None
                )

                if existing_incident is None:
                    resolved_incidents.append(incident)
                else:
                    # check for unassigned units
                    for unit in existing_incident.units:
                        if unit not in incident.units:
                            unassigned_units.setdefault(number, []).append(unit)
                            self.logger.info(
                                f"Unit {unit} unassigned from incident {number}"
                            )

        except Exception as e:
            self.logger.error(e)

        self.logger.info(
            f"New: {len(new_incidents)} | Known: {len(known_incidents)} | Resolved: {len(resolved_incidents)}"
        )

        with self.db.atomic():
            for incident in live_incidents:
                try:
                    query = Incident.insert(
                        {
                            Incident.category: incident.category,
                            Incident.description: incident.description,
                            Incident.intersection: incident.intersection,
                            Incident.township: incident.township,
                            Incident.dispatched_at: incident.date,
                            Incident.number: incident.number,
                            Incident.priority: incident.priority,
                            Incident.agency: incident.agency,
                            Incident.added_at: datetime.datetime.utcnow(),
                            Incident.client: client_str,

                            Incident.latitude: incident.coordinates.latitude,
                            Incident.longitude: incident.coordinates.longitude,
                        }
                    ).on_conflict(
                        update={
                            Incident.category: incident.category,
                            Incident.description: incident.description,
                            Incident.intersection: incident.intersection,
                            Incident.township: incident.township,
                            Incident.updated_at: datetime.datetime.utcnow(),
                        }
                    )
                    r = query.execute()
                except Exception as e:
                    self.logger.error(e)

                try:
                    r = query.execute()
                except Exception as e:
                    self.logger.error(query.sql())
                    self.logger.error(e)
        """
        # mark de-listed incidents as resolved
        for incident in resolved_incidents:
            (Incident
            .update(resolved_at=datetime.datetime.utcnow())
            .where(Incident.guid == incident.guid)
            .execute()
        )

        # update the units
        for guid, units in unassigned_units.items():
            for unit in units:
                (Incident
                .update(removed_at=datetime.datetime.utcnow())
                .where(Incident.guid == guid)
                .execute()
            )
        """

        self.active_incidents = {x.number: x for x in live_incidents}
        self.last_update = datetime.datetime.utcnow()
        # add

        # units_data = [(incident.guid, unit) for unit in incident.units]
        # UnitModel().insert_many(units_data).execute()

        # TODO mark old incidents as resolved
        # query = Incident.select().bulk_update(resolved=datetime.datetime.now()).where(Incident.resolved.is_null() and Incident.guid not in active_ids)

        # clean up residual units
