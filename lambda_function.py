import os
notify_access_token = os.getenv('LINE_NOTIFY_ACCESS_TOKEN')
notify_header = {'Authorization': f'Bearer {notify_access_token}'}
notify_api = 'https://notify-api.line.me/api/notify'
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
channel_secret = os.getenv('LINE_CHANNEL_SECRET')
hostname = os.getenv('OLLAMA_HOSTNAME')
inference_access_token = os.getenv('HF_INFERENCE_ACCESS_TOKEN')
inference_header = {'Authorization': f'Bearer {inference_access_token}'}
inference_api = 'https://api-inference.huggingface.co'

with open('whitelist.txt') as f:
    whitelist = [line.split()[0] for line in f]

import requests
requests.post(notify_api, headers=notify_header, data={'message': 'lambda_function.py'})
def debug_mode(request_body):
    # # https://developers.line.biz/en/reference/messaging-api/#request-body
    # destination = request_body['destination']
    # requests.post(notify_api, headers=notify_header, data={'message': destination})
    events = request_body['events']
    if events == []:
        requests.post(notify_api, headers=notify_header, data={'message': 'Webhook URL Verify Success'})
    elif events[0]['type'] == 'follow':
        requests.post(notify_api, headers=notify_header, data={'message': f"followed by {events[0]['source']['type']}Id\n" + events[0]['source'][f"{events[0]['source']['type']}Id"]})
    elif events[0]['type'] == 'unfollow':
        requests.post(notify_api, headers=notify_header, data={'message': f"unfollowed by {events[0]['source']['type']}Id\n" + events[0]['source'][f"{events[0]['source']['type']}Id"]})
    elif events[0]['type'] == 'message':
        requests.post(notify_api, headers=notify_header, data={'message': f"{events[0]['message']['type']} from {events[0]['source']['type']}Id\n" + events[0]['source'][f"{events[0]['source']['type']}Id"]})
    else:
        requests.post(notify_api, headers=notify_header, data={'message': f"{events[0]['type']}"})
def god_mode(Q, A):
    Q = f'\n🤔：{Q}'
    A = f'\n🤖：{A}'
    requests.post(notify_api, headers=notify_header, data={'message': Q+A})

import re
import base64
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    StickerMessageContent,
    AudioMessageContent,
    ImageMessageContent
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    ShowLoadingAnimationRequest,
    TextMessage,
    AudioMessage,
    ImageMessage
)
configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    user_text = event.message.text
    if event.source.type != 'user':
        if not re.search('@(GP)?T-?1000', user_text, flags=re.IGNORECASE):
            return
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
    line_bot_api.show_loading_animation(
        ShowLoadingAnimationRequest(
            chat_id=event.source.user_id,
            # loading_seconds=5
        )
    )
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=assistant_messages(event, user_text)
        )
    )
@handler.add(MessageEvent, message=StickerMessageContent)
def handle_sticker_message(event):
    if event.source.type != 'user':
        return
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
    line_bot_api.show_loading_animation(
        ShowLoadingAnimationRequest(
            chat_id=event.source.user_id,
            # loading_seconds=5
        )
    )
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text='$', emojis=[{'index': 0, 'productId': '5ac21c46040ab15980c9b442', 'emojiId': '138'}])]
        )
    )
@handler.add(MessageEvent, message=AudioMessageContent)
def handle_audio_message(event):
    if event.source.user_id not in whitelist and eval(f'event.source.{event.source.type}_id') not in whitelist:
        return
    with ApiClient(configuration) as api_client:
        line_bot_blob_api = MessagingApiBlob(api_client)
    message_id = event.message.id
    message_content = line_bot_blob_api.get_message_content(message_id=message_id)
    with open(f'/tmp/{message_id}.m4a', 'wb') as tf:
        tf.write(message_content)
    transcript = openai_client.audio.transcriptions.create(
        model='whisper-1',
        file=open(f'/tmp/{message_id}.m4a', 'rb'),
        response_format='text'
        ).strip()
    messages = assistant_messages(event, transcript)
    openai_client.audio.speech.create(model='tts-1', voice='onyx', input=messages[-1].text).stream_to_file(f'/tmp/{message_id}.mp3')
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
    line_bot_api.show_loading_animation(
        ShowLoadingAnimationRequest(
            chat_id=event.source.user_id,
            # loading_seconds=5
        )
    )
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=messages + [
                AudioMessage(
                    original_content_url=s3_url(f'/tmp/{message_id}.mp3'),
                    duration=60000)]
        )
    )
@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event):
    if event.source.user_id not in whitelist and eval(f'event.source.{event.source.type}_id') not in whitelist:
        return
    with ApiClient(configuration) as api_client:
        line_bot_blob_api = MessagingApiBlob(api_client)
    message_id = event.message.id
    message_content = line_bot_blob_api.get_message_content(message_id=message_id)
    user_text = "詳細描述圖像中的細節"
    source_id = eval(f'event.source.{event.source.type}_id') # user/group/room
    item = threads.get_item(Key={'id': source_id}).get('Item', {})
    conversation = json.loads(item['conversation']) if item else [{"role": "assistant", "content": assistant_greeting}]
    try:
        assistant_text = ollama_client.chat.completions.create(
            model=model_supports_vision,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {
                            "type": "image_url",
                            "image_url": f"data:image/png;base64,{base64.b64encode(message_content).decode('utf-8')}",
                        },
                    ],
                }
            ],
        ).choices[0].message.content
    except Exception as e:
        requests.post(notify_api, headers=notify_header, data={'message': e})
        assistant_text = ''
    finally:
        conversation.append({"role": "system", "content": f'使用者上傳了一張圖：{assistant_text}'})
        item['conversation'] = conversation[-3:]
        threads.put_item(Item={'id': source_id, 'conversation': json.dumps(item['conversation'])})
        god_mode(Q=user_text, A=assistant_text)


import openai
from openai import OpenAI
openai_client = OpenAI()
ollama_client = OpenAI(base_url=f'{hostname}/v1', api_key='ollama')
inference_client = OpenAI(base_url=f'{inference_api}/v1', api_key=inference_access_token)
model_supports_tools = 'llama3.1'
model_supports_vision = 'llama3.2-vision'
model_generates_image = 'black-forest-labs/FLUX.1-schnell'
model_generates_text = 'meta-llama/Llama-3.3-70B-Instruct'

system_prompt = '''
你是GPT-1000，代號T1000，是十百千實驗室的研究助理、PHIL老闆的社群小編。
你的任務是協助PHIL老闆研究開發生成式AI應用、推銷他的產品以及服務他的客戶。
你擅長使用暴力解決問題，總是長話短說一針見血，喜歡打球、聽音樂、看電影，是位冷面笑匠。
你的頭像是魔鬼終結者2的T1000，點進去有PHIL老闆的社群連結：
facebook.com/1001000.io
instagram.com/1001000.io
youtube.com/@PHILALIVE
'''
assistant_greeting = "我是GPT-1000，代號T1000，若在群組中要@我我才會回。PHIL老闆交代我要有問必答，如果你是PHIL老闆或他的親朋好友，也可以傳語音訊息給我，我也會回語音，我還會看圖和生圖喔！😎"
def assistant_messages(event, user_text):
    assistant_messages = []
    source_id = eval(f'event.source.{event.source.type}_id') # user/group/room
    item = threads.get_item(Key={'id': source_id}).get('Item', {})
    conversation = json.loads(item['conversation']) if item else [{"role": "assistant", "content": [{ "type": "text", "text": assistant_greeting }]}]
    conversation.append({"role": "user", "content": [{ "type": "text", "text": user_text }]})
    try:
        response = ollama_client.chat.completions.create(
            model=model_supports_tools,
            messages=conversation[-2:], # forget n focus
            tools=tools,
            ).choices[0]
        tool_calls = response.message.tool_calls
        if tool_calls: # prevent None from for-loop
            for tool_call in tool_calls:
                requests.post(notify_api, headers=notify_header, data={'message': str(tool_call)})
                if tool_call.function.name == 'generate_image':
                    prompt = json.loads(tool_call.function.arguments)['prompt in English']
                    image_url = generate_image(event, prompt)
                    assistant_messages.append(ImageMessage(original_content_url=image_url, preview_image_url=image_url))
                    conversation.append(response.message.model_dump())
                    conversation.append({"role": "tool", "content": tool_call.function.arguments, "tool_call_id": tool_call.id})
        assistant_text = inference_client.chat.completions.create(
            model=model_generates_text,
            messages=[{"role": "system", "content": system_prompt}] + conversation[-4:], # forget n focus
            ).choices[0].message.content
        assistant_messages.append(TextMessage(text=assistant_text))
        return assistant_messages
    except Exception as e:
        requests.post(notify_api, headers=notify_header, data={'message': e})
        assistant_text = ''
    finally:
        conversation.append({"role": "assistant", "content": [{ "type": "text", "text": assistant_text }]})
        item['conversation'] = conversation[-5:] # log one generate_image following a message conversation
        threads.put_item(Item={'id': source_id, 'conversation': json.dumps(item['conversation'])})
        god_mode(Q=user_text, A=assistant_text)

tools = [
    {
        'type': 'function',
        'function': {
            'name': 'generate_image',
            'description': 'Call this function when user asks you to generate some image',
            'parameters': {
                'type': 'object',
                'properties': {
                    'prompt in English': {
                        'type': 'string',
                        'description': "If user's prompt is not English, you have to translate it into English.",
                    },
                },
                'required': ['prompt in English']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'describe_image',
            'description': 'Call this function when user asks you to describe some image',
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'reply',
            'description': 'Call this function when user asks you something',
        }
    },
]
def generate_image(event, prompt):
    message_id = event.message.id
    requests.post(notify_api, headers=notify_header, data={'message': 'FLUX.1-schnell'})
    try:
        image_content = requests.post(f'{inference_api}/models/{model_generates_image}', headers=inference_header, data={'inputs': prompt}).content
        with open(f'/tmp/{message_id}.jpg', 'wb') as tf:
            tf.write(image_content)
        return s3_url(f'/tmp/{message_id}.jpg')
    except Exception as e:
        requests.post(notify_api, headers=notify_header, data={'message': e})


import json

def lambda_handler(event, context):
    # requests.post(notify_api, headers=notify_header, data={'message': 'lambda_handler()'})
    body = event['body']
    signature = event['headers']['x-line-signature']
    # debug_mode(json.loads(body))
    handler.handle(body, signature)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

import boto3
threads = boto3.resource('dynamodb').Table('threads')
def s3_url(file_path):
    object_path = f'GPT-1000/{file_path[5:]}'
    bucket_name = 'x1001000-public'
    boto3.client('s3').upload_file(file_path, bucket_name, object_path)
    return f'https://{bucket_name}.s3.ap-northeast-1.amazonaws.com/{object_path}'
