import datetime
import logging
from app.api.models.incident import Incident

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
        then = now - self.resolution_threshold
        self.logger.info(f"Pruning unresolved incidents older than {then}")

        try:
            q = Incident.update(
                {
                    Incident.resolved_at: datetime.datetime.utcnow(),
                    Incident.automatically_resolved: True,
                }
            ).where(
                (Incident.resolved_at.is_null(True)) & (Incident.updated_at <= then)
            )

            r = q.execute()
            self.logger.info(f"Resolved {r} previously unresolved incident(s)")

        except Exception as e:
            self.logger.error(f"Failed to resolve unresolved incidents: {e}")
