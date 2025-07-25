from flask import Flask, request
import telebot
import threading
import time

API_TOKEN = '7217912729:AAGXxp8wDSX1dSpWrRw5RhAY8zDIV1QLvIo'
ADMIN_ID = 6994772164
WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com/'

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

users = {}
waiting_users = []
chats = {}

# امتیاز روزانه
def daily_points():
    while True:
        time.sleep(86400)
        for uid in users:
            users[uid]['points'] += 10

threading.Thread(target=daily_points, daemon=True).start()

# شروع
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    if uid not in users:
        users[uid] = {'points': 10, 'chatting_with': None, 'blocked': False}
    bot.send_message(uid, "👋 خوش آمدی! برای شروع چت ناشناس روی دکمه زیر بزن.", reply_markup=menu())

def menu():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🚀 شروع چت ناشناس", callback_data="start_chat"))
    return markup

# دکمه‌ها
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id

    if call.data == 'start_chat':
        if users[uid]['points'] <= 0:
            bot.answer_callback_query(call.id, "❌ امتیاز کافی نداری.")
            return

        if uid in waiting_users:
            bot.answer_callback_query(call.id, "⏳ در حال جستجو هستی...")
            return

        waiting_users.append(uid)
        bot.answer_callback_query(call.id, "🔍 در حال جستجو برای چت...")

        for other in waiting_users:
            if other != uid:
                waiting_users.remove(uid)
                waiting_users.remove(other)
                users[uid]['chatting_with'] = other
                users[other]['chatting_with'] = uid
                users[uid]['points'] -= 1
                users[other]['points'] -= 1
                chats[uid] = other
                chats[other] = uid
                send_both(uid, other, "💬 چت شروع شد! پیام بفرست.\nبرای پایان چت /end را بزن.")
                return

        bot.send_message(uid, "🔎 کسی پیدا نشد، لطفا صبر کن...")

# ارسال پیام‌ها
@bot.message_handler(func=lambda m: True)
def relay_message(message):
    uid = message.from_user.id
    if uid in users and users[uid]['chatting_with']:
        receiver = users[uid]['chatting_with']
        if receiver in users:
            try:
                bot.send_message(receiver, message.text)
            except:
                bot.send_message(uid, "❌ کاربر مقابل دریافت نکرد.")
    elif message.text == '/end':
        end_chat(uid)
    elif message.text == '/panel' and uid == ADMIN_ID:
        bot.send_message(uid, f"👑 پنل مدیریت:\nکاربران: {len(users)}\nدر حال چت: {len(chats)//2}")

# پایان چت
def end_chat(uid):
    partner = users[uid]['chatting_with']
    if partner:
        users[uid]['chatting_with'] = None
        users[partner]['chatting_with'] = None
        chats.pop(uid, None)
        chats.pop(partner, None)
        bot.send_message(uid, "✅ چت پایان یافت.")
        bot.send_message(partner, "❌ طرف مقابل چت را پایان داد.")

def send_both(a, b, text):
    bot.send_message(a, text)
    bot.send_message(b, text)

# وب‌هوک
@app.route('/', methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return 'ok'

@app.route('/', methods=['GET'])
def index():
    return 'Bot is running'

# تنظیم وب‌هوک
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
