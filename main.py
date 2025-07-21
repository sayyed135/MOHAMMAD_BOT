import telebot
from flask import Flask, request

TOKEN = '8077313575:AAF_B4ZS0_JPyqaJV4gBmqfJsUHh2gGPzsI'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

waiting_users = []
active_chats = {}

def find_partner(user_id):
    if waiting_users and waiting_users[0] != user_id:
        partner = waiting_users.pop(0)
        active_chats[user_id] = partner
        active_chats[partner] = user_id
        bot.send_message(user_id, "✅ به یک ناشناس وصل شدی.")
        bot.send_message(partner, "✅ به یک ناشناس وصل شدی.")
    else:
        if user_id not in waiting_users:
            waiting_users.append(user_id)
        bot.send_message(user_id, "⌛ منتظر یک کاربر دیگر هستی...")

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "سلام! برای شروع چت /chat و برای پایان /end بزن.")

@bot.message_handler(commands=['chat'])
def chat(message):
    user_id = message.chat.id
    if user_id in active_chats:
        bot.send_message(user_id, "⚠️ شما در حال چت هستید. برای پایان /end بزنید.")
    else:
        find_partner(user_id)

@bot.message_handler(commands=['end'])
def end_chat(message):
    user_id = message.chat.id
    if user_id in active_chats:
        partner = active_chats.pop(user_id)
        if partner in active_chats:
            active_chats.pop(partner)
            bot.send_message(partner, "❌ چت توسط طرف مقابل پایان یافت.")
        bot.send_message(user_id, "✅ چت پایان یافت.")
    elif user_id in waiting_users:
        waiting_users.remove(user_id)
        bot.send_message(user_id, "✅ از صف انتظار خارج شدی.")
    else:
        bot.send_message(user_id, "❌ در چتی نیستی.")

@bot.message_handler(func=lambda m: True)
def relay_msg(message):
    user_id = message.chat.id
    if user_id in active_chats:
        partner = active_chats[user_id]
        try:
            bot.send_message(partner, message.text)
        except:
            bot.send_message(user_id, "❌ خطا در ارسال پیام.")
    else:
        bot.send_message(user_id, "🔒 ابتدا با /chat چت را شروع کن.")

@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok", 200

@app.route('/')
def index():
    return 'Bot is Running.', 200

if __name__ == "__main__":
    import os
    bot.remove_webhook()
    bot.set_webhook(url=f"https://mohammad-bot-2.onrender.com/{TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
