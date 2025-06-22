import telebot
from flask import Flask, request
import sqlite3
import requests
import json
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import random

API_TOKEN = '7217912729:AAG-7SZpd6HAh6j0al--kRYNXmpsIFAhmcQ'  # توکن ربات
OPENAI_API_KEY = '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'  # کلید ChatGPT

WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com/'  # وب‌هوک خودت

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# دیتابیس
conn = sqlite3.connect('botdata.db', check_same_thread=False)
cursor = conn.cursor()

# ایجاد جداول
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    last_daily_date TEXT,
    coin INTEGER DEFAULT 0,
    gold INTEGER DEFAULT 0,
    diamond INTEGER DEFAULT 0,
    subscription_level TEXT DEFAULT 'free'
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS chat_memory (
    user_id INTEGER,
    role TEXT,
    content TEXT
)
''')

conn.commit()

# ذخیره و دریافت حافظه چت
def save_to_memory(user_id, role, content):
    cursor.execute('INSERT INTO chat_memory (user_id, role, content) VALUES (?, ?, ?)', (user_id, role, content))
    cursor.execute('''
        DELETE FROM chat_memory
        WHERE user_id = ? AND rowid NOT IN (
            SELECT rowid FROM chat_memory
            WHERE user_id = ?
            ORDER BY rowid DESC
            LIMIT 10
        )
    ''', (user_id, user_id))
    conn.commit()

def get_chat_history(user_id):
    cursor.execute('SELECT role, content FROM chat_memory WHERE user_id = ? ORDER BY rowid', (user_id,))
    return [{"role": role, "content": content} for role, content in cursor.fetchall()]

# ثبت کاربر
def register_user(user):
    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user.id,))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)',
                       (user.id, user.username, user.first_name, user.last_name))
        conn.commit()

# امتیاز روزانه
def add_daily_point(user_id):
    cursor.execute('SELECT last_daily_date, coin FROM users WHERE user_id = ?', (user_id,))
    data = cursor.fetchone()
    today = datetime.utcnow().date()
    if data:
        last_date_str, coin = data
        if last_date_str:
            last_date = datetime.strptime(last_date_str, '%Y-%m-%d').date()
            if last_date >= today:
                return False
        coin += 1
        cursor.execute('UPDATE users SET last_daily_date = ?, coin = ? WHERE user_id = ?',
                       (today.strftime('%Y-%m-%d'), coin, user_id))
        conn.commit()
        return True
    return False

# دکمه‌های کاربر
def user_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🎁 امتیاز روزانه", "📊 اطلاعات من")
    markup.row("🛒 خرید اشتراک", "💬 چت با AI")
    markup.row("🎮 بازی‌ها")
    return markup

# سوالات بازی جرأت و حقیقت
dare_questions = [
    "یک رقص کوتاه انجام بده!",
    "یک چیز خنده‌دار بگو!",
    "یک پیامک تصادفی به کسی که دوست داری بفرست!",
    "یک جوک تعریف کن!",
    "یک جمله با صدای بلند بگو!"
]

truth_questions = [
    "بهترین خاطره‌ات چیست؟",
    "یک راز از خودت بگو.",
    "آیا تا به حال دروغ گفته‌ای؟",
    "از چه چیزی می‌ترسی؟",
    "دوست داری کجا سفر کنی؟"
]

active_games = {}

def game_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("جرأت", "حقیقت")
    markup.row("/stopgame")
    return markup

# دستورات و هندلرها

@bot.message_handler(commands=['start'])
def send_welcome(message):
    register_user(message.from_user)
    bot.send_message(message.chat.id, f"سلام {message.from_user.first_name}! خوش آمدی 👋", reply_markup=user_menu())

@bot.message_handler(func=lambda m: m.text == "🎁 امتیاز روزانه")
def daily_point_button(message):
    if add_daily_point(message.from_user.id):
        bot.send_message(message.chat.id, "✅ یک امتیاز اضافه شد.")
    else:
        bot.send_message(message.chat.id, "⏳ امروز قبلاً امتیاز گرفتی. فردا بیا دوباره.")

@bot.message_handler(func=lambda m: m.text == "📊 اطلاعات من")
def my_info(message):
    cursor.execute('SELECT coin, gold, diamond, subscription_level FROM users WHERE user_id = ?', (message.from_user.id,))
    coin, gold, diamond, level = cursor.fetchone()
    msg = f"""📊 اطلاعات تو:

🪙 سکه: {coin}
💛 طلایی: {gold}
💎 الماسی: {diamond}
🎖 اشتراک: {level}
"""
    bot.send_message(message.chat.id, msg)

@bot.message_handler(func=lambda m: m.text == "🛒 خرید اشتراک")
def buy_subscription(message):
    bot.send_message(message.chat.id, "🛒 این بخش بزودی فعال می‌شود...")

@bot.message_handler(func=lambda m: m.text == "🎮 بازی‌ها")
def show_games(message):
    bot.send_message(message.chat.id, "🎮 بازی جرأت و حقیقت شروع شد! برای بازی یکی از گزینه‌ها را انتخاب کن:", reply_markup=game_menu())
    active_games[message.from_user.id] = True

@bot.message_handler(func=lambda m: m.text in ["جرأت", "حقیقت"])
def handle_game_choice(message):
    user_id = message.from_user.id
    if user_id not in active_games:
        bot.send_message(message.chat.id, "برای شروع بازی ابتدا دکمه «🎮 بازی‌ها» را بزن.")
        return

    if message.text == "جرأت":
        question = random.choice(dare_questions)
    else:
        question = random.choice(truth_questions)
    bot.send_message(message.chat.id, question)

@bot.message_handler(commands=['stopgame'])
def stop_game(message):
    user_id = message.from_user.id
    if user_id in active_games:
        del active_games[user_id]
        bot.send_message(message.chat.id, "بازی متوقف شد. هر وقت خواستی دوباره بازی کن!")
    else:
        bot.send_message(message.chat.id, "شما الان بازی نمی‌کنی!")

def chat_with_gpt(user_id, user_message):
    save_to_memory(user_id, "user", user_message)
    messages = [{"role": "system", "content": "تو یک هوش مصنوعی فارسی‌زبان، صمیمی و باهوش هستی."}]
    messages += get_chat_history(user_id)

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "gpt-3.5-turbo",
        "messages": messages
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, data=json.dumps(body))
    if response.status_code == 200:
        reply = response.json()['choices'][0]['message']['content']
        save_to_memory(user_id, "assistant", reply)
        return reply
    else:
        return "❌ مشکلی در اتصال با هوش مصنوعی پیش آمد."

@bot.message_handler(func=lambda m: m.text == "💬 چت با AI")
def start_ai_chat(message):
    bot.send_message(message.chat.id, "🧠 حالت چت با هوش مصنوعی فعال شد! هرچی خواستی بپرس:")

@bot.message_handler(func=lambda m: True)
def ai_chat_handler(message):
    if message.text in ["🎁 امتیاز روزانه", "📊 اطلاعات من", "🛒 خرید اشتراک", "🎮 بازی‌ها", "جرأت", "حقیقت", "/stopgame"]:
        return
    user_id = message.from_user.id
    bot.send_chat_action(message.chat.id, 'typing')
    response = chat_with_gpt(user_id, message.text)
    bot.send_message(message.chat.id, response)

@app.route('/', methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.data.decode("utf-8"))])
    return '', 200

def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

if __name__ == '__main__':
    set_webhook()
    app.run(host='0.0.0.0', port=8000)
