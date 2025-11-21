from telebot import TeleBot, types
from datetime import datetime, timedelta
import json
import os

TOKEN = "7961151930:AAEM2r0BhaOp99eZtuL5BRQQYZc9335YHRs"
ADMIN_ID = 6994772164
BOT_VERSION = "1.0"

bot = TeleBot(TOKEN)

# ذخیره‌سازی اطلاعات کاربران در فایل JSON تا بعد از ری‌استارت پاک نشه
DATA_FILE = "users_data.json"

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        users_data = json.load(f)
else:
    users_data = {}

# ذخیره اطلاعات به فایل
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(users_data, f)

# استارت ربات
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = str(message.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    if message.from_user.id == ADMIN_ID:
        markup.add(types.KeyboardButton("مدیریت"))
        bot.send_message(chat_id, f"سلام مدیر! نسخه ربات: {BOT_VERSION}", reply_markup=markup)
    else:
        if chat_id not in users_data:
            users_data[chat_id] = {
                "name": "",
                "phone": "",
                "score": 0,
                "referrals": 0,
                "subscription": "اشتراک 1",
                "last_daily": None,
                "version": BOT_VERSION
            }
            save_data()
        markup.add(types.KeyboardButton("شروع"))
        bot.send_message(chat_id, "سلام! روی شروع بزن تا کار با ربات رو شروع کنی.", reply_markup=markup)

# دکمه مدیریت
@bot.message_handler(func=lambda m: m.text == "مدیریت" and m.from_user.id == ADMIN_ID)
def admin_panel(message):
    chat_id = str(message.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("آمار کاربران", "نسخه جدید ربات", "دکمه‌ها")
    bot.send_message(chat_id, "پنل مدیریت:", reply_markup=markup)

# نمایش آمار کاربران
@bot.message_handler(func=lambda m: m.text == "آمار کاربران" and m.from_user.id == ADMIN_ID)
def stats(message):
    total_users = len(users_data)
    active_users = sum(1 for u in users_data.values() if u["score"] > 0)
    bot.send_message(message.chat.id, f"کل کاربران: {total_users}\nکاربران فعال: {active_users}")

# شروع برای کاربران عادی
@bot.message_handler(func=lambda m: m.text == "شروع")
def start_user(message):
    chat_id = str(message.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("ثبت نام"), types.KeyboardButton("حساب کاربری"), types.KeyboardButton("امتیاز روزانه"))
    bot.send_message(chat_id, "صفحه اصلی:", reply_markup=markup)

# ثبت نام
@bot.message_handler(func=lambda m: m.text == "ثبت نام")
def register(message):
    chat_id = str(message.chat.id)
    msg = bot.send_message(chat_id, "لطفا اسم خود را وارد کنید:")
    bot.register_next_step_handler(msg, set_name)

def set_name(message):
    chat_id = str(message.chat.id)
    users_data[chat_id]["name"] = message.text
    save_data()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("ارسال شماره"))
    msg = bot.send_message(chat_id, "لطفا شماره خود را ارسال کنید:", reply_markup=markup)
    bot.register_next_step_handler(msg, set_phone)

def set_phone(message):
    chat_id = str(message.chat.id)
    if message.contact:  # اگه شماره از طریق دکمه تلگرام فرستاده شد
        users_data[chat_id]["phone"] = message.contact.phone_number
    else:
        users_data[chat_id]["phone"] = message.text
    save_data()
    bot.send_message(chat_id, "شماره ثبت شد!")

# حساب کاربری
@bot.message_handler(func=lambda m: m.text == "حساب کاربری")
def account(message):
    chat_id = str(message.chat.id)
    user = users_data.get(chat_id)
    if user:
        bot.send_message(chat_id, f"اسم: {user['name']}\nامتیاز: {user['score']}\nاشتراک: {user['subscription']}\nنسخه ربات: {user['version']}")

# امتیاز روزانه
@bot.message_handler(func=lambda m: m.text == "امتیاز روزانه")
def daily_score(message):
    chat_id = str(message.chat.id)
    user = users_data.get(chat_id)
    today = datetime.now().date()
    if user["last_daily"] != str(today):
        user["score"] += 2 if user["subscription"]=="اشتراک 1" else 4 if user["subscription"]=="اشتراک 2" else 50
        user["last_daily"] = str(today)
        save_data()
        bot.send_message(chat_id, f"امتیاز روزانه اضافه شد! امتیاز جدید: {user['score']}")
    else:
        bot.send_message(chat_id, "امتیاز روزانه امروز قبلا گرفته شده.")

bot.infinity_polling()
