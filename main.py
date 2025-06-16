import telebot
from flask import Flask, request
import os, logging
from random import choice

TOKEN = '7217912729:AAHEug-znb_CGJTXlITt3Zrjp2dJan0a9Gs'
WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com/'
ADMIN_ID = 6994772164

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# وضعیت بازی
active_games = {}
hard_truths = ["📖 بزرگترین دروغی که گفتی چی بود؟", "📖 تا حالا به کسی خیانت کردی؟"]
hard_dares = ["🎭 صدای عجیب بفرست", "🎭 به یکی بگو عاشقش بودی!"]

# Webhook route
@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.data.decode("utf-8"))
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid content type', 403

# /start
@bot.message_handler(commands=['start'])
def start(msg):
    if msg.from_user.id == ADMIN_ID:
        mk = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        mk.add("🛠 مدیریت")
        bot.send_message(msg.chat.id, "سلام مدیر عزیز 👑", reply_markup=mk)
    else:
        mk = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        mk.add("🎮 بازی‌ها", "📊 امتیاز من", "📋 پروفایل")
        bot.send_message(msg.chat.id, "سلام! یکی از گزینه‌های زیر رو انتخاب کن 👇", reply_markup=mk)

# مدیریت
@bot.message_handler(func=lambda m: m.text == "🛠 مدیریت" and m.from_user.id == ADMIN_ID)
def admin_panel(msg):
    bot.send_message(msg.chat.id, "🎛 پنل مدیریت فعاله.")

# دکمه بازی‌ها
@bot.message_handler(func=lambda m: m.text == "🎮 بازی‌ها")
def games_menu(msg):
    mk = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    mk.add("🎭 جرأت و حقیقت با مدیر", "❌ برگشت")
    bot.send_message(msg.chat.id, "🎲 یکی از بازی‌ها رو انتخاب کن:", reply_markup=mk)

# درخواست بازی
@bot.message_handler(func=lambda m: m.text == "🎭 جرأت و حقیقت با مدیر")
def dare_request(msg):
    uid = msg.from_user.id
    active_games[uid] = {"accepted": False, "turn": "truth"}
    btn = telebot.types.InlineKeyboardButton("قبول بازی", callback_data=f"accept_{uid}")
    ik = telebot.types.InlineKeyboardMarkup().add(btn)
    bot.send_message(ADMIN_ID, f"🎮 {msg.from_user.first_name} درخواست بازی داده", reply_markup=ik)
    bot.send_message(uid, "📩 درخواستت برای مدیر ارسال شد.")

# مدیر بازی رو قبول کنه
@bot.callback_query_handler(func=lambda c: c.data.startswith("accept_"))
def accept_game(c):
    uid = int(c.data.split("_")[1])
    active_games[uid]["accepted"] = True
    bot.send_message(uid, "✅ مدیر بازی رو قبول کرد. شروع کنیم!")
    next_turn(ADMIN_ID, uid)

def next_turn(player, opponent):
    turn = active_games[opponent]["turn"]
    q = choice(hard_truths if turn == "truth" else hard_dares)
    bot.send_message(player, f"{'📖 حقیقت' if turn=='truth' else '🎭 جرأت'}: {q}")
    active_games[opponent]["turn"] = "dare" if turn == "truth" else "truth"

# ادامه بازی
@bot.message_handler(func=lambda m: m.from_user.id in active_games and active_games[m.from_user.id]["accepted"])
def continue_game(m):
    uid = m.from_user.id
    other = ADMIN_ID if uid != ADMIN_ID else [u for u in active_games if active_games[u]["accepted"]][0]
    if m.text == "❌ پایان":
        bot.send_message(uid, "❎ بازی تموم شد.")
        bot.send_message(other, "❎ بازی تموم شد.")
        del active_games[uid if uid != ADMIN_ID else other]
    else:
        next_turn(other, other if uid == ADMIN_ID else uid)

# سایر دکمه‌ها
@bot.message_handler(func=lambda m: m.text == "📊 امتیاز من")
def score(msg):
    bot.reply_to(msg, "💠 امتیاز شما: ۰ (آزمایشی)")

@bot.message_handler(func=lambda m: m.text == "📋 پروفایل")
def profile(msg):
    user = msg.from_user
    bot.reply_to(msg, f"🧑‍💻 نام: {user.first_name}\n🆔 آیدی عددی: {user.id}")

@bot.message_handler(func=lambda m: m.text == "❌ برگشت")
def back(msg):
    start(msg)

# پاسخ به سایر پیام‌ها
@bot.message_handler(func=lambda m: True)
def fallback(msg):
    bot.send_message(msg.chat.id, "❗️دستور نامعتبره. لطفاً از دکمه‌ها استفاده کن.")

# اجرای برنامه
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
