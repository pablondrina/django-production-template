import requests, json
from project import settings


def send_message(phone, message, timeout=5):
    # Send text message to a phone number

    url = "https://api.wassenger.com/v1/messages"
    payload = f'{{\"phone\":\"{phone}\",\"message\":\"{message}\"}}'
    headers = {
        'content-type': 'application/json',
        'token': settings.WASSENGER_API_KEY
        }
    response = requests.post(
        url,
        data=payload.encode('utf-8'),
        headers=headers,
        timeout=timeout,
    )

    print(response.text)

    return response.ok


# Examples requires to have installed requests Python package.
# Install it by running: pip install requests

def get_contact(phone, timeout=5):
    # Get device contact details

    device = '5fa1a16956d6163cd31a523f' # Device ID
    url = f"https://api.wassenger.com/v1/io/{device}/contacts/{phone}"
    headers = {'token': settings.WASSENGER_API_KEY}
    response = requests.get(url, headers=headers)
    data = json.loads(response.text)

    return data
