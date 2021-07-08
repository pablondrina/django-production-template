import messagebird
from project import settings

client = messagebird.Client(settings.MESSAGEBIRD_API_TOKEN)


def send_sms(phone, message):
    try:
        msg = client.message_create(phone, message)
        print(msg.__dict__)
    except messagebird.client.ErrorException as e:
        for error in e.errors:
            print(error)
