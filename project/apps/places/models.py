import geopy
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from project import settings


def get_default_city():
    return City.objects.get_or_create(name=settings.base.DEFAULT_CITY)[0].id

def get_default_state():
    return State.objects.get_or_create(code=settings.base.DEFAULT_STATE_CODE, name=settings.base.DEFAULT_STATE)[0].code

def get_default_country():
    return Country.objects.get_or_create(code=settings.base.DEFAULT_COUNTRY_CODE, name=settings.base.DEFAULT_COUNTRY)[0].code

# def get_default_address_tag():
#     return AddressTag.objects.get_or_create(name=settings.DEFAULT_ADDRESS_TAG)[0].id

def get_help_text(choicelist):
    n = 0  # Position of the item on the list. Zero is the first position.
    output = ''
    for i in choicelist:
        choice = str(i[n]) + ' = ' + str(i[n+1]) + '; '
        output += choice
    return output


class Address(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, verbose_name=_(
        'Usuário'), blank=True, null=True, related_name="user_address")
    location = models.PointField(_('localização'), null=True, blank=True, help_text=_(''))
    address = models.CharField(_('endereço'), max_length=256, null=True, blank=True, help_text=_('Rua e número'))
    complement = models.CharField(_('complemento'), max_length=256, null=True, blank=True, help_text=_('Apto, bloco, casa'))
    neighbourhood = models.CharField(_('bairro'), max_length=256, null=True, blank=True)
    city = models.ForeignKey('City', on_delete=models.SET_NULL, verbose_name=_(
        'Cidade'), default=get_default_city, null=True, blank=True)

    postal_code = models.CharField(_('código postal'), max_length=16, null=True, blank=True)
    instructions = models.CharField(_('ponto de referência'), max_length=256, null=True, blank=True, help_text=_('Ou alguma informação que devemos saber ao entregar o pedido.'))
    extra = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _('Endereço')
        verbose_name_plural = _('Endereços')

    def __str__(self):
        return f'{self.address}, {self.complement}, {self.city}'

    def get_coords(self):
        if self.location:
            return f"({self.location.y} {self.location.x})"
    get_coords.short_description = 'coordenadas'
    coords = property(get_coords)

    def get_address_line1(self):
        if self.address:
            B = f"{self.address}"
        else:
            B = ''

        if self.complement:
            C = f", {self.complement}"
        else:
            C = ''
        return B+C
    # get_address_line1.short_description = 'Endereço Linha 1'
    address_line1 = property(get_address_line1)

    def get_address_line2(self):
        if self.neighbourhood:
            D = f"{self.neighbourhood}, "
        else:
            D = ''

        if self.city:
            E = f"{self.city}"
        else:
            E = ''
        return D+E
    # get_address_line2.short_description = 'Endereço Linha 2'
    address_line2 = property(get_address_line2)

    def get_local_address(self):
        if self.neighbourhood:
            D = f", {self.neighbourhood}"
        else:
            D = ''

        return self.address_line1+D

    local_address = property(get_local_address)

class Country(models.Model):
    code = models.CharField(_('Código internacional'),
                            max_length=2,
                            primary_key=True,
                            help_text=_('Código de duas letras, conforme ISO 3166-1 alpha-2'))
    name = models.CharField(_('Nome'), max_length=32, blank=False)

    class Meta():
        verbose_name = _('País')
        verbose_name_plural = _('Países')

    def __str__(self):
        return f"[{self.code}] {self.name}"


class State(models.Model):
    code = models.CharField(_('Sigla'),
                            max_length=2,
                            primary_key=True,
                            help_text=_('Código de duas letras.'))
    name = models.CharField(_('Nome'), max_length=32, blank=False)

    class Meta():
        verbose_name = _('UF')
        verbose_name_plural = _("UFs")

    def __str__(self):
        return self.code


class City(models.Model):
    name = models.CharField(_('Nome'), max_length=32, blank=False)
    state = models.ForeignKey('State', on_delete=models.CASCADE, verbose_name=_(
        'UF'), default=get_default_state, blank=True, null=True)
    country = models.ForeignKey('Country', on_delete=models.CASCADE, verbose_name=_(
        'País'), default=get_default_country, blank=True, null=True)

    class Meta():
        verbose_name = _('Cidade')
        verbose_name_plural = _("Cidades")

    def __str__(self):
        return f"{self.name} - {self.state}"


class Neighbourhood(models.Model):
    name = models.CharField(_('Nome'), max_length=64, blank=False, unique=True)
    # city = models.ForeignKey('City', on_delete=models.CASCADE, verbose_name=_('Cidade'), blank=True, null=True)

    class Meta():
        verbose_name = _('Bairro')
        verbose_name_plural = _("Bairros")

    def __str__(self):
        return f"{self.name}" # ({self.city})"
