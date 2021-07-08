from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from . import get_credential_model
from .exceptions import (
    CredentialConfirmationExpired, CredentialIsPrimary, CredentialNotConfirmed,
)
from .signals import (
    credential_confirmed, unconfirmed_credential_created, primary_credential_changed,
)
# from django.utils.crypto import get_random_string # DEPRECATED, using django token generation instead
from utils.tokens import account_activation_token


class CredentialConfirmationUserMixin(object):
    """
    Mixin to be used with your django 1.5+ custom User model.
    Provides python-level functionality only.
    """

    # if your User object stores the User's primary phone number
    # in a place other than User.phone, you can override the
    # primary_phone_field_name and/or primary_phone get/set methods.
    # All access to a User's primary_phone in this app passes through
    # these two get/set methods.

    primary_credential_field_name = 'phone' or 'email' # or username

    def get_primary_credential(self):
        return getattr(self, self.primary_credential_field_name)

    def set_primary_credential(self, credential, require_confirmed=True):
        "Set a phone number or email address as primary"
        old_credential = self.get_primary_credential()
        if credential == old_credential:
            return

        if credential not in self.get_confirmed_credentials() and require_confirmed:
            raise CredentialNotConfirmed()

        setattr(self, self.primary_credential_field_name, credential)
        self.save(update_fields=[self.primary_credential_field_name])
        primary_credential_changed.send(
            sender=self.__class__,
            user=self,
            old_credential=old_credential,
            new_credential=credential,
        )

    @property
    def is_confirmed(self):
        "Is the User's primary phone number or email address confirmed?"
        return self.get_primary_credential() in self.get_confirmed_credentials()

    @property
    def confirmed_at(self):
        "When the User's primary phone number or email address was confirmed, or None"
        credential = self.credential_set.get(Q(phone=self.get_primary_credential()) | Q(email=self.get_primary_credential()))
        return credential.confirmed_at

    @property
    def confirmation_key(self):
        """
        Confirmation key for the User's primary phone or email

        DEPRECATED. Use get_credential_confirmation_key() instead.
        """
        credential = self.get_primary_credential()
        return self.get_confirmation_key(credential)

    @property
    def confirmed_credentials(self):
        "DEPRECATED. Use get_confirmed_credentials() instead."
        return self.get_confirmed_credentials()

    @property
    def unconfirmed_credentials(self):
        "DEPRECATED. Use get_unconfirmed_credentials() instead."
        return self.get_unconfirmed_credentials()

    def get_credential_confirmation_key(self, username=None): #TODO Dúvida 'username' ou credential?
        "Get the confirmation key for a phone or email"
        credential = username or self.get_primary_credential()
        credential = self.credential_set.get(Q(phone=self.get_primary_credential()) | Q(email=self.get_primary_credential()))
        return credential.key

    def get_confirmed_credentials(self):
        "List of phones or emails this User has confirmed"
        credential_qs = self.credential_set.filter(confirmed_at__isnull=False)
        return [credential.credential for credential in credential_qs]

    def get_unconfirmed_credentials(self):
        "List of phones or emails this User has been associated with but not confirmed"
        credential_qs = self.credential_set.filter(confirmed_at__isnull=True)
        return [credential.credential for credential in credential_qs]

    def confirm_credential(self, credential_confirmation_key, save=True):
        """
        Attempt to confirm a phone or email using the given key.
        Returns the phone or email that was confirmed, or raise an exception.
        """
        credential = self.credential_set.confirm(credential_confirmation_key, save=save, user=self)
        return credential.credential

    def add_confirmed_credential(self, credential):
        "Adds a phone or email to the user that's already in the confirmed state"
        # if phone or email already exists, let exception be thrown
        credential = self.credential_set.create_confirmed(credential)
        return credential.key

    def add_unconfirmed_credential(self, credential):
        "Adds an unconfirmed phone number or email address and returns it's confirmation key"
        # if phone or email already exists, let exception be thrown
        credential = self.credential_set.create_unconfirmed(credential)
        return credential.key

    def add_credential_if_not_exists(self, credential):
        """
        If the user already has the phone or email, and it's confirmed, do nothing
        and return None.

        If the user already has the phone or email, and it's unconfirmed, reset the
        confirmation. If the confirmation is unexpired, do nothing. Return
        the confirmation key of the phone or email.
        """
        try:
            credential = self.credential_set.get(Q(phone=credential) | Q(email=credential))
        except get_credential_model().DoesNotExist:
            key = self.add_unconfirmed_credential(credential)
        else:
            if not credential.is_confirmed:
                key = credential.reset_confirmation()
            else:
                key = None

        return key

    def reset_credential_confirmation(self, credential):
        "Reset the expiration of a phone or email confirmation"
        credential = self.credential_set.get(Q(phone=credential) | Q(email=credential))
        return credential.reset_confirmation()

    def remove_credential(self, credential):
        "Remove an phone number or email address"
        # if phone or email already exists, let exception be thrown
        if credential == self.get_primary_credential():
            raise CredentialIsPrimary()
        credential = self.credential_set.get(Q(phone=credential) | Q(email=credential))
        credential.delete()


class CredentialManager(models.Manager):

    def generate_key(self, user):
        "Generate a new random key and return it"
        # By default, a length of keys is 12. If you want to change it, set
        # settings.SIMPLE_EMAIL_CONFIRMATION_KEY_LENGTH to integer value (max 40).
        # return get_random_string(
        #     length=min(getattr(settings, 'SIMPLE_EMAIL_CONFIRMATION_KEY_LENGTH', 12), 40)
        # )
        return account_activation_token.make_token(user) # Using Django Token generation, as per Vitor Freitas

    def create_confirmed(self, credential, user=None):
        "Create an phone number or email address in the confirmed state"
        user = user or getattr(self, 'instance', None)
        if not user:
            raise ValueError('Must specify user or call from related manager')
        key = self.generate_key(user)
        now = timezone.now()
        # let phone-already-exists exception propagate through
        credential = self.create(
            user=user, credential=credential, key=key, set_at=now, confirmed_at=now,
        )
        return credential

    def create_unconfirmed(self, credential, user=None):
        "Create an phone number in the unconfirmed state"
        user = user or getattr(self, 'instance', None)
        if not user:
            raise ValueError('Must specify user or call from related manager')
        key = self.generate_key(user)
        # let phone-already-exists exception propagate through
        credential = self.create(user=user, credential=credential, key=key)
        unconfirmed_credential_created.send(
            sender=user.__class__,
            user=user,
            credential=credential,
        )
        return number

    def confirm(self, key, user=None, save=True):
        "Confirm a phone number. Returns the number that was confirmed."
        queryset = self.all()
        if user:
            queryset = queryset.filter(user=user)
        credential = queryset.get(key=key)

        if credential.is_key_expired:
            raise CredentialConfirmationExpired()

        if not credential.is_confirmed:
            credential.confirmed_at = timezone.now()
            if save:
                credential.save(update_fields=['confirmed_at'])
                credential_confirmed.send(
                    sender=credential.user.__class__,
                    user=credential.user,
                    credential=credential.credential
                )

        return credential


def get_user_primary_credential(user):
    # softly failing on using these methods on `user` to support
    # not using the SimplePhoneConfirmationMixin in your User model
    # https://github.com/mfogel/django-simple-email-confirmation/pull/3
    if hasattr(user, 'get_primary_credential'):
        return user.get_primary_credential()
    return user.credential #TODO Dúvida phone, email ou credential?


class AbstractCredentialNumber(models.Model):
    "A phone number or email address belonging to a User"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='credential_set',
        on_delete=models.CASCADE, verbose_name=_('user')
    )
    credential = models.CharField(_('número de telefone'), blank=True, null=True, unique=True, max_length=255)
    key = models.CharField(max_length=50, unique=True, verbose_name=_('chave de acesso'))

    set_at = models.DateTimeField(
        default=timezone.now,
        help_text=_('When the confirmation key expiration was set'),
        verbose_name=_('registrado em'),
    )
    confirmed_at = models.DateTimeField(
        blank=True, null=True,
        help_text=_('First time this credential was confirmed'),
        verbose_name=_('confirmado em'),

    )

    objects = CredentialManager()

    class Meta:
        unique_together = (('user', 'credential'),)
        verbose_name_plural = _("credenciais")
        abstract = True

    def __str__(self):
        return '{} <{}>'.format(self.user, self.credential)

    @property
    def is_confirmed(self):
        return self.confirmed_at is not None

    @property
    def is_primary(self):
        primary_credential = get_user_primary_credential(self.user)
        return bool(primary_credential == self.credential)

    @property
    def key_expires_at(self):
        # By default, keys don't expire. If you want them to, set
        # settings.SIMPLE_PHONE_CONFIRMATION_PERIOD to a timedelta.
        period = getattr(
            settings, 'CREDENTIAL_CONFIRMATION_PERIOD', None
        )
        return self.set_at + period if period is not None else None

    @property
    def is_key_expired(self):
        return self.key_expires_at and timezone.now() >= self.key_expires_at

    def reset_confirmation(self):
        """
        Re-generate the confirmation key and key expiration associated
        with this phone. Note that the previous confirmation key will
        cease to work.
        """
        self.key = get_credential_number_model()._default_manager.generate_key(self.user)
        self.set_at = timezone.now()

        self.confirmed_at = None
        self.save(update_fields=['key', 'set_at', 'confirmed_at'])
        return self.key


# class PhoneNumber(AbstractPhoneNumber):
#     class Meta(AbstractPhoneNumber.Meta):
#         swappable = 'SIMPLE_PHONE_CONFIRMATION_PHONE_NUMBER_MODEL'


# by default, auto-add unconfirmed PhoneNumber objects for new Users
if getattr(settings, 'CREDENTIAL_CONFIRMATION_AUTO_ADD', True):
    def auto_add(sender, **kwargs):
        if sender == get_user_model() and kwargs['created'] and not kwargs['raw']:
            user = kwargs.get('instance')
            credential = get_user_primary_credential(user)
            if credential:
                if hasattr(user, 'add_unconfirmed_credential'):
                    user.add_unconfirmed_credential(credential)
                else:
                    user.credential_set.create_unconfirmed(credential)

    # TODO: try to only connect this to the User model. We can't use
    #       get_user_model() here - results in import loop.

    post_save.connect(auto_add)
