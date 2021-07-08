from django.contrib.auth.decorators import login_required
from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views
from apps.accounts import views as accounts
from apps.accounts.forms import PwdResetForm

app_name = 'accounts'

urlpatterns = [
    # Home
    path('', accounts.home_view, name="home"),

    # Auth
    path('cadastrar-se/', accounts.signup_view, name='signup'),
    path('entrar/', auth_views.LoginView.as_view(), name='login'),
    path('sair/', auth_views.LogoutView.as_view(), name='logout'),

    path('perfil/', login_required(accounts.profile_update), name='update'),

    path('ativar/whatsapp/', accounts.activation_whatsapp_sent, name='activation_whatsapp_sent'),
    path('ativar/email/', accounts.activation_email_sent, name='activation_email_sent'),
    path('ativar/<uidb64>/<token>/', accounts.activate, name='activate'),
    path('completar/', accounts.welcome_view, name='welcome'),

    path('senha/alterar/', accounts.change_password, name='password_change'),

    path('senha/recuperar/', auth_views.PasswordResetView.as_view(template_name='registration/pwd_reset_form.html',
                                                                  email_template_name='registration/pwd_reset_email.html',
                                                                  success_url = reverse_lazy('accounts:pwd_reset_done'),
                                                                  form_class = PwdResetForm
                                                                  ), name='pwd_reset_form'),
    path('senha/recuperar/solicitado/', auth_views.PasswordResetDoneView.as_view(template_name='registration/pwd_reset_done.html',), name='pwd_reset_done'),
    path('senha/recuperar/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/pwd_reset_confirm.html',
                                                                                            success_url = reverse_lazy('accounts:pwd_reset_complete')
                                                                                          ), name='pwd_reset_confirm'),
    path('senha/recuperar/concluido/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/pwd_reset_complete.html'), name='pwd_reset_complete'),

    # path('user-tag-autocomplete/', accounts.UserTagAutocomplete.as_view(), name='user-tag-autocomplete',),

]
