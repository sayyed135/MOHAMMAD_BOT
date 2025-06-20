import telebot
from flask import Flask, request
import os
from datetime import datetime
from random import choice

TOKEN = '7217912729:AAHEug-znb_CGJTXlITt3Zrjp2dJan0a9Gs'
WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com/'
ADMIN_ID = 6994772164

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

connected_users = {}
pending_requests = set()
blocked_users = set()
chat_logs = {}
chat_enabled = True
chat_start_times = {}
truth_dare_sessions = {}
pending_truth_dare = {}

truth_questions = [
    "📖 بزرگ‌ترین دروغی که گفتی چی بوده؟",
    "📖 آیا تا حالا به کسی خیانت کردی؟",
    "📖 چه چیزی رو از همه مخفی نگه داشتی؟"
]

dare_missions = [
    "🎭 یک عکس عجیب از خودت بفرست!",
    "🎭 اسم کسی که ازش متنفری رو بفرست!",
    "🎭 یه پیام عاشقانه به یکی از مخاطبینت بده و اسکرین بفرست!"
]

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.data.decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid content type', 403

def send_main_menu(user_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💬 شروع چت ناشناس", "🎭 جرأت و حقیقت")
    if user_id in connected_users:
        markup.add("❌ قطع چت")
    bot.send_message(user_id, "لطفاً یک گزینه انتخاب کنید:", reply_markup=markup)

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📊 پنل مدیریت")
        bot.send_message(user_id, "سلام مدیر عزیز! به پنل خوش آمدی.", reply_markup=markup)
    else:
        send_main_menu(user_id)

@bot.message_handler(func=lambda m: m.text == "📊 پنل مدیریت" and m.from_user.id == ADMIN_ID)
def admin_panel(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔎 جستجوی کاربران", "🚫 قطع چت فعال", "📣 درخواست‌های جرأت و حقیقت")
    markup.add("📥 پیام همگانی", "❌ بستن پنل")
    bot.send_message(message.chat.id, "پنل مدیریت:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📥 پیام همگانی" and m.from_user.id == ADMIN_ID)
def ask_broadcast(message):
    bot.send_message(message.chat.id, "پیام خود را بنویس تا برای همه کاربران ارسال شود:")
    bot.register_next_step_handler(message, do_broadcast)

def do_broadcast(message):
    msg = message.text
    for uid in connected_users.keys():
        try:
            bot.send_message(uid, f"📣 پیام از مدیر:\n{msg}")
        except:
            continue
    bot.send_message(ADMIN_ID, "✅ پیام برای کاربران فعال ارسال شد.")

@bot.message_handler(func=lambda m: m.text == "❌ بستن پنل" and m.from_user.id == ADMIN_ID)
def close_panel(message):
    send_main_menu(message.chat.id)

@bot.message_handler(func=lambda m: m.text == "🚫 قطع چت فعال" and m.from_user.id == ADMIN_ID)
def disconnect_any(message):
    for uid in list(connected_users):
        partner = connected_users.get(uid)
        if partner:
            bot.send_message(uid, "❌ چت شما توسط مدیر قطع شد.")
            bot.send_message(partner, "❌ چت شما توسط مدیر قطع شد.")
            connected_users.pop(uid, None)
            connected_users.pop(partner, None)
            return
    bot.send_message(message.chat.id, "هیچ چت فعالی پیدا نشد.")

@bot.message_handler(func=lambda m: m.text == "💬 شروع چت ناشناس")
def start_chat(message):
    user_id = message.from_user.id
    if user_id in connected_users:
        return bot.send_message(user_id, "شما در حال حاضر در یک چت هستید.")
    if user_id in pending_requests:
        return bot.send_message(user_id, "منتظر اتصال به کاربر دیگر هستید...")

    pending_requests.add(user_id)
    for uid in list(pending_requests):
        if uid != user_id:
            connected_users[uid] = user_id
            connected_users[user_id] = uid
            pending_requests.remove(uid)
            pending_requests.remove(user_id)
            chat_start_times[(user_id, uid)] = datetime.now()
            bot.send_message(uid, "✅ به یک کاربر متصل شدید. پیام بده!")
            bot.send_message(user_id, "✅ به یک کاربر متصل شدید. پیام بده!")
            return
    bot.send_message(user_id, "⏳ در حال جستجوی یک کاربر...")

@bot.message_handler(func=lambda m: m.text == "❌ قطع چت")
def disconnect(message):
    user_id = message.from_user.id
    partner_id = connected_users.get(user_id)
    if partner_id:
        bot.send_message(partner_id, "❌ طرف مقابل چت را قطع کرد.")
        connected_users.pop(partner_id, None)
    if user_id in connected_users:
        bot.send_message(user_id, "❌ چت قطع شد.")
        connected_users.pop(user_id, None)
    send_main_menu(user_id)

@bot.message_handler(func=lambda m: m.text == "🎭 جرأت و حقیقت")
def start_truth_dare(message):
    user_id = message.from_user.id
    if user_id in truth_dare_sessions:
        return bot.send_message(user_id, "شما قبلاً وارد بازی شدید.")
    truth_dare_sessions[user_id] = {"partner": None, "turn": "truth"}

    for uid, data in truth_dare_sessions.items():
        if uid != user_id and data["partner"] is None:
            truth_dare_sessions[user_id]["partner"] = uid
            truth_dare_sessions[uid]["partner"] = user_id
            bot.send_message(user_id, "✅ به بازی متصل شدید!")
            bot.send_message(uid, "✅ به بازی متصل شدید!")
            send_truth_dare(uid)
            return
    bot.send_message(user_id, "در حال جستجوی بازیکن دیگر...")

def send_truth_dare(user_id):
    data = truth_dare_sessions[user_id]
    partner = data["partner"]
    if data["turn"] == "truth":
        q = choice(truth_questions)
        bot.send_message(user_id, f"سوال حقیقت: {q}")
        data["turn"] = "dare"
    else:
        q = choice(dare_missions)
        bot.send_message(user_id, f"ماموریت جرأت: {q}")
        data["turn"] = "truth"
    truth_dare_sessions[partner]["turn"] = data["turn"]

@bot.message_handler(func=lambda m: m.from_user.id in connected_users and connected_users[m.from_user.id] is not None)
def handle_chat(message):
    uid = message.from_user.id
    partner = connected_users[uid]
    bot.send_message(partner, message.text)
    key = tuple(sorted([uid, partner]))
    chat_logs.setdefault(key, []).append((uid, message.text, datetime.now().strftime('%H:%M')))

@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(message.chat.id, "دستور نامشخص است. لطفاً از منو استفاده کنید.")

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
