import datetime
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from app.models.incident import Incident
from app.utils.logging import get_custom_logger

""" Prunes unresolved incidents after an extended period of time from the database """
class IncidentResolver:

    logger = get_custom_logger('lcwc-resolver')

    def __init__(self, app: FastAPI, prune_interval: datetime.timedelta, resolution_threshold: datetime.timedelta):
        """ Initializes the incident resolver
        
        Args:
            app (FastAPI): The FastAPI application
            prune_interval (datetime.timedelta): The interval at which to prune incidents
            resolution_threshold (datetime.timedelta): The threshold at which to prune incidents
        """

        self.app = app
        self.resolution_threshold = resolution_threshold

        @app.on_event("startup")
        @repeat_every(seconds=prune_interval.total_seconds())
        def prune_repeater():
            self.prune_unresolved_incidents()     

    def prune_unresolved_incidents(self):
        now = datetime.datetime.utcnow()
        then = now - self.resolution_threshold
        self.logger.info(f'Pruning unresolved incidents older than {then}')

        try:
            q = Incident.update(
                {
                    Incident.resolved_at: datetime.datetime.utcnow(),
                    Incident.automatically_resolved: True
                }
            ).where(Incident.resolved_at == None, Incident.updated_at <= then)
        
            r = q.execute()    
            self.logger.info(f'Resolved {r} previously unresolved incidents')

        except Exception as e:
            self.logger.error(f'Failed to resolve unresolved incidents: {e}')