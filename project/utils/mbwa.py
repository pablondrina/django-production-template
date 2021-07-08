import requests
from project import settings
import messagebird


def reply(conversation_id):

    client = messagebird.Client(settings.MESSAGEBIRD_API_TOKEN)
    # you need to get or start a conversation
    message = client.conversation_create_message(conversation_id, {
        'channelId': '0a57014e12bc4b2281df2f548b1b4cfb',
        'type': 'text',
        'content': {
            'text': 'Olá, tudo bem? 😊'
        }
    })
    print(message.__str__())


def send_message():
    import messagebird
    from messagebird.conversation_message import MESSAGE_TYPE_TEXT
    # client = messagebird.Client(args['accessKey'])
    client = messagebird.Client('oYEd4ku89kHTHe2dAtOtvGjMT', features = [messagebird.Feature.ENABLE_CONVERSATIONS_API_WHATSAPP_SANDBOX])
    msg = client.conversation_create_message('27f91c68e95745b18ae3947c1e634847', {
      'channelId': '0a57014e12bc4b2281df2f548b1b4cfb',
      'type': MESSAGE_TYPE_TEXT,
      'content': {
        'text': 'Olá, tudo bem, aí? 😊 Segundo teste...'
      }
    })


def get_conversation():
    url = "https://conversations.messagebird.com/v1/conversations"
    headers = {
        'Accept': 'application/json',
        'Authorization': settings.MESSAGEBIRD_API_TOKEN
        }
    response = requests.get(
        url,
        headers=headers,
    )
    print(response.text)

# url = "https://conversations.messagebird.com/v1/send"
#
#
# def send_message(phone, message, timeout=5):
#     payload = f'{{\"to\":\"{phone}\", \"from\":\"5543984049009\", \"type\": \"text\", \"content\": {{\"text\":\"{message}\"}} }}'
#     headers = {
#         'content-type': 'application/json',
#         'Authorization': '0a57014e12bc4b2281df2f548b1b4cfb'
#         }
#     response = requests.post(
#         url,
#         data=payload.encode('utf-8'),
#         headers=headers,
#         timeout=timeout,
#     )
#
#     print(response.text)