# main.py
from telebot import TeleBot, types
from flask import Flask, request
from datetime import datetime, timedelta
import threading

TOKEN = "7961151930:AAEM2r0BhaOp99eZtuL5BRQQYZc9335YHRs"
ADMIN_ID = 6994772164
WEBHOOK_URL = "https://code-ai-0alo.onrender.com/" + TOKEN

bot = TeleBot(TOKEN)
app = Flask(__name__)

# ---- حافظه داخلی ----
users = {}  # {user_id: {"name":..., "phone":..., "weekly_pass":..., "points":..., "subscription":..., "referrals":...}}
weekly_pass = "CODEAI2025"
current_version = "1.0"
user_buttons = {}  # {button_id: {"name":..., "message":..., "points":..., "expiry":...}}

# ---- کمکی ----
def check_user(user_id):
    if user_id not in users:
        return False
    if users[user_id].get("verified_weekly") != weekly_pass:
        return False
    return True

def add_points(user_id, points):
    if user_id in users:
        users[user_id]["points"] += points

# ---- استارت و ثبت نام ----
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("شروع ثبت نام"))
    bot.send_message(user_id, "سلام! برای استفاده از ربات ابتدا ثبت نام کنید.", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "شروع ثبت نام")
def register_name(message):
    user_id = message.from_user.id
    msg = bot.send_message(user_id, "لطفاً اسم خود را وارد کنید:")
    bot.register_next_step_handler(msg, get_name)

def get_name(message):
    user_id = message.from_user.id
    name = message.text
    users[user_id] = {"name": name, "points": 0, "subscription": "اشتراک یک", "referrals": 0}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("ارسال شماره 📱", request_contact=True))
    bot.send_message(user_id, "حالا شماره خود را ارسال کنید:", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def get_phone(message):
    user_id = message.from_user.id
    if message.contact is not None:
        users[user_id]["phone"] = message.contact.phone_number
        users[user_id]["verified_weekly"] = None
        bot.send_message(user_id, "شماره شما ثبت شد. لطفاً رمز هفتگی را وارد کنید:")

@bot.message_handler(func=lambda m: True)
def check_weekly_pass(message):
    user_id = message.from_user.id
    if user_id in users and users[user_id].get("verified_weekly") != weekly_pass:
        if message.text == weekly_pass:
            users[user_id]["verified_weekly"] = weekly_pass
            bot.send_message(user_id, "رمز هفتگی درست است. حالا می‌توانید از ربات استفاده کنید.")
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("کمک"))
            bot.send_message(user_id, "رمز اشتباه است! لطفاً رمز درست را وارد کنید.", reply_markup=markup)
        return
    # اینجا می‌تونی قابلیت‌های اصلی ربات اضافه بشه
    bot.send_message(user_id, "سلام! شما هم اکنون دسترسی دارید.")

# ---- دکمه امتیاز روزانه ----
@bot.message_handler(func=lambda m: m.text == "امتیاز روزانه")
def daily_points(message):
    user_id = message.from_user.id
    if not check_user(user_id):
        bot.send_message(user_id, "لطفاً ابتدا رمز هفتگی را وارد کنید.")
        return
    today = datetime.now().date()
    last_claim = users[user_id].get("last_daily")
    if last_claim == today:
        bot.send_message(user_id, "امتیاز امروز را قبلاً دریافت کرده‌اید.")
    else:
        points = 2 if users[user_id]["subscription"] == "اشتراک یک" else 4 if users[user_id]["subscription"] == "اشتراک دو" else 5
        add_points(user_id, points)
        users[user_id]["last_daily"] = today
        bot.send_message(user_id, f"امتیاز امروز اضافه شد: {points} امتیاز. کل امتیاز شما: {users[user_id]['points']}")

# ---- رفرال ----
@bot.message_handler(func=lambda m: m.text == "رفرال من")
def referral(message):
    user_id = message.from_user.id
    bot.send_message(user_id, f"لینک رفرال شما: https://t.me/CODE_AI_BOT?start={user_id}")

# ---- حساب کاربری ----
@bot.message_handler(func=lambda m: m.text == "حساب من")
def my_account(message):
    user_id = message.from_user.id
    if not check_user(user_id):
        bot.send_message(user_id, "لطفاً ابتدا رمز هفتگی را وارد کنید.")
        return
    u = users[user_id]
    bot.send_message(user_id, f"اسم: {u['name']}\nامتیاز: {u['points']}\nاشتراک: {u['subscription']}")

# ---- مدیریت ----
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("آمار کاربران")
    markup.add("افزودن دکمه جدید")
    bot.send_message(ADMIN_ID, "پنل مدیریت:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "آمار کاربران")
def stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    active_users = sum(1 for u in users.values() if u.get("verified_weekly") == weekly_pass)
    total_users = len(users)
    total_points = sum(u["points"] for u in users.values())
    bot.send_message(ADMIN_ID, f"کاربران فعال: {active_users}\nکل کاربران: {total_users}\nمجموع امتیازها: {total_points}")

# ---- وب هوک ----
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

# ---- سرور ----
if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=10000)
