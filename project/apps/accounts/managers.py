from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from phonenumber_field.phonenumber import PhoneNumber
from phonenumber_field.validators import validate_international_phonenumber


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, password,
                     is_staff, is_superuser, **extra_fields):
        """ Create EmailPhoneUser with the given email or phone and password.
        :param str email_or_phone: user email or phone
        :param str password: user password
        :param bool is_staff: whether user staff or not
        :param bool is_superuser: whether user admin or not
        :return settings.AUTH_USER_MODEL user: user
        :raise ValueError: email or phone is not set
        :raise NumberParseException: phone does not have correct format
        """
        if not username:
            raise ValueError(_('The given username must be set'))

        if "@" in username:
            username = self.normalize_email(username)
            username, email, phone = (username, username, "")
        else:
            username = PhoneNumber.from_string(username).as_e164
            username, email, phone = (username, "", username)

        now = timezone.now()
        is_active = extra_fields.pop("is_active", True)
        user = self.model(
            username=username,
            email=email,
            phone=phone,
            is_staff=is_staff,
            is_active=is_active,
            is_superuser=is_superuser,
            # last_login=now,
            # date_joined=now,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        return self._create_user(username, password, False, False,)# **extra_fields)

    def create_superuser(self, username, password, **extra_fields):
        return self._create_user(username, password, True, True,)# **extra_fields)
