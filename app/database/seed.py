import peewee
import faker
from faker.providers import BaseProvider


from lcwc.category import IncidentCategory


from app.api.models.agency import Agency
from app.api.models.incident import Incident
from app.api.models.unit import Unit


class AgencyProvider(BaseProvider):
    def agency_company(self, city: str, category: IncidentCategory):
        if category == IncidentCategory.FIRE:
            return f"{city} Fire Department"
        elif category == IncidentCategory.TRAFFIC:
            return f"{city} Police Department"
        elif category == IncidentCategory.MEDICAL:
            return f"{city} Medical Services"
        else:
            return f"{city} Department"

    def agency_category(self):
        return self.random_element(
            elements=(
                IncidentCategory.FIRE,
                IncidentCategory.MEDICAL,
                IncidentCategory.TRAFFIC,
            )
        )

    def agency_station_id(self):
        id = self.random_int(min=1, max=99)
        return f"{id:02d}"


class IncidentProvider(BaseProvider):
    def incident_number(self):
        return self.random_int(min=100000, max=999999)

    def incident_category(self):
        return self.random_element(
            elements=(
                IncidentCategory.FIRE,
                IncidentCategory.MEDICAL,
                IncidentCategory.TRAFFIC,
            )
        )


class UnitProvider(BaseProvider):
    def unit_name(self):
        return f"{''.join(self.random_letters(3)).upper()}-{self.random_int(min=10, max=99)}"


fake = faker.Faker()
fake.add_provider(AgencyProvider)
fake.add_provider(IncidentProvider)
fake.add_provider(UnitProvider)


def seed_incidents():
    Incident.delete().execute()
    Unit.delete().execute()

    for _ in range(10):
        incident = Incident(
            category=str(fake.incident_category().value),
            description=fake.sentence(nb_words=6, variable_nb_words=True),
            intersection=fake.street_name(),
            municipality=fake.city(),
            dispatched_at=fake.date_time_between(start_date="-1d", end_date="now"),
            number=fake.unique.incident_number(),
            priority=fake.random_int(min=1, max=3),
            agency=fake.name(),
            latitude=fake.latitude(),
            longitude=fake.longitude(),
            added_at=fake.date_time_between(start_date="-1d", end_date="now"),
            updated_at=fake.date_time_between(start_date="-1d", end_date="now"),
            resolved_at=fake.date_time_between(start_date="-1d", end_date="now"),
            client=fake.name(),
            automatically_resolved=False,
        )
        try:
            incident.save(force_insert=True)
        except Exception as e:
            print(f"Error saving incident: {e}")

        random_unit_count = fake.random_int(min=1, max=3)
        for _ in range(random_unit_count):
            try:
                unit = Unit(
                    incident=incident,
                    short_name=fake.unit_name(),
                    added_at=fake.date_time_between(start_date="-1d", end_date="now"),
                    last_seen=fake.date_time_between(start_date="-1d", end_date="now"),
                )
                unit.save(force_insert=True)
            except Exception as e:
                print(f"Error saving unit: {e}")


def seed_agencies():
    """Seed agencies with fake data"""

    Agency.delete().execute()

    for _ in range(10):
        cat = fake.agency_category()
        city = fake.unique.city()
        agency = Agency(
            category=str(cat.value),
            station_id=fake.unique.agency_station_id(),
            name=fake.agency_company(city, cat),
            url=fake.url(),
            address=fake.street_address(),
            city=city,
            state="PA",
            zip_code=fake.zipcode_in_state("PA"),
            phone=fake.phone_number(),
        )
        try:
            agency.save(force_insert=True)
        except Exception as e:
            print(f"Error saving agency: {e}")
