from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _


class PhoneConfirmationConfig(AppConfig):
    name = 'utils.phone_confirmation'
    verbose_name = _('Telefones')

    # def ready(self):
    #     from utils.phone_confirmation.models import AbstractPhoneNumber
    #     post_migrate.connect(
    #         AbstractPhoneNumber.post_migrate_handler, sender=self)