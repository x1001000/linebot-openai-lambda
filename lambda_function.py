from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    prompt = f'GPT-1000是十百千實驗室開發的深度問答機器人，但只有2021年以前的知識，目前不提供連續問答。\n使用者問：{event.message.text}\nGPT-1000答：'
    payload = json.dumps({
        "model": "text-davinci-003",
        "prompt": prompt,
        "temperature": 0.5,
        "max_tokens": 2048,
        "top_p": 0.3,
        "frequency_penalty": 0.5,
        "presence_penalty": 0.0})
    r = requests.post(openai_api, headers=headers, data=payload)
    completion = json.loads(r.text)['choices'][0]['text']
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=completion)
    )

import requests
openai_api = 'https://api.openai.com/v1/completions'
headers = {
    "Content-Type": "application/json",
    "Authorization": f'Bearer {OPENAI_API_KEY}'}

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
