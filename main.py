import os
import telebot
from flask import Flask, request
import sqlite3
from datetime import datetime

# ----------------- تنظیمات اصلی -----------------
TOKEN = "7961151930:AAGiq4-yqNpMc3aZ1F1k8DpNqjHqFKmpxyY"
WEBHOOK_URL = "https://code-ai-0alo.onrender.com"  # آدرس وب‌سرویس Render
ADMIN_ID = 6994772164

# ساخت پوشه بکاپ اگر وجود نداشت
if not os.path.exists("backups"):
    os.makedirs("backups")

DB_PATH = "bot_data.db"

# ----------------- دیتابیس -----------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    points INTEGER DEFAULT 0,
                    lang TEXT DEFAULT 'en'
                )""")
    conn.commit()
    conn.close()

init_db()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT points, lang FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if row is None:
        c.execute("INSERT INTO users (user_id, points, lang) VALUES (?, 0, 'en')", (user_id,))
        conn.commit()
        conn.close()
        return 0, 'en'
    conn.close()
    return row

def update_points(user_id, amount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET points = points + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def set_language(user_id, lang):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, user_id))
    conn.commit()
    conn.close()

# ----------------- ربات -----------------
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# پیام شروع
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    points, lang = get_user(user_id)
    if lang == 'fa':
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("پشتیبانی", "امتیاز روزانه")
        bot.send_message(user_id, "سلام! خوش آمدی 🌹", reply_markup=markup)
    else:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Support", "Daily Points")
        bot.send_message(user_id, "Welcome! 👋", reply_markup=markup)

# دکمه‌ها
@bot.message_handler(func=lambda m: True)
def handle_buttons(message):
    user_id = message.from_user.id
    points, lang = get_user(user_id)

    if message.text in ["امتیاز روزانه", "Daily Points"]:
        update_points(user_id, 1)
        points, lang = get_user(user_id)
        if lang == 'fa':
            bot.send_message(user_id, f"✅ یک امتیاز اضافه شد. امتیاز فعلی: {points}")
        else:
            bot.send_message(user_id, f"✅ One point added. Current points: {points}")

    elif message.text in ["پشتیبانی", "Support"]:
        if lang == 'fa':
            bot.send_message(user_id, "📩 برای پشتیبانی با مدیر در تماس باشید.")
        else:
            bot.send_message(user_id, "📩 Contact admin for support.")

    elif message.text == "Language":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("فارسی", "English")
        bot.send_message(user_id, "Select Language:", reply_markup=markup)

    elif message.text == "فارسی":
        set_language(user_id, 'fa')
        bot.send_message(user_id, "✅ زبان روی فارسی تنظیم شد.")

    elif message.text == "English":
        set_language(user_id, 'en')
        bot.send_message(user_id, "✅ Language set to English.")

    elif message.text == "آمار" and user_id == ADMIN_ID:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*), SUM(points) FROM users")
        total_users, total_points = c.fetchone()
        conn.close()
        bot.send_message(user_id, f"👥 Users: {total_users}\n⭐ Total Points: {total_points if total_points else 0}")

# ----------------- وبهوک -----------------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot is running!", 200

if __name__ == "__main__":
    import threading
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
