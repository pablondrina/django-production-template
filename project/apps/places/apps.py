from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PlacesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = 'project.apps.places'
    verbose_name = _('Geolocalização')

    def ready(self):
        import project.apps.places.signals # noqa
