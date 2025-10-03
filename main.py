import os
import sqlite3
from flask import Flask, request
import telebot
from telebot import types
import requests

# توکن جدید ربات
TOKEN = "7961151930:AAEMibfYlZJ6hr5Ji9k-3lMY8Hf0ZU0Dvrc"
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# آیدی مدیر
ADMIN_ID = 6994772164

# دیتابیس SQLite
DB_FILE = "data.db"

# ───────────── دیتابیس ─────────────
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            stars INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def add_user(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()

def add_stars(chat_id, amount=1):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET stars = stars + ? WHERE chat_id = ?", (amount, chat_id))
    conn.commit()
    conn.close()

def get_stars(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT stars FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

# ───────────── دکمه‌ها ─────────────
@bot.message_handler(commands=['start'])
def start_message(message):
    add_user(message.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("GET STARS")
    btn2 = types.KeyboardButton("Premium Subscription")
    btn3 = types.KeyboardButton("Support")
    markup.add(btn1, btn2, btn3)

    if message.chat.id == ADMIN_ID:
        btn4 = types.KeyboardButton("Admin Stats")
        markup.add(btn4)

    bot.send_message(
        message.chat.id,
        "Welcome! Choose an option below 👇",
        reply_markup=markup
    )

# ───────────── عملکرد دکمه‌ها ─────────────
@bot.message_handler(func=lambda msg: msg.text == "GET STARS")
def get_stars_button(message):
    add_stars(message.chat.id, 1)
    stars = get_stars(message.chat.id)
    bot.send_message(message.chat.id, f"⭐ You received 1 star! Total stars: {stars}")

@bot.message_handler(func=lambda msg: msg.text == "Premium Subscription")
def premium(message):
    bot.send_message(message.chat.id, "🌟 Premium subscription gives you extra features!")

@bot.message_handler(func=lambda msg: msg.text == "Support")
def support(message):
    bot.send_message(message.chat.id, "🔗 Contact Support: t.me/mohammadsadat_afg")

@bot.message_handler(func=lambda msg: msg.text == "Admin Stats")
def admin_stats(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ You are not admin!")
        return
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, stars FROM users")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        bot.send_message(message.chat.id, "No users yet.")
        return

    text = "📊 User Stars:\n"
    for chat_id, stars in rows:
        text += f"ID: {chat_id} → Stars: {stars}\n"

    bot.send_message(message.chat.id, text)

# ───────────── وبهوک برای Render ─────────────
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    return "Bot is running!"

@app.route("/set_webhook")
def set_webhook():
    external_url = os.environ.get("RENDER_EXTERNAL_URL")
    if not external_url:
        return "RENDER_EXTERNAL_URL not set", 500
    webhook_url = f"{external_url}/{TOKEN}"
    r = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook", params={"url": webhook_url})
    return r.text

# ───────────── شروع دیتابیس ─────────────
init_db()
