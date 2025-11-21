# main.py
from flask import Flask, request, jsonify
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
from datetime import datetime, timedelta

TELEGRAM_TOKEN = "7961151930:AAEM2r0BhaOp99eZtuL5BRQQYZc9335YHRs"
ADMIN_ID = 6994772164
WEBHOOK_URL = "https://code-ai-0alo.onrender.com/webhook"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# داده‌های کاربران در حافظه
try:
    with open("users.json", "r") as f:
        users = json.load(f)
except:
    users = {}

# تابع ذخیره‌سازی داده‌ها
def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f)

# مرحله بعد ثبت نام
def ask_name(message):
    users[str(message.chat.id)] = {"step": "name"}
    save_users()
    bot.send_message(message.chat.id, "سلام! لطفاً اسمت رو وارد کن:")

@bot.message_handler(func=lambda m: str(m.chat.id) not in users)
def start_user(message):
    ask_name(message)

@bot.message_handler(func=lambda m: str(m.chat.id) in users)
def handle_user(message):
    uid = str(message.chat.id)
    user = users[uid]
    step = user.get("step", "name")
    
    print(f"[LOG] کاربر {uid} در مرحله {step} پیام فرستاد: {message.text}")

    if step == "name":
        user["name"] = message.text
        user["step"] = "phone"
        save_users()
        # دکمه شیشه‌ای ارسال شماره
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("ارسال شماره من", callback_data="send_phone"))
        bot.send_message(uid, "لطفاً شماره‌ت رو ارسال کن:", reply_markup=markup)

    elif step == "weekly":
        if message.text == user.get("weekly_pass"):
            bot.send_message(uid, "رمز صحیح است! خوش آمدی.")
            user["step"] = "done"
            save_users()
        else:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("کمک", url="https://t.me/mohammadsadat_afg"))
            bot.send_message(uid, "رمز اشتباه است! برای کمک اینجا کلیک کن:", reply_markup=markup)

# دریافت شماره
@bot.callback_query_handler(func=lambda call: call.data == "send_phone")
def send_phone(call):
    uid = str(call.message.chat.id)
    user = users[uid]
    user["phone"] = call.message.contact.phone_number if call.message.contact else "شماره ثبت نشده"
    user["step"] = "weekly"
    user["weekly_pass"] = "1234"  # رمز هفتگی ثابت برای مثال
    save_users()
    bot.send_message(uid, "شماره دریافت شد. حالا لطفاً رمز هفتگی خود را وارد کنید:")

# وب‌هوک
@app.route("/webhook", methods=["POST"])
def webhook():
    json_data = request.get_json()
    if json_data:
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=10000)
