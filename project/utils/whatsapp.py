import json
import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from phonenumber_field.phonenumber import PhoneNumber
from phonenumber_field.validators import validate_international_phonenumber

BASE_URL = f'https://api.z-api.io/instances/{settings.WHATSAPP_API_INSTANCE}/token/{settings.WHATSAPP_API_TOKEN}'
# BASE_URL = f"https://api.whatsweb.app/send/pqh7hcx/?"

def format_phone(phone, timeout=5):

    # Raises a validation error if the number is not valid:
    validate_international_phonenumber(phone)

    # Format the number as the z-API expects, like e164 without the '+' signal
    phone = PhoneNumber.from_string(str(phone)).as_e164.strip('+') # That way it doesn't matter if given phone is a string or a Phonenumber object

    return phone

    # # Uses the z-API to verify if the number exists on WhatsApp
    # path = 'phone-exists/'
    # response = requests.get(url = f'{BASE_URL}{path}{phone}',timeout = timeout,)
    # data = json.loads(response.content.decode('utf-8')).get('exists')
    # ok = bool(data is True)
    #
    # if ok:
    #     # If the number is on WhatsApp, returns the number already formatted
    #     return phone
    # else:
    #     # Raise a validation error if the number is not on WhatsApp, even if a valid phone number:
    #     raise ValidationError('Este número de telefone não está no WhatsApp')


def check_phone(phone, timeout=5):

    # Return BOOLEAN if the given phone is on WhatsApp

    validate_international_phonenumber(phone)
    phone = PhoneNumber.from_string(phone).as_e164.strip('+')

    # Uses the Z-API to verify if the number exists on WhatsApp
    path = 'phone-exists/'
    response = requests.get(url = f'{BASE_URL}{path}{phone}',timeout = timeout,)
    data = json.loads(response.content.decode('utf-8')).get('exists')
    return data


# TODO: Deprecated until find a new API
# def validate_phone(phone, timeout=5):
#
#     # Just raises VALIDATION ERROR if the given phone is NOT on WhatsApp
#
#     validate_international_phonenumber(phone)
#     phone = PhoneNumber.from_string(phone).as_e164.strip('+')
#
#     # Uses the Z-API to verify if the number exists on WhatsApp
#     path = 'phone-exists/'
#     response = requests.get(url = f'{BASE_URL}{path}{phone}',timeout = timeout,)
#     data = json.loads(response.content.decode('utf-8')).get('exists')
#     ok = bool(data is True)
#
#     if not ok:
#         raise ValidationError('Este número de telefone não está no WhatsApp')

# TODO: Deprecated until find a new API
# def instance_status(timeout=5,):
#     path = 'status/'
#     url = f'{BASE_URL}{path}'
#     response = requests.get(url=url, timeout=timeout,)
#     # response.raise_for_status()
#     status_ok = bool(response.status_code == requests.codes.ok)
#     if status_ok:
#         print('A instância está ativa')
#     else:
#         print('Parece que a instância NÃO está ativa')
#     return status_ok


def send_message(phone, message, type='text', timeout=5):
    headers = {
        'content-type': 'application/json'
    }
    path = 'send-text'
    payload = {
        'phone': format_phone(phone),
        'message': message,
    }
    url = f"{BASE_URL}/{path}"

    # cmd = 'chat'
    # id = '11OZ6VGPF5'
    # to = '5543984049009' #f'{format_phone(phone)}'
    # msg = 'message'
    # url = f"{BASE_URL}cmd={cmd}&id={id}&to={to}@c.us&msg={msg}"

    response = requests.post(
        url = url,
        json = payload,
        headers = headers,
        timeout = timeout,
    )
    print(f'Status: {response.status_code} - {response.text}')
    response.raise_for_status()

    return response

#TODO: postar online só pra testar isso, pq dai não precisa pedir o nome pra pessoa no signup
#@require_POST
#@csrf_exempt
def on_message_received(request):
    # Get data POSTed
    json_data = json.load(request.data)  # body.decode("utf-8")
    phone = json_data['phone']
    message = json_data['text']['message']
    contact = json_data['contact']['displayName']

    # TODO: 1) Reconhecer se é um cliente já cadastrado, se é um numero novo,
    #       Caso seja identificado o cliente, verificar se há pedido em andamento...
    #       Se sim, puxar os dados do pedido. Se não, perguntar se quer abrir novo pedido.

    # TODO: 2) Tratar o que fazer quando há cada tipo de mídia na mensagem recebida...
    #       Ex: Imagem, documento, áudio, contato, localização
    #       Caso real: Clientes mandam prints do menu com suas escolhas...

    # Send e-mail to ADMINs
    # msg = '%s - Mensagem de whatsapp recebida às %s do dia %s' % (
    #     message, timezone.now().strftime("%H:%M:%S"), timezone.now().strftime("%d/%m/%y"))
    # send_mail('Mensagem de WhatsApp recebida', msg,
    #           settings.SERVER_EMAIL, settings.ADMINS,)

    data = f"{contact} Enviou ums mensagem de WhatsApp {phone}: '{message}'"
    print(data)

    return HttpResponse(f'Tenho isso pra te retornar: {data}')
