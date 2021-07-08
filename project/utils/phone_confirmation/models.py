from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save, post_delete, pre_save
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from . import get_phone_number_model
from .cache import del_cached_primary_phone
from .exceptions import (
    PhoneConfirmationExpired, PhoneIsPrimary, PhoneNotConfirmed,
)
from .signals import (
    phone_confirmed, unconfirmed_phone_created, primary_phone_changed,
)
# from django.utils.crypto import get_random_string # DEPRECATED, using django token generation instead
from project.utils.tokens import phone_activation_token


class SimplePhoneConfirmationUserMixin(object):
    """
    Mixin to be used with your django 1.5+ custom User model.
    Provides python-level functionality only.
    """

    # if your User object stores the User's primary phone number
    # in a place other than User.phone, you can override the
    # primary_phone_field_name and/or primary_phone get/set methods.
    # All access to a User's primary_phone in this app passes through
    # these two get/set methods.

    primary_phone_field_name = 'phone'

    def get_primary_phone(self):
        return getattr(self, self.primary_phone_field_name)

    def set_primary_phone(self, phone, require_confirmed=True):
        "Set a phone number as primary"
        old_phone = self.get_primary_phone()
        if phone == old_phone:
            return

        if phone not in self.get_confirmed_phones() and require_confirmed:
            raise PhoneNotConfirmed()

        setattr(self, self.primary_phone_field_name, phone)
        self.save(update_fields=[self.primary_phone_field_name])
        primary_phone_changed.send(
            sender=self.__class__,
            user=self,
            old_phone=old_phone,
            new_phone=phone,
        )

    @property
    def is_phone_confirmed(self):
        "Is the User's primary phone number confirmed?"
        return self.get_primary_phone() in self.get_confirmed_phones()

    @property
    def confirmed_at(self):
        "When the User's primary phone number was confirmed, or None"
        number = self.phone_number_set.get(phone=self.get_primary_phone())
        return number.confirmed_at

    @property
    def phone_confirmation_key(self):
        """
        Confirmation key for the User's primary phone

        DEPRECATED. Use get_phone_confirmation_key() instead.
        """
        phone = self.get_primary_phone()
        return self.get_phone_confirmation_key(phone)

    @property
    def confirmed_phones(self):
        "DEPRECATED. Use get_confirmed_phones() instead."
        return self.get_confirmed_phones()

    @property
    def unconfirmed_phones(self):
        "DEPRECATED. Use get_unconfirmed_phones() instead."
        return self.get_unconfirmed_phones()

    def get_phone_confirmation_key(self, phone=None):
        "Get the confirmation key for a phone"
        phone = phone or self.get_primary_phone()
        number = self.phone_number_set.get(phone=phone)
        return number.key

    def get_confirmed_phones(self):
        "List of phones this User has confirmed"
        number_qs = self.phone_number_set.filter(confirmed_at__isnull=False)
        return [number.phone for number in number_qs]

    def get_unconfirmed_phones(self):
        "List of phones this User has been associated with but not confirmed"
        number_qs = self.phone_number_set.filter(confirmed_at__isnull=True)
        return [number.phone for number in number_qs]

    def confirm_phone(self, phone_confirmation_key, save=True):
        """
        Attempt to confirm a phone using the given key.
        Returns the phone that was confirmed, or raise an exception.
        """
        number = self.phone_number_set.confirm(phone_confirmation_key, save=save, user=self)
        return number.phone

    def add_confirmed_phone(self, phone):
        "Adds a phone to the user that's already in the confirmed state"
        # if phone already exists, let exception be thrown
        number = self.phone_number_set.create_confirmed(phone)
        return number.key

    def add_unconfirmed_phone(self, phone):
        "Adds an unconfirmed phone number and returns it's confirmation key"
        # if phone already exists, let exception be thrown
        number = self.phone_number_set.create_unconfirmed(phone)
        return number.key

    def add_phone_if_not_exists(self, phone):
        """
        If the user already has the phone, and it's confirmed, do nothing
        and return None.

        If the user already has the phone, and it's unconfirmed, reset the
        confirmation. If the confirmation is unexpired, do nothing. Return
        the confirmation key of the phone.
        """
        try:
            number = self.phone_number_set.get(phone=phone)
        except get_phone_number_model().DoesNotExist:
            key = self.add_unconfirmed_phone(phone)
        else:
            if not number.is_phone_confirmed:
                key = number.reset_confirmation()
            else:
                key = None

        return key

    def reset_phone_confirmation(self, phone):
        "Reset the expiration of a phone confirmation"
        number = self.phone_number_set.get(phone=phone)
        return number.reset_confirmation()

    def remove_phone(self, phone):
        "Remove an phone number"
        # if phone already exists, let exception be thrown
        if phone == self.get_primary_phone():
            raise PhoneIsPrimary()
        number = self.phone_number_set.get(phone=phone)
        number.delete()


class PhoneNumberManager(models.Manager):

    def generate_key(self, user):
        "Generate a new random key and return it"
        # By default, a length of keys is 12. If you want to change it, set
        # settings.SIMPLE_EMAIL_CONFIRMATION_KEY_LENGTH to integer value (max 40).
        # return get_random_string(
        #     length=min(getattr(settings, 'SIMPLE_EMAIL_CONFIRMATION_KEY_LENGTH', 12), 40)
        # )
        return phone_activation_token.make_token(user) # Using Django Token generation, as per Vitor Freitas

    def create_confirmed(self, phone, user=None):
        "Create an phone number in the confirmed state"
        user = user or getattr(self, 'instance', None)
        if not user:
            raise ValueError('Must specify user or call from related manager')
        key = self.generate_key(user)
        now = timezone.now()
        # let phone-already-exists exception propagate through
        number = self.create(
            user=user, phone=phone, key=key, set_at=now, confirmed_at=now,
        )
        return number

    def create_unconfirmed(self, phone, user=None):
        "Create an phone number in the unconfirmed state"
        user = user or getattr(self, 'instance', None)
        if not user:
            raise ValueError('Must specify user or call from related manager')
        key = self.generate_key(user)
        # let phone-already-exists exception propagate through
        number = self.create(user=user, phone=phone, key=key)
        unconfirmed_phone_created.send(
            sender=user.__class__,
            user=user,
            phone=phone,
        )
        return number

    def confirm(self, key, user=None, save=True):
        "Confirm a phone number. Returns the number that was confirmed."
        queryset = self.all()
        if user:
            queryset = queryset.filter(user=user)
        number = queryset.get(key=key)

        if number.is_key_expired:
            raise PhoneConfirmationExpired()

        if not number.is_phone_confirmed:
            number.confirmed_at = timezone.now()
            if save:
                number.save(update_fields=['confirmed_at'])
                phone_confirmed.send(
                    sender=number.user.__class__,
                    user=number.user,
                    phone=number.phone
                )

        return number


def get_user_primary_phone(user):
    # softly failing on using these methods on `user` to support
    # not using the SimplePhoneConfirmationMixin in your User model
    # https://github.com/mfogel/django-simple-email-confirmation/pull/3
    if hasattr(user, 'get_primary_phone'):
        return user.get_primary_phone()
    return user.phone


class AbstractPhoneNumber(models.Model):
    "A phone number belonging to a User"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='phone_number_set',
        on_delete=models.CASCADE, verbose_name=_('user')
    )
    phone = PhoneNumberField(_('número de telefone'), null=True, blank=True, unique=True)
    key = models.CharField(max_length=50, null=True, blank=True, unique=True, verbose_name=_('chave de acesso'))

    set_at = models.DateTimeField(
        default=timezone.now,
        help_text=_('When the confirmation key expiration was set'),
        verbose_name=_('registrado em'),
    )
    confirmed_at = models.DateTimeField(
        blank=True, null=True,
        help_text=_('First time this phone was confirmed'),
        verbose_name=_('confirmado em'),
    )
    is_primary = models.BooleanField(
        default=True,
        verbose_name=_('principal'))

    objects = PhoneNumberManager()

    class Meta:
        unique_together = (('user', 'phone'),)
        verbose_name_plural = _("números de telefone")
        abstract = True

    def save(self, *args, **kwargs):
        # Empty strings are not unique, but we can save multiple NULLs
        # This will check for empty values on the model's concrete fields and set them to None
        for field in self._meta.concrete_fields:
            field_val = getattr(self, field.name)
            if field_val is not None and str(field_val).strip() == '':
                setattr(self, field.name, None)
        super().save(*args, **kwargs)

    def __str__(self):
        return '{} <{}>'.format(self.user, self.phone)

    # def _is_confirmed(self):
    #     return self.confirmed_at is not None
    # _is_confirmed.short_description = _('Confirmado')
    # _is_confirmed.boolean = True
    # is_confirmed = property(_is_confirmed)

    @property
    def is_phone_confirmed(self):
        return self.confirmed_at is not None

    @property
    def key_expires_at(self):
        # By default, keys don't expire. If you want them to, set
        # settings.SIMPLE_PHONE_CONFIRMATION_PERIOD to a timedelta.
        period = getattr(
            settings, 'SIMPLE_PHONE_CONFIRMATION_PERIOD', None # TODO: Resolve if is a good idea to unify email and phone confirmation variables like this
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
        self.key = get_phone_number_model()._default_manager.generate_key(self.user)
        self.set_at = timezone.now()

        self.confirmed_at = None
        self.save(update_fields=['key', 'set_at', 'confirmed_at'])
        return self.key


# class PhoneNumber(AbstractPhoneNumber):
#     class Meta(AbstractPhoneNumber.Meta):
#         swappable = 'SIMPLE_PHONE_CONFIRMATION_PHONE_NUMBER_MODEL'


# by default, auto-add unconfirmed PhoneNumber objects for new Users
if getattr(settings, 'SIMPLE_PHONE_CONFIRMATION_AUTO_ADD', True):
    def auto_add(sender, **kwargs):
        if sender == get_user_model() and kwargs['created'] and not kwargs['raw']:
            user = kwargs.get('instance')
            phone = get_user_primary_phone(user)
            if phone:
                if hasattr(user, 'add_unconfirmed_phone'):
                    print('De primeira, no if mesmo')
                    user.add_unconfirmed_phone(phone)
                else:
                    print('Foi no else')
                    user.phone_number_set.create_unconfirmed(phone)

    # TODO: try to only connect this to the User model. We can't use
    #       get_user_model() here - results in import loop.

    post_save.connect(auto_add)
