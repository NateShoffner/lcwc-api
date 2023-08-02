import googlemaps
import hashlib
import json
import logging
import redis
from lcwc.arcgis import ArcGISIncident as Incident


class IncidentGeocoder:
    """Geocodes incidents using the Google Maps API using Redis as a cache"""

    def __init__(self, client: googlemaps.Client, redis: redis.Redis) -> None:
        self.client = client
        self.redis = redis
        self.logger = logging.getLogger(__name__)

    def get_absolute_address(self, incident: Incident) -> str:
        """Creates an absolute address from the given incident

        :param incident: The incident to create an absolute address from
        :return: The absolute address
        :rtype: str
        """
        if incident.intersection is None:
            self.logger.debug(f"No intersection found for incident: {incident.number}")
            return None

        addr = f"{incident.intersection}, {incident.municipality}, LANCASTER COUNTY, PA"
        return addr

    def get_coordinates(self, incident: Incident) -> tuple[float, float]:
        """Gets the coordinates of the given incident

        :param incident: The incident to get the coordinates of
        :return: The coordinates of the incident
        :rtype: tuple[float, float]
        """
        absolute_address = self.get_absolute_address(incident)

        if absolute_address is None:
            return None

        GEOCODE_KEY_PREFIX = "geocode"
        hash = hashlib.sha1(absolute_address.encode("utf-8")).hexdigest()
        key = f"{GEOCODE_KEY_PREFIX}:{hash}"

        if self.redis.exists(key):
            coords_json = self.redis.get(key)
            coords = json.loads(coords_json)
            # self.logger.debug(f'Found cached coordinates for address: {absolute_address} - {coords}')
            return coords

        self.logger.debug(f"Geocoding address: {absolute_address}")

        try:
            geocode_result = self.client.geocode(absolute_address)

            if len(geocode_result) == 0:
                return None

            location = geocode_result[0]["geometry"]["location"]
            lat = location["lat"]
            lng = location["lng"]

            self.redis.set(key, json.dumps((lat, lng)))
            return (lat, lng)
        except Exception as e:
            self.logger.error(f"Error geocoding address: {e}")
