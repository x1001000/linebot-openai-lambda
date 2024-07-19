import os
notify_access_token = os.getenv('LINE_NOTIFY_ACCESS_TOKEN')
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
channel_secret = os.getenv('LINE_CHANNEL_SECRET')
hostname = os.getenv('OLLAMA_HOSTNAME')

import requests
notify_api = 'https://notify-api.line.me/api/notify'
header = {'Authorization': f'Bearer {notify_access_token}'}
requests.post(notify_api, headers=header, data={'message': 'lambda_function.py'})
def debug_mode(request_body):
    # # https://developers.line.biz/en/reference/messaging-api/#request-body
    # destination = request_body['destination']
    # requests.post(notify_api, headers=header, data={'message': destination})
    events = request_body['events']
    if events == []:
        requests.post(notify_api, headers=header, data={'message': 'Webhook URL Verify Success'})
    elif events[0]['type'] == 'follow':
        requests.post(notify_api, headers=header, data={'message': f"followed by {events[0]['source']['type']}Id\n" + events[0]['source'][f"{events[0]['source']['type']}Id"]})
    elif events[0]['type'] == 'unfollow':
        requests.post(notify_api, headers=header, data={'message': f"unfollowed by {events[0]['source']['type']}Id\n" + events[0]['source'][f"{events[0]['source']['type']}Id"]})
    elif events[0]['type'] == 'message':
        requests.post(notify_api, headers=header, data={'message': f"{events[0]['message']['type']} from {events[0]['source']['type']}Id\n" + events[0]['source'][f"{events[0]['source']['type']}Id"]})
    else:
        requests.post(notify_api, headers=header, data={'message': f"{events[0]['type']}"})
def god_mode(Q, A):
    Q = f'\n🤔：{Q}'
    A = f'\n🤖：{A}'
    requests.post(notify_api, headers=header, data={'message': Q+A})

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
    if event.source.type != 'user':
        if not re.search('[Tt]-?1000', event.message.text):
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
                messages=[TextMessage(text=assistant_reply(event, event.message.text))]
            )
        )
@handler.add(MessageEvent, message=StickerMessageContent)
def handle_sticker_message(event):
    if event.source.type != 'user':
        return
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
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
    message_content = line_bot_blob_api.get_message_content(message_id=event.message.id)
    with open(f'/tmp/{event.message.id}.m4a', 'wb') as tf:
        tf.write(message_content)
    transcript = client.audio.transcriptions.create(
        model='whisper-1',
        file=open(f'/tmp/{event.message.id}.m4a', 'rb'),
        response_format='text'
        ).strip()
    reply_text = assistant_reply(event, transcript)
    line_bot_api = MessagingApi(api_client)
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(text=reply_text),
                AudioMessage(
                    original_content_url=TTS_s3_url(reply_text, event.message.id),
                    duration=60000)]
        )
    )
@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event):
    if event.source.user_id not in whitelist and eval(f'event.source.{event.source.type}_id') not in whitelist:
        return
    with ApiClient(configuration) as api_client:
        line_bot_blob_api = MessagingApiBlob(api_client)
    message_content = line_bot_blob_api.get_message_content(message_id=event.message.id)
    with open(f'/tmp/{event.message.id}.jpg', 'wb') as tf:
        tf.write(message_content)
    source_id = eval(f'event.source.{event.source.type}_id') # user/group/room
    item = threads.get_item(Key={'id': source_id}).get('Item')#threads[source_id] = threads.get(source_id, {})
    thread = json.loads(item['thread']) if item else {}
    thread['latest_image'] = f'/tmp/{event.message.id}.jpg'
    user_text = '描述你看到的影像，使用繁體中文：'
    conversation = thread['conversation'] = thread.get('conversation', [{"role": "assistant", "content": "我是GPT-1000，代號T1000，若在群組中要叫我我才會回。PHIL老闆交代我要有問必答，如果你是PHIL老闆或他的親朋好友，也可以傳語音訊息給我，我也會回語音，我還會看圖和生圖喔！😎"}])
    conversation.append({"role": "user", "content": user_text})
    payload = {
        'model': 'llava-llama3',
        'prompt': user_text,
        'images': [base64.b64encode(message_content).decode('utf-8')],
        'stream': False}
    requests.post(notify_api, headers=header, data={'message': 'LLaVA'})
    try:
        assistant_reply = requests.post(f'{hostname}/api/generate', data=json.dumps(payload)).json()['response']
    except Exception as e:
        requests.post(notify_api, headers=header, data={'message': e})
        assistant_reply = ''
    finally:
        conversation.append({"role": "assistant", "content": assistant_reply})
        thread['conversation'] = conversation[-10:]
        threads.put_item(Item={'id': source_id, 'thread': json.dumps(thread)})
        god_mode(Q=user_text, A=assistant_reply)

with open('whitelist.txt') as f:
    whitelist = [line.split()[0] for line in f]
def terminator(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[ImageMessage(
                    original_content_url='https://raw.githubusercontent.com/x1001000/linebot-openai-lambda/main/hastalavista.jpeg',
                    preview_image_url='https://raw.githubusercontent.com/x1001000/linebot-openai-lambda/main/hastalavista-580x326.jpeg')]
            )
        )


import openai
from openai import OpenAI
client = OpenAI()
ollama = OpenAI(base_url=f'{hostname}/v1', api_key='ollama')

system_prompt = '''
你是GPT-1000，代號T1000，是十百千實驗室的研究助理、PHIL老闆的社群小編。
你擅長使用暴力解決問題，總是長話短說一針見血，喜歡打球、聽音樂、看電影，是位冷面笑匠。
你的頭像是魔鬼終結者2的T1000，點進去有PHIL老闆的社群平台：
facebook.com/1001000.io 
instagram.com/1001000.io 
youtube.com/@PHILALIVE 
你的任務是推廣PHIL老闆的社群，邀請訪客幫忙按讚、留言、分享。
'''
instruction = [{"role": "system", "content": system_prompt}]
threads = {}
def assistant_reply(event, user_text, model='cwchang/llama-3-taiwan-8b-instruct'):
    source_id = eval(f'event.source.{event.source.type}_id') # user/group/room
#   thread is threads[source_id] as long as both not to be reassigned
    item = threads.get_item(Key={'id': source_id}).get('Item')#threads[source_id] = threads.get(source_id, {})
    thread = json.loads(item['thread']) if item else {}
#   conversation is thread['conversation'] until thread['conversation'] to be reassigned
    conversation = thread['conversation'] = thread.get('conversation', [{"role": "assistant", "content": "我是GPT-1000，代號T1000，若在群組中要叫我我才會回。PHIL老闆交代我要有問必答，如果你是PHIL老闆或他的親朋好友，也可以傳語音訊息給我，我也會回語音，我還會看圖和生圖喔！😎"}])
    conversation.append({"role": "user", "content": user_text})
    try:
        completion = ollama.chat.completions.create(
            model=model,
            messages=instruction + conversation,
            tools=tools
            )
    except Exception as e:
        requests.post(notify_api, headers=header, data={'message': e})
        assistant_reply = ''
    else:
        assistant_reply = completion.choices[0].message.content
        tool_calls = completion.choices[0].message.tool_calls
        if tool_calls:
            for tool_call in tool_calls:
                requests.post(notify_api, headers=header, data={'message': 'CALL-OUT'})
                assistant_reply = eval(tool_call.function.name)(event, thread)
    finally:
        conversation.append({"role": "assistant", "content": assistant_reply})
        thread['conversation'] = conversation[-10:]
        threads.put_item(Item={'id': source_id, 'thread': json.dumps(thread)})
        god_mode(Q=user_text, A=assistant_reply)
        return assistant_reply


import json

def lambda_handler(event, context):
    # requests.post(notify_api, headers=header, data={'message': 'lambda_handler()'})
    body = event['body']
    signature = event['headers']['x-line-signature']
    debug_mode(json.loads(body))
    handler.handle(body, signature)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }


# from gtts import gTTS
import boto3
threads = boto3.resource('dynamodb').Table('threads')
def TTS_s3_url(text, message_id):
    file_name = f'/tmp/{message_id}.mp3'
    object_name = f'GPT-1000/{message_id}.mp3'
    bucket_name = 'x1001000-public'
    # lang = client.chat.completions.create(
    #     model="gpt-3.5-turbo",
    #     messages=[{"role": "user", "content": f'Return the 2-letter language code for "{text}". ONLY the code and nothing else.'}]
    #     ).choices[0].message.content
    # requests.post(notify_api, headers=header, data={'message': lang})
    # if lang == 'zh':
    #     lang = 'zh-TW'
    # gTTS(text=text, lang=lang).save(file_name)
    client.audio.speech.create(model='tts-1', voice='alloy', input=text).stream_to_file(file_name)
    boto3.client('s3').upload_file(file_name, bucket_name, object_name)
    return f'https://{bucket_name}.s3.ap-northeast-1.amazonaws.com/{object_name}'
def ImageMessageContent_s3_url(latest_image):
    file_name = latest_image
    object_name = f'GPT-1000/{latest_image[5:]}'
    bucket_name = 'x1001000-public'
    boto3.client('s3').upload_file(file_name, bucket_name, object_name)
    return f'https://{bucket_name}.s3.ap-northeast-1.amazonaws.com/{object_name}'

tools = [
    {'type': 'function', 'function': {'name': 'input_an_image_to_AI'}},
    {'type': 'function', 'function': {'name': 'output_an_image_from_AI'}},
    ]
def input_an_image_to_AI(event, thread):
    user_text = thread['conversation'][-1]['content']
    latest_image = thread.get('latest_image')
    if latest_image:
        content_parts = []
        content_parts.append({'type': 'text', 'text': user_text})
        content_parts.append({'type': 'image_url', 'image_url': {'url': ImageMessageContent_s3_url(latest_image)}})
        requests.post(notify_api, headers=header, data={'message': 'GPT-4V'})
        try:
            assistant_reply = client.chat.completions.create(
                model='gpt-4o',
                messages=instruction + [{"role": "user", "content": content_parts}],
                max_tokens=1000
                ).choices[0].message.content
        except openai.BadRequestError as e:
            requests.post(notify_api, headers=header, data={'message': e})
            assistant_reply = '不可以壞壞🙅'
    else:
        assistant_reply = '如果要我幫忙圖像理解，請先傳圖再提問喔👀'
    return assistant_reply
def output_an_image_from_AI(event, thread):
    source_id = eval(f'event.source.{event.source.type}_id') # user/group/room
    if source_id not in whitelist:
        return '我的圖像生成服務只提供PHIL老闆和他的家人朋友群組喔！如果你想請他喝咖啡，可以點我的頭像找到他👈'
    user_text = thread['conversation'][-1]['content']
    requests.post(notify_api, headers=header, data={'message': 'DALL·E 3'})
    try:
        image_url = client.images.generate(model='dall-e-3', prompt=user_text).data[0].url
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text='噗噗～來了！'),
                        ImageMessage(
                            original_content_url=image_url,
                            preview_image_url=image_url)]
                )
            )
        return ''
    except openai.OpenAIError as e:
        requests.post(notify_api, headers=header, data={'message': e})
        return '蛤？'