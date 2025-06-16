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

# متغیرهای مدیریت
waiting_for_broadcast_message = False
waiting_for_score_game = None
active_games = {}  # user_id: {"accepted": bool, "turn": "truth"/"dare"}

# سوالات سخت حقیقت و جرأت
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

# شروع
@bot.message_handler(commands=['start'])
def handle_start(message):
    if message.from_user.id == ADMIN_ID:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🛠 مدیریت")
        bot.send_message(message.chat.id, "سلام مدیر عزیز! ✅ ربات با webhook فعاله.", reply_markup=markup)
    else:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🎲 GAMES")
        bot.send_message(message.chat.id, "سلام دوست عزیز😁", reply_markup=markup)

# مدیریت
@bot.message_handler(func=lambda m: m.text == "🛠 مدیریت" and m.from_user.id == ADMIN_ID)
def handle_admin_button(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("📊 تنظیم امتیاز برای بازی‌ها", "📬 ارسال پیام همگانی")
    markup.add("📌 بررسی کاربران", "❌ بستن منو")
    bot.send_message(message.chat.id, "🎛 منوی مدیریت:", reply_markup=markup)

# دستورات مدیر
@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID)
def admin_buttons(message):
    global waiting_for_broadcast_message, waiting_for_score_game
    if waiting_for_broadcast_message:
        users = get_all_users()
        for user_id in users:
            try:
                bot.send_message(user_id, f"پیام همگانی از مدیر:\n\n{message.text}")
            except: continue
        bot.reply_to(message, f"📨 پیام فرستاده شد.")
        waiting_for_broadcast_message = False
        return

    if waiting_for_score_game:
        try:
            score = int(message.text)
            game_scores[waiting_for_score_game] = score
            bot.reply_to(message, f"✅ امتیاز بازی {waiting_for_score_game} ثبت شد.")
        except:
            bot.reply_to(message, "❌ لطفاً فقط عدد بنویس.")
        waiting_for_score_game = None
        return

    if message.text == "📊 تنظیم امتیاز برای بازی‌ها":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("جرأت و حقیقت", "درصد", "❌ بازگشت")
        bot.send_message(message.chat.id, "بازی مورد نظر رو انتخاب کن:", reply_markup=markup)

    elif message.text in game_scores.keys():
        waiting_for_score_game = message.text
        bot.send_message(message.chat.id, f"امتیاز جدید برای بازی «{message.text}» رو وارد کن:")

    elif message.text == "📬 ارسال پیام همگانی":
        waiting_for_broadcast_message = True
        bot.send_message(message.chat.id, "📝 پیام همگانی خود را بنویس:")

    elif message.text == "📌 بررسی کاربران":
        bot.send_message(message.chat.id, "👥 بررسی کاربران...")

    elif message.text == "❌ بستن منو":
        markup = telebot.types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "❎ منوی مدیریت بسته شد.", reply_markup=markup)

# دکمه GAMES
@bot.message_handler(func=lambda m: m.text == "🎲 GAMES")
def show_games(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("🎭 جرأت و حقیقت با مدیر", "❌ بازگشت")
    bot.send_message(message.chat.id, "🎮 یکی از بازی‌ها رو انتخاب کن:", reply_markup=markup)

# درخواست بازی با مدیر
@bot.message_handler(func=lambda m: m.text == "🎭 جرأت و حقیقت با مدیر")
def request_game(message):
    user_id = message.from_user.id
    active_games[user_id] = {"accepted": False, "turn": "truth"}
    bot.send_message(ADMIN_ID, f"👤 کاربر {message.from_user.first_name} درخواست بازی داده.", reply_markup=telebot.types.InlineKeyboardMarkup().add(
        telebot.types.InlineKeyboardButton(f"قبول بازی با {message.from_user.first_name}", callback_data=f"accept_{user_id}")
    ))
    bot.send_message(user_id, "📨 درخواست شما به مدیر فرستاده شد. منتظر تایید باشید.")

# تایید بازی توسط مدیر
@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_"))
def accept_game(call):
    user_id = int(call.data.split("_")[1])
    active_games[user_id]["accepted"] = True
    bot.send_message(user_id, "✅ مدیر بازی رو قبول کرد! شروع می‌کنیم.")
    ask_turn(ADMIN_ID, user_id)

# پرسیدن سوال یا جرأت به نوبت
def ask_turn(player_id, opponent_id):
    game = active_games[opponent_id]
    if game["turn"] == "truth":
        q = choice(hard_truths)
        bot.send_message(player_id, f"📖 سوال حقیقت: {q}")
        game["turn"] = "dare"
    else:
        q = choice(hard_dares)
        bot.send_message(player_id, f"🎭 ماموریت جرأت: {q}")
        game["turn"] = "truth"

# ادامه بازی
@bot.message_handler(func=lambda m: m.from_user.id in active_games and active_games[m.from_user.id]["accepted"])
def continue_game(message):
    user_id = message.from_user.id
    target_id = ADMIN_ID if user_id != ADMIN_ID else [uid for uid in active_games if active_games[uid]["accepted"]][0]
    if message.text == "❌ پایان":
        bot.send_message(user_id, "❎ بازی پایان یافت.")
        bot.send_message(target_id, "❎ بازی پایان یافت.")
        del active_games[user_id if user_id != ADMIN_ID else target_id]
    else:
        ask_turn(target_id, target_id if user_id == ADMIN_ID else user_id)

# کاربران تست
def get_all_users():
    return [ADMIN_ID]

# دستورات ناشناخته
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    bot.reply_to(message, "دستور نامشخصه. لطفاً /start یا گزینه‌های منو رو بزن.")

# اجرا
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
