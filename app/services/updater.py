import logging
import aiohttp
import time
import datetime
import peewee
import redis
from app.api.models.unit import Unit as UnitModel
from app.services.geocoder import IncidentGeocoder
from lcwc.arcgis import ArcGISClient as Client, ArcGISIncident as Incident
from app.utils.info import get_lcwc_dist
from app.api.models.incident import Incident as IncidentModel

""" Updates the list of active incidents from the LCWC feed """


class IncidentUpdater:
    def __init__(
        self,
        db: peewee.Database,
        redis: redis.Redis,
        geocoder: IncidentGeocoder,
        use_geocoder: bool = False,
    ):
        """Initializes the incident updater

        Args:
            db (peewee.Database): The database connection
            redis (redis.Redis): The redis connection
            geocoder (IncidentGeocoder): The geocoder to use
            use_geocoder (bool, optional): Whether or not to use the geocoder. Defaults to False.
        """

        self.db = db
        self.redis = redis
        self.geocoder = geocoder
        self.use_geocoder = use_geocoder
        self.incident_client = Client()
        self.cached_incidents = {}
        self.last_update = None
        self.logger = logging.getLogger(__name__)

        # TODO initialize cached incidents from redis

        self.parser_name = f"{self.incident_client.name} v{get_lcwc_dist().version}"

        self.update_count = 0

    @property
    def last_updated(self) -> datetime.datetime:
        return self.last_update

    def __process_incidents(self, incidents: list[Incident]):
        """Processes the incidents by organizing them and their respective units"""

        active_ids = [x.number for x in incidents]

        # organize incidents into new, known, and resolved when compared to the cached incidents
        resolved_incidents = [
            x for x in self.cached_incidents.values() if x.number not in active_ids
        ]

        known_incidents = [x for x in incidents if x.number in self.cached_incidents]
        new_incidents = [x for x in incidents if x.number not in self.cached_incidents]

        # track units that have been assigned and unassigned, keyed by incident number
        newly_assigned_units = {}
        unassigned_units = {}
        persisted_units = {}

        # check all the known incidents and see what units have been assigned and unassigned
        for incident in known_incidents:
            cached_incident = self.cached_incidents[incident.number]

            # check for newly assigned units
            for unit in incident.units:
                if unit not in cached_incident.units:
                    newly_assigned_units.setdefault(incident.number, []).append(unit)
                    self.logger.info(
                        f"Unit {unit} assigned to incident {incident.number}"
                    )
                else:  # unit has persisted
                    persisted_units.setdefault(incident.number, []).append(unit)

            # check for unassigned units
            for unit in cached_incident.units:
                if unit not in incident.units:
                    unassigned_units.setdefault(incident.number, []).append(unit)
                    self.logger.info(
                        f"Unit {unit} unassigned from incident {incident.number}"
                    )

        # custom geocoding
        if self.use_geocoder:
            self.logger.info("Geocoding new incidents...")
            geocode_count = 0
            geocode_start = time.perf_counter()
            for incident in new_incidents:
                coords = self.geocoder.get_coordinates(incident)
                if coords is not None:
                    # TODO set this properly
                    incident._coordinates = coords
                    geocode_count += 1
            geocode_end = time.perf_counter()
            self.logger.info(
                f"Geocoded {geocode_count} incidents in {geocode_end - geocode_start:0.2f} seconds"
            )

        if (
            len(new_incidents) > 0
            or len(resolved_incidents) > 0
            or len(known_incidents) > 0
        ):
            self.logger.info(
                f"New: {len(new_incidents)} | Known: {len(known_incidents)} | Resolved: {len(resolved_incidents)}"
            )

        total_assigned = 0
        total_unassigned = 0
        total_persisted = 0

        for units in newly_assigned_units.values():
            total_assigned = total_assigned + len(units)
        for units in unassigned_units.values():
            total_unassigned = total_unassigned + len(units)
        for units in persisted_units.values():
            total_persisted = total_persisted + len(units)

        self.logger.info(
            f"Units Assigned: {total_assigned} | Units Unassigned: {total_unassigned} | Units Persisted: {total_persisted}"
        )
        self.cached_incidents = {x.number: x for x in incidents}
        self.save_incidents(incidents, resolved_incidents)

        self.update_units(newly_assigned_units, True)
        self.update_units(unassigned_units, False)

    async def update_incidents(self) -> None:
        self.logger.info("Updating incidents...")

        live_incidents = []

        async with aiohttp.ClientSession() as session:
            fetch_start = time.perf_counter()
            try:
                live_incidents = await self.incident_client.get_incidents(session)
                fetch_end = time.perf_counter()
                self.logger.info(
                    f"Found {len(live_incidents)} live incidents in {fetch_end - fetch_start:0.2f} seconds via {self.parser_name}"
                )
            except Exception as e:
                self.logger.error(f"Error fetching incidents: {e}")
                return

        self.update_count += 1

        self.last_update = datetime.datetime.utcnow()
        self.__process_incidents(live_incidents)

    def update_units(self, units_dict: dict[int, list[str]], assigned: bool):
        if assigned:
            print("Saving assigned units...")
            with self.db.atomic():
                for incident_number, units in units_dict.items():
                    print(f"Getting incident {incident_number}...")

                    incident = IncidentModel.get(
                        IncidentModel.number == incident_number
                    )

                    print(f"Saving units for incident {incident_number}...")

                    for unit in units:
                        try:
                            UnitModel.create(
                                incident=incident,
                                name=unit,
                                added_at=datetime.datetime.utcnow(),
                            )
                        except Exception as e:
                            self.logger.error(f"Error saving unit {unit}: {e}")

        else:
            with self.db.atomic():
                for incident_number, units in units_dict.items():
                    incident = IncidentModel.get(
                        IncidentModel.number == incident_number
                    )
                    for unit in units:
                        query = UnitModel.update(
                            removed_at=datetime.datetime.utcnow()
                        ).where(UnitModel.name == unit)
                        query.execute()

    def save_incidents(
        self, incidents: list[Incident], resolved_incidents: list[Incident]
    ):
        with self.db.atomic():
            for incident in incidents:
                try:
                    query = IncidentModel.insert(
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
                        },
                    )

                    r = query.execute()
                    self.logger.debug(f"Inserted incident {incident.number}")
                except Exception as e:
                    self.logger.error(query.sql())
                    self.logger.error(e)

        with self.db.atomic():
            self.logger.info(
                f"Marking {len(resolved_incidents)} incidents as resolved..."
            )
            for incident in resolved_incidents:
                try:
                    query = IncidentModel.update(
                        resolved_at=datetime.datetime.utcnow()
                    ).where(IncidentModel.number == incident.number)
                    r = query.execute()
                    self.logger.debug(f"Resolved incident {incident.number} ({r})")
                except Exception as e:
                    self.logger.error(
                        f"Error resolving incident {incident.number}: {e}"
                    )
