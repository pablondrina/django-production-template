from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.tokens import default_token_generator
from django.contrib.gis.geos import Point
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import ReadOnlyPasswordHashField, AdminPasswordChangeForm, UserCreationForm, \
    UsernameField, UserChangeForm, PasswordChangeForm, SetPasswordForm, _unicode_ci_compare
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from mapwidgets import GooglePointFieldWidget
from phonenumber_field.phonenumber import PhoneNumber
from phonenumber_field.validators import validate_international_phonenumber

from apps.places.models import Address, Country, State, City
from utils import whatsapp, functions

User = get_user_model()


class UserChangeAdminForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        label=_("Password"),
        help_text=_('Senhas brutas não são armazenadas, então não há como visualizar a senha desse usuário, '
                    'porém você pode mudar a senha usando &nbsp;<a href=\"../password/\">&nbsp; esse formulário</a>.'),
    )
    # 'Raw passwords are not stored, so there is no way to see this user’s password, but you can change the
    # password using <a href="{}"> this form</a>.'

    class Meta:
        model = User
        fields = '__all__'
        labels = {
            'username': _('Nome de usuário'),
            'phone': _('Telefone principal'),
            'email': _('Email principal'),
            'avatar': _('Foto'),
            'last_login': _('Último acesso'),
        }
        field_classes = {'username': UsernameField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        password = self.fields.get('password')
        if password:
            password.help_text = password.help_text.format('../password/')
        user_permissions = self.fields.get('user_permissions')
        if user_permissions:
            user_permissions.queryset = user_permissions.queryset.select_related('content_type')

    # def save_model(self, request, obj, form, change):
    #     pass # don't actually save the parent instance
    #
    # def save_formset(self, request, form, formset, change):
    #     formset.save() # this will save the children
    #     form.instance.save() # form.instance is the parent

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        try:
            if phone:
                validate_international_phonenumber(phone)
                return phone
        except Exception:
            raise ValidationError ('Zulimou aqui')
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            if email:
                validate_email(email)
        except ValidationError:
            raise
        return email


class UserCreationAdminForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('username','first_name', 'last_name',)
        # exclude = ('password1', 'password2')

    username = forms.CharField(
        label=_('Telefone (ou email)'),
        help_text=_('Telefone com DDD, preferencialmente WhatsApp')
    )

    first_name = forms.CharField(
        label=_('Nome'),
        help_text=_('Será usado em mensagens')
    )


    def clean_username(self):
        username = self.cleaned_data.get('username')

        try:
            if "@" in username:
                validate_email(username)
            else:
                # whatsapp.validate_phone(username)  # Tries to validate through z-API
                validate_international_phonenumber(username) # If there is no connection, validates just the phonenumber
                username = PhoneNumber.from_string(username).as_e164
        except ValidationError:
            raise

        if User.objects.filter(Q(username=username) | Q(phone=username) | Q(email=username)).exists():
            credential_type = functions.get_credential_type(username)
            self.add_error('username', ValidationError(f'Este {credential_type} já é usado como credencial de acesso por outro usuário.', code='unique'))

        return username


class CustomAdminPasswordChangeForm(AdminPasswordChangeForm):
    '''
    Django não permitiu usar o 'form' nativo.
    Então só exibiu normalmente os campos para alteração
    de senha quando herdei aqui (mesmo que apenas dando 'pass')
    '''
    pass


class SignUpForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('username',) # 'password1', 'password2', )

    def clean_username(self):
        username = self.cleaned_data.get('username')

        try:
            if "@" in username:
                validate_email(username)
            else:
                # whatsapp.validate_phone(username)  # TODO: Try to validate through some WhatsApp API (z-API deprecated)
                validate_international_phonenumber(username) # If there is no connection, validates just the phonenumber
                username = PhoneNumber.from_string(username).as_e164
        except ValidationError:
            raise

        if User.objects.filter(Q(username=username) | Q(phone=username) | Q(email=username)).exists():
            credential_type = functions.get_credential_type(username)
            self.add_error('username', ValidationError(f'Este {credential_type} já é usado como credencial de acesso por outro usuário.', code='unique'))

        return username


class AddressInlineForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = '__all__'

class AddressInlineFormset(forms.models.BaseInlineFormSet):
    class Meta:
        model = Address
        fields = ('geodata', 'location', 'address', 'complement', 'neighbourhood', 'instructions', 'postal_code', 'city',)
        widgets = {
            'location': GooglePointFieldWidget,
        }

    geodata = forms.CharField(
        widget=forms.Textarea(
            attrs={'hidden':'true'}),
            label='',
            required=False,
        )

    def clean_location(self):
        return self.cleaned_data.get('location')

    def clean_address(self):
        if 'location' in self.changed_data:
            return self.cleaned_data.get('geodata')[0]
        else:
            return self.cleaned_data.get('address')

    def clean_complement(self):
        if 'location' in self.changed_data:
            return self.cleaned_data.get('geodata')[1]
        else:
            return self.cleaned_data.get('complement')

    def clean_neighbourhood(self):
        return self.cleaned_data.get('geodata')[2]

    def clean_city(self):
        if self.cleaned_data.get('geodata'):
            _city = str(self.cleaned_data.get('geodata')[3])
            _state = str(self.cleaned_data.get('geodata')[4].upper())[0:2]
            _state_long = str(self.cleaned_data.get('geodata')[5])
            _country = str(self.cleaned_data.get('geodata')[6].upper())[0:2]
            _country_long = str(self.cleaned_data.get('geodata')[7])

            my_country, country_created = Country.objects.get_or_create(code=_country, name=_country_long)
            my_state, state_created = State.objects.get_or_create(code=_state, name=_state_long)
            my_city, city_created = City.objects.get_or_create(state=my_state, country=my_country, name=_city)

            return my_city
        else:
            return self.cleaned_data.get('city')

    def clean_postal_code(self):
        return self.cleaned_data.get('geodata')[8]

    def clean_instructions(self):
        # a = self.cleaned_data.get('location')
        # b = self.cleaned_data.get('geodata')
        # return f"Address:{a}\n\n Coords:{a.y}, {a.x} \n\n Raw data:{b}"
        return self.cleaned_data.get('instructions')

    def clean_geodata(self):
        location = self.cleaned_data.get('location')
        coords = f"{location.y},{location.x}"

        import geopy
        geolocator = geopy.GoogleV3(api_key=settings.GOOGLE_MAPS_API_KEY)
        response = geolocator.reverse(coords,language='pt-br',)

        if response is not None:
            components = response.raw['address_components']
            address = {}
            for component in components:
                for type in component['types']:
                    address[f"{type}"] = component['short_name']
                    # address[f"{type}_long"] = component['long_name'] # Se for assim, tudo vem com a opção long, mesmo que obsoleta/duplicada
                    if 'country' in type:
                        address[f"{type}"] = component['short_name']
                        address[f"{type}_long"] = component['long_name']
                    if 'administrative_area_level_1' in type:
                        address[f"{type}"] = component['short_name']
                        address[f"{type}_long"] = component['long_name']

            address_route = ''
            address_street_number = ''
            address_sublocality = ''
            address_premise = ''
            address_subpremise = ''
            address_city = ''
            address_state = ''
            address_country = ''
            address_postal_code = ''

            if 'route' in address:
                address_route = address['route']
            if 'street_number' in address:
                address_street_number = address['street_number']
            if 'sublocality' in address:
                address_sublocality = address['sublocality_level_1'] or address['sublocality']
            if 'premise' in address:
                address_premise =  address['premise']
            if 'subpremise' in address:
                address_subpremise = address['subpremise']
            if 'administrative_area_level_2' in address:
                address_city = address['administrative_area_level_2']
            if 'administrative_area_level_1' in address:
                address_state = address['administrative_area_level_1']
            if 'administrative_area_level_1_long' in address:
                address_state_long = address['administrative_area_level_1_long']
            if 'country' in address:
                address_country = address['country']
            if 'country_long' in address:
                address_country_long = address['country_long']
            if 'postal_code' in address:
                address_postal_code = address['postal_code']

            address_line1 = f"{address_route}, {address_street_number}"

            if address_premise and not address_subpremise:
                address_line2 = f"{address_premise}"
            elif address_premise and address_subpremise:
                address_line2 = f"{address_premise}, {address_subpremise}"
            elif address_subpremise and not address_premise:
                address_line2 = f"{address_subpremise}"
            else:
                address_line2 = ''

            lat = response.raw['geometry']['location']['lat']
            lng = response.raw['geometry']['location']['lng']
            # coords = fromstr(f"POINT({lng}, {lat})", srid=4326)

            coords = Point(lng, lat, srid=4326)

            return address_line1,\
                   address_line2,\
                   address_sublocality,\
                   address_city, \
                   address_state, \
                   address_state_long, \
                   address_country, \
                   address_country_long, \
                   address_postal_code,\
                   coords,\
                   response.raw['formatted_address'],\
                   response.raw

    # def update_address_fields(self):
    #     location = self.cleaned_data.get('location')
    #     coords = f"{location.y},{location.x}"
    #
    #     import geopy
    #     geolocator = geopy.GoogleV3(api_key=settings.GOOGLE_MAPS_API_KEY)
    #     response = geolocator.reverse(coords,language='pt-br',)
    #
    #     if response is not None:
    #         components = response.raw['address_components']
    #         address = {}
    #         for component in components:
    #             for type in component['types']:
    #                 address[f"{type}"] = component['short_name']
    #                 # address[f"{type}_long"] = component['long_name'] # Se for assim, tudo vem com a opção long, mesmo que obsoleta/duplicada
    #                 if 'country' in type:
    #                     address[f"{type}"] = component['short_name']
    #                     address[f"{type}_long"] = component['long_name']
    #                 if 'administrative_area_level_1' in type:
    #                     address[f"{type}"] = component['short_name']
    #                     address[f"{type}_long"] = component['long_name']
    #
    #         address_route = ''
    #         address_street_number = ''
    #         address_sublocality = ''
    #         address_premise = ''
    #         address_subpremise = ''
    #         address_city = ''
    #         address_state = ''
    #         address_country = ''
    #         address_postal_code = ''
    #
    #         if 'route' in address:
    #             address_route = address['route']
    #         if 'street_number' in address:
    #             address_street_number = address['street_number']
    #         if 'sublocality' in address:
    #             address_sublocality = address['sublocality_level_1'] or address['sublocality']
    #         if 'premise' in address:
    #             address_premise =  address['premise']
    #         if 'subpremise' in address:
    #             address_subpremise = address['subpremise']
    #         if 'administrative_area_level_2' in address:
    #             address_city = address['administrative_area_level_2']
    #         if 'administrative_area_level_1' in address:
    #             address_state = address['administrative_area_level_1']
    #         if 'administrative_area_level_1_long' in address:
    #             address_state_long = address['administrative_area_level_1_long']
    #         if 'country' in address:
    #             address_country = address['country']
    #         if 'country_long' in address:
    #             address_country_long = address['country_long']
    #         if 'postal_code' in address:
    #             address_postal_code = address['postal_code']
    #
    #         address_line1 = f"{address_route}, {address_street_number}"
    #
    #         if address_premise and not address_subpremise:
    #             address_line2 = f"{address_premise}"
    #         elif address_premise and address_subpremise:
    #             address_line2 = f"{address_premise}, {address_subpremise}"
    #         elif address_subpremise and not address_premise:
    #             address_line2 = f"{address_subpremise}"
    #         else:
    #             address_line2 = ''
    #
    #         lat = response.raw['geometry']['location']['lat']
    #         lng = response.raw['geometry']['location']['lng']
    #         # coords = fromstr(f"POINT({lng}, {lat})", srid=4326)
    #
    #         coords = Point(lng, lat, srid=4326)
    #
    #         print('Foi até o fim da função...')
    #         # return address_line1,\
    #         #        address_line2,\
    #         #        address_sublocality,\
    #         #        address_city, \
    #         #        address_state, \
    #         #        address_state_long, \
    #         #        address_country, \
    #         #        address_country_long, \
    #         #        address_postal_code,\
    #         #        coords,\
    #         #        response.raw['formatted_address'],\
    #         #        response.raw

class PasswordSetForm(SetPasswordForm):

    class Meta:
        model = User
        fields = ('new_password1', 'new_password2', )


class WelcomeForm(UserChangeForm):
    # password = forms.CharField(label="", widget=forms.TextInput(attrs={'type': 'hidden'}))

    password = ReadOnlyPasswordHashField(
        label=_(""),
        help_text=_("É necessário definir uma senha para poder utilizar sua nova conta."),
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', ) # 'password1', 'password2')

    error_messages = {
        'password_mismatch': _('The two password fields didn’t match.'),
        'first_name_required': _('Queremos chamar você pelo nome.'),
    }

    password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    first_name = forms.CharField(label=_('Nome'), required=True)
    last_name = forms.CharField(label=_('Sobrenome'), required=False, error_messages={"required": "Queremos te chamar pelo nome :)"})

    def clean_password2(self):
        if self.cleaned_data.get('password2') != self.cleaned_data.get('password1'):
            raise ValidationError(self.error_messages['password_mismatch'], code='password_mismatch')
        else:
            return self.cleaned_data.get('password2')


class ProfileUpdateForm(UserChangeForm):
    password = forms.CharField(label="", widget=forms.TextInput(attrs={'type': 'hidden'}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone', 'email', 'password')


class PwdResetForm(forms.Form):

    credential = forms.CharField(
        label=_("Whatsapp (ou email):"),
        max_length=254,
        widget=forms.TextInput(attrs={'autocomplete': ('email', 'phone')})
    )

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """
        Send a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
        if html_email_template_name is not None:
            html_email = loader.render_to_string(html_email_template_name, context)
            email_message.attach_alternative(html_email, 'text/html')

        email_message.send()

    def get_users(self, credential):
        """Given an email, return matching user(s) who should receive a reset.

        This allows subclasses to more easily customize the default policies
        that prevent inactive users and users with unusable passwords from
        resetting their password.
        """
        if '@' in self.cleaned_data.get('credential'):
            credential_field_name = User.get_email_field_name()
        else:
            credential_field_name = 'phone'

        active_users = User._default_manager.filter(**{
            '%s__iexact' % credential_field_name: credential,
            'is_active': True,
        })
        return (
            u for u in active_users
            if u.has_usable_password() and
            _unicode_ci_compare(credential, getattr(u, credential_field_name))
        )

    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None, html_email_template_name=None,
             extra_email_context=None):
        """
        Generate a one-use only link for resetting password and send it to the
        user.
        """
        credential = self.cleaned_data["credential"]
        if not domain_override:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override

        if '@' in self.cleaned_data.get('credential'):
            credential_field_name = User.get_email_field_name()
        else:
            credential_field_name = 'phone'

        for user in self.get_users(credential):
            user_email = getattr(user, credential_field_name)
            context = {
                'email': user_email,
                'domain': domain,
                'site_name': site_name,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
                **(extra_email_context or {}),
            }
            self.send_mail(
                subject_template_name, email_template_name, context, from_email,
                user_email, html_email_template_name=html_email_template_name,
            )