import telebot
from flask import Flask, request
import logging
import os

TOKEN = '7217912729:AAHEug-znb_CGJTXlITt3Zrjp2dJan0a9Gs'
WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com/'

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
ADMIN_ID = 6994772164

logging.basicConfig(level=logging.INFO)

# دیتابیس ساده کلمات
dictionary = {
    "apple": "سیب",
    "book": "کتاب",
    "hello": "سلام",
    "world": "جهان",
    "computer": "رایانه",
    "python": "پایتون",
    "sun": "خورشید",
    "moon": "ماه",
    "love": "عشق",
    "friend": "دوست"
}

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        try:
            update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
            bot.process_new_updates([update])
            return '', 200
        except Exception as e:
            logging.error(f'Webhook Error: {e}')
            return 'Internal Error', 500
    return 'Invalid content-type', 403

@bot.message_handler(commands=['start'])
def start_command(message):
    welcome = "سلام! 👋\nکلمه انگلیسی رو بفرست تا معنی فارسی‌شو بگم!"
    bot.send_message(message.chat.id, welcome)

@bot.message_handler(func=lambda m: True)
def translate_word(message):
    word = message.text.lower().strip()
    if word in dictionary:
        bot.reply_to(message, f"✅ معنی «{word}» میشه: {dictionary[word]}")
    else:
        bot.reply_to(message, "❌ متاسفم، این کلمه رو نمی‌شناسم.")

# شروع سرور
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get('PORT', 10000))
    app.run(host="0.0.0.0", port=port)
