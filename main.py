# main.py
from flask import Flask, request, jsonify
from telebot import TeleBot, types
import json, os, datetime
from persiantools.jdatetime import JalaliDate

# ====== تنظیمات ======
TELEGRAM_TOKEN = "7961151930:AAEM2r0BhaOp99eZtuL5BRQQYZc9335YHRs"
WEBHOOK_URL = "https://code-ai-0alo.onrender.com/webhook"
ADMIN_ID = 6994772164
DATA_FILE = "users.json"
WEEKLY_PASSWORD = "CODEAI123"

bot = TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# ====== بارگذاری اطلاعات کاربران ======
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
else:
    users = {}

def save_users():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# ====== کیبورد شیشه‌ای ======
def make_button(text, callback_data=None, url=None):
    return types.InlineKeyboardButton(text=text, callback_data=callback_data, url=url)

def main_menu(user_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(make_button("حساب کاربری", f"account_{user_id}"))
    kb.add(make_button("امتیاز روزانه", f"daily_{user_id}"))
    kb.add(make_button("هدیه هفتگی", f"weekly_{user_id}"))
    kb.add(make_button("لینک رفرال", f"ref_{user_id}"))
    return kb

def help_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(make_button("کمک", url="https://t.me/MohammadSadat_Afg"))
    return kb

# ====== دستور start ======
@bot.message_handler(commands=["start"])
def start(message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        users[user_id] = {
            "step": "name", "name": "", "phone": "", "weekly_pass": False,
            "score": 0, "subscription": 1, "ref_count": 0, "ref_code": f"CODE{user_id}"
        }
        save_users()
    bot.send_message(user_id, "سلام! لطفا اسم خود را وارد کنید:")

# ====== دریافت پیام ======
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        bot.send_message(user_id, "لطفا ابتدا /start را بزنید.")
        return

    user = users[user_id]

    # مرحله وارد کردن اسم
    if user["step"] == "name":
        user["name"] = message.text
        user["step"] = "phone"
        save_users()
        kb = types.InlineKeyboardMarkup()
        kb.add(make_button("ارسال شماره", "send_phone"))
        bot.send_message(user_id, "اسم ثبت شد. شماره خود را ارسال کنید:", reply_markup=kb)
        return

    # مرحله رمز هفتگی
    if user["step"] == "weekly":
        if message.text == WEEKLY_PASSWORD:
            user["weekly_pass"] = True
            save_users()
            bot.send_message(user_id, "رمز هفتگی تایید شد!", reply_markup=main_menu(user_id))
        else:
            bot.send_message(user_id, "رمز اشتباه است.", reply_markup=help_kb())
        return

# ====== دکمه‌ها ======
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = str(call.from_user.id)
    user = users[user_id]
    data = call.data

    if data == "send_phone":
        user["phone"] = "شماره ثبت شده"  # شماره واقعی دستی نمیاد
        user["step"] = "weekly"
        save_users()
        bot.send_message(user_id, "شماره ثبت شد. لطفا رمز هفتگی را وارد کنید:")

    elif data.startswith("account_"):
        text = f"نام: {user['name']}\nامتیاز: {user['score']}\nاشتراک: {user['subscription']}\nلینک رفرال: {user['ref_code']}"
        bot.send_message(user_id, text, reply_markup=main_menu(user_id))

    elif data.startswith("daily_"):
        today = datetime.datetime.now().date().isoformat()
        if "last_daily" not in user or user["last_daily"] != today:
            points = 2 if user["subscription"] == 1 else 4 if user["subscription"] == 2 else 0
            user["score"] += points
            user["last_daily"] = today
            save_users()
            bot.send_message(user_id, f"امتیاز روزانه اضافه شد: {points}")
        else:
            bot.send_message(user_id, "امتیاز روزانه قبلا گرفته شده.")

    elif data.startswith("weekly_"):
        points = 5 if user["subscription"] in [1,2] else 50
        user["score"] += points
        save_users()
        bot.send_message(user_id, f"هدیه هفتگی اضافه شد: {points}")

    elif data.startswith("ref_"):
        bot.send_message(user_id, f"لینک رفرال شما: https://t.me/YourBot?start={user['ref_code']}")

    elif data == "stats" and call.from_user.id == ADMIN_ID:
        total_users = len(users)
        active_users = sum(1 for u in users.values() if u.get("weekly_pass"))
        total_score = sum(u.get("score",0) for u in users.values())
        now = JalaliDate.today()
        bot.send_message(ADMIN_ID, f"کاربران فعال: {active_users}\nکل کاربران: {total_users}\nمجموع امتیاز: {total_score}\nتاریخ شمسی: {now}")

# ====== وبهوک ======
@app.route("/webhook", methods=["POST"])
def webhook():
    json_data = request.get_json()
    if json_data:
        bot.process_new_updates([types.Update.de_json(json_data)])
    return jsonify({"status": "ok"})

# ====== اجرای وبهوک ======
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=10000)
