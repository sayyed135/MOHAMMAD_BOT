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

# وضعیت‌ها
waiting_for_broadcast_message = False
waiting_for_score_game = None
active_games = {}  # user_id: {accepted, turn, last_q, last_type}
game_scores = {"جرأت و حقیقت": 0, "درصد": 0}
users_list = [ADMIN_ID]  # لیست تستی کاربران

hard_truths = [
    "📖 سخت‌ترین رازی که تا حالا مخفی کردی چیه؟",
    "📖 تا حالا به کسی خیانت کردی؟",
]
hard_dares = [
    "🎭 یه صدای عجیب بفرست برای مدیر!",
    "🎭 اسم کسی رو که ازش متنفری بفرست!"
]

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        try:
            update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
            bot.process_new_updates([update])
            return '', 200
        except Exception as e:
            logging.error(f'❌ Error: {e}')
            return 'Internal Error', 500
    return 'Invalid content-type', 403

@bot.message_handler(commands=['start'])
def handle_start(message):
    if message.from_user.id not in users_list:
        users_list.append(message.from_user.id)
    if message.from_user.id == ADMIN_ID:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🛠 پنل مدیریت")
        bot.send_message(message.chat.id, "سلام مدیر عزیز! ✅", reply_markup=markup)
    else:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🎲 GAMES")
        bot.send_message(message.chat.id, "سلام دوست عزیز😁", reply_markup=markup)

# پنل مدیریت
@bot.message_handler(func=lambda m: m.text == "🛠 پنل مدیریت" and m.from_user.id == ADMIN_ID)
def show_admin_panel(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📬 پیام همگانی", "📊 تنظیم امتیاز")
    markup.add("📋 لیست کاربران", "❌ بستن")
    bot.send_message(message.chat.id, "🎛 پنل مدیریت:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID)
def admin_actions(message):
    global waiting_for_broadcast_message, waiting_for_score_game
    if waiting_for_broadcast_message:
        for uid in users_list:
            try:
                bot.send_message(uid, f"📢 پیام مدیر:\n{message.text}")
            except: continue
        bot.reply_to(message, "✅ ارسال شد.")
        waiting_for_broadcast_message = False
        return
    if waiting_for_score_game:
        try:
            score = int(message.text)
            game_scores[waiting_for_score_game] = score
            bot.reply_to(message, f"✅ امتیاز جدید ثبت شد.")
        except:
            bot.reply_to(message, "❌ عدد وارد کن.")
        waiting_for_score_game = None
        return
    if message.text == "📬 پیام همگانی":
        waiting_for_broadcast_message = True
        bot.send_message(message.chat.id, "متن پیام رو بفرست:")
    elif message.text == "📊 تنظیم امتیاز":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(*game_scores.keys())
        bot.send_message(message.chat.id, "کدوم بازی:", reply_markup=markup)
    elif message.text in game_scores:
        waiting_for_score_game = message.text
        bot.send_message(message.chat.id, f"امتیاز جدید برای {message.text} رو بفرست:")
    elif message.text == "📋 لیست کاربران":
        bot.send_message(message.chat.id, f"👥 کاربران: {len(users_list)} نفر")
    elif message.text == "❌ بستن":
        bot.send_message(message.chat.id, "❎ بسته شد.", reply_markup=telebot.types.ReplyKeyboardRemove())

# GAMES
@bot.message_handler(func=lambda m: m.text == "🎲 GAMES")
def show_games(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎭 جرأت و حقیقت با مدیر", "❌ خروج از GAMES")
    bot.send_message(message.chat.id, "🎮 انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "❌ خروج از GAMES")
def leave_games(message):
    bot.send_message(message.chat.id, "🚪 خارج شدی.", reply_markup=telebot.types.ReplyKeyboardRemove())

# درخواست بازی
@bot.message_handler(func=lambda m: m.text == "🎭 جرأت و حقیقت با مدیر")
def truth_or_dare_request(message):
    uid = message.from_user.id
    active_games[uid] = {"accepted": False, "turn": "truth", "last_q": None, "last_type": None}
    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(telebot.types.InlineKeyboardButton("قبول بازی", callback_data=f"accept_{uid}"))
    bot.send_message(ADMIN_ID, f"درخواست بازی از {uid}", reply_markup=kb)
    bot.send_message(uid, "درخواست فرستاده شد.")

@bot.callback_query_handler(func=lambda c: c.data.startswith("accept_"))
def accept_game(c):
    uid = int(c.data.split("_")[1])
    if uid in active_games:
        active_games[uid]["accepted"] = True
        bot.send_message(uid, "✅ مدیر قبول کرد. بازی شروع شد.")
        ask_turn(ADMIN_ID, uid)

def ask_turn(player_id, opponent_id):
    g = active_games[opponent_id]
    q = choice(hard_truths if g["turn"] == "truth" else hard_dares)
    g["last_q"] = q
    g["last_type"] = g["turn"]
    bot.send_message(player_id, f"{'🟢 حقیقت:' if g['turn'] == 'truth' else '🔴 جرأت:'}\n{q}")

@bot.message_handler(func=lambda m: m.from_user.id in active_games and active_games[m.from_user.id]["accepted"])
def game_reply(m):
    user = m.from_user.id
    target = ADMIN_ID if user != ADMIN_ID else [i for i in active_games if active_games[i]["accepted"] and i != ADMIN_ID][0]
    text = m.text
    game = active_games[target]

    bot.send_message(target, f"👤 جواب طرف مقابل:\n{text}")
    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(
        telebot.types.InlineKeyboardButton("✅ قبول", callback_data=f"ok_{user}"),
        telebot.types.InlineKeyboardButton("❌ قبول ندارم", callback_data=f"no_{user}")
    )
    bot.send_message(target, "آیا جواب رو قبول داری؟", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ok_") or c.data.startswith("no_"))
def verify_answer(c):
    uid = int(c.data.split("_")[1])
    if uid not in active_games:
        return
    if c.data.startswith("ok_"):
        active_games[uid]["turn"] = "dare" if active_games[uid]["last_type"] == "truth" else "truth"
        next_player = uid if c.from_user.id == ADMIN_ID else ADMIN_ID
        ask_turn(next_player, uid)
    else:
        bot.send_message(uid, "❌ طرف مقابل جوابتو قبول نکرد. دوباره جواب بده:")

# ناشناس
@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.reply_to(message, "دستور نامعتبره.")

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
