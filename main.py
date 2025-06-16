import telebot
from flask import Flask, request
import logging
import os

# ============== تنظیمات ==============
TOKEN = '7217912729:AAGsCp-YNxnlMUB8M352p2EcVGB2K0at2Xg'
WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com/'  # آدرس رباتت در Render

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ============== لاگ‌ها برای دیباگ ==============
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============== ست کردن وب هوک ==============
@app.before_first_request
def set_webhook():
    bot.remove_webhook()
    success = bot.set_webhook(url=WEBHOOK_URL)
    if success:
        logger.info("✅ Webhook set successfully.")
    else:
        logger.error("❌ Failed to set webhook!")

# ============== دریافت پیام از تلگرام ==============
@app.route('/', methods=['POST'])
def receive_update():
    if request.headers.get('content-type') == 'application/json':
        try:
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return '', 200
        except Exception as e:
            logger.exception("❌ Error processing update: %s", e)
            return 'Internal Server Error', 500
    return 'Invalid content-type', 403

# ============== دستورات ربات ==============
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "سلام محمد! 🌟\nمن فعالم و منتظر دستورات تو هستم.")

@bot.message_handler(commands=['help'])
def handle_help(message):
    bot.reply_to(message, "📌 دستورات من:\n/start - شروع\n/help - راهنما")

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    bot.reply_to(message, "متوجه نشدم. لطفاً یکی از دستورات رو وارد کن یا /help رو بزن.")

# ============== اجرای سرور Flask ==============
if __name__ == '__main__':
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=PORT)
