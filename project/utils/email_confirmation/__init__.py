__version__ = '0.70'
__all__ = [
    'email_confirmed',
    'unconfirmed_email_created',
    'primary_email_changed',
    'get_email_address_model',
]

from django.conf import settings
from django.apps import apps as a

from .signals import (
    email_confirmed, unconfirmed_email_created, primary_email_changed,
)


def get_email_address_model():
    """Convenience method to return the email model being used."""
    return a.get_model(getattr(
        settings,
        'SIMPLE_EMAIL_CONFIRMATION_EMAIL_ADDRESS_MODEL',
        'email_confirmation.EmailAddress'
    ))

default_app_config = 'utils.email_confirmation.apps.EmailConfirmationConfig'
