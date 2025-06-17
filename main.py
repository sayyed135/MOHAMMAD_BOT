import telebot
from flask import Flask, request
import os

TOKEN = '7217912729:AAHEug-znb_CGJTXlITt3Zrjp2dJan0a9Gs'
WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com/'

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

connected_users = {}  # user_id: connected_user_id
pending_requests = {}  # target_user_id: requester_user_id

# شروع
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("✉️ شروع چت ناشناس", "❌ قطع چت")
    bot.send_message(message.chat.id, "سلام! به ربات چت ناشناس خوش آمدی. 👻", reply_markup=markup)

# درخواست اتصال با آیدی عددی
@bot.message_handler(func=lambda m: m.text == "✉️ شروع چت ناشناس")
def ask_target(message):
    msg = bot.send_message(message.chat.id, "آیدی عددی کسی که می‌خوای باهاش ناشناس چت کنی رو بنویس:")
    bot.register_next_step_handler(msg, connect_by_id)

def connect_by_id(message):
    try:
        sender_id = message.chat.id
        target_id = int(message.text.strip())

        if sender_id == target_id:
            bot.send_message(sender_id, "❌ نمی‌تونی با خودت چت کنی!")
            return

        if target_id in connected_users or target_id in pending_requests:
            bot.send_message(sender_id, "❌ کاربر مورد نظر در حال چته یا درخواست باز داره.")
            return

        pending_requests[target_id] = sender_id
        bot.send_message(sender_id, "📨 درخواست چت ناشناس ارسال شد.")

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("قبول چت ✅", callback_data=f"accept_{sender_id}"))
        bot.send_message(target_id, "📩 یک نفر می‌خواد باهات ناشناس چت کنه. قبول می‌کنی؟", reply_markup=markup)

    except:
        bot.send_message(message.chat.id, "❌ آیدی عددی معتبر وارد کن (فقط عدد).")

# پاسخ به درخواست
@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_"))
def accept_chat(call):
    target_id = call.from_user.id
    requester_id = int(call.data.split("_")[1])

    if pending_requests.get(target_id) != requester_id:
        bot.send_message(target_id, "❌ این درخواست منقضی شده.")
        return

    connected_users[target_id] = requester_id
    connected_users[requester_id] = target_id
    del pending_requests[target_id]

    bot.send_message(requester_id, "✅ طرف مقابل درخواستت رو قبول کرد. حالا می‌تونید پیام بدید.")
    bot.send_message(target_id, "✅ چت ناشناس شروع شد. حالا می‌تونی پیام بدی.")

# ارسال پیام ناشناس
@bot.message_handler(func=lambda m: m.chat.id in connected_users)
def forward_anonymous_message(message):
    target_id = connected_users[message.chat.id]
    try:
        bot.send_message(target_id, f"پیام ناشناس:\n{message.text}")
    except:
        bot.send_message(message.chat.id, "❌ ارسال پیام ممکن نیست.")

# قطع چت
@bot.message_handler(func=lambda m: m.text == "❌ قطع چت")
def disconnect_chat(message):
    user_id = message.chat.id
    if user_id in connected_users:
        partner_id = connected_users[user_id]
        bot.send_message(partner_id, "❌ طرف مقابل چت رو قطع کرد.")
        bot.send_message(user_id, "✅ چت قطع شد.")
        del connected_users[partner_id]
        del connected_users[user_id]
    else:
        bot.send_message(user_id, "⛔️ شما در حال حاضر با کسی چت نمی‌کنید.")

# پیام‌های نامشخص
@bot.message_handler(func=lambda m: True)
def handle_unknown(message):
    bot.send_message(message.chat.id, "لطفاً یکی از گزینه‌های منو را انتخاب کن.")

# راه‌اندازی وب‌هوک
@app.route("/", methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
        bot.process_new_updates([update])
        return '', 200
    return '', 403

# اجرای Flask
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
