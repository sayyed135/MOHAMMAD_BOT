import os
from flask import Flask, request
import telebot
from telebot import types
import requests

# ⛔️ هشدار: این توکن محرمانه است، اگر لو رفت سریع توی BotFather عوضش کن
TOKEN = "7961151930:AAEFlo4B0A_uWZv-17NSqQPl6-UVHFynkZQ"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# ───────────── دکمه‌ها ─────────────
@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("GET STARS")
    btn2 = types.KeyboardButton("Premium Subscription")
    btn3 = types.KeyboardButton("Support")
    markup.add(btn1, btn2, btn3)

    bot.send_message(
        message.chat.id,
        "Welcome! Choose an option below 👇",
        reply_markup=markup
    )

# ───────────── عملکرد دکمه‌ها ─────────────
@bot.message_handler(func=lambda msg: msg.text == "GET STARS")
def get_stars(message):
    bot.send_message(message.chat.id, "⭐ You received some stars!")

@bot.message_handler(func=lambda msg: msg.text == "Premium Subscription")
def premium(message):
    bot.send_message(message.chat.id, "🌟 Premium subscription gives you extra features!")

@bot.message_handler(func=lambda msg: msg.text == "Support")
def support(message):
    bot.send_message(message.chat.id, "🔗 Contact Support: t.me/mohammadsadat_afg")

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

# فقط یکبار برای ست کردن وبهوک استفاده کن
@app.route("/set_webhook")
def set_webhook():
    external_url = os.environ.get("RENDER_EXTERNAL_URL")
    if not external_url:
        return "RENDER_EXTERNAL_URL not set", 500
    webhook_url = f"{external_url}/{TOKEN}"
    r = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook", params={"url": webhook_url})
    return r.text
