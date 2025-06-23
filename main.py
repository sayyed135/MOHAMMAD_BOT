import telebot
from flask import Flask, request
import json
import os
import openai

API_TOKEN = "7217912729:AAFihwxHEbbaMJec31GhFYlfaUA1jXxU-Ac"
OPENAI_API_KEY = "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"
ADMIN_ID = 6994772164

openai.api_key = OPENAI_API_KEY
bot = telebot.TeleBot(API_TOKEN, threaded=True)
app = Flask(__name__)

DATA_FILE = "data.json"
SETTINGS = {"mode": "TON", "cost": 1}

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

users = load_data()

def get_user(uid):
    if str(uid) not in users:
        users[str(uid)] = {"TON": 10, "DIAMOND": 5}
    return users[str(uid)]

@app.route("/", methods=["GET"])
def home():
    return "ربات فعال است ✅"

@app.route("/", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        update = telebot.types.Update.de_json(request.data.decode("utf-8"))
        bot.process_new_updates([update])
        return "", 200
    return "403", 403

@bot.message_handler(commands=["start"])
def start(message):
    get_user(message.from_user.id)
    save_data(users)
    bot.send_message(message.chat.id, "سلام! به ربات خوش آمدی 😊", reply_markup=main_buttons())

@bot.message_handler(commands=["delete"])
def delete(message):
    uid = str(message.from_user.id)
    if uid in users:
        del users[uid]
        save_data(users)
        bot.reply_to(message, "اطلاعات شما حذف شد.")

def main_buttons():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🧠 هوش مصنوعی", callback_data="ai"))
    markup.add(telebot.types.InlineKeyboardButton("👑 پنل مدیریت", callback_data="admin"))
    return markup

@bot.callback_query_handler(func=lambda call: True)
def handle_inline(call):
    uid = call.from_user.id
    if call.data == "ai":
        bot.send_message(uid, "سوالت رو بنویس تا جواب بدم.")
        bot.register_next_step_handler_by_chat_id(uid, ai_chat)
    elif call.data == "admin" and uid == ADMIN_ID:
        admin_panel(uid)

def admin_panel(uid):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🔁 تغییر نوع امتیاز", callback_data="setmode"))
    markup.add(telebot.types.InlineKeyboardButton("💰 تغییر قیمت", callback_data="setcost"))
    markup.add(telebot.types.InlineKeyboardButton("📢 پیام همگانی", callback_data="broadcast"))
    markup.add(telebot.types.InlineKeyboardButton("📊 لیست کاربران", callback_data="listusers"))
    bot.send_message(uid, "پنل مدیریت:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "setmode")
def change_mode(call):
    SETTINGS["mode"] = "DIAMOND" if SETTINGS["mode"] == "TON" else "TON"
    bot.send_message(call.message.chat.id, f"حالت مصرف روی {SETTINGS['mode']} تنظیم شد.")

@bot.callback_query_handler(func=lambda call: call.data == "setcost")
def change_cost(call):
    bot.send_message(call.message.chat.id, "مقدار جدید هزینه هر پیام را بفرست.")
    bot.register_next_step_handler(call.message, save_cost)

def save_cost(msg):
    try:
        SETTINGS["cost"] = int(msg.text.strip())
        bot.reply_to(msg, f"هزینه جدید: {SETTINGS['cost']}")
    except:
        bot.reply_to(msg, "عدد نامعتبر")

@bot.callback_query_handler(func=lambda call: call.data == "broadcast")
def broadcast_start(call):
    bot.send_message(call.message.chat.id, "پیام همگانی رو بفرست.")
    bot.register_next_step_handler(call.message, do_broadcast)

def do_broadcast(msg):
    for uid in users:
        try:
            bot.send_message(uid, msg.text)
        except:
            continue
    bot.reply_to(msg, "پیام به همه ارسال شد.")

@bot.callback_query_handler(func=lambda call: call.data == "listusers")
def list_users(call):
    count = len(users)
    bot.send_message(call.message.chat.id, f"تعداد کاربران: {count}")

def ai_chat(msg):
    uid = str(msg.from_user.id)
    user = get_user(uid)
    mode = SETTINGS["mode"]
    cost = SETTINGS["cost"]

    if user[mode] < cost:
        bot.reply_to(msg, f"امتیاز کافی نداری ({mode})")
        return

    prompt = msg.text.strip()
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        reply = response.choices[0].message.content
        bot.reply_to(msg, reply)
        user[mode] -= cost
        save_data(users)
    except Exception as e:
        bot.reply_to(msg, f"خطا: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
