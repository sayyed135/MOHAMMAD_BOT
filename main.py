import telebot
from flask import Flask, request
import os
from datetime import datetime
import random
import string

TOKEN = '7217912729:AAHEug-znb_CGJTXlITt3Zrjp2dJan0a9Gs'
WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com/'
ADMIN_ID = 6994772164

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

connected_users = {}
chat_logs = {}
chat_start_times = {}
blocked_users = set()
chat_enabled = True
feedbacks = []
reports = []
deferred_reports = {}  # user_id: reason
delete_requests = set()
user_points = {}
report_categories = ["🔞 محتوای جنسی", "🤬 توهین", "👤 جعلی بودن", "🚻 جنسیت اشتباه"]
custom_links_price = 2

def generate_history_code():
    return ''.join(random.choices(string.ascii_lowercase, k=7))

history_map = {}  # code: (u1, u2)

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.data.decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid content type', 403

@bot.message_handler(commands=['start'])
def handle_start(message):
    uid = message.from_user.id
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    if uid == ADMIN_ID:
        markup.add("📊 پنل مدیریت")
        bot.send_message(uid, "سلام مدیر! به پنل خوش اومدی.", reply_markup=markup)
    else:
        markup.add("💬 شروع چت ناشناس", "📛 گزارش تخلف", "📢 بازخورد", "🆔 اتصال با آیدی")
        if uid in connected_users:
            markup.add("❌ قطع چت")
        bot.send_message(uid, "سلام! به ربات پیام ناشناس خوش اومدی 😄", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "💬 شروع چت ناشناس")
def start_chat(message):
    uid = message.from_user.id
    if uid in blocked_users:
        return bot.send_message(uid, "🚫 شما مسدود هستید.")
    if not chat_enabled:
        return bot.send_message(uid, "❌ چت غیر فعال شده.")
    if uid in connected_users:
        return bot.send_message(uid, "ℹ️ در حال حاضر در چت هستی.")
    for u in connected_users:
        if connected_users[u] is None and u != uid:
            connected_users[u] = uid
            connected_users[uid] = u
            now = datetime.now()
            chat_start_times[(uid, u)] = now
            bot.send_message(u, "✅ به یک کاربر وصل شدید.")
            bot.send_message(uid, "✅ به یک کاربر وصل شدید.")
            return
    connected_users[uid] = None
    bot.send_message(uid, "🔎 در حال جستجوی کاربر...")

@bot.message_handler(func=lambda m: m.text == "❌ قطع چت")
def disconnect(message):
    uid = message.from_user.id
    pid = connected_users.get(uid)
    if pid:
        bot.send_message(pid, "❌ طرف مقابل چت را قطع کرد.")
        connected_users.pop(pid, None)
    connected_users.pop(uid, None)
    bot.send_message(uid, "✅ چت پایان یافت.")

@bot.message_handler(func=lambda m: m.text == "📢 بازخورد")
def feedback(message):
    bot.send_message(message.chat.id, "✍️ لطفاً بازخورد خود را بنویس:")
    bot.register_next_step_handler(message, save_feedback)

def save_feedback(message):
    feedbacks.append((message.from_user.id, message.text))
    bot.send_message(message.chat.id, "✅ ممنون بابت بازخوردت!")

@bot.message_handler(func=lambda m: m.text == "📛 گزارش تخلف")
def report_start(message):
    if message.from_user.id not in connected_users or connected_users[message.from_user.id] is None:
        return bot.send_message(message.chat.id, "❌ در حال حاضر در چت نیستی.")
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for r in report_categories:
        markup.add(r)
    bot.send_message(message.chat.id, "🔍 نوع تخلف را انتخاب کن:", reply_markup=markup)
    bot.register_next_step_handler(message, report_reason)

def report_reason(message):
    user = message.from_user.id
    partner = connected_users.get(user)
    if not partner:
        return bot.send_message(user, "❌ چت فعال نیست.")
    reports.append((user, partner, message.text))
    bot.send_message(user, "📨 گزارش شما ثبت شد.")
    deferred_reports[partner] = message.text

@bot.message_handler(func=lambda m: m.text == "🆔 اتصال با آیدی")
def connect_by_id(message):
    bot.send_message(message.chat.id, "لطفاً آیدی عددی کاربر را وارد کن:")
    bot.register_next_step_handler(message, handle_id_connection)

def handle_id_connection(message):
    try:
        target = int(message.text)
        uid = message.from_user.id
        if target == uid:
            return bot.send_message(uid, "❌ نمی‌تونی با خودت چت کنی.")
        connected_users[uid] = target
        connected_users[target] = uid
        bot.send_message(uid, "✅ اتصال با موفقیت انجام شد.")
        bot.send_message(target, "✅ شما به یک کاربر متصل شدید.")
    except:
        bot.send_message(message.chat.id, "❌ آیدی نامعتبر بود.")

@bot.message_handler(func=lambda m: m.from_user.id in connected_users and connected_users[m.from_user.id])
def relay_msg(message):
    sender = message.from_user.id
    receiver = connected_users.get(sender)
    if receiver not in connected_users or connected_users[receiver] != sender:
        return bot.send_message(sender, "❌ ارتباط قطع شده.")
    if "http" in message.text.lower():
        user_points.setdefault(sender, 0)
        if user_points[sender] < custom_links_price:
            return bot.send_message(sender, "❌ برای ارسال لینک، امتیاز کافی ندارید.")
        user_points[sender] -= custom_links_price
    bot.send_message(receiver, message.text)
    key = tuple(sorted([sender, receiver]))
    chat_logs.setdefault(key, []).append((sender, message.text, datetime.now().strftime('%H:%M')))

@bot.message_handler(func=lambda m: m.text == "📊 پنل مدیریت" and m.from_user.id == ADMIN_ID)
def admin_panel(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📈 آمار", "📁 تاریخچه چت", "🚫 مسدودها", "🧹 حذف گفتگو", "📬 گزارش تخلفات", "❌ بستن پنل")
    bot.send_message(message.chat.id, "🛠 پنل مدیریت:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID)
def admin_commands(message):
    if message.text == "📈 آمار":
        total = len(chat_logs)
        active = sum(1 for u in connected_users if connected_users[u])
        bot.send_message(ADMIN_ID, f"📊 کل گفتگوها: {total}\n👥 چت‌های فعال: {active}")

    elif message.text == "📁 تاریخچه چت":
        bot.send_message(ADMIN_ID, "🔍 آیدی کاربر را ارسال کنید:")
        bot.register_next_step_handler(message, send_histories)

    elif message.text == "🚫 مسدودها":
        if blocked_users:
            bot.send_message(ADMIN_ID, "🔒 مسدودی‌ها:\n" + "\n".join(map(str, blocked_users)))
        else:
            bot.send_message(ADMIN_ID, "✅ هیچ کاربر مسدودی نیست.")

    elif message.text == "📬 گزارش تخلفات":
        if not reports:
            return bot.send_message(ADMIN_ID, "📭 گزارشی وجود ندارد.")
        for uid, pid, reason in reports:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(
                telebot.types.InlineKeyboardButton("🚫 بلاک", callback_data=f"block_{pid}"),
                telebot.types.InlineKeyboardButton("⚠️ اخطار", callback_data=f"warn_{pid}")
            )
            bot.send_message(ADMIN_ID, f"📛 کاربر {uid} از {pid} بابت «{reason}» گزارش داده.", reply_markup=markup)

    elif message.text == "🧹 حذف گفتگو":
        bot.send_message(ADMIN_ID, "آیدی دو کاربر رو با فاصله بده:")
        bot.register_next_step_handler(message, delete_conversation)

    elif message.text == "❌ بستن پنل":
        markup = telebot.types.ReplyKeyboardRemove()
        bot.send_message(ADMIN_ID, "✅ پنل بسته شد.", reply_markup=markup)

def send_histories(message):
    uid = int(message.text)
    found = False
    for (u1, u2), logs in chat_logs.items():
        if uid in [u1, u2]:
            code = generate_history_code()
            history_map[code] = (u1, u2)
            other = u2 if uid == u1 else u1
            time = chat_start_times.get((u1, u2), "نامشخص")
            bot.send_message(ADMIN_ID, f"{uid} با {other} چت داشته است. برای دیدن تاریخچه: /hist_{code}")
            found = True
    if not found:
        bot.send_message(ADMIN_ID, "❌ سابقه‌ای یافت نشد.")

@bot.message_handler(func=lambda m: m.text.startswith("/hist_") and m.from_user.id == ADMIN_ID)
def show_history(message):
    code = message.text.split("_")[1]
    pair = history_map.get(code)
    if not pair:
        return bot.send_message(ADMIN_ID, "❌ کد نامعتبر.")
    logs = chat_logs.get(tuple(sorted(pair)), [])
    text = "\n".join([f"[{t}] {s}: {msg}" for s, msg, t in logs])
    bot.send_message(ADMIN_ID, text or "📭 بدون پیام.")

def delete_conversation(message):
    try:
        ids = list(map(int, message.text.strip().split()))
        if len(ids) == 2:
            key = tuple(sorted(ids))
            chat_logs.pop(key, None)
            bot.send_message(ADMIN_ID, "✅ گفتگو حذف شد.")
        else:
            bot.send_message(ADMIN_ID, "❌ فرمت اشتباه.")
    except:
        bot.send_message(ADMIN_ID, "❌ خطا در حذف گفتگو.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("block_"))
def block_user(call):
    uid = int(call.data.split("_")[1])
    blocked_users.add(uid)
    bot.send_message(ADMIN_ID, f"✅ کاربر {uid} مسدود شد.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("warn_"))
def warn_user(call):
    uid = int(call.data.split("_")[1])
    bot.send_message(uid, "⚠️ هشدار: لطفاً قوانین را رعایت کنید.")
    bot.send_message(ADMIN_ID, f"✅ به کاربر {uid} هشدار داده شد.")

@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(message.chat.id, "⛔ دستور نامشخص.")

# اجرای برنامه
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
