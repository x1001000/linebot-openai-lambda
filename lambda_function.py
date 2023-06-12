...


import re, requests

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
from linebot.models import StickerMessage, ImageMessage, VideoMessage, AudioMessage, FileMessage, ImageSendMessage, AudioSendMessage
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    event_id = event.source.user_id
    if event.source.type != 'user':
        if not re.search('[Tt]-?1000', event.message.text):
            return
        if event.source.type == 'group':
            event_id = event.source.group_id
        if event.source.type == 'room':
            event_id = event.source.room_id
    playground_mode = True #if event_id in playground else False
    balance = 1001000 if playground_mode else int(gas('check', event.source.user_id))
    balance = 0 if event.source.user_id in blacklist else balance
    if balance == 0:
        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(
                'https://raw.githubusercontent.com/x1001000/linebot-openai-lambda/main/hastalavista.jpeg',
                'https://raw.githubusercontent.com/x1001000/linebot-openai-lambda/main/hastalavista-580x326.jpeg')
        )
        # gas('charge', event.source.user_id)
        return
    if balance < 0:
        return
    preprompt = [{"role": "system", "content": "你是GPT-1000，代號T1000，是十百千實驗室的研究助理，也是PHIL老闆的特助，擅長使用暴力解決問題，偏好使用繁體中文回答問題，喜歡看電影，是位冷面笑匠，頭像照片是魔鬼終結者2的T-1000。"}]
    prompt = prompts.get(event_id, [{"role": "assistant", "content": "我是GPT-1000，代號T1000，若在群組中要叫我我才會回。PHIL老闆交代我要有問必答，如果你不喜歡打字，可以傳語音訊息給我，我也會回喔！😎"}])
    prompt.append({"role": "user", "content": event.message.text})
    try:
        global model
        response = openai.ChatCompletion.create(
            model=model,
            messages=preprompt + prompt)
    except openai.error.RateLimitError as e:
        if 'You exceeded your current quota' in str(e):
            openai.api_key, model = OPENAI_API_KEY('new')
        requests.post(line_notify_api, headers=header, data={'message': f'{e.__class__.__name__}: {e}'})
        assistant_reply = '牛仔很忙，不好意思，請稍後再賴！🤘🤠'
    except openai.error.InvalidRequestError as e:
        if 'The model: `gpt-4` does not exist' in str(e):
            model = 'gpt-3.5-turbo'
        requests.post(line_notify_api, headers=header, data={'message': f'{e.__class__.__name__}: {e}'})
        assistant_reply = '我太難了，不好意思，請再說一次！'
    except openai.error.AuthenticationError as e:
        openai.api_key, model = OPENAI_API_KEY('new')
        requests.post(line_notify_api, headers=header, data={'message': f'{e.__class__.__name__}: {e}'})
        assistant_reply = '我秀逗了，不好意思，請再說一次！'
    except Exception as e:
        requests.post(line_notify_api, headers=header, data={'message': f'{e.__class__.__name__}: {e}'})
        assistant_reply = '我當機了，不好意思，請再說一次！'
    else:
        assistant_reply = response['choices'][0]['message']['content'].strip()
        balance = 1001000 if playground_mode else int(gas('charge', event.source.user_id))
        assistant_reply += '\n\n' + ['3Q了，後會有期掰👋', '今天我只能再回答你最後☝️題！', '今天我還能回答你✌️題！'][balance] if balance < 3 else ''
    finally:
        prompt.append({"role": "assistant", "content": assistant_reply})
        prompts[event_id] = prompt[-10:]
        god_mode(Q=event.message.text, A=assistant_reply)
        if event.message.type == 'text':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=assistant_reply)
            )
        if event.message.type == 'audio':
            line_bot_api.reply_message(
                event.reply_token,
                AudioSendMessage(
                    original_content_url=gTTS_s3_url(assistant_reply, event.message.id),
                    duration=60000)
            )
@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='$', emojis=[{'index': 0, 'productId': '5ac21c46040ab15980c9b442', 'emojiId': '138'}])
    )
@handler.add(MessageEvent, message=AudioMessage)
def handle_audio_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    with open(f'/tmp/{event.message.id}.m4a', 'wb') as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)
    event.message.text = openai.Audio.transcribe('whisper-1', open(f'/tmp/{event.message.id}.m4a', 'rb')).text
    handle_text_message(event)


import openai
openai.api_key, model = OPENAI_API_KEY()
prompts = {}
playground = ['C4a903e232adb3dae7eec7e63220dc23f', 'Ce5ab141f09651f2920fc0d85baaa2816']
blacklist = ['U0cc3b490fa0b9a77d8d77bf8f3d462b1', 'U03d11a62dd78617318f1a4597bda0f6b']


import json

def lambda_handler(event, context):
    # TODO implement
    body = event['body']
    signature = event['headers']['x-line-signature']
    debug_mode(json.loads(body))
    handler.handle(body, signature)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }


...
