from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import validate_email
from django.db.models import ProtectedError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from phonenumber_field.validators import validate_international_phonenumber
from project.utils.phone_confirmation.models import SimplePhoneConfirmationUserMixin, AbstractPhoneNumber
from project.utils.email_confirmation.models import SimpleEmailConfirmationUserMixin, AbstractEmailAddress
from project.utils import whatsapp
from .managers import UserManager


def validate_username(value):
    if "@" in value:
        validate_email(value)
    else:
        validate_international_phonenumber(value)


class CustomerManager(models.Manager):
    def get_queryset(self):
        return User.objects.filter(groups__name__in=['cliente'])

    @classmethod
    def normalize_email(cls, email):
        """
        Normalize the email address by lowercasing the domain part of it.
        """
        email = email or ''
        try:
            email_name, domain_part = email.strip().rsplit('@', 1)
        except ValueError:
            pass
        else:
            email = email_name + '@' + domain_part.lower()
        return email


class User( SimpleEmailConfirmationUserMixin, SimplePhoneConfirmationUserMixin, AbstractUser):
    username = models.CharField(
        _('whatsapp (ou email)'), max_length=128, unique=True, db_index=True,
        help_text=_('Requerido. Informe um número de whatsapp (com DDD) ou um email válido.'),
        validators=[validate_username],
        error_messages={
            'unique': _("Um usuário com este email ou telefone já existe."),
        })

    phone = PhoneNumberField(_('número de telefone'), blank=True, null=True, unique=True)
    email = models.EmailField(_('endereço de email'), null=True, blank=True, unique=True)
    # email_confirmed = models.BooleanField(default=False)

    cpf = models.CharField(_('CPF').upper(), validators=[], max_length=16, null=True, blank=True, )#unique=True, )

    first_name = models.CharField(_('nome'), max_length=32, blank=True, help_text=_('Será usado em mensagens'))
    last_name = models.CharField(_('sobrenome'), max_length=32, blank=True)

    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    last_login = models.DateTimeField(_('last login'), null=True, blank=True)

    is_active = models.BooleanField(_('ativo'), default=True, help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))
    is_staff = models.BooleanField(_('membro da equipe'), default=False, help_text=_('Designates whether the user can log into this admin '
                    'site.'))

    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    date_of_birth = models.DateField(blank=True, null=True)

    # addresses = models.ManyToManyField(
    #     'places.Address', verbose_name=_('Endereços'), blank=True, related_name="user_addresses", limit_choices_to={'user': 1})

    objects = UserManager()
    customers = CustomerManager()

    USERNAME_FIELD = 'username'

    class Meta:
        verbose_name = _('usuário')
        verbose_name_plural = _('usuários')
        ordering = ('first_name',)

    def __str__(self):
        verbose_phone =''
        if self.phone:
            verbose_phone = f' • {str(self.phone.as_national)}'
        if self.first_name:
            if self.last_name:
                return f'{self.first_name} {self.last_name}{verbose_phone}'
            else:
                return f'{self.first_name}{verbose_phone}'
        elif self.phone:
            return str(self.phone.as_national)
        elif self.email:
            return self.email
        else:
            return f"<id: {self.pk}>"

    def save(self, *args, **kwargs):
        # Empty strings are not unique, but we can save multiple NULLs
        # This will check for empty values on the model's concrete fields and set them to None

        # for field in self._meta.concrete_fields:
        #     field_val = getattr(self, field.name)
        #     if field_val is not None and str(field_val).strip() == '':
        #         if field_val == 'password':
        #             setattr(self, field.name, None)
        #             User.set_unusable_password()
        #         else:
        #             setattr(self, field.name, None)

        # The above snippet was causing problems with users with unset password,
        # so I did the same only to the fields that matter:
        if self.phone is not None and str(self.phone).strip() == '':
            self.phone = None

        if self.email is not None and str(self.email).strip() == '':
            self.email = None

        self.get_new_username() # Atualiza o username para qualquer atualização de email ou telefone, nessa ordem.
        self.assign_username_data()

        super().save(*args, **kwargs)  # Call the "real" save() method.

    # def get_absolute_url(self):
    #     from django.urls import reverse
    #     return reverse('accounts:update', args=[str(self.id)])

    # TODO: Melhorar esse tratamento de erro!
    def avoid_delete_sentinel_customer(self):
        obj = User.objects.get(first_name=settings.DEFAULT_SENTINEL_CUSTOMER_NAME)
        if self.first_name == settings.DEFAULT_SENTINEL_CUSTOMER_NAME:
            raise ProtectedError('Não é permitido excluir o usuário padrão', protected_objects=obj)

    def add_address(self, address):
        if address not in self.addresses.all():
            self.addresses.add(address)
            self.save()
        return self

    def is_whatsapp(self):
        # return whatsapp.check_phone(self.phone.as_e164)
        return None #TODO: Until find a new API
    is_whatsapp.boolean = True
    is_whatsapp.short_description = 'WhatsApp?'
    # is_whatsapp = property(is_whatsapp)

    def whatsapp_user(self, subject, message, **kwargs):
        """Send a whatsapp to this user."""
        subject = f'*{subject}*'
        message = subject + message
        whatsapp.send_message(self.phone, message, type='text', timeout=5)

    # def sms_user # TODO: If needed, as chosen by user in signup form

    def get_full_name(self):
        if self.first_name:
            if self.last_name:
                return f'{self.first_name} {self.last_name}'
            else:
                return self.first_name
    get_full_name.short_description = 'nome completo'
    get_full_name.admin_order_field = 'first_name'
    full_name = property(get_full_name)

    def get_new_username(self):
        if self.phone:  # Atualiza o username para toda atualização de telefone.
            mystring = str(self.phone)
            self.username = mystring
            User.objects.filter(id=self.pk).update(username=mystring)
        elif self.email: # Atualiza o username para toda atualização de email, sendo que telefone prevalesce.
            mystring = self.email
            self.username = mystring
            User.objects.filter(id=self.pk).update(username=mystring)
            # self.assign_unconfirmed_email()

    def assign_username_data(self):
        if "@" in self.username:
            self.email = self.username
        else:
            if not self.email and not self.phone:
                self.phone = self.username


class PhoneNumber(AbstractPhoneNumber):
    class Meta(AbstractPhoneNumber.Meta):
        swappable = 'SIMPLE_PHONE_CONFIRMATION_PHONE_NUMBER_MODEL'
        verbose_name = _('Telefone')
        verbose_name_plural = _('Telefones')


class EmailAddress(AbstractEmailAddress):
    class Meta(AbstractEmailAddress.Meta):
        swappable = 'SIMPLE_EMAIL_CONFIRMATION_EMAIL_ADDRESS_MODEL'
        verbose_name = _('Email')
        verbose_name_plural = _('Emails')
