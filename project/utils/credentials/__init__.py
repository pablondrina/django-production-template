__version__ = '0.1'
__all__ = [
    'credential_confirmed',
    'unconfirmed_credential_created',
    'primary_credential_changed',
    'get_credential_model',
]

from django.conf import settings
from django.apps import apps as a

from .signals import (
    credential_confirmed, unconfirmed_credential_created, primary_credential_changed,
)


def get_credential_model():
    """Convenience method to return the phone or email model being used."""
    return a.get_model(getattr(
        settings,
        'CREDENTIAL_CONFIRMATION_MODEL',
        'credential_confirmation.Credential'
    ))


default_app_config = 'utils.credential_confirmation.apps.CredentialConfirmationConfig'
