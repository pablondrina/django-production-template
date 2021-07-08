# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.cache import cache, caches


def app_cache():
    return caches['utils'] if 'utils' in settings.CACHES else cache


def del_cached_primary_phone():
    app_cache().delete('utils_phone_confirmation')


def get_cached_primary_phone():
    return app_cache().get('utils_phone_confirmation', None)


def set_cached_primary_phone(phone):
    app_cache().set('utils_phone_confirmation', phone)
