from flask import Flask, request
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = '7217912729:AAFAS2EHB9MsYQpKKYqyPA_dMAUg25I0yWY'
WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com'
ADMIN_ID = 8077313575  # شناسه عددی مدیر

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

waiting_users = []
chat_pairs = {}
blocked = {}  # user_id: [blocked_user_ids]
last_messages = {}  # user_id: last message

# ساخت کیبورد کاربر
def user_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("🎭 شروع چت ناشناس"))
    kb.row(KeyboardButton("❌ قطع چت"), KeyboardButton("🚫 بلاک"), KeyboardButton("📢 گزارش"))
    return kb

# ساخت کیبورد پنل مدیریت
def admin_panel():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("📊 آمار"), KeyboardButton("🔎 بررسی کاربر"))
    kb.row(KeyboardButton("❗️ هشدار"), KeyboardButton("⛔️ قطع دستی"))
    kb.row(KeyboardButton("🧾 پیام‌های آخر"), KeyboardButton("♻️ رفع بلاک"))
    kb.row(KeyboardButton("🔐 بستن پنل مدیریت"))
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "سلام! به چت ناشناس خوش آمدی.", reply_markup=user_menu())

@bot.message_handler(func=lambda m: m.text == "🎭 شروع چت ناشناس")
def start_chat(message):
    user_id = message.chat.id
    if user_id in chat_pairs:
        bot.send_message(user_id, "شما در حال چت هستید.")
        return
    for uid in waiting_users:
        if uid != user_id and user_id not in blocked.get(uid, []) and uid not in blocked.get(user_id, []):
            waiting_users.remove(uid)
            chat_pairs[user_id] = uid
            chat_pairs[uid] = user_id
            bot.send_message(user_id, "✅ متصل شدید. حالا می‌تونید چت کنید.")
            bot.send_message(uid, "✅ متصل شدید. حالا می‌تونید چت کنید.")
            return
    if user_id not in waiting_users:
        waiting_users.append(user_id)
    bot.send_message(user_id, "منتظر اتصال به کاربر دیگر هستید...")

@bot.message_handler(func=lambda m: m.text == "❌ قطع چت")
def cut_chat(message):
    end_chat(message.chat.id)

def end_chat(user_id):
    if user_id in chat_pairs:
        partner = chat_pairs.pop(user_id)
        chat_pairs.pop(partner, None)
        bot.send_message(partner, "🔌 چت توسط طرف مقابل قطع شد.", reply_markup=user_menu())
        bot.send_message(user_id, "🔌 چت پایان یافت.", reply_markup=user_menu())
    elif user_id in waiting_users:
        waiting_users.remove(user_id)
        bot.send_message(user_id, "از صف انتظار خارج شدید.", reply_markup=user_menu())
    else:
        bot.send_message(user_id, "شما در چت نبودید.", reply_markup=user_menu())

@bot.message_handler(func=lambda m: m.text == "🚫 بلاک")
def block_user(message):
    user = message.chat.id
    if user in chat_pairs:
        partner = chat_pairs[user]
        blocked.setdefault(user, []).append(partner)
        end_chat(user)
        bot.send_message(user, "🚫 کاربر بلاک شد و چت پایان یافت.")
    else:
        bot.send_message(user, "شما در حال چت نیستید.")

@bot.message_handler(func=lambda m: m.text == "📢 گزارش")
def report_user(message):
    user = message.chat.id
    if user in chat_pairs:
        partner = chat_pairs[user]
        bot.send_message(ADMIN_ID, f"📢 کاربر {user}، کاربر {partner} را گزارش کرد.")
        end_chat(user)
        bot.send_message(user, "✅ گزارش ارسال شد و چت پایان یافت.")
    else:
        bot.send_message(user, "شما در حال چت نیستید.")

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.text == "📊 آمار")
def stats(message):
    total = len(chat_pairs) // 2
    bot.send_message(ADMIN_ID, f"👥 چت‌های فعال: {total}\n⏳ در انتظار: {len(waiting_users)}")

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.text == "🔎 بررسی کاربر")
def check_user(message):
    bot.send_message(ADMIN_ID, "آی‌دی عددی کاربر را ارسال کنید...")

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.text == "❗️ هشدار")
def warn_user(message):
    bot.send_message(ADMIN_ID, "آی‌دی عددی کاربری که می‌خوای هشدار بدی را بفرست.")

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.text == "⛔️ قطع دستی")
def manual_cut(message):
    bot.send_message(ADMIN_ID, "آی‌دی یکی از طرف‌های چت را بفرست...")

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.text == "🧾 پیام‌های آخر")
def show_last(message):
    txt = ""
    for uid, msg in last_messages.items():
        txt += f"{uid}: {msg}\n"
    bot.send_message(ADMIN_ID, txt or "پیامی ثبت نشده.")

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.text == "♻️ رفع بلاک")
def unblock(message):
    bot.send_message(ADMIN_ID, "آی‌دی کاربری که می‌خوای رفع بلاک بشه رو بفرست...")

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.text == "🔐 بستن پنل مدیریت")
def close_panel(message):
    bot.send_message(ADMIN_ID, "پنل بسته شد.", reply_markup=user_menu())

@bot.message_handler(func=lambda m: m.text == "/admin" and m.chat.id == ADMIN_ID)
def open_admin(message):
    bot.send_message(ADMIN_ID, "📥 پنل مدیریت باز شد.", reply_markup=admin_panel())

@bot.message_handler(func=lambda m: True)
def relay(message):
    uid = message.chat.id
    last_messages[uid] = message.text
    if uid in chat_pairs:
        partner = chat_pairs[uid]
        try:
            bot.send_message(partner, message.text)
        except:
            bot.send_message(uid, "❗️ خطا در ارسال.")
    else:
        if uid == ADMIN_ID:
            bot.send_message(uid, "🔧 دستور پنل مدیریت: /admin")
        else:
            bot.send_message(uid, "ابتدا چت را شروع کنید.", reply_markup=user_menu())

@app.route('/', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode('utf-8'))
    bot.process_new_updates([update])
    return 'OK', 200

@app.route('/')
def home():
    return 'ربات فعال است.'

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host='0.0.0.0', port=10000)
