import telebot
from flask import Flask, request
import logging
import os

TOKEN = '7217912729:AAHEug-znb_CGJTXlITt3Zrjp2dJan0a9Gs'
WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com/'

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

ADMIN_ID = 6994772164

logging.basicConfig(level=logging.INFO)

# دیکشنری برای ذخیره امتیازات بازی‌ها
game_scores = {
    "جرأت و حقیقت": 0,
    "درصد": 0,
    "بازی‌های دیگر": 0
}

# متغیرهای وضعیت
waiting_for_broadcast_message = False
waiting_for_score_game = None  # نام بازی‌ای که منتظر امتیاز آن هستیم

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
        markup.add("🛠 مدیریت")
        bot.send_message(message.chat.id, "سلام مدیر عزیز! ✅ ربات با webhook فعاله.", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "سلام دوست عزیز😁")

@bot.message_handler(func=lambda m: m.text == "🛠 مدیریت" and m.from_user.id == ADMIN_ID)
def handle_admin_button(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("📊 تنظیم امتیاز برای بازی‌ها", "📬 ارسال پیام همگانی")
    markup.add("📌 بررسی کاربران", "❌ بستن منو")
    bot.send_message(message.chat.id, "🎛 منوی مدیریت:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID)
def admin_buttons(message):
    global waiting_for_broadcast_message, waiting_for_score_game

    if waiting_for_broadcast_message:
        # ارسال پیام همگانی
        broadcast_text = message.text
        users = get_all_users()  # تابع باید همه کاربران را بدهد
        sent_count = 0
        for user_id in users:
            try:
                bot.send_message(user_id, f"پیام همگانی از مدیر:\n\n{broadcast_text}")
                sent_count += 1
            except Exception as e:
                logging.error(f"خطا در ارسال به {user_id}: {e}")

        bot.reply_to(message, f"پیام به {sent_count} کاربر ارسال شد.")
        waiting_for_broadcast_message = False
        return

    if waiting_for_score_game:
        try:
            score = int(message.text)
            game_scores[waiting_for_score_game] = score
            bot.reply_to(message, f"امتیاز بازی «{waiting_for_score_game}» با موفقیت به {score} تنظیم شد.")
        except ValueError:
            bot.reply_to(message, "❌ لطفاً فقط عدد وارد کنید.")
            return
        waiting_for_score_game = None
        return

    if message.text == "📊 تنظیم امتیاز برای بازی‌ها":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("جرأت و حقیقت", "درصد", "بازی‌های دیگر", "❌ بازگشت")
        bot.send_message(message.chat.id, "لطفاً بازی مورد نظر را انتخاب کنید:", reply_markup=markup)

    elif message.text in game_scores.keys():
        waiting_for_score_game = message.text
        bot.reply_to(message, f"لطفاً امتیاز جدید برای بازی «{message.text}» را وارد کنید:")

    elif message.text == "❌ بازگشت":
        handle_admin_button(message)

    elif message.text == "📬 ارسال پیام همگانی":
        waiting_for_broadcast_message = True
        bot.reply_to(message, "📝 لطفاً پیام همگانی خود را ارسال کنید:")

    elif message.text == "📌 بررسی کاربران":
        bot.reply_to(message, "👥 در حال بررسی کاربران... (باید تابع مناسب بنویسی)")

    elif message.text == "❌ بستن منو":
        markup = telebot.types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "❎ منوی مدیریت بسته شد.", reply_markup=markup)

    else:
        bot.reply_to(message, "دستور نامشخصه. لطفاً گزینه‌های منو را انتخاب کن.")

def get_all_users():
    # اینجا باید همه آیدی کاربران را ذخیره و برگردونی
    # الان فقط مدیر رو داریم برای تست
    return [ADMIN_ID]

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    bot.reply_to(message, "دستور نامشخصه. لطفاً /start یا گزینه‌های موجود رو انتخاب کن.")

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
