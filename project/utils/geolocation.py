import geopy
from django.conf import settings
from django.contrib.gis.geos import Point
from project.apps.places.models import Country, State, City


def point_to_address(point, instance):
    if point:
        coords = f"{point.y},{point.x}"
        geolocator = geopy.GoogleV3(api_key=settings.GOOGLE_MAPS_API_KEY)
        response = geolocator.reverse(coords, language='pt-br', )

        if response is not None:
            components = response.raw['address_components']
            address = {}
            for component in components:
                for type in component['types']:
                    address[f"{type}"] = component['short_name']
                    if 'country' in type:
                        address[f"{type}"] = component['short_name']
                        address[f"{type}_long"] = component['long_name']
                    if 'administrative_area_level_1' in type:
                        address[f"{type}"] = component['short_name']
                        address[f"{type}_long"] = component['long_name']

            address_route = ''
            address_street_number = ''
            neighbourhood = ''
            address_premise = ''
            address_subpremise = ''
            address_city = ''
            address_state = ''
            address_country = ''
            address_postal_code = ''

            if 'route' in address:
                address_route = address['route']
            if 'street_number' in address:
                address_street_number = address['street_number']
            if 'sublocality' in address:
                neighbourhood = address['sublocality_level_1'] or address['sublocality']
            if 'premise' in address:
                address_premise = address['premise']
            if 'subpremise' in address:
                address_subpremise = address['subpremise']
            if 'administrative_area_level_2' in address:
                address_city = address['administrative_area_level_2']
            if 'administrative_area_level_1' in address:
                address_state = address['administrative_area_level_1']
            if 'administrative_area_level_1_long' in address:
                address_state_long = address['administrative_area_level_1_long']
            if 'country' in address:
                address_country = address['country']
            if 'country_long' in address:
                address_country_long = address['country_long']
            if 'postal_code' in address:
                address_postal_code = address['postal_code']

            address = f"{address_route}, {address_street_number}"

            if address_premise and not address_subpremise:
                complement = f"{address_premise}"
            elif address_premise and address_subpremise:
                complement = f"{address_premise}, {address_subpremise}"
            elif address_subpremise and not address_premise:
                complement = f"{address_subpremise}"
            else:
                complement = ''

            # lat = response.raw['geometry']['location']['lat']
            # lng = response.raw['geometry']['location']['lng']
            # coords = fromstr(f"POINT({lng}, {lat})", srid=4326)
            # coords = Point(lng, lat, srid=4326)

            instance.address = address
            instance.complement = complement
            instance.neighbourhood = neighbourhood
            instance.postal_code = address_postal_code

            _city = address_city
            _state = address_state.upper()[0:2]
            _state_long = address_state_long
            _country = address_country.upper()[0:2]
            _country_long = address_country_long

            my_country, country_created = Country.objects.get_or_create(code=_country, name=_country_long)
            my_state, state_created = State.objects.get_or_create(code=_state, name=_state_long)
            my_city, city_created = City.objects.get_or_create(state=my_state, country=my_country, name=_city)

            instance.city = my_city
