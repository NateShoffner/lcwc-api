
import aiohttp
import urllib
from lcwc.arcgis import Incident

class Geocoder:
    """ Geocodes addresses using the Google Maps API """

    def __init__(self, api_key):
        self.api_key = api_key

    async def get_address_coords(self, incident: Incident) -> tuple[float, float]:
        """ Returns the coordinates of an incident """

        lat, lng = None, None
        absolute_address = self.__create_absolute_address(incident)

        if absolute_address is None:
            return lat, lng

        base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        async with aiohttp.ClientSession() as session:
            
            endpoint = f"{base_url}?address={urllib.parse.quote_plus(absolute_address)}&key={self.api_key}"

            async with session.get(endpoint) as response:
                if response.status not in range(200, 299):
                    return None, None
                try:
                    j = await response.json()

                    if len(j['results']) == 0:
                        print('No results found: ' + endpoint)
                        return None, None
                    
                    results = j['results'][0]

                    lat = results['geometry']['location']['lat']
                    lng = results['geometry']['location']['lng']

                except Exception as e:
                    print(e)

                return lat, lng

    def __create_absolute_address(self, incident: Incident) -> str:
        """ Creates an absolute address from an incident object """


        # TODO maybe allow broad suppport for township-level alerts if an intersection is not provided
        if incident.intersection is None:
            return None

        addr = f"{incident.intersection}, {incident.township}, LANCASTER COUNTY, PA"
        return addr
