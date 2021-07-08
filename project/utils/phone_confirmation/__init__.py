__version__ = '0.1'
__all__ = [
    'phone_confirmed',
    'unconfirmed_phone_created',
    'primary_phone_changed',
    'get_phone_number_model',
]

from django.conf import settings
from django.apps import apps as a

from .signals import (
    phone_confirmed, unconfirmed_phone_created, primary_phone_changed,
)


def get_phone_number_model():
    """Convenience method to return the phone model being used."""
    return a.get_model(getattr(
        settings,
        'SIMPLE_PHONE_CONFIRMATION_PHONE_NUMBER_MODEL',
        'phone_confirmation.PhoneNumber'
    ))


default_app_config = 'utils.phone_confirmation.apps.PhoneConfirmationConfig'
