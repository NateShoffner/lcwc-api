import logging
import os
import redis
import toml
import uvicorn
from datetime import timedelta
from app.models import database_proxy
from app.models.incident import Incident as IncidentModel
from app.models.unit import Unit as UnitModel
from app.routers import incidents, root
from app.services.geocoder import IncidentGeocoder
from app.services.incidentresolver import IncidentResolver
from app.services.updater import IncidentUpdater
from app.utils.info import get_lcwc_version
from dotenv import dotenv_values
from fastapi import FastAPI
from peewee import *

env = dotenv_values(".env")
config = toml.load("config/config.toml")

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

database = MySQLDatabase(
    env["DB_NAME"],
    user=env["DB_USER"],
    password=env["DB_PASSWORD"],
    host=env["DB_HOST"],
    port=int(env["DB_PORT"]),
)

database_proxy.initialize(database)
database.connect()
database.create_tables([IncidentModel, UnitModel])

redis_client = redis.Redis(host=env["REDIS_HOST"], port=env["REDIS_PORT"])

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

app.include_router(root.router, include_in_schema=False)
app.include_router(incidents.router, prefix="/api/v1")

root_logger.info("Starting LCWC API...")
root_logger.info("Database: %s", database.database)

root_logger.info("lcwc version: %s", get_lcwc_version())

lcwc_config = config["lcwc"]

geocoder = IncidentGeocoder(env["GOOGLE_MAPS_API_KEY"], redis_client)

updater = IncidentUpdater(
    app,
    database,
    timedelta(seconds=int(lcwc_config["update_interval"])),
    redis_client,
    geocoder,
    env["GEOCODING_ENABLED"].lower() == "true",
)

resolver_config = config["resolver"]
if resolver_config["enabled"]:
    pruner = IncidentResolver(
        app,
        timedelta(minutes=int(resolver_config["interval"])),
        timedelta(minutes=int(resolver_config["threshold"])),
    )

if __name__ == "__main__":
    uvicorn.run(app, host=env["HOSTNAME"], port=int(env["PORT"]))
