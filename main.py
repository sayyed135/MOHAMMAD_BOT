import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from flask import Flask, request
import random

API_TOKEN = '7217912729:AAHGslCoRLKfVm1VEZ0qG7riZ3fiGMQ1t7I'
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

admins = [6994772164]
users = {}
anon_waiting = []

truths = ["آخرین باری که گریه کردی کی بود؟", "تا حالا دزدی کردی؟", "عاشق شدی؟"]
dares = ["۵ بار بپر بالا و پایین", "به مامانت بگو دوستت دارم", "به یه نفر غریبه بگو سلام قشنگ!"]

def get_keyboard(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
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
        users[user_id] = {'score': 0, 'level': 'عادی', 'mode': 'معمولی', 'anon': None}
    bot.send_message(user_id, "سلام 👋 خوش آمدی!", reply_markup=get_keyboard(user_id))

@bot.message_handler(func=lambda m: users.get(m.from_user.id, {}).get('anon') is not None)
def handle_anon_chat(message: Message):
    sender = message.from_user.id
    partner = users[sender]['anon']
    if partner and partner in users:
        bot.send_message(partner, f"📨 پیام ناشناس:\n{message.text}")
    else:
        bot.send_message(sender, "❗ طرف مقابل قطع شده.")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    data = call.data

    if user_id not in users:
        users[user_id] = {'score': 0, 'level': 'عادی', 'mode': 'معمولی', 'anon': None}

    if data == 'daily_score':
        users[user_id]['score'] += 1
        bot.answer_callback_query(call.id, "✅ ۱ امتیاز اضافه شد!")

    elif data == 'my_info':
        u = users[user_id]
        text = f"🎯 اطلاعات شما:\nامتیاز: {u['score']}\nسطح: {u['level']}\nحالت چت: {u['mode']}"
        bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text=text, reply_markup=get_keyboard(user_id))

    elif data == 'buy_vip':
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("معمولی - ۵🪙", callback_data='buy_normal'),
            InlineKeyboardButton("حرفه‌ای - ۱۰🪙", callback_data='buy_pro'),
            InlineKeyboardButton("VIP - ۲۰🪙", callback_data='buy_vip2')
        )
        bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text="🎁 سطح موردنظر را انتخاب کن:", reply_markup=markup)

    elif data == 'buy_normal':
        if users[user_id]['score'] >= 5:
            users[user_id]['score'] -= 5
            users[user_id]['level'] = 'معمولی'
            bot.answer_callback_query(call.id, "✅ سطح شما به معمولی تغییر یافت.")
        else:
            bot.answer_callback_query(call.id, "❌ امتیاز کافی نداری!")

    elif data == 'buy_pro':
        if users[user_id]['score'] >= 10:
            users[user_id]['score'] -= 10
            users[user_id]['level'] = 'حرفه‌ای'
            bot.answer_callback_query(call.id, "✅ سطح شما به حرفه‌ای تغییر یافت.")
        else:
            bot.answer_callback_query(call.id, "❌ امتیاز کافی نداری!")

    elif data == 'buy_vip2':
        if users[user_id]['score'] >= 20:
            users[user_id]['score'] -= 20
            users[user_id]['level'] = 'VIP'
            bot.answer_callback_query(call.id, "✅ سطح شما به VIP تغییر یافت.")
        else:
            bot.answer_callback_query(call.id, "❌ امتیاز کافی نداری!")

    elif data == 'ai_chat':
        bot.send_message(user_id, "🤖 بپرس: (مثل: ۲+۲؟)")
        bot.register_next_step_handler(call.message, simple_ai)

    elif data == 'anon_chat':
        if users[user_id]['anon'] is not None:
            bot.send_message(user_id, "🔴 شما در حال چت هستید.")
        elif anon_waiting and anon_waiting[0] != user_id:
            partner = anon_waiting.pop(0)
            users[user_id]['anon'] = partner
            users[partner]['anon'] = user_id
            bot.send_message(user_id, "🟢 به یک نفر وصل شدی!")
            bot.send_message(partner, "🟢 یک نفر بهت وصل شد!")
        else:
            anon_waiting.append(user_id)
            bot.send_message(user_id, "⏳ منتظر طرف مقابل...")

    elif data == 'truth_dare':
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🎯 حقیقت", callback_data='truth'),
            InlineKeyboardButton("🔥 جرأت", callback_data='dare')
        )
        bot.send_message(user_id, "بازی رو انتخاب کن:", reply_markup=markup)

    elif data == 'truth':
        bot.send_message(user_id, "❓ " + random.choice(truths))

    elif data == 'dare':
        bot.send_message(user_id, "🔥 " + random.choice(dares))

    elif data == 'change_mode':
        mode = users[user_id]['mode']
        next_mode = 'شوخی' if mode == 'معمولی' else 'عاشقانه' if mode == 'شوخی' else 'معمولی'
        users[user_id]['mode'] = next_mode
        bot.answer_callback_query(call.id, f"💬 حالت چت شد: {next_mode}")

    elif data == 'broadcast' and user_id in admins:
        bot.send_message(user_id, "📢 پیام همگانی رو بفرست:")
        bot.register_next_step_handler(call.message, handle_broadcast)

    elif data == 'admin_panel' and user_id in admins:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("📊 نمایش کاربران", callback_data='show_users'),
            InlineKeyboardButton("🛠 تنظیم امتیاز", callback_data='set_score'),
            InlineKeyboardButton("↩ خروج", callback_data='back')
        )
        bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text="پنل مدیریت:", reply_markup=markup)

    elif data == 'show_users':
        msg = "\n".join([str(i) for i in users])
        bot.send_message(user_id, f"📋 کاربران ثبت شده:\n{msg}")

    elif data == 'set_score':
        bot.send_message(user_id, "🔢 فرمت: آیدی امتیاز\nمثال: 123456789 10")
        bot.register_next_step_handler(call.message, set_score)

    elif data == 'back':
        bot.send_message(user_id, "↩ برگشتی به منو", reply_markup=get_keyboard(user_id))

    elif data == 'close':
        bot.delete_message(user_id, call.message.message_id)

def handle_broadcast(message):
    for uid in users:
        try:
            bot.send_message(uid, f"📢 پیام از مدیر:\n{message.text}")
        except:
            pass
    bot.send_message(message.chat.id, "✅ پیام برای همه فرستاده شد.")

def set_score(message):
    try:
        uid, score = map(int, message.text.strip().split())
        if uid in users:
            users[uid]['score'] = score
            bot.send_message(message.chat.id, "✅ امتیاز تنظیم شد.")
        else:
            bot.send_message(message.chat.id, "❌ کاربر یافت نشد.")
    except:
        bot.send_message(message.chat.id, "❗ فرمت اشتباهه.")

def simple_ai(message):
    try:
        answer = eval(message.text.strip())
        bot.send_message(message.chat.id, f"✅ جواب: {answer}")
    except:
        bot.send_message(message.chat.id, "🤖 نتونستم بفهمم!")

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
