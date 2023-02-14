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
    prompt = preprompt.get(event.source.user_id, 'GPT-1000是串接OpenAI API的LINE機器人，所使用的語言模型GPT-3只有2021年以前的知識，made in 十百千實驗室 by Phil Alive。\n') + f'使用者問：{event.message.text}\nGPT-1000答：'
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=0.5,
        max_tokens=1024,
        top_p=0.3,
        frequency_penalty=0.5,
        presence_penalty=0.0)
    completion = response.choices[0]
    completion.text = completion.text.strip()
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=completion.text)
    )
    preprompt[event.source.user_id] = f'{prompt}{completion.text}\n'

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
