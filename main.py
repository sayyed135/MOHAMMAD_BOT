import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = '7217912729:AAFuXcRQNl0p-uCQZb64cxakJD15_b414q8'
bot = telebot.TeleBot(TOKEN)

# ساخت کیبورد ساده با دو دکمه
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton('جرأت یا حقیقت'))
keyboard.add(KeyboardButton('AI-CHAT'))

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "سلام! من ربات ساده تو هستم. یک گزینه انتخاب کن:", reply_markup=keyboard)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == 'جرأت یا حقیقت':
        bot.send_message(message.chat.id, "بازی جرأت یا حقیقت شروع شد! (هنوز در حال توسعه)")
    elif message.text == 'AI-CHAT':
        bot.send_message(message.chat.id, "اینجا میتونی با یه هوش مصنوعی ساده چت کنی. (در حال توسعه)")
    else:
        bot.send_message(message.chat.id, "متوجه نشدم، لطفاً یکی از دکمه‌ها را بزن.")

bot.polling()
