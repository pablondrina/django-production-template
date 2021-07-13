import json

from django.http import request

from project import settings
from django.contrib.gis import forms
from django.contrib.gis.geos import Point, GEOSGeometry, fromstr
from django.utils.translation import gettext_lazy as _
from mapwidgets import GooglePointFieldWidget, GoogleStaticMapWidget

from project.apps.places.models import Address, City, State, Country, Neighbourhood


class LocationAdminAddForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ('geodata', 'location', 'address', 'complement', 'neighbourhood', 'instructions', 'postal_code', 'city',)
        widgets = {
            'location': GooglePointFieldWidget,
        }

    geodata = forms.CharField(
        widget=forms.Textarea(
            attrs={'hidden':'true'}),
            label='',
            required=False,
        )

    def clean_location(self):
        return self.cleaned_data.get('location')

    def clean_address(self):
        return self.cleaned_data.get('geodata')[0]

    def clean_complement(self):
        return self.cleaned_data.get('geodata')[1]

    def clean_neighbourhood(self):
        return self.cleaned_data.get('geodata')[2]

    def clean_city(self):
        _city = str(self.cleaned_data.get('geodata')[3])
        _state = str(self.cleaned_data.get('geodata')[4].upper())[0:2]
        _state_long = str(self.cleaned_data.get('geodata')[5])
        _country = str(self.cleaned_data.get('geodata')[6].upper())[0:2]
        _country_long = str(self.cleaned_data.get('geodata')[7])

        my_country, country_created = Country.objects.get_or_create(code=_country, name=_country_long)
        my_state, state_created = State.objects.get_or_create(code=_state, name=_state_long)
        my_city, city_created = City.objects.get_or_create(state=my_state, country=my_country, name=_city)

        return my_city

    def clean_postal_code(self):
        return self.cleaned_data.get('geodata')[8]

    def clean_instructions(self):
        return self.cleaned_data.get('instructions')

    def clean_geodata(self):
        location = self.cleaned_data.get('location')
        coords = f"{location.y},{location.x}"

        import geopy
        geolocator = geopy.GoogleV3(api_key=settings.GOOGLE_MAPS_API_KEY)
        response = geolocator.reverse(coords,language='pt-br',)

        if response is not None:
            components = response.raw['address_components']
            address = {}
            for component in components:
                for type in component['types']:
                    address[f"{type}"] = component['short_name']
                    # address[f"{type}_long"] = component['long_name'] # Se for assim, tudo vem com a opção long, mesmo que obsoleta/duplicada
                    if 'country' in type:
                        address[f"{type}"] = component['short_name']
                        address[f"{type}_long"] = component['long_name']
                    if 'administrative_area_level_1' in type:
                        address[f"{type}"] = component['short_name']
                        address[f"{type}_long"] = component['long_name']

            address_route = ''
            address_street_number = ''
            address_sublocality = ''
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
                address_sublocality = address['sublocality_level_1'] or address['sublocality']
            if 'premise' in address:
                address_premise =  address['premise']
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

            address_line1 = f"{address_route}, {address_street_number}"

            if address_premise and not address_subpremise:
                address_line2 = f"{address_premise}"
            elif address_premise and address_subpremise:
                address_line2 = f"{address_premise}, {address_subpremise}"
            elif address_subpremise and not address_premise:
                address_line2 = f"{address_subpremise}"
            else:
                address_line2 = ''

            lat = response.raw['geometry']['location']['lat']
            lng = response.raw['geometry']['location']['lng']
            # coords = fromstr(f"POINT({lng}, {lat})", srid=4326)

            coords = Point(lng, lat, srid=4326)

            return address_line1,\
                   address_line2,\
                   address_sublocality,\
                   address_city, \
                   address_state, \
                   address_state_long, \
                   address_country, \
                   address_country_long, \
                   address_postal_code,\
                   coords,\
                   response.raw['formatted_address'],\
                   response.raw


class LocationAdminChangeForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ('geodata', 'location', 'address', 'complement', 'neighbourhood', 'instructions', 'postal_code', 'city',)
        widgets = {
            'location': GooglePointFieldWidget,
        }

    geodata = forms.CharField(
        widget=forms.Textarea(
            attrs={'hidden':'true'}),
            label='',
            required=False,
        )

    def clean_location(self):
        return self.cleaned_data.get('location')

    def clean_address(self):
        if 'location' in self.changed_data:
            return self.cleaned_data.get('geodata')[0]
        else:
            return self.cleaned_data.get('address')

    def clean_complement(self):
        if 'location' in self.changed_data:
            return self.cleaned_data.get('geodata')[1]
        else:
            return self.cleaned_data.get('complement')

    def clean_neighbourhood(self):
        if 'location' in self.changed_data:
            return self.cleaned_data.get('geodata')[2]
        else:
            return self.cleaned_data.get('neighbourhood')

    def clean_city(self):
        if 'location' in self.changed_data:
            _city = str(self.cleaned_data.get('geodata')[3])
            _state = str(self.cleaned_data.get('geodata')[4].upper())[0:2]
            _state_long = str(self.cleaned_data.get('geodata')[5])
            _country = str(self.cleaned_data.get('geodata')[6].upper())[0:2]
            _country_long = str(self.cleaned_data.get('geodata')[7])

            my_country, country_created = Country.objects.get_or_create(code=_country, name=_country_long)
            my_state, state_created = State.objects.get_or_create(code=_state, name=_state_long)
            my_city, city_created = City.objects.get_or_create(state=my_state, country=my_country, name=_city)

            return my_city
        else:
            return self.cleaned_data.get('city')

    def clean_postal_code(self):
        if 'location' in self.changed_data:
            return self.cleaned_data.get('geodata')[8]
        else:
            return self.cleaned_data.get('postal_code')

    def clean_instructions(self):
        return self.cleaned_data.get('instructions')

    def clean_geodata(self):
        if self.cleaned_data.get('location'):
            location = self.cleaned_data.get('location')
            coords = f"{location.y},{location.x}"

            import geopy
            geolocator = geopy.GoogleV3(api_key=settings.GOOGLE_MAPS_API_KEY)
            response = geolocator.reverse(coords,language='pt-br',)

            if response is not None:
                components = response.raw['address_components']
                address = {}
                for component in components:
                    for type in component['types']:
                        address[f"{type}"] = component['short_name']
                        # address[f"{type}_long"] = component['long_name'] # Se for assim, tudo vem com a opção long, mesmo que obsoleta/duplicada
                        if 'country' in type:
                            address[f"{type}"] = component['short_name']
                            address[f"{type}_long"] = component['long_name']
                        if 'administrative_area_level_1' in type:
                            address[f"{type}"] = component['short_name']
                            address[f"{type}_long"] = component['long_name']

                address_route = ''
                address_street_number = ''
                address_sublocality = ''
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
                    address_sublocality = address['sublocality_level_1'] or address['sublocality']
                if 'premise' in address:
                    address_premise =  address['premise']
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

                address_line1 = f"{address_route}, {address_street_number}"

                if address_premise and not address_subpremise:
                    address_line2 = f"{address_premise}"
                elif address_premise and address_subpremise:
                    address_line2 = f"{address_premise}, {address_subpremise}"
                elif address_subpremise and not address_premise:
                    address_line2 = f"{address_subpremise}"
                else:
                    address_line2 = ''

                lat = response.raw['geometry']['location']['lat']
                lng = response.raw['geometry']['location']['lng']
                # coords = fromstr(f"POINT({lng}, {lat})", srid=4326)

                coords = Point(lng, lat, srid=4326)

                return address_line1,\
                       address_line2,\
                       address_sublocality,\
                       address_city, \
                       address_state, \
                       address_state_long, \
                       address_country, \
                       address_country_long, \
                       address_postal_code,\
                       coords,\
                       response.raw['formatted_address'],\
                       response.raw


class LocationAdminForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ('geodata', 'location', 'address', 'complement', 'neighbourhood', 'instructions', 'postal_code', 'city',)
        widgets = {
            'location': GooglePointFieldWidget,
        }

    geodata = forms.CharField(
        widget=forms.Textarea(
            attrs={'hidden':'true'}),
            label='',
            required=False,
        )

    def clean_location(self):
        return self.cleaned_data.get('location')

    def clean_address(self):
        if 'location' in self.changed_data:
            return self.cleaned_data.get('geodata')[0]
        else:
            return self.cleaned_data.get('address')

    def clean_complement(self):
        if 'location' in self.changed_data:
            return self.cleaned_data.get('geodata')[1]
        else:
            return self.cleaned_data.get('complement')

    def clean_neighbourhood(self):
        if 'location' in self.changed_data:
            return self.cleaned_data.get('geodata')[2]
        else:
            return self.cleaned_data.get('neighbourhood')

    def clean_city(self):
        if 'location' in self.changed_data:
            _city = str(self.cleaned_data.get('geodata')[3])
            _state = str(self.cleaned_data.get('geodata')[4].upper())[0:2]
            _state_long = str(self.cleaned_data.get('geodata')[5])
            _country = str(self.cleaned_data.get('geodata')[6].upper())[0:2]
            _country_long = str(self.cleaned_data.get('geodata')[7])

            my_country, country_created = Country.objects.get_or_create(code=_country, name=_country_long)
            my_state, state_created = State.objects.get_or_create(code=_state, name=_state_long)
            my_city, city_created = City.objects.get_or_create(state=my_state, country=my_country, name=_city)

            return my_city
        else:
            return self.cleaned_data.get('city')

    def clean_postal_code(self):
        if 'location' in self.changed_data:
            return self.cleaned_data.get('geodata')[8]
        else:
            return self.cleaned_data.get('postal_code')

    def clean_instructions(self):
        return self.cleaned_data.get('instructions')

    def clean_geodata(self):
        if self.cleaned_data.get('location'):
            location = self.cleaned_data.get('location')
            coords = f"{location.y},{location.x}"

            import geopy
            geolocator = geopy.GoogleV3(api_key=settings.GOOGLE_MAPS_API_KEY)
            response = geolocator.reverse(coords,language='pt-br',)

            if response is not None:
                components = response.raw['address_components']
                address = {}
                for component in components:
                    for type in component['types']:
                        address[f"{type}"] = component['short_name']
                        # address[f"{type}_long"] = component['long_name'] # Se for assim, tudo vem com a opção long, mesmo que obsoleta/duplicada
                        if 'country' in type:
                            address[f"{type}"] = component['short_name']
                            address[f"{type}_long"] = component['long_name']
                        if 'administrative_area_level_1' in type:
                            address[f"{type}"] = component['short_name']
                            address[f"{type}_long"] = component['long_name']

                address_route = ''
                address_street_number = ''
                address_sublocality = ''
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
                    address_sublocality = address['sublocality_level_1'] or address['sublocality']
                if 'premise' in address:
                    address_premise =  address['premise']
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

                address_line1 = f"{address_route}, {address_street_number}"

                if address_premise and not address_subpremise:
                    address_line2 = f"{address_premise}"
                elif address_premise and address_subpremise:
                    address_line2 = f"{address_premise}, {address_subpremise}"
                elif address_subpremise and not address_premise:
                    address_line2 = f"{address_subpremise}"
                else:
                    address_line2 = ''

                lat = response.raw['geometry']['location']['lat']
                lng = response.raw['geometry']['location']['lng']
                # coords = fromstr(f"POINT({lng}, {lat})", srid=4326)

                coords = Point(lng, lat, srid=4326)

                return address_line1,\
                       address_line2,\
                       address_sublocality,\
                       address_city, \
                       address_state, \
                       address_state_long, \
                       address_country, \
                       address_country_long, \
                       address_postal_code,\
                       coords,\
                       response.raw['formatted_address'],\
                       response.raw
