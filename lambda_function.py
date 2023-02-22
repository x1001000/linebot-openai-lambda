from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
from linebot.models import StickerMessage, ImageMessage, VideoMessage, AudioMessage, FileMessage, ImageSendMessage
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    balance = int(gas('check', event.source.user_id))
    if '餘額' in event.message.text:
        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(
                'https://memeprod.sgp1.digitaloceanspaces.com/user-wtf/1664586622774.jpg',
                'https://i.imgur.com/PdTJwFZ.jpg')
        )
        return
    if balance <= 0:
        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(
                'https://raw.githubusercontent.com/x1001000/linebot-openai-lambda/main/hastalavista.jpeg',
                'https://raw.githubusercontent.com/x1001000/linebot-openai-lambda/main/hastalavista-580x326.jpeg')
        )
        return
    prompt = preprompt.get(event.source.user_id, 'GPT-1000是串接OpenAI API的LINE機器人，只提供使用者三次免費問答，made in 十百千實驗室 by Phil Alive。\n') + f'使用者問：{event.message.text}\nGPT-1000答：'
    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            temperature=0.5,
            max_tokens=1024,
            top_p=0.3,
            frequency_penalty=0.5,
            presence_penalty=0.0)
    except:
        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(
                'https://phoneky.co.uk/thumbs/screensavers/down/abstract/systemcras_ncl37enz.gif',
                'https://phoneky.co.uk/thumbs/screensavers/down/abstract/systemcras_ncl37enz.gif')
        )
        return
    completion = response.choices[0]
    completion.text = completion.text.strip()
    balance = int(gas('charge', event.source.user_id))
    reminder = '\n\n' + ['3Q, no more.', '拉死抖☝️', '您還可以問我✌️個問題️'][balance] if balance < 3 else ''
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=completion.text + reminder)
    )
    preprompt[event.source.user_id] = f'{prompt}{completion.text}\n'[-(4097-1024)//2:]
@handler.add(MessageEvent, message=[StickerMessage, ImageMessage, VideoMessage, AudioMessage, FileMessage])
def handle_nontext_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='$', emojis=[{'index': 0, 'productId': '5ac21c46040ab15980c9b442', 'emojiId': '160'}])
    )

preprompt = {}

import openai
openai.api_key = OPENAI_API_KEY

import json

def lambda_handler(event, context):
    # TODO implement
    body = event['body']
    signature = event['headers']['x-line-signature']
    handler.handle(body, signature)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
