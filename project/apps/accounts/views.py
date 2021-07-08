from dal import autocomplete
from django.contrib import messages
from django.contrib.auth import get_user_model, login, update_session_auth_hash, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_protect
from django.views.generic import DetailView, UpdateView
from rules.contrib.views import AutoPermissionRequiredMixin

from apps.accounts.forms import SignUpForm, PasswordSetForm, WelcomeForm, ProfileUpdateForm
from utils.tokens import phone_activation_token, email_activation_token


User = get_user_model()


@login_required
def home_view(request):
    return render(request, 'accounts/home.html')


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)

            if '@' in form.cleaned_data.get('username'):
                token = user.confirmation_key
            else:
                token = user.phone_confirmation_key

            subject = f'Ative sua conta {current_site.name}'
            message = render_to_string('accounts/activation_message.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': token, #TODO: Vale a pena / é correto gerar o token ainda no form? Ja viria pra cá resolvido...
            })

            if '@' in form.clean_username(): #TODO: diferença pode ser tratada em uma função send_etc()
                user.email_user(subject, message)
                return redirect('accounts:activation_email_sent')
            else:
                user.whatsapp_user(subject, message)
                return redirect('accounts:activation_whatsapp_sent')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})


def activation_whatsapp_sent(request):
    return render(request, 'accounts/activation_whatsapp_sent.html')


def activation_email_sent(request):
    return render(request, 'accounts/activation_email_sent.html')

@csrf_protect
def activate(request, uidb64, token): #TODO: verificar comportamento, se está adicionando novos phones ou emails para verificação (django-allauth faz isso)
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and (phone_activation_token.check_token(user, token) or email_activation_token.check_token(user, token)):
        user.is_active = True

        # Resolve field
        if '@' in user.username or user.email:
            user.confirm_email(token)
        elif not '@' in user.username or user.phone:
            user.confirm_phone(token)
        user.save()

        # This is necessarily the first login of this user, ok.
        login(request, user, backend='apps.accounts.backends.CustomAuthBackend')

        # TODO: Direcionar novo usuario para resetar sua senha na ativação + Nome, por exemplo
        #  Importante: tem que ter outro jeito pra resetar a senha depois, caso ele não faça, acho que da pelas vias normais de reset password (esqueceu a senha!)
        return redirect('accounts:welcome')
    else:
        return render(request, 'accounts/invalid_activation_link.html')


def welcome_view(request):
    if request.method == 'POST':
        form = WelcomeForm(request.POST, instance=request.user) #PasswordSetForm
        if form.is_valid():
            first_name = request.POST.get("first_name", "")
            last_name = request.POST.get("last_name", "")
            password1 = request.POST.get("password1", "")
            password2 = request.POST.get("password2", "")

            user = User.objects.get(pk=request.user.id)
            user.password = make_password(password2)
            user.first_name = first_name
            user.last_name = last_name
            user.save()

            # user = authenticate(username=user.username, password=raw_password)
            login(request, user, backend='apps.accounts.backends.CustomAuthBackend')

            return redirect('accounts:home')
    else:
        form = WelcomeForm(instance=request.user)

    context = {'form': form}
    return render(request, 'accounts/password_set.html', context)


@login_required
def profile_update(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            # Alert user on screen
            # messages.success(
            #     request, ('Perfil atualizado.'))
            return redirect('accounts:update')
    else:
        form = ProfileUpdateForm(instance=request.user)

    context = {'form': form}
    return render(request, 'accounts/profile/update.html', context)


def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(data=request.POST, user=request.user)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, ('Senha atualizada.'))
            return redirect('accounts:home')
    else:
        form = PasswordChangeForm(user=request.user)

    context = {'form': form}
    return render(request, 'accounts/profile/password_change.html', context)
