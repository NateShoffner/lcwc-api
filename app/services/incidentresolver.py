import datetime
import logging
from app.database.models.incident import Incident
from app.database.models.unit import Unit

""" Prunes unresolved incidents after an extended period of time from the database """


class IncidentResolver:
    def __init__(
        self,
        resolution_threshold: datetime.timedelta,
    ):
        """Initializes the incident resolver

        Args:
            resolution_threshold (datetime.timedelta): The threshold at which to prune incidents
        """

        self.resolution_threshold = resolution_threshold
        self.logger = logging.getLogger(__name__)

    def resolve_hanging_incidents(self):
        now = datetime.datetime.utcnow()
        threshold = now - self.resolution_threshold

        self.logger.info(f"Pruning unresolved incidents older than {threshold}")

        try:
            incident_prune = Incident.update(
                {
                    Incident.resolved_at: datetime.datetime.utcnow(),
                    Incident.automatically_resolved: True,
                }
            ).where(
                (Incident.resolved_at.is_null(True))
                & (Incident.updated_at <= threshold)
            )

            print(incident_prune.sql())

            incident_prune_result = incident_prune.execute()

            self.logger.info(
                f"Pruned {incident_prune_result} previously unresolved incident(s)"
            )

            unit_prune_result = (
                Unit.update(
                    {
                        Unit.removed_at: datetime.datetime.utcnow(),
                        Unit.automatically_removed: True,
                    }
                )
                .where((Unit.removed_at.is_null(True)) & (Unit.last_seen <= threshold))
                .execute()
            )

            self.logger.info(
                f"Pruned {unit_prune_result} previously unresolved unit(s)"
            )

        except Exception as e:
            self.logger.error(f"Failed to resolve unresolved incidents: {e}")
