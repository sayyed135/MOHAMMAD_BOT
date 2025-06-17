import telebot
from flask import Flask, request
import os

TOKEN = '7217912729:AAHEug-znb_CGJTXlITt3Zrjp2dJan0a9Gs'
WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com/'

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ساختار چت‌های فعال
active_chats = {}  # user_id: partner_id
pending_requests = {}  # user_id: target_username
usernames = {}  # user_id: username

# شروع
@bot.message_handler(commands=['start'])
def start(message):
    usernames[message.chat.id] = message.from_user.username
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("✉️ شروع چت ناشناس")
    bot.send_message(message.chat.id, "سلام! به ربات چت ناشناس خوش اومدی 🤫", reply_markup=markup)

# مرحله درخواست چت
@bot.message_handler(func=lambda m: m.text == "✉️ شروع چت ناشناس")
def ask_target(message):
    msg = bot.send_message(message.chat.id, "آیدی کسی که می‌خوای باهاش ناشناس چت کنی رو بنویس (بدون @):")
    bot.register_next_step_handler(msg, check_user)

def check_user(message):
    target_username = message.text.strip().lower()
    sender_id = message.chat.id
    receiver_id = None

    for uid, uname in usernames.items():
        if uname and uname.lower() == target_username:
            receiver_id = uid
            break

    if receiver_id:
        pending_requests[receiver_id] = sender_id
        bot.send_message(sender_id, "📨 درخواست چت ناشناس فرستاده شد. منتظر تایید باش.")
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("قبول چت ناشناس ✅", callback_data=f"accept_{sender_id}"))
        bot.send_message(receiver_id, f"📩 درخواست چت ناشناس از یک نفر داری. می‌خوای قبول کنی؟", reply_markup=markup)
    else:
        bot.send_message(sender_id, "❌ این آیدی هنوز در ربات ثبت‌نام نکرده یا اشتباه نوشتی.")

# تایید چت ناشناس
@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_"))
def accept_chat(call):
    receiver_id = call.from_user.id
    sender_id = int(call.data.split("_")[1])
    if receiver_id in pending_requests and pending_requests[receiver_id] == sender_id:
        active_chats[sender_id] = receiver_id
        active_chats[receiver_id] = sender_id
        del pending_requests[receiver_id]

        bot.send_message(sender_id, "✅ چت ناشناس شروع شد. می‌تونی پیام بفرستی.")
        bot.send_message(receiver_id, "✅ چت ناشناس شروع شد. می‌تونی پیام بفرستی.")
    else:
        bot.send_message(receiver_id, "❌ درخواستی معتبر پیدا نشد.")

# پیام‌های داخل چت ناشناس
@bot.message_handler(func=lambda m: m.chat.id in active_chats)
def anonymous_chat(message):
    sender = message.chat.id
    receiver = active_chats[sender]

    if message.text.strip().lower() == "پایان":
        bot.send_message(sender, "❌ چت ناشناس پایان یافت.")
        bot.send_message(receiver, "❌ طرف مقابل چت ناشناس رو پایان داد.")
        del active_chats[sender]
        del active_chats[receiver]
        return

    bot.send_message(receiver, f"📨 پیام ناشناس:\n{message.text}")

# پیام‌های نامشخص
@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(message.chat.id, "برای شروع چت ناشناس روی «✉️ شروع چت ناشناس» بزن.")

# Webhook
@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return '', 403

# اجرا
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
