"Simple Phone Confirmation Exceptions"


class SimplePhoneConfirmationException(Exception):
    pass


class PhoneNotConfirmed(SimplePhoneConfirmationException):
    pass


class PhoneConfirmationExpired(SimplePhoneConfirmationException):
    pass


class PhoneIsPrimary(SimplePhoneConfirmationException):
    pass