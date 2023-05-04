import uvicorn
from datetime import timedelta
from app.models import database_proxy
from app.models.incident import Incident as IncidentModel
from app.models.unit import Unit as UnitModel
from app.routers import incidents, root
from app.services.incidentresolver import IncidentResolver
from app.services.updater import IncidentUpdater
from app.utils.info import get_lcwc_version
from app.utils.logging import get_custom_logger
from fastapi import FastAPI
from peewee import *

database = MySQLDatabase('lcwc_api', user='lcwc', password='lcwc',
                         host='lcwc_db', port=3306)
database_proxy.initialize(database)
database.connect()
database.create_tables([IncidentModel, UnitModel])

app = FastAPI(
    description= 'LCWC API',
    title='LCWC API',
    version='0.0.1',
    docs_url='/api/v1/docs',
    contact={
        'name': 'Nate Shoffner',
        'url': 'https://nateshoffner.com',
        'email': 'nate.shoffner@Gmail.com'
    }
)

app.include_router(root.router, include_in_schema=False)
app.include_router(incidents.router, prefix='/api/v1')

logger = get_custom_logger('lcwc-service')
logger.info('Starting LCWC API...')
logger.info('Database: %s', database.database)

logger.info('lcwc version: %s', get_lcwc_version())

updater = IncidentUpdater(app, database, timedelta(seconds=10))
pruner = IncidentResolver(app, timedelta(minutes=10), timedelta(hours=12))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8081)