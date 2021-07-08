from django.contrib import admin

from . import get_phone_number_model


class PhoneNumberAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'key', 'set_at', 'confirmed_at')
    search_fields = ('phone', 'key')


admin.site.register(get_phone_number_model(), PhoneNumberAdmin) #TODO: Update to decorator registration