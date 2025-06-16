import telebot
from flask import Flask, request
import logging
import os

# ✅ تنظیمات
TOKEN = '7217912729:AAHEug-znb_CGJTXlITt3Zrjp2dJan0a9Gs'
WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com/'

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ✅ لاگ‌ها
logging.basicConfig(level=logging.INFO)

# ✅ دریافت پیام از تلگرام
@app.route('/', methods=['POST'])
def receive_update():
    if request.headers.get('content-type') == 'application/json':
        try:
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return '', 200
        except Exception as e:
            logging.error(f'❌ Error: {e}')
            return 'Internal Error', 500
    return 'Invalid content-type', 403

# ✅ دستورات اصلی ربات
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "سلام محمد! ✅ ربات با وب‌هوک فعاله.")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    bot.reply_to(message, "دستور نامشخصه. لطفاً /start رو بزن.")

# ✅ اجرای Flask و تنظیم Webhook
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
