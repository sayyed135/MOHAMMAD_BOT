import telebot
from flask import Flask, request
import logging
import os

TOKEN = '7217912729:AAHEug-znb_CGJTXlITt3Zrjp2dJan0a9Gs'
WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com/'

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# آیدی مدیر (تو خودتی 😎)
ADMIN_ID = 6994772164

# تنظیم لاگ
logging.basicConfig(level=logging.INFO)

# دریافت پیام‌های وب‌هوک از تلگرام
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

# شروع
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "سلام! ✅ ربات با webhook فعاله.")

# ✅ منوی مدیریت (فقط برای مدیر)
@bot.message_handler(commands=['admin'])
def handle_admin(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔️ فقط مدیر به این بخش دسترسی دارد.")
        return

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("📊 تنظیم امتیاز برای بازی‌ها", "📬 ارسال پیام همگانی")
    markup.add("📌 بررسی کاربران", "❌ بستن منو")

    bot.send_message(message.chat.id, "🎛 منوی مدیریت:", reply_markup=markup)

# پاسخ به دکمه‌های منوی مدیریت
@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID)
def admin_buttons(message):
    if message.text == "📊 تنظیم امتیاز برای بازی‌ها":
        bot.reply_to(message, "🔧 لطفاً امتیاز بازی مورد نظر را وارد کنید...")
    elif message.text == "📬 ارسال پیام همگانی":
        bot.reply_to(message, "📝 پیام خود را بفرست تا به همه ارسال شود.")
    elif message.text == "📌 بررسی کاربران":
        bot.reply_to(message, "👥 در حال بررسی کاربران...")
    elif message.text == "❌ بستن منو":
        markup = telebot.types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "❎ منوی مدیریت بسته شد.", reply_markup=markup)

# پیام‌های نامشخص
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    bot.reply_to(message, "دستور نامشخصه. لطفاً /start یا /admin رو بزن.")

# اجرای سرور Flask و فعال‌سازی webhook
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
