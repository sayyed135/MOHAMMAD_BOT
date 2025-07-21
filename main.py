import telebot
from flask import Flask, request
import os

TOKEN = "8077313575:AAF_B4ZS0_JPyqaJV4gBmqfJsUHh2gGPzsI"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

WEBHOOK_URL = "https://chatgpt-telegram-bkp1.onrender.com/"

waiting_users = []
active_chats = {}

from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("🎯 شروع چت ناشناس"))
    kb.row(KeyboardButton("❌ خروج از چت"))
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
                     "سلام! به ربات چت ناشناس خوش آمدید.\nروی «🎯 شروع چت ناشناس» بزن تا یه نفر بهت وصل شه!",
                     reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_id = message.chat.id
    text = message.text

    if text == "🎯 شروع چت ناشناس":
        if user_id in active_chats:
            bot.send_message(user_id, "شما الان توی چت هستی.")
            return
        if user_id in waiting_users:
            bot.send_message(user_id, "منتظر اتصال هستی...")
            return
        if waiting_users:
            partner_id = waiting_users.pop(0)
            active_chats[user_id] = partner_id
            active_chats[partner_id] = user_id
            bot.send_message(user_id, "✅ به چت ناشناس وصل شدی!", reply_markup=get_main_keyboard())
            bot.send_message(partner_id, "✅ یه نفر بهت وصل شد!", reply_markup=get_main_keyboard())
        else:
            waiting_users.append(user_id)
            bot.send_message(user_id, "🔍 منتظر یه نفر دیگه هستی...")

    elif text == "❌ خروج از چت":
        if user_id in active_chats:
            partner_id = active_chats[user_id]
            del active_chats[partner_id]
            del active_chats[user_id]
            bot.send_message(user_id, "✅ از چت خارج شدی.", reply_markup=get_main_keyboard())
            bot.send_message(partner_id, "❌ طرف مقابل از چت خارج شد.", reply_markup=get_main_keyboard())
        elif user_id in waiting_users:
            waiting_users.remove(user_id)
            bot.send_message(user_id, "❌ از صف انتظار خارج شدی.", reply_markup=get_main_keyboard())
        else:
            bot.send_message(user_id, "⛔ شما الان توی چت نیستی.")

    else:
        if user_id in active_chats:
            partner_id = active_chats[user_id]
            bot.send_message(partner_id, f"👤 ناشناس:\n{text}")
        else:
            bot.send_message(user_id, "برای شروع چت ناشناس، روی «🎯 شروع چت ناشناس» بزن.")

@app.route("/", methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/", methods=['GET'])
def home():
    return "✅ ربات در حال اجراست", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
