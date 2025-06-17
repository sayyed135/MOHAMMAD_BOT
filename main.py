import telebot
from flask import Flask, request
import os

TOKEN = '7217912729:AAHEug-znb_CGJTXlITt3Zrjp2dJan0a9Gs'
WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com/'  # آدرس رندر تو

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

users = {}  # user_id: {"username": "name"}

@bot.message_handler(commands=['start'])
def start(message):
    users[message.chat.id] = {"username": message.from_user.username}
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("✉️ ارسال پیام ناشناس")
    bot.send_message(message.chat.id, "سلام! خوش آمدی به ربات پیام ناشناس 😎", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "✉️ ارسال پیام ناشناس")
def ask_for_receiver(message):
    msg = bot.send_message(message.chat.id, "آیدی کسی که می‌خوای براش پیام بفرستی رو بنویس (مثلاً: @ali123):")
    bot.register_next_step_handler(msg, get_target_username)

def get_target_username(message):
    target_username = message.text.strip().lstrip('@')
    user_id = None
    for uid, data in users.items():
        if data.get("username") == target_username:
            user_id = uid
            break

    if user_id:
        msg = bot.send_message(message.chat.id, "خب، حالا متن پیامت رو بنویس:")
        bot.register_next_step_handler(msg, send_anonymous_message, user_id)
    else:
        bot.send_message(message.chat.id, "❌ کسی با این آیدی هنوز توی ربات ثبت‌نام نکرده!")

def send_anonymous_message(message, user_id):
    bot.send_message(user_id, f"📩 پیام ناشناس برات اومده:\n\n{message.text}")
    bot.send_message(message.chat.id, "✅ پیام ناشناس ارسال شد!")

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return '', 403

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
