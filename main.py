import telebot
from flask import Flask, request
import threading
import time
import requests

API_TOKEN = '7217912729:AAGD-TTQclyqz54VdPmRGgMne5g1XaamDWY'
WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com/'

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

def ping_self():
    while True:
        try:
            requests.get(WEBHOOK_URL)
        except:
            pass
        time.sleep(300)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.reply_to(message, "ربات همیشه فعاله و جواب می‌ده! ✅")

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return '', 403

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    threading.Thread(target=ping_self).start()
    app.run(host='0.0.0.0', port=10000)
