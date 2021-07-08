#D7 Network SMS Settings

import requests
from project import settings
import binascii


def str2hex(text):
    """Convert a string to Hex"""
    encoded = binascii.hexlify(bytes(text, "utf-8"))
    encoded = str(encoded).strip("b")
    encoded = encoded.strip("'")
    return encoded

def send_message(phone, message, timeout=5):
    # TODO: Unicode SMS not working yet, need to topup account to make more tests (payment failed, waiting a reply)
    # message = str2hex(message)
    # payload = f'{{\n\t"from":5543984049009,\n\t"to":{phone}\n,\n\t"coding":"8",\n\t"hex-content":"{str2hex(message)}"}}'

    url = "https://rest-api.d7networks.com/secure/send"
    payload = f'{{\n\t"from":5543984049009,\n\t"to":{phone}\n,\n\t"content":"{message}"}}'
    headers = {
      # 'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': settings.SMS_API_TOKEN
    }
    response = requests.post(
        url=url,
        headers=headers,
        data=payload,
        timeout=timeout,
    )

    print(response.text.encode('utf8'))
