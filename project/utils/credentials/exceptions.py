"Credential Confirmation Exceptions"


class CredentialConfirmationException(Exception):
    pass


class CredentialNotConfirmed(CredentialConfirmationException):
    pass


class CredentialConfirmationExpired(CredentialConfirmationException):
    pass


class CredentialIsPrimary(CredentialConfirmationException):
    pass