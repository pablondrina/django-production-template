from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six


class PhoneActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
                six.text_type(user.pk) + six.text_type(timestamp) +
                six.text_type(user.is_phone_confirmed)
        )



class EmailActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.is_email_confirmed)
        )


phone_activation_token = PhoneActivationTokenGenerator()
email_activation_token = EmailActivationTokenGenerator()