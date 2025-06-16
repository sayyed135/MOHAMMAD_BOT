import telebot
from flask import Flask, request
import logging
import os

# تنظیمات
TOKEN = '7217912729:AAGsCp-YNxnlMUB8M352p2EcVGB2K0at2Xg'
WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com/'

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# لاگ
logging.basicConfig(level=logging.INFO)

# مسیر دریافت پیام از تلگرام
@app.route('/', methods=['POST'])
def receive_update():
    if request.headers.get('content-type') == 'application/json':
        try:
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return '', 200
        except Exception as e:
            logging.error(f'Error: {e}')
            return 'Internal Error', 500
    return 'Invalid content-type', 403

# پیام‌های ساده
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "✅ ربات با webhook فعال است.")

# اجرای سرور و تنظیم Webhook
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
