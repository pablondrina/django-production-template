from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "project.apps.accounts"
    verbose_name = _('Contas de usuário')

    # def ready(self):
    #     import apps.accounts.signals # noqa
