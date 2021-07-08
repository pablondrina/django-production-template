from django.contrib.auth import get_user_model, login
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, redirect
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string

from apps.accounts.forms import SignUpForm
from utils.tokens import account_activation_token


User = get_user_model()


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            subject = f'Ative sua conta {current_site.name}'
            message = render_to_string('accounts/account_activation_phone.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': user.phone_confirmation_key, #TODO: tratar diferenciação de email/phone. Aqui é Crítico!
            })
            user.whatsapp_user(subject, message) #TODO: If para verificar, se email ou phone, como vai enviar...
            # email_user()
            return redirect('accounts/account_activation_sent')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})

def account_activation_sent(request):
    return render(request, 'accounts/account_activation_sent.html')

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.is_staff = True # TODO tirar isso!
        user.confirm_phone(token) #TODO: If para verificar, se email ou phone, como vai confirmar...
        # user.confirm_email(token)
        user.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('admin:index')
    else:
        return render(request, 'account_activation_invalid.html')