
import configparser

from flask import Flask, request, abort


from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

app = Flask(__name__)
config = configparser.ConfigParser()
config.read("config.ini")

line_bot_api = LineBotApi('r7uHxtXwtjDXYHoAWazEgWw93ZBdr5+m5kiyLPp2aGKA1KXxlzrvMvDyz8WVWhfk7tzeX5l3Q+Etrr4pA8ezmg7QYKQ70c27UMG/ZatLlvyIIqmnNHq3l6BmHCNsVfpuzEjMPUjOb/XRTZ8LsHW+JgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('b334451f4eaeabb48c0050a013167f01')

@app.route("/callback", methods=['POST'])

def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    # print("body:",body)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'ok'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("event.reply_token:", event.reply_token)
    print("event.message.text:", event.message.text)

    if(event.message.text == "電影"):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=日新)
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=event.message.text)
        )



if __name__ == '__main__':
    app.run()
