import telebot
from flask import Flask, request
import logging
import os
from random import choice

TOKEN = '7217912729:AAHEug-znb_CGJTXlITt3Zrjp2dJan0a9Gs'
WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com/'

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
ADMIN_ID = 6994772164

logging.basicConfig(level=logging.INFO)

waiting_for_approval = {}
active_games = {}

hard_truths = [
    "📖 سخت‌ترین رازی که تا حالا مخفی کردی چیه؟",
    "📖 آخرین باری که از کسی سوءاستفاده کردی کی بود؟",
    "📖 تا حالا به کسی خیانت کردی؟",
    "📖 بزرگترین دروغی که گفتی چی بود؟"
]

hard_dares = [
    "🎭 از مادرت بپرس: «مامان، تا حالا عاشق شدی؟»",
    "🎭 یه صدای عجیب بفرست برای مدیر!",
    "🎭 به یه دوستت بگو: «من عاشقت بودم!»",
    "🎭 اسم کسی رو که ازش متنفری بفرست!"
]

@app.route('/', methods=['POST'])
def receive_update():
    if request.headers.get('content-type') == 'application/json':
        try:
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return '', 200
        except Exception as e:
            logging.error(f'❌ Error: {e}')
            return 'Internal Error', 500
    return 'Invalid content-type', 403

@bot.message_handler(commands=['start'])
def handle_start(message):
    if message.from_user.id == ADMIN_ID:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🛠 پنل مدیریت")
        bot.send_message(message.chat.id, "سلام مدیر عزیز! ✅ ربات فعاله.", reply_markup=markup)
    else:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🎲 GAMES", "ℹ️ اطلاعات من")
        bot.send_message(message.chat.id, "سلام دوست عزیز! از منو یکی رو انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🎲 GAMES")
def show_games(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("🎭 جرأت و حقیقت با مدیر", "❌ بازگشت")
    bot.send_message(message.chat.id, "🎮 یکی از بازی‌ها رو انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🎭 جرأت و حقیقت با مدیر")
def request_game(message):
    user_id = message.from_user.id
    active_games[user_id] = {"accepted": False, "turn": "truth", "last_q": None}
    bot.send_message(ADMIN_ID, f"👤 {message.from_user.first_name} درخواست بازی داده.", reply_markup=telebot.types.InlineKeyboardMarkup().add(
        telebot.types.InlineKeyboardButton("قبول", callback_data=f"accept_{user_id}")
    ))
    bot.send_message(user_id, "📨 درخواست شما برای مدیر ارسال شد.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_"))
def accept_game(call):
    user_id = int(call.data.split("_")[1])
    active_games[user_id]["accepted"] = True
    bot.send_message(user_id, "✅ مدیر بازی را قبول کرد!")
    ask_turn(ADMIN_ID, user_id)

def ask_turn(player, opponent):
    game = active_games[opponent]
    q = choice(hard_truths if game["turn"] == "truth" else hard_dares)
    game["last_q"] = q
    waiting_for_approval[player] = opponent
    bot.send_message(player, f"{'📖 حقیقت' if game['turn'] == 'truth' else '🎭 جرأت'}:
{q}")
    game["turn"] = "dare" if game["turn"] == "truth" else "truth"

@bot.message_handler(func=lambda m: m.from_user.id in waiting_for_approval)
def handle_answer(m):
    opponent = waiting_for_approval[m.from_user.id]
    game = active_games[opponent]
    ans = m.text
    del waiting_for_approval[m.from_user.id]

    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(
        telebot.types.InlineKeyboardButton("✅ تأیید", callback_data=f"ok_{m.from_user.id}"),
        telebot.types.InlineKeyboardButton("❌ رد", callback_data=f"retry_{m.from_user.id}")
    )
    bot.send_message(opponent, f"👤 طرف مقابل پاسخ داد:

{ans}

آیا قبول داری نوبت رد بشه؟", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ok_") or c.data.startswith("retry_"))
def handle_judge(c):
    uid = int(c.data.split("_")[1])
    game = active_games[uid]
    if c.data.startswith("ok_"):
        next_turn = ADMIN_ID if uid != ADMIN_ID else uid
        ask_turn(next_turn, uid if uid != ADMIN_ID else [u for u in active_games if u != ADMIN_ID][0])
    else:
        q = game["last_q"]
        waiting_for_approval[uid] = c.from_user.id
        bot.send_message(uid, f"❌ طرف مقابل نپذیرفت! دوباره پاسخ بده:
{q}")

@bot.message_handler(func=lambda m: m.text == "🛠 پنل مدیریت")
def admin_panel(m):
    if m.from_user.id != ADMIN_ID: return
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("📊 تنظیم بازی", "👥 کاربران", "🏁 بازی‌های فعال", "❌ خروج")
    bot.send_message(m.chat.id, "🔧 پنل مدیریت:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🏁 بازی‌های فعال" and m.from_user.id == ADMIN_ID)
def list_games(m):
    if not active_games:
        bot.send_message(m.chat.id, "📭 هیچ بازی فعالی وجود ندارد.")
    else:
        text = "\n".join([f"{uid} => {'قبول شد' if d['accepted'] else 'منتظر تایید'}" for uid, d in active_games.items()])
        bot.send_message(m.chat.id, f"🎮 بازی‌های فعال:
{text}")

@bot.message_handler(func=lambda m: True)
def fallback(m):
    bot.send_message(m.chat.id, "❓ لطفاً از منوی ربات استفاده کن.")

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
