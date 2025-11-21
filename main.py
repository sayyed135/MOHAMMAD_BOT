# app.py
from flask import Flask, request, jsonify
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os

# ====== تنظیمات توکن ======
TELEGRAM_TOKEN = "7961151930:AAEM2r0BhaOp99eZtuL5BRQQYZc9335YHRs"
# ========================

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# ====== ثابت ======
WEEKLY_PASSWORD = "A"  # رمز ثابت یک حرف
HELP_LINK = "https://t.me/mohammadsadat_afg"
USERS_FILE = "users.json"

# ====== دیتای کاربران ======
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        user_data = json.load(f)
else:
    user_data = {}  # {chat_id: {"name": "", "number": "", "verified": False}}

# ====== توابع ذخیره و بارگذاری ======
def save_users():
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=4)

# ====== استارت و گرفتن اسم ======
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = str(message.chat.id)
    user_data[chat_id] = {"name": "", "number": "", "verified": False}
    save_users()
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("ارسال اسم", callback_data="ask_name"))
    bot.send_message(chat_id, "سلام! لطفاً اسم خود را وارد کنید:", reply_markup=markup)

# ====== هندل دکمه‌ها ======
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = str(call.message.chat.id)

    if call.data == "ask_name":
        msg = bot.send_message(chat_id, "اسم خود را تایپ کنید:")
        bot.register_next_step_handler(msg, get_name)

    elif call.data == "ask_number":
        msg = bot.send_message(chat_id, "شماره خود را تایپ کنید:")
        bot.register_next_step_handler(msg, get_number)

    elif call.data == "ask_password":
        msg = bot.send_message(chat_id, "رمز هفتگی خود را وارد کنید:")
        bot.register_next_step_handler(msg, check_password)

    elif call.data == "help":
        bot.send_message(chat_id, f"برای کمک روی لینک زیر کلیک کنید:\n{HELP_LINK}")

# ====== گرفتن اسم ======
def get_name(message):
    chat_id = str(message.chat.id)
    user_data[chat_id]["name"] = message.text
    save_users()
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("ارسال شماره", callback_data="ask_number"))
    bot.send_message(chat_id, f"اسم شما ثبت شد: {message.text}", reply_markup=markup)

# ====== گرفتن شماره ======
def get_number(message):
    chat_id = str(message.chat.id)
    user_data[chat_id]["number"] = message.text
    save_users()
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("تایید رمز هفتگی", callback_data="ask_password"))
    bot.send_message(chat_id, f"شماره شما ثبت شد: {message.text}", reply_markup=markup)

# ====== چک کردن رمز ======
def check_password(message):
    chat_id = str(message.chat.id)
    if message.text == WEEKLY_PASSWORD:
        user_data[chat_id]["verified"] = True
        save_users()
        bot.send_message(chat_id, "رمز صحیح است! شما تایید شدید ✅")
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("کمک", callback_data="help"))
        bot.send_message(chat_id, "رمز اشتباه است ❌", reply_markup=markup)

# ====== وب‌هوک ======
@app.route("/webhook", methods=['POST'])
def webhook():
    json_data = request.get_json()
    if json_data:
        bot.process_new_updates([telebot.types.Update.de_json(json_data)])
    return jsonify({"status": "ok"})

# ====== اجرا ======
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url="https://code-ai-0alo.onrender.com/webhook")
    app.run(host="0.0.0.0", port=10000)
