from distutils.util import strtobool
import logging
import os
import aioredis
from fastapi_cache import FastAPICache
import redis
import uvicorn
from datetime import timedelta
from app.database.models.feed_request import FeedRequest
from app.middleware import ProcessTimeHeaderMiddleware
from app.database.models import database_proxy
from app.database.models.incident import Incident as IncidentModel
from app.database.models.unit import Unit as UnitModel
from app.database.models.agency import Agency as AgencyModel
from app.api.routes import incident, incidents, root, agencies, meta
from app.services.agencyupdater import AgencyUpdater
from app.services.geocoder import IncidentGeocoder
from app.services.incidentresolver import IncidentResolver
from app.services.updater import IncidentUpdater
from app.utils.info import get_lcwc_version
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from peewee import *
from fastapi_cache.backends.redis import RedisBackend

env = load_dotenv(".env")

LOG_DIRECTORY = "logs"

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

if not os.path.exists(LOG_DIRECTORY):
    os.makedirs(LOG_DIRECTORY)

file_logger = logging.handlers.TimedRotatingFileHandler(
    os.path.join(LOG_DIRECTORY, "server.log"), when="midnight"
)
file_logger.setFormatter(logging.Formatter("%(asctime)s %(levelname)-2s %(message)s"))
file_logger.setLevel(logging.DEBUG)
root_logger.addHandler(file_logger)

console_logger = logging.StreamHandler()
console_logger.setLevel(logging.INFO)
console_logger.setFormatter(
    logging.Formatter(
        "%(asctime)s %(levelname)-2s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
)
root_logger.addHandler(console_logger)

root_logger.info("Connecting to database...")

sqlite_db = os.getenv("SQLITE_DB")

if sqlite_db:
    database = SqliteDatabase(sqlite_db)
else:
    database = MySQLDatabase(
        os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
    )

database_proxy.initialize(database)
database.connect()
database.create_tables([IncidentModel, UnitModel, AgencyModel, FeedRequest])


redis_client = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"))

app = FastAPI(
    description="LCWC API",
    title="LCWC API",
    version="0.0.1",
    docs_url="/api/v1/docs",
    contact={
        "name": "Nate Shoffner",
        "url": "https://nateshoffner.com",
        "email": "nate.shoffner@gmail.com",
    },
)

# TODO shove CORS into config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ProcessTimeHeaderMiddleware)

app.include_router(root.router, include_in_schema=False)
app.include_router(meta.router, prefix="/api/v1")
app.include_router(incidents.router, prefix="/api/v1")
app.include_router(incident.router, prefix="/api/v1")
app.include_router(agencies.agency_router, prefix="/api/v1")

root_logger.info("Starting LCWC API...")
root_logger.info("Database: %s", database.database)

root_logger.info("lcwc version: %s", get_lcwc_version())

geocoder = IncidentGeocoder(os.getenv("GOOGLE_MAPS_API_KEY"), redis_client)

# incident updater

updater = IncidentUpdater(
    database,
    redis_client,
    geocoder,
    strtobool(os.getenv("GEOCODING_ENABLED")),
)


@app.on_event("startup")
@repeat_every(
    seconds=timedelta(seconds=int(os.getenv("LCWC_UPDATE_INTERVAL"))).total_seconds()
)
async def update_repeater():
    await updater.update_incidents()


# agency updater

agency_updater = AgencyUpdater(database, redis_client)


@app.on_event("startup")
@repeat_every(
    seconds=timedelta(
        hours=int(os.getenv("LCWC_AGENCY_UPDATE_INTERVAL"))
    ).total_seconds()
)
async def update_repeater():
    await agency_updater.update_agencies()


# automatic incident resolver
if strtobool(os.getenv("INCIDENT_RESOLVER_ENABLED")):
    resolver = IncidentResolver(
        timedelta(minutes=int(os.getenv("INCIDENT_RESOLVER_THRESHOLD"))),
    )

    @app.on_event("startup")
    @repeat_every(
        seconds=timedelta(
            hours=int(os.getenv("INCIDENT_RESOLVER_INTERVAL"))
        ).total_seconds()
    )
    async def update_repeater():
        await resolver.resolve_hanging_incidents()


@app.on_event("startup")
async def startup():
    redis = aioredis.from_url(
        f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}"
    )
    FastAPICache.init(RedisBackend(redis), prefix=os.getenv("CACHE_REDIS_KEY"))


if __name__ == "__main__":
    uvicorn.run(app, host=os.getenv("HOSTNAME"), port=int(os.getenv("PORT")))
