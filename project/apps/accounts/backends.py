from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import HttpResponse

User = get_user_model()


class CustomAuthBackend(BaseBackend):
    def authenticate(self, request, **kwargs):
        credential = kwargs['username'].lower()  # If you made email case insensitive add lower()
        password = kwargs['password']
        try:
            my_user = User.objects.get(Q(phone=credential) | Q(email=credential))
        except Exception:
            return None
        else:
            if my_user.is_email_confirmed or my_user.is_phone_confirmed: #and my_user.is_first_login
                if my_user.check_password(password): #my_user.is_active and
                    return my_user
            else:
                raise ValidationError('Credencial não verificada. Use o link de verificação enviado para liberar o acesso')
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except Exception:
            return None


class EmailAuthBackend(BaseBackend):
    def authenticate(self, request, **kwargs):
        email = kwargs['username'].lower()  # If you made email case insensitive add lower()
        password = kwargs['password']
        try:
            my_user = User.objects.get(email=email)
        except Exception:
            # raise ValidationError('Endereço de email não encontrado')
            return None
        else:
            if my_user.is_email_confirmed:
                if my_user.is_active and my_user.check_password(password):
                    return my_user
            else:
                raise ValidationError('Email não verificado. Use o link de verificação enviado para liberar o acesso')
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except Exception:
            return None
