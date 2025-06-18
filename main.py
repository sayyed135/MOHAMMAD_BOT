import telebot
from flask import Flask, request
import os
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = '7217912729:AAHEug-znb_CGJTXlITt3Zrjp2dJan0a9Gs'
WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com/'
ADMIN_ID = 6994772164

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

connected_users = {}  # user_id: partner_id
blocked_users = set()
chat_logs = {}  # (user_id, partner_id): [(sender_id, msg, time)]
chat_enabled = True
chat_start_times = {}
user_scores = {}  # user_id: int
user_reports = []  # [(reporter_id, reported_id, reason)]
user_feedback = []  # [(user_id, partner_id, feedback)]
deleted_chats = set()  # (user_id, partner_id)

# Webhook
@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.data.decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid content type', 403

# start
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📊 پنل مدیریت")
        bot.send_message(user_id, "سلام مدیر عزیز!", reply_markup=markup)
    else:
        user_scores.setdefault(user_id, 5)
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("💬 شروع چت ناشناس")
        if user_id in connected_users:
            markup.add("❌ قطع چت ناشناس")
        bot.send_message(user_id, "سلام به چت ناشناس خوش آمدی!", reply_markup=markup)

# قطع چت
@bot.message_handler(func=lambda m: m.text == "❌ قطع چت ناشناس")
def disconnect(message):
    uid = message.from_user.id
    partner = connected_users.get(uid)
    bot.send_message(uid, "❌ چت شما قطع شد.")
    if partner:
        bot.send_message(partner, "❌ طرف مقابل چت را قطع کرد.")
        del connected_users[partner]
    if uid in connected_users:
        del connected_users[uid]
    # سوال درباره رضایت
    if partner:
        ask_feedback(uid, partner)
        ask_feedback(partner, uid)
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🗑 حذف کامل گفتگو", callback_data=f"del_{uid}_{partner}"))
        bot.send_message(uid, "آیا می‌خواهی کل گفتگو پاک شود؟", reply_markup=markup)

# شروع چت
@bot.message_handler(func=lambda m: m.text == "💬 شروع چت ناشناس")
def start_chat(message):
    uid = message.from_user.id
    if not chat_enabled:
        return bot.send_message(uid, "❌ چت غیر فعال است.")
    if uid in blocked_users:
        return bot.send_message(uid, "🚫 مسدود هستید.")
    if uid in connected_users:
        return bot.send_message(uid, "🔄 شما در چت هستید.")
    for other in connected_users:
        if connected_users[other] is None and other != uid:
            connected_users[uid] = other
            connected_users[other] = uid
            now = datetime.now()
            chat_start_times[(uid, other)] = now
            bot.send_message(uid, "✅ متصل شدی!")
            bot.send_message(other, "✅ متصل شدی!")
            return
    connected_users[uid] = None
    bot.send_message(uid, "⏳ درحال جستجو...")

# پیام چت
@bot.message_handler(func=lambda m: m.from_user.id in connected_users and connected_users[m.from_user.id])
def handle_chat(message):
    sender = message.from_user.id
    receiver = connected_users[sender]
    if not receiver:
        return
    if any(bad in message.text.lower() for bad in ["fuck", "shit", "porn"]):
        bot.send_message(sender, "⚠️ لطفاً از کلمات مناسب استفاده کن!")
    if "http" in message.text or ".com" in message.text:
        if user_scores.get(sender, 0) >= 2:
            user_scores[sender] -= 2
        else:
            return bot.send_message(sender, "❌ امتیاز کافی برای ارسال لینک نداری.")
    bot.send_message(receiver, message.text)
    log_key = tuple(sorted([sender, receiver]))
    chat_logs.setdefault(log_key, []).append((sender, message.text, datetime.now().strftime('%H:%M:%S')))

# بازخورد
def ask_feedback(uid, pid):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("😊 راضی", callback_data=f"feed_yes_{uid}_{pid}"),
        InlineKeyboardButton("😠 ناراضی", callback_data=f"feed_no_{uid}_{pid}")
    )
    bot.send_message(uid, "نظرت درباره رفتار طرف مقابل؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("feed_"))
def handle_feedback(call):
    parts = call.data.split("_")
    typ, uid, pid = parts[1], int(parts[2]), int(parts[3])
    if typ == "no":
        user_feedback.append((uid, pid, "نا‌رضایتی"))
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🚫 بلاک", callback_data=f"block_{pid}"))
        markup.add(InlineKeyboardButton("⚠️ اخطار", callback_data=f"warn_{pid}"))
        bot.send_message(ADMIN_ID, f"❗️کاربر {uid} از {pid} ناراضی بود!", reply_markup=markup)

# حذف گفتگو
@bot.callback_query_handler(func=lambda c: c.data.startswith("del_"))
def delete_chat(call):
    _, uid, pid = call.data.split("_")
    uid, pid = int(uid), int(pid)
    chat_logs.pop(tuple(sorted([uid, pid])), None)
    deleted_chats.add((uid, pid))
    bot.send_message(uid, "✅ گفتگو حذف شد.")

# گزارش تخلف
@bot.message_handler(commands=['report'])
def report_user(message):
    reporter = message.from_user.id
    if reporter not in connected_users or not connected_users[reporter]:
        return bot.send_message(reporter, "❌ شما در چت نیستید.")
    reported = connected_users[reporter]
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🧑‍🦰 جنسیت اشتباه", callback_data=f"rep_{reporter}_{reported}_جنسیت اشتباه"),
        InlineKeyboardButton("🤬 توهین", callback_data=f"rep_{reporter}_{reported}_توهین"),
        InlineKeyboardButton("📛 جعلی", callback_data=f"rep_{reporter}_{reported}_جعلی"),
        InlineKeyboardButton("🔞 پورن", callback_data=f"rep_{reporter}_{reported}_پورن")
    )
    bot.send_message(reporter, "🔍 علت تخلف رو انتخاب کن:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("rep_"))
def handle_report(call):
    _, reporter, reported, reason = call.data.split("_", 3)
    user_reports.append((int(reporter), int(reported), reason))
    bot.send_message(int(reporter), "✅ گزارش ثبت شد. در دست بررسی مدیر است.")

# پنل مدیریت
@bot.message_handler(func=lambda m: m.text == "📊 پنل مدیریت" and m.from_user.id == ADMIN_ID)
def admin_panel(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📁 گزارش تخلفات", "🗂 بازخورد کاربران")
    markup.add("❌ بستن پنل")
    bot.send_message(message.chat.id, "📋 پنل پیشرفته مدیریت:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text == "📁 گزارش تخلفات")
def show_reports(message):
    text = "📌 گزارش‌ها:\n"
    for i, (r1, r2, reason) in enumerate(user_reports):
        text += f"{i+1}. {r1} از {r2} بابت {reason}\n"
    bot.send_message(ADMIN_ID, text or "هیچ گزارشی نیست")

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text == "🗂 بازخورد کاربران")
def show_feedbacks(message):
    text = "💬 بازخورد‌ها:\n"
    for uid, pid, fb in user_feedback:
        text += f"{uid} از {pid} => {fb}\n"
    bot.send_message(ADMIN_ID, text or "بازخوردی نیست.")

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text == "❌ بستن پنل")
def close_panel(message):
    markup = telebot.types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "منو بسته شد.", reply_markup=markup)

# اجرای ربات
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
