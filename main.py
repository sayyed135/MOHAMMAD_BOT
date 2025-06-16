import telebot
from flask import Flask, request

TOKEN = '7217912729:AAGsCp-YNxnlMUB8M352p2EcVGB2K0at2Xg'
bot = telebot.TeleBot(TOKEN)
WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com/'

app = Flask(__name__)

# تنظیم Webhook
@app.before_first_request
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

# روت دریافت پیام‌های تلگرام
@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid content-type', 403

# دستور تست ساده
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام محمد! رباتت با Webhook فعال شد 😎")

# اجرای Flask سرور
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
