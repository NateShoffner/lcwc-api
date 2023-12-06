import logging
import os
import aiohttp
import time
import datetime
import peewee
from app.database.models.feed_request import FeedRequest
from app.database.models.unit import Unit as UnitModel
from lcwc.arcgis import ArcGISClient as Client, ArcGISIncident as Incident
from app.utils.info import get_lcwc_dist
from app.database.models.incident import Incident as IncidentModel

""" Updates the list of active incidents from the LCWC feed """


class IncidentUpdater:
    def __init__(self, db: peewee.Database):
        """Initializes the incident updater

        Args:
            db (peewee.Database): The database connection
        """

        self.db = db
        self.incident_client = Client()
        self.cached_incidents = {}
        self.logger = logging.getLogger(__name__)

        self.parser_name = f"{self.incident_client.name} v{get_lcwc_dist().version}"

    def __log_incident(self, incident: Incident, tag: str = None):
        """Logs an incident to the logger/console"""

        prefix = ""
        if tag is not None:
            prefix = f"{tag} "

        self.logger.info(
            f"{prefix}{incident.category} incident #{incident.number} at {incident.intersection} in {incident.municipality} for {incident.description}"
        )

    def process_live_incidents(self, incidents: list[Incident]):
        """Processes live incidents and compares them against the database, updating when needed"""
        with self.db.atomic():
            # TODO get modified incidents and log out the changes
            
            for incident in incidents:
                try:
                    incident_query = IncidentModel.insert(
                        {
                            IncidentModel.category: incident.category,
                            IncidentModel.description: incident.description,
                            IncidentModel.intersection: incident.intersection,
                            IncidentModel.municipality: incident.municipality,
                            IncidentModel.dispatched_at: incident.date,
                            IncidentModel.number: incident.number,
                            IncidentModel.priority: incident.priority,
                            IncidentModel.agency: incident.agency,
                            IncidentModel.added_at: datetime.datetime.utcnow(),
                            IncidentModel.client: self.parser_name,
                            IncidentModel.latitude: incident.coordinates.latitude,
                            IncidentModel.longitude: incident.coordinates.longitude,
                        }
                    ).on_conflict(
                        conflict_target=[IncidentModel.number],
                        update={
                            IncidentModel.category: incident.category,
                            IncidentModel.description: incident.description,
                            IncidentModel.intersection: incident.intersection,
                            IncidentModel.municipality: incident.municipality,
                            IncidentModel.priority: incident.priority,
                            IncidentModel.updated_at: datetime.datetime.utcnow(),
                            # TODO allow incidents to be re-activated until upstream issue is resolved
                            # involving gaps in incident resolution
                            IncidentModel.resolved_at: None,
                            IncidentModel.automatically_resolved: False,
                        },
                    )

                    res = incident_query.execute()
                except Exception as e:
                    self.logger.error(f"Error adding incident to db: {e}")

                db_incident = IncidentModel.get(IncidentModel.number == incident.number)

                try:
                    for unit in incident.units:
                        r = (
                            UnitModel.insert(
                                incident=db_incident,
                                short_name=unit.full_name,
                                added_at=datetime.datetime.utcnow(),
                                last_seen=datetime.datetime.utcnow(),
                            )
                            .on_conflict(
                                conflict_target=[
                                    UnitModel.incident,
                                    UnitModel.short_name,
                                ],
                                update={
                                    UnitModel.last_seen: datetime.datetime.utcnow(),
                                },
                            )
                            .execute()
                        )

                except Exception as e:
                    self.logger.error(f"Error adding unit to db: {e}")

            try:
                # select all recently unresolved incidents
                active_numbers = (
                    IncidentModel.select(IncidentModel.number)
                    .where(
                        IncidentModel.resolved_at.is_null(),
                        IncidentModel.updated_at
                        < datetime.datetime.utcnow()
                        - datetime.timedelta(
                            minutes=int(os.getenv("ACTIVE_INCIDENT_RESOLVER_MIN"))
                        ),
                        IncidentModel.updated_at
                        > datetime.datetime.utcnow()
                        - datetime.timedelta(
                            minutes=int(os.getenv("ACTIVE_INCIDENT_RESOLVER_MAX"))
                        ),
                    )
                    .dicts()
                )

                self.logger.info(
                    f"Found {len(active_numbers)} incidents to resolve that are older than {os.getenv('ACTIVE_INCIDENT_RESOLVER_MIN')} minutes but not older than {os.getenv('ACTIVE_INCIDENT_RESOLVER_MAX')} minutes"
                )

                # mark them as resolved
                resolved = (
                    IncidentModel.update(
                        resolved_at=datetime.datetime.utcnow(),
                        automatically_resolved=True,
                    )
                    .where(IncidentModel.number.in_(active_numbers))
                    .execute()
                )

                self.logger.info(f"Resolved {resolved} incidents")

            except Exception as e:
                self.logger.error(f"Error resolving incidents: {e}")

    async def get_incidents(self) -> list[Incident]:
        """Fetches the incidents from the LCWC feed"""
        live_incidents = []
        success = False

        async with aiohttp.ClientSession() as session:
            fetch_start = time.perf_counter()
            try:
                live_incidents = await self.incident_client.get_incidents(
                    session, throw_on_error=True
                )
                fetch_end = time.perf_counter()
                self.logger.info(
                    f"Found {len(live_incidents)} live incidents in {fetch_end - fetch_start:0.2f} seconds via {self.parser_name}"
                )
                success = True
            except Exception as e:
                self.logger.error(f"Error fetching incidents: {e}")
                return

        self.log_request(success, fetch_end - fetch_start, len(live_incidents))

        return live_incidents

    async def update_incidents(self) -> None:
        self.logger.info("Updating incidents...")

        live_incidents = await self.get_incidents()
        if live_incidents is None:
            self.logger.error(
                "All sequential attempts to get incidents failed, skipping..."
            )
            return

        self.process_live_incidents(live_incidents)

    def log_request(
        self, success: bool, execution_time: float, incidents: int, msg: str = None
    ) -> FeedRequest:
        """Logs a feed request to the database"""
        fr = FeedRequest.create(
            execution_time=execution_time,
            success=success,
            incidents=incidents,
            parser=self.parser_name,
            msg=msg,
        )

        return fr
