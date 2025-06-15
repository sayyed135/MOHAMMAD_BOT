import telebot
from flask import Flask, request

TOKEN = '7217912729:AAFuXcRQNl0p-uCQZb64cxakJD15_b414q8'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.reply_to(message, "سلام، ربات با webhook فعال است!")

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

@app.route('/')
def index():
    return "ربات فعال است", 200

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    bot.remove_webhook()
    bot.set_webhook(url=f'https://MOHAMMAD-BOT.onrender.com/{TOKEN}')
    app.run(host='0.0.0.0', port=port)
