import telebot
import openai

BOT_TOKEN = "7217912729:AAE8pW3xQE8hmhqJtN08EU4oAqii8ilDRic"
OPENAI_API_KEY = "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"

bot = telebot.TeleBot(BOT_TOKEN)
openai.api_key = OPENAI_API_KEY

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "سلام محمد! سوالت رو بپرس تا با ChatGPT جواب بدم 🧠")

@bot.message_handler(func=lambda m: True)
def chat_with_ai(message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": message.text}
            ]
        )
        reply = response.choices[0].message.content
        bot.reply_to(message, reply)
    except Exception as e:
        bot.reply_to(message, f"خطا: {e}")

bot.infinity_polling()
