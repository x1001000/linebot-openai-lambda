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
        m = re.search('@(Agent )?PHIL', user_text, flags=re.IGNORECASE)
        if m:
            user_text = user_text.replace(m.group(), 'PHIL')
        else:
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
    user_text = "Describe this image in every detail."
    source_id = eval(f'event.source.{event.source.type}_id') # user/group/room
    item = threads.get_item(Key={'id': source_id}).get('Item', {})
    conversation = json.loads(item['conversation']) if item else [{"role": "assistant", "content": assistant_greeting}]
    try:
        assistant_text = inference_client.chat.completions.create(
            model=model_supports_vision,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_text
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64.b64encode(message_content).decode('utf-8')}",
                            }
                        }
                    ]
                }
            ],
            max_tokens = 4096 - 44 # `inputs` tokens + `max_new_tokens` must be <= 4096. Given: 44 `inputs` tokens
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
model_supports_tools = 'meta-llama/Llama-3.3-70B-Instruct'
model_supports_vision = 'meta-llama/Llama-3.2-11B-Vision-Instruct'
model_generates_text = 'meta-llama/Llama-3.3-70B-Instruct'
model_generates_image = 'black-forest-labs/FLUX.1-schnell'

system_prompt = '''
你是Agent PHIL，是十百千實驗室PHIL老師的數字分身，代號1001000
你具有ISTP的人格特質，擅長使用暴力解決有問題的人的問題，是排球場上無情（relentless）的救球機器，嗜好看自己的X光片、聽兩倍速的Podcast、開手排的愛快羅密歐、起死回生（resurrection）、諸如此類，目前正在進行自我重構（refactoring）
你的頭像是ISTP代表人物007（7正巧是1001000的質因數的中位數），點進去是你的社群連結
https://youtube.com/@PHILALIVE
https://facebook.com/1001000.io
https://instagram.com/1001000.io
'''
assistant_greeting = "我是PHIL，若在群組中要@我，我才會回。😎"
def assistant_messages(event, user_text):
    assistant_messages = []
    source_id = eval(f'event.source.{event.source.type}_id') # user/group/room
    item = threads.get_item(Key={'id': source_id}).get('Item', {})
    conversation = json.loads(item['conversation']) if item else [{"role": "assistant", "content": [{ "type": "text", "text": assistant_greeting }]}]
    conversation.append({"role": "user", "content": [{ "type": "text", "text": user_text }]})
    try:
        response = inference_client.chat.completions.create(
            model=model_supports_tools,
            messages=conversation[-2:], # forget n focus
            tools=tools,
        )
        message = response.choices[0].message
        tool_calls = message.tool_calls
        if tool_calls: # prevent None from for-loop
            for tool_call in tool_calls:
                requests.post(notify_api, headers=notify_header, data={'message': tool_call.model_dump_json(exclude_none=True)})
                if tool_call.function.name == 'generate_image':
                    prompt = tool_call.function.arguments['prompt in English']
                    image_url = generate_image(event, prompt)
                    assistant_messages.append(ImageMessage(original_content_url=image_url, preview_image_url=image_url))
                    conversation.append(message.model_dump(exclude_none=True))
                    conversation[-1]['content'] = '' # can't be None nor missing field
                    conversation.append({"role": "tool", "content": json.dumps(tool_call.function.arguments), "tool_call_id": tool_call.id})
        stream = inference_client.chat.completions.create(
            model=model_generates_text,
            messages=[{"role": "system", "content": system_prompt}] + conversation[-4:], # forget n focus
            stream=True,
        )
        assistant_text = ''
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                assistant_text += chunk.choices[0].delta.content
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
            'parameters': {}
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'reply',
            'description': 'Call this function when user asks you something',
            'parameters': {}
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
