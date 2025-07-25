from flask import Flask, request
import telebot

TOKEN = '7217912729:AAFAS2EHB9MsYQpKKYqyPA_dMAUg25I0yWY'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode("utf-8"))
    bot.process_new_updates([update])
    return 'OK', 200

@bot.message_handler(func=lambda m: True)
def reply_all(m):
    bot.send_message(m.chat.id, "✅ پیام شما با موفقیت دریافت شد.")

@app.route('/')
def index():
    return 'ربات در حال اجراست.'

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url='https://mohammad-bot-2.onrender.com')
    app.run(host='0.0.0.0', port=10000)
