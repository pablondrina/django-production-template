from django import template
from utils.phone_confirmation.models import AbstractPhoneNumber


register = template.Library()
simple_tag = register.simple_tag


@simple_tag(takes_context=True)
def get_user_primary_phone(context):
    phone = AbstractPhoneNumber.get_primary_phone()
    return phone
