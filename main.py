import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
from datetime import datetime, timedelta
import json
import requests

TOKEN = "8209281771:AAETjo_FJOJZcSfgk26RsQxYr1sjQwNAXUo"
ADMIN_ID = 6994772164
WEBHOOK_URL = f"https://code-ai-0alo.onrender.com/{TOKEN}"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# ------------------- داده‌ها -------------------
accounts = {}  # user_id: {"name":..., "phone":..., "diamond":0,"gold":0,"coin":0,"last_bonus":None,"history":[]}
pending_action = {}
DATA_FILE = "accounts.json"

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(accounts, f)

def load_data():
    global accounts
    try:
        with open(DATA_FILE, "r") as f:
            accounts.update(json.load(f))
    except:
        accounts.clear()

load_data()

# ------------------- دکمه‌ها -------------------
def get_main_keyboard(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    if user_id in accounts and "phone" in accounts[user_id]:
        markup.add("پنل من")
    else:
        markup.add("اکانت")
        markup.add(KeyboardButton("ارسال شماره", request_contact=True))
    return markup

def get_user_panel():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📊 مشاهده امتیاز", callback_data="view_score"))
    markup.add(InlineKeyboardButton("💰 دریافت امتیاز روزانه", callback_data="daily_bonus"))
    markup.add(InlineKeyboardButton("📞 تغییر شماره", callback_data="change_phone"))
    markup.add(InlineKeyboardButton("✉️ پیام به مدیر", callback_data="msg_to_admin"))
    markup.add(InlineKeyboardButton("📜 تاریخچه تغییرات", callback_data="history"))
    return markup

def get_admin_panel():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("مشاهده شماره‌ها", callback_data="view_contacts"),
        InlineKeyboardButton("تعداد کاربران", callback_data="count_users"),
        InlineKeyboardButton("مشاهده امتیازها", callback_data="view_bonus")
    )
    markup.add(
        InlineKeyboardButton("ارسال پیام به کاربران", callback_data="send_msg_multi"),
        InlineKeyboardButton("تغییر امتیاز کاربران", callback_data="change_bonus_multi")
    )
    return markup

# ------------------- دریافت شماره -------------------
@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    user_id = message.from_user.id
    phone = message.contact.phone_number
    name = message.from_user.first_name

    if user_id not in accounts:
        accounts[user_id] = {"name": name, "phone": phone,
                             "diamond":0,"gold":0,"coin":0,"last_bonus":None,"history":[]}
        accounts[user_id]["history"].append(f"{datetime.now()} - ثبت شماره: {phone}")
    else:
        accounts[user_id]["phone"] = phone
        accounts[user_id]["history"].append(f"{datetime.now()} - تغییر شماره: {phone}")
    save_data()

    bot.send_message(message.chat.id, f"شماره شما ثبت شد: {phone}", reply_markup=get_user_panel())
    if user_id == ADMIN_ID:
        bot.send_message(message.chat.id, "پنل مدیریت فعال شد:", reply_markup=get_admin_panel())

# ------------------- کال‌بک‌ها -------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    acc = accounts.get(user_id)

    if call.data == "view_score" and acc:
        bot.send_message(call.message.chat.id,
                         f"📊 امتیاز شما:\nالماسی: {acc['diamond']}\nطلایی: {acc['gold']}\nسکه‌ای: {acc['coin']}\nآخرین دریافت امتیاز: {acc['last_bonus']}",
                         reply_markup=get_user_panel())
    elif call.data == "daily_bonus" and acc:
        now = datetime.now()
        last = datetime.fromisoformat(acc["last_bonus"]) if acc["last_bonus"] else None
        if not last or now - last >= timedelta(days=1):
            acc["coin"] += 5
            acc["last_bonus"] = str(now)
            acc["history"].append(f"{now} - دریافت ۵ امتیاز روزانه")
            save_data()
            bot.answer_callback_query(call.id, "۵ امتیاز روزانه اضافه شد!")
        else:
            bot.answer_callback_query(call.id, "امتیاز روزانه قبلاً دریافت شده.")
    elif call.data == "change_phone":
        bot.send_message(call.message.chat.id, "لطفاً شماره جدید خود را ارسال کنید.")
        pending_action[user_id] = "change_phone"
    elif call.data == "msg_to_admin":
        bot.send_message(call.message.chat.id, "پیام خود را برای مدیر ارسال کنید:")
        pending_action[user_id] = "msg_to_admin"
    elif call.data == "history" and acc:
        text = "\n".join(acc["history"][-10:]) if acc["history"] else "تاریخچه‌ای وجود ندارد."
        bot.send_message(call.message.chat.id, f"📜 آخرین تغییرات:\n{text}", reply_markup=get_user_panel())
    elif user_id == ADMIN_ID:
        if call.data == "view_contacts":
            text = "\n".join([f"{info['name']}: {info['phone']}" for info in accounts.values()]) or "هنوز شماره‌ای ثبت نشده."
            bot.send_message(call.message.chat.id, text, reply_markup=get_admin_panel())
        elif call.data == "count_users":
            bot.send_message(call.message.chat.id, f"تعداد کل کاربران: {len(accounts)}", reply_markup=get_admin_panel())

# ------------------- مدیریت پیام‌ها -------------------
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    acc = accounts.get(user_id)

    if pending_action.get(user_id) == "change_phone" and acc:
        new_phone = message.text
        acc["phone"] = new_phone
        acc["history"].append(f"{datetime.now()} - تغییر شماره: {new_phone}")
        save_data()
        bot.send_message(message.chat.id, f"شماره شما به {new_phone} تغییر یافت.", reply_markup=get_user_panel())
        pending_action.pop(user_id, None)
    elif pending_action.get(user_id) == "msg_to_admin" and acc:
        msg_text = message.text
        bot.send_message(ADMIN_ID, f"پیام از {acc['name']} ({acc['phone']}):\n{msg_text}")
        bot.send_message(message.chat.id, "پیام شما به مدیر ارسال شد.", reply_markup=get_user_panel())
        pending_action.pop(user_id, None)
    else:
        bot.send_message(message.chat.id, "لطفاً گزینه مورد نظر را انتخاب کنید:", reply_markup=get_main_keyboard(user_id))

# ------------------- مسیر وب‌هوک -------------------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/")
def index():
    return "Bot is running!", 200

# ------------------- ست کردن Webhook -------------------
try:
    requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")
except:
    print("Webhook not set!")

# ------------------- اجرای Flask -------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
