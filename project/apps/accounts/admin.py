from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
# from django.contrib.gis.db import models # production only
from import_export import resources
from import_export.admin import ImportExportActionModelAdmin
from mapwidgets import GooglePointFieldInlineWidget
from tabbed_admin import TabbedModelAdmin

from .forms import CustomAdminPasswordChangeForm, UserCreationAdminForm, \
    AddressInlineFormset, UserChangeAdminForm
from django.utils.translation import ugettext_lazy as _

from .models import PhoneNumber, EmailAddress
from ..places.models import Address
from ..sales.admin import CustomerOrderInline
from ..sales.models import Order

User = get_user_model()


class UserResource(resources.ModelResource):
    class Meta:
        model = User


class PhoneInline(admin.TabularInline):
    model = PhoneNumber
    fields = ['phone', 'is_confirmed', 'is_primary',]
    extra = 1
    # classes = ['tab-item-inline']
    readonly_fields = ['is_confirmed']

    def get_extra(self, request, obj=None, **kwargs):
        """Dynamically sets the number of extra forms. 0 if the related object
        already exists or the extra configuration otherwise."""
        if obj:
            # Don't add any extra forms if the related object already exists.
            return 0
        return self.extra


class EmailInline(admin.TabularInline):
    model = EmailAddress
    fields = ['email', 'confirmed_at',]
    extra = 1
    classes = ['tab-item-inline']

    def get_extra(self, request, obj=None, **kwargs):
        """Dynamically sets the number of extra forms. 0 if the related object
        already exists or the extra configuration otherwise."""
        if obj:
            # Don't add any extra forms if the related object already exists.
            return 0
        return self.extra


class AddressMapInline(admin.StackedInline):
    model = Address
    formset = AddressInlineFormset
    fields = ('location','address','complement', 'neighbourhood', 'city','postal_code','instructions','extra')
    extra = 0
    autocomplete_fields = ['city',]
    # formfield_overrides = {
    #     models.PointField: {"widget": GooglePointFieldInlineWidget}
    # }


class HasAddressFilter(admin.SimpleListFilter):
    title = 'Tem endereço?'
    parameter_name = 'has_address'

    def lookups(self, request, model_admin):
        return (
            ('Yes', 'Sim'),
            ('No', 'Não'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'Yes':
            return queryset.filter(user_address__id__isnull=False).distinct()
        elif value == 'No':
            return queryset.exclude(user_address__id__isnull=False).distinct()
        return queryset


@admin.register(User)
class UserAdmin(ImportExportActionModelAdmin, TabbedModelAdmin, UserAdmin):

    add_form_template = None
    add_form = UserCreationAdminForm

    change_form = UserChangeAdminForm

    change_user_password_template = None
    change_password_form = CustomAdminPasswordChangeForm

    list_display = ('get_full_name', 'phone', 'email',)
    list_editable = ('phone', 'email',)
    list_filter = ('groups', HasAddressFilter, 'addresses__city')
    search_fields = ('email', 'phone', 'first_name', 'last_name',)
    ordering = ('first_name',)
    filter_horizontal = ('groups', 'user_permissions',)
    save_on_top = True

    class Media:
        css = {
            'all': ('css/jquery-ui.theme.min.css',)
        }

    def save_related(self, request, form, formsets, change):
        obj = form.instance
        # whatever your formset dependent logic is to change obj.filedata
        obj.save()
        super().save_related(request, form, formsets, change)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['username', 'get_full_name', 'is_whatsapp',]
        else:
            return []

    # def get_form(self, request, obj=None, **kwargs):
    #     if not obj:
    #         self.form = self.add_form
    #     else:
    #         self.form = self.change_form
    #     return super().get_form(request, obj, **kwargs)

    def get_form(self, request, obj=None, **kwargs):

        if not obj:
            self.form = self.add_form
        else:
            self.form = self.change_form
        return super().get_form(request, obj, **kwargs)

        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser
        disabled_fields = set()  # type: Set[str]

        if not is_superuser:
            disabled_fields |= {
                'username',
                'is_superuser',
                'user_permissions',
            }

        # Prevent non-superusers from editing their own permissions
        if (
                not is_superuser
                and obj is not None
                and obj == request.user
        ):
            disabled_fields |= {
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
                'last_login',
                'date_joined'
            }

        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True

        return form

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'first_name', 'last_name',),
        }),
    )

    inlines = [
        AddressMapInline #, PhoneInline, EmailInline
    ]

    tab_create = (
        (None, {
            'fields': ('username', 'first_name', 'last_name',)
        }),
    )
    tab_personal = (
        (None, {
            'fields': ('first_name', 'last_name', ('phone','is_whatsapp'), 'email',),
        }),
    )
    # tab_orders = (
    #     CustomerOrderInline,
    # )
    tab_messages = ()
    # tab_contact = (
    #     PhoneInline,
    #     EmailInline,
    # )
    tab_address = (
        AddressMapInline,
    )

    tab_permissions = (
        (_('Credenciais'), {'fields': ('username', 'password',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'groups', 'user_permissions',)}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    tabs = [
        (_('Dados pessoais'), tab_create),
        (_('Dados pessoais'), tab_personal),
        # (_('Contatos'), tab_contact),
        (_('Endereço'), tab_address),
        # (_('Pedidos'), tab_orders),
        (_('Acesso ao sistema'), tab_permissions),
    ]

    def get_tabs(self, request, obj=None):
        tabs = self.tabs
        if obj is None:
            tab_create = self.tab_create
            tabs = [
                (_('Dados pessoais'), tab_create),
            ]
        else:
            tab_personal = self.tab_personal
            # tab_contact = self.tab_contact
            tab_address = self.tab_address
            # tab_orders = self.tab_orders
            tab_messages = self.tab_messages
            tab_permissions = self.tab_permissions

            tabs = [
                (_('Dados pessoais'), tab_personal),
                # (_('Contatos'), tab_contact),
                (_('Endereço'), tab_address),
                # (_('Pedidos'), tab_orders), # Let it just on customer admin
                (_('Mensagens'), tab_messages),
                (_('Acesso ao sistema'), tab_permissions),

            ]
        self.tabs = tabs
        return super().get_tabs(request, obj)

    # def changelist_view(self, request, extra_context=None):
    #     extra_context = {'title': 'Change this for a custom title.'}
    #     return super().changelist_view(request, extra_context=extra_context)
