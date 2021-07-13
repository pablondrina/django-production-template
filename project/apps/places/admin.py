from django.contrib import messages
from django.contrib.gis.admin import OSMGeoAdmin
from django.contrib.gis import admin
from django.http import HttpResponseRedirect
from import_export import resources
from import_export.admin import ImportExportActionModelAdmin
from tabbed_admin import TabbedModelAdmin

from .models import Address, City, State, Country, Neighbourhood
from .forms import LocationAdminForm, LocationAdminAddForm, LocationAdminChangeForm


class AddressResource(resources.ModelResource):
    class Meta:
        model = Address


@admin.register(Address)
class LocationAdmin(ImportExportActionModelAdmin, TabbedModelAdmin):
    resource_class = AddressResource

    change_form = LocationAdminChangeForm
    add_form = LocationAdminAddForm

    list_display = ['address', 'complement', 'neighbourhood', 'city', 'postal_code', 'coords']
    autocomplete_fields = ['city',]
    save_on_top = True

    class Media:
        css = {
            'all': ('css/jquery-ui.theme.min.css',)
        }

    tab_search = (
        (None, {
            'fields': ('location','geodata')
        }),
    )

    tab_address = (
        (None, {
            'fields': ('user','address', 'complement', 'neighbourhood', 'city', 'postal_code', 'instructions','extra')
        }),
    )

    tabs = [
        ('Pesquisar', tab_search),
        ('Editar', tab_address),
    ]

    # def get_tabs(self, request, obj=None):
    #     tabs = self.tabs
    #     if obj is None:
    #         tab_search = self.tab_search
    #         tabs = [
    #             ('Pesquisar', tab_search),
    #         ]
    #     else:
    #         tab_address = self.tab_address
    #         tabs = [
    #             ('Editar', tab_address),
    #         ]
    #     self.tabs = tabs
    #     return super().get_tabs(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if obj:
            self.form = self.change_form
            self.change_form_template = "places/change_form.html"
        else:
            self.form = self.add_form
        return super().get_form(request, obj, **kwargs)

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'user' and kwargs['request'].GET.get('_popup') == '1':
            field.initial = kwargs['request'].session.__getitem__('_session_customer_id')
        return field


@admin.register(City)
class CityAdmin(OSMGeoAdmin):
    search_fields = ('name',)

@admin.register(State)
class StateAdmin(OSMGeoAdmin):
    search_fields = ('name',)

@admin.register(Country)
class CountryAdmin(OSMGeoAdmin):
    search_fields = ('name',)

# @admin.register(Neighbourhood)
# class NeighbourhoodAdmin(OSMGeoAdmin):
#     search_fields = ('name',)