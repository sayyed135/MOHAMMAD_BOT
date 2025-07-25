import sqlite3
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = '7217912729:AAGXxp8wDSX1dSpWrRw5RhAY8zDIV1QLvIo'
ADMIN_ID = 6994772164
WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com/'

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# دیتابیس
conn = sqlite3.connect("bot_db.sqlite", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 10,
    level TEXT DEFAULT 'free'
)
''')
conn.commit()

# پنل اصلی کاربر
def user_panel(user_id):
    cursor.execute("SELECT points, level FROM users WHERE user_id=?", (user_id,))
    data = cursor.fetchone()
    if data:
        points, level = data
    else:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        points, level = 10, 'free'

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("امتیاز روزانه", callback_data='daily_point'),
        InlineKeyboardButton("خرید اشتراک", callback_data='buy_sub')
    )
    if user_id == ADMIN_ID:
        markup.add(InlineKeyboardButton("پنل مدیریت", callback_data='admin_panel'))

    text = f"🧑‍💼 شناسه: `{user_id}`\n💎 امتیاز شما: {points}\n⭐ سطح: {level}"
    return text, markup

# پنل خرید اشتراک
def subscription_panel():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("معمولی (کسر 5 امتیاز)", callback_data='sub_normal'),
        InlineKeyboardButton("حرفه‌ای (کسر 10 امتیاز)", callback_data='sub_pro'),
        InlineKeyboardButton("VIP (کسر 20 امتیاز)", callback_data='sub_vip')
    )
    return markup

# پنل مدیر
def admin_panel():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("ارسال پیام به همه", callback_data='broadcast')
    )
    return markup

# شروع
@bot.message_handler(commands=['start'])
def start(message):
    text, markup = user_panel(message.from_user.id)
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# کال‌بک‌ها
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.from_user.id

    if call.data == "daily_point":
        cursor.execute("UPDATE users SET points = points + 1 WHERE user_id=?", (user_id,))
        conn.commit()
        bot.answer_callback_query(call.id, "۱ امتیاز اضافه شد!")
        text, markup = user_panel(user_id)
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "buy_sub":
        bot.edit_message_text("💳 لطفاً یک گزینه را انتخاب کنید:", call.message.chat.id, call.message.message_id, reply_markup=subscription_panel())

    elif call.data.startswith("sub_"):
        levels = {
            "sub_normal": ("معمولی", 5),
            "sub_pro": ("حرفه‌ای", 10),
            "sub_vip": ("VIP", 20)
        }
        name, cost = levels[call.data]
        cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        points = cursor.fetchone()[0]
        if points >= cost:
            cursor.execute("UPDATE users SET points = points - ?, level = ? WHERE user_id=?", (cost, name, user_id))
            conn.commit()
            bot.answer_callback_query(call.id, f"✅ اشتراک {name} فعال شد.")
        else:
            bot.answer_callback_query(call.id, "❌ امتیاز کافی ندارید.")

        text, markup = user_panel(user_id)
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "admin_panel" and user_id == ADMIN_ID:
        bot.edit_message_text("🛠 پنل مدیریت:", call.message.chat.id, call.message.message_id, reply_markup=admin_panel())

    elif call.data == "broadcast" and user_id == ADMIN_ID:
        msg = bot.send_message(user_id, "✏️ پیام مورد نظر را برای ارسال به همه بنویس:")
        bot.register_next_step_handler(msg, broadcast_message)

def broadcast_message(message):
    cursor.execute("SELECT user_id FROM users")
    ids = cursor.fetchall()
    for (uid,) in ids:
        try:
            bot.send_message(uid, f"📢 پیام مدیر:\n\n{message.text}")
        except:
            continue
    bot.send_message(ADMIN_ID, "✅ پیام به همه کاربران ارسال شد.")

# Webhook
@app.route('/', methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return 'ok', 200

@app.route('/')
def index():
    return 'ربات فعال است!'

# ست کردن وبهوک فقط یکبار
import requests
requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
