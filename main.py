import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from flask import Flask, request

# 🔐 توکن جدید
API_TOKEN = '7217912729:AAHGslCoRLKfVm1VEZ0qG7riZ3fiGMQ1t7I'
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# آی‌دی عددی مدیر جدید
admins = [6994772164]

# دیتابیس ساده
users = {}

def get_keyboard(user_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("امتیاز روزانه 🪙", callback_data='daily_score'),
        InlineKeyboardButton("اطلاعات من 📄", callback_data='my_info'),
        InlineKeyboardButton("خرید اشتراک 💎", callback_data='buy_vip'),
        InlineKeyboardButton("AI CHAT 🤖", callback_data='ai_chat'),
        InlineKeyboardButton("چت ناشناس 🕵️", callback_data='anon_chat'),
        InlineKeyboardButton("بازی جرأت و حقیقت 🎯", callback_data='truth_dare'),
        InlineKeyboardButton("تغییر حالت چت 🔁", callback_data='change_mode'),
        InlineKeyboardButton("ارسال پیام همگانی 📢", callback_data='broadcast'),
        InlineKeyboardButton("پنل مدیریت 🛠️", callback_data='admin_panel'),
        InlineKeyboardButton("بستن منو ❌", callback_data='close')
    )
    return markup

@bot.message_handler(commands=['start'])
def start(message: Message):
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = {
            'score': 0,
            'level': 'عادی',
            'mode': 'معمولی'
        }
    bot.send_message(user_id, f"سلام {message.from_user.first_name} 👋\nبه ربات خوش آمدی!", reply_markup=get_keyboard(user_id))

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    data = call.data

    if user_id not in users:
        users[user_id] = {'score': 0, 'level': 'عادی', 'mode': 'معمولی'}

    if data == 'daily_score':
        users[user_id]['score'] += 1
        bot.answer_callback_query(call.id, "۱ امتیاز بهت دادم! 🪙")

    elif data == 'my_info':
        info = users[user_id]
        msg = f"امتیاز: {info['score']}\nسطح: {info['level']}\nحالت چت: {info['mode']}"
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=get_keyboard(user_id))

    elif data == 'buy_vip':
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("خرید سطح معمولی - ۵ امتیاز", callback_data='buy_normal'),
            InlineKeyboardButton("حرفه‌ای - ۱۰ امتیاز", callback_data='buy_pro'),
            InlineKeyboardButton("VIP - 20 امتیاز", callback_data='buy_vip2')
        )
        bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text="نوع اشتراک را انتخاب کن:", reply_markup=markup)

    elif data == 'buy_normal':
        if users[user_id]['score'] >= 5:
            users[user_id]['score'] -= 5
            users[user_id]['level'] = 'معمولی'
            bot.answer_callback_query(call.id, "سطح شما به معمولی تغییر کرد.")
        else:
            bot.answer_callback_query(call.id, "امتیاز کافی نداری!")

    elif data == 'buy_pro':
        if users[user_id]['score'] >= 10:
            users[user_id]['score'] -= 10
            users[user_id]['level'] = 'حرفه‌ای'
            bot.answer_callback_query(call.id, "سطح شما به حرفه‌ای تغییر کرد.")
        else:
            bot.answer_callback_query(call.id, "امتیاز کافی نداری!")

    elif data == 'buy_vip2':
        if users[user_id]['score'] >= 20:
            users[user_id]['score'] -= 20
            users[user_id]['level'] = 'VIP'
            bot.answer_callback_query(call.id, "سطح شما به VIP تغییر کرد.")
        else:
            bot.answer_callback_query(call.id, "امتیاز کافی نداری!")

    elif data == 'ai_chat':
        bot.send_message(user_id, "🧠 این بخش در حال ساخت است. به‌زودی فعال می‌شود.")

    elif data == 'anon_chat':
        bot.send_message(user_id, "🔒 اتصال ناشناس فعلاً غیرفعال است.")

    elif data == 'truth_dare':
        bot.send_message(user_id, "🎮 بازی جرأت و حقیقت در دست ساخت است.")

    elif data == 'change_mode':
        current = users[user_id]['mode']
        next_mode = 'شوخی' if current == 'معمولی' else 'عاشقانه' if current == 'شوخی' else 'معمولی'
        users[user_id]['mode'] = next_mode
        bot.answer_callback_query(call.id, f"حالت چت تغییر کرد به: {next_mode}")

    elif data == 'broadcast' and user_id in admins:
        bot.send_message(user_id, "لطفاً پیام همگانی را بفرست:")
        bot.register_next_step_handler(call.message, handle_broadcast)

    elif data == 'admin_panel' and user_id in admins:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("نمایش کاربران", callback_data='show_users'),
            InlineKeyboardButton("تنظیم امتیاز", callback_data='set_score'),
            InlineKeyboardButton("خروج از پنل", callback_data='back')
        )
        bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text="پنل مدیریت:", reply_markup=markup)

    elif data == 'show_users':
        user_list = "\n".join([str(uid) for uid in users])
        bot.send_message(user_id, f"کاربران:\n{user_list}")

    elif data == 'set_score':
        bot.send_message(user_id, "فرمت: id امتیاز\nمثال: 123456789 10")
        bot.register_next_step_handler(call.message, set_score)

    elif data == 'back':
        bot.send_message(user_id, "از پنل مدیریت خارج شدی.", reply_markup=get_keyboard(user_id))

    elif data == 'close':
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

def handle_broadcast(message):
    for uid in users:
        try:
            bot.send_message(uid, f"📢 پیام مدیر:\n{message.text}")
        except:
            continue
    bot.send_message(message.chat.id, "پیام همگانی ارسال شد.")

def set_score(message):
    try:
        uid, score = map(int, message.text.split())
        if uid in users:
            users[uid]['score'] = score
            bot.send_message(message.chat.id, "امتیاز تنظیم شد.")
        else:
            bot.send_message(message.chat.id, "کاربر یافت نشد.")
    except:
        bot.send_message(message.chat.id, "فرمت اشتباه است.")

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid', 403

@app.route('/setwebhook')
def setwebhook():
    bot.remove_webhook()
    bot.set_webhook(url="https://mohammad-bot-2.onrender.com/")
    return "Webhook set!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
