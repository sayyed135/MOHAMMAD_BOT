import telebot
import openai
from flask import Flask, request

BOT_TOKEN = "7217912729:AAE8pW3xQE8hmhqJtN08EU4oAqii8ilDRic"
OPENAI_API_KEY = "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"

client = openai.OpenAI(api_key=OPENAI_API_KEY)
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "ربات فعاله ✅"

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.data.decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return '403', 403

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "سلام! سوالت رو بپرس تا با ChatGPT جواب بدم 🧠")

@bot.message_handler(func=lambda m: True)
def ask_gpt(message):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message.text}]
        )
        answer = response.choices[0].message.content
        bot.reply_to(message, answer)
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {e}")

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    bot.remove_webhook()
    bot.set_webhook(url='https://mohammad-bot-2.onrender.com/')
    app.run(host="0.0.0.0", port=port)
