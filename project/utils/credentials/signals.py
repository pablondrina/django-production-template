from django.dispatch import Signal

credential_confirmed = Signal(providing_args=['user', 'username']) #TODO: Verificar essa referência
unconfirmed_credential_created = Signal(providing_args=['user', 'username'])
primary_credential_changed = Signal(
    providing_args=['user', 'old_credential', 'new_credential'],
)