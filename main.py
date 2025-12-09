import telebot
from googlesearch import search
import requests
from bs4 import BeautifulSoup

# توکن ربات تلگرام
TOKEN = "7961151930:AAE3FK2Of5aSwidCRer_hmNyNfT6-P0-4ZE"
bot = telebot.TeleBot(TOKEN)

def get_answer_from_google(query):
    try:
        # جستجوی گوگل، فقط لینک اول
        for url in search(query, num_results=1):
            r = requests.get(url, timeout=5)
            soup = BeautifulSoup(r.text, 'html.parser')
            paragraphs = soup.find_all('p')
            if paragraphs:
                return paragraphs[0].get_text().strip()
        return "نتونستم جوابشو پیدا کنم 😅"
    except:
        return "مشکل پیش اومد! 😵"

@bot.message_handler(func=lambda message: True)
def reply(message):
    user_input = message.text
    response = get_answer_from_google(user_input)
    bot.reply_to(message, response)

# ربات همیشه آنلاین
bot.infinity_polling()
