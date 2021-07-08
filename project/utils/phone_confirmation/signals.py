from django.dispatch import Signal

phone_confirmed = Signal(providing_args=['user', 'phone'])
unconfirmed_phone_created = Signal(providing_args=['user', 'phone'])
primary_phone_changed = Signal(
    providing_args=['user', 'old_phone', 'new_phone'],
)