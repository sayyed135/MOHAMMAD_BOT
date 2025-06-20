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

connected_users = {}  # user_id: partner_id
pending_requests = set()
truth_dare_sessions = {}  # user_id: {"partner": id, "turn": str, "last_question": str}
blocked_users = set()

# سوالات
truth_questions = [
    "📖 بزرگترین دروغی که گفتی چی بوده؟",
    "📖 چیزی که از همه مخفی کردی چیه؟",
    "📖 تا حالا دزدکی کاری کردی؟"
]

dare_missions = [
    "🎭 یه صدای عجیب بفرست!",
    "🎭 به یکی پیام بده: «من عاشقت بودم»",
    "🎭 بدون توضیح یه شکلک عجیب بفرست!"
]

def main_menu(uid):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💬 شروع چت ناشناس", "🎭 جرأت و حقیقت")
    if uid in connected_users:
        markup.add("❌ قطع چت")
    bot.send_message(uid, "👇 لطفاً گزینه‌ای را انتخاب کنید:", reply_markup=markup)

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.data.decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid content type', 403

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    if uid == ADMIN_ID:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📊 پنل مدیریت")
        bot.send_message(uid, "سلام مدیر عزیز، به ربات خوش آمدی.", reply_markup=markup)
    else:
        main_menu(uid)

@bot.message_handler(func=lambda m: m.text == "📊 پنل مدیریت" and m.from_user.id == ADMIN_ID)
def admin_panel(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🚫 قطع چت فعال", "❌ بستن پنل")
    bot.send_message(message.chat.id, "📍 پنل مدیریت:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "❌ بستن پنل" and m.from_user.id == ADMIN_ID)
def close_panel(message):
    main_menu(message.chat.id)

@bot.message_handler(func=lambda m: m.text == "🚫 قطع چت فعال" and m.from_user.id == ADMIN_ID)
def disconnect_all(message):
    for uid in list(connected_users):
        pid = connected_users[uid]
        if pid:
            bot.send_message(uid, "❌ چت شما توسط مدیر قطع شد.")
            bot.send_message(pid, "❌ چت شما توسط مدیر قطع شد.")
            connected_users.pop(uid, None)
            connected_users.pop(pid, None)
    bot.send_message(message.chat.id, "✅ همه چت‌های فعال قطع شدند.")

@bot.message_handler(func=lambda m: m.text == "💬 شروع چت ناشناس")
def start_chat(message):
    uid = message.from_user.id
    if uid in connected_users:
        return bot.send_message(uid, "📌 شما هم‌اکنون در یک چت هستید.")
    pending_requests.add(uid)
    for u in pending_requests:
        if u != uid:
            bot.send_message(u, f"📨 یک نفر درخواست چت ناشناس داده است.\nبرای قبول روی /accept_{uid} بزنید.")
    bot.send_message(uid, "📡 درخواست شما برای کاربران دیگر ارسال شد...")

@bot.message_handler(func=lambda m: m.text.startswith("/accept_"))
def accept_request(message):
    try:
        target_id = int(message.text.split("_")[1])
        user_id = message.from_user.id
        if user_id in pending_requests and target_id in pending_requests:
            connected_users[user_id] = target_id
            connected_users[target_id] = user_id
            pending_requests.remove(user_id)
            pending_requests.remove(target_id)
            bot.send_message(user_id, "✅ به یک کاربر متصل شدید. گفتگو را شروع کنید!")
            bot.send_message(target_id, "✅ یک نفر درخواست شما را پذیرفت. گفتگو شروع شد!")
    except:
        pass

@bot.message_handler(func=lambda m: m.text == "❌ قطع چت")
def disconnect(message):
    uid = message.from_user.id
    pid = connected_users.get(uid)
    if pid:
        bot.send_message(pid, "🔌 طرف مقابل چت را قطع کرد.")
        connected_users.pop(pid, None)
    connected_users.pop(uid, None)
    main_menu(uid)

@bot.message_handler(func=lambda m: m.text == "🎭 جرأت و حقیقت")
def start_truth_dare(message):
    uid = message.from_user.id
    if uid in truth_dare_sessions:
        return bot.send_message(uid, "⏳ شما در حال حاضر در بازی هستید.")
    truth_dare_sessions[uid] = {"partner": None, "turn": "truth", "last_question": ""}
    for u in truth_dare_sessions:
        if u != uid and truth_dare_sessions[u]["partner"] is None:
            truth_dare_sessions[uid]["partner"] = u
            truth_dare_sessions[u]["partner"] = uid
            send_truth_or_dare(uid)
            send_truth_or_dare(u)
            return
    bot.send_message(uid, "🔍 در حال جستجوی بازیکن...")

def send_truth_or_dare(uid):
    data = truth_dare_sessions[uid]
    partner = data["partner"]
    if data["turn"] == "truth":
        q = choice(truth_questions)
        data["last_question"] = q
        bot.send_message(uid, f"❓ سوال حقیقت:\n{q}")
    else:
        q = choice(dare_missions)
        data["last_question"] = q
        bot.send_message(uid, f"🎯 ماموریت جرأت:\n{q}")

@bot.message_handler(func=lambda m: m.from_user.id in truth_dare_sessions)
def handle_truth_dare_reply(message):
    uid = message.from_user.id
    session = truth_dare_sessions.get(uid)
    if not session: return
    partner = session["partner"]
    if not partner: return

    # ارسال پاسخ به طرف مقابل
    bot.send_message(partner, f"👤 پاسخ طرف مقابل به سوال قبلی:\n{message.text}")
    
    # گزینه قبول یا رد
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ قبول", callback_data=f"td_accept_{uid}"),
        telebot.types.InlineKeyboardButton("❌ قابل قبول نیست", callback_data=f"td_reject_{uid}")
    )
    bot.send_message(partner, "👀 آیا پاسخ طرف مقابل را قبول دارید؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("td_"))
def handle_td_buttons(call):
    parts = call.data.split("_")
    action = parts[1]
    uid = int(parts[2])
    partner = call.from_user.id

    if action == "accept":
        truth_dare_sessions[uid]["turn"] = "dare" if truth_dare_sessions[uid]["turn"] == "truth" else "truth"
        send_truth_or_dare(uid)
    elif action == "reject":
        q = truth_dare_sessions[uid]["last_question"]
        bot.send_message(uid, f"🚫 طرف مقابل پاسخ شما را نپذیرفت.\nلطفاً دوباره به این پاسخ دهید:\n{q}")

@bot.message_handler(func=lambda m: m.from_user.id in connected_users and connected_users[m.from_user.id] is not None)
def anonymous_message(message):
    uid = message.from_user.id
    pid = connected_users[uid]
    bot.send_message(pid, message.text)

@bot.message_handler(func=lambda m: True)
def unknown(message):
    bot.send_message(message.chat.id, "❓ دستور ناشناس. لطفاً از منو استفاده کنید.")

# اجرای برنامه
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
