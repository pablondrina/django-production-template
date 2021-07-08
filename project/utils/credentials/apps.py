from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PhoneConfirmationConfig(AppConfig):
    name = 'utils.phone_confirmation'
    verbose_name = _('Telefones')