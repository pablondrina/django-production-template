from django.contrib.admin.options import BaseModelAdmin
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.contrib.admin.widgets import (
    AutocompleteSelect, AutocompleteSelectMultiple,
)
from django.utils.http import urlencode
from urllib.parse import unquote, quote_plus, parse_qsl


class AutocompleteUrl(object):
    def __init__(self, *args, **kwargs):
        self.order_by = kwargs.pop('order_by', [])
        super().__init__(*args, **kwargs)

    def get_url_params(self):
        params = {}
        if self.rel.limit_choices_to:
            params['limit_choices_to'] = quote_plus(urlencode(self.rel.limit_choices_to))
        if self.order_by:
            params['order_by'] = quote_plus(','.join(self.order_by))
        return params

    def get_url(self):
        url = super().get_url()
        return url + '?' + urlencode(self.get_url_params())


class ManyToManyAutocompleteSelect(AutocompleteUrl, AutocompleteSelectMultiple):
    pass


class ForeignKeyAutocompleteSelect(AutocompleteUrl, AutocompleteSelect):
    pass


class LimitAutocompleteJsonView(AutocompleteJsonView):
    # Filter the results with the arguments passed to the url
    def get_queryset(self):
        qs = super().get_queryset()
        order_by = filter(None, self.request.GET.get('order_by', '').split(','))
        if order_by:
            qs = qs.order_by(*order_by)
        limit_choices_to = self.request.GET.get('limit_choices_to')
        if limit_choices_to:
            params = dict(parse_qsl(unquote(limit_choices_to)))
            qs = qs.complex_filter(params)
        return qs


# Extend your admin class from HelperAdmin
class HelperAdmin(BaseModelAdmin):
    autocomplete_fields_extra = {}

    # Use autocomplete_fields_extra on your admin class
    # to set fields that need to be extended, and set order_by if needed
    # autocomplete_fields_extra = {'field': {'order_by': ['name']}}

    def autocomplete_view(self, request):
        return LimitAutocompleteJsonView.as_view(model_admin=self)(request)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in self.autocomplete_fields_extra.keys():
            db = kwargs.get('using')
            kwargs['widget'] = ForeignKeyAutocompleteSelect(
                rel=db_field.remote_field,
                admin_site=self.admin_site,
                order_by=self.limit_choices_fields[db_field.name].get('order_by', []),
                using=db)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name in self.autocomplete_fields_extra.keys():
            db = kwargs.get('using')
            kwargs['widget'] = ManyToManyAutocompleteSelect(
                rel=db_field.remote_field,
                admin_site=self.admin_site,
                order_by=self.limit_choices_fields[db_field.name].get('order_by', []),
                using=db)
        return super().formfield_for_manytomany(db_field, request, **kwargs)