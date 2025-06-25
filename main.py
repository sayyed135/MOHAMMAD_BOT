import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from flask import Flask, request
import time, random

API_TOKEN = '7217912729:AAHGslCoRLKfVm1VEZ0qG7riZ3fiGMQ1t7I'
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

admins = [6994772164]
users = {}
anon_waiting = []

truths = ["آخرین دروغی که گفتی چی بوده؟", "تاحالا حسودی کردی؟", "آخرین بار کی ترسیدی؟"]
dares = ["۵ تا شنا برو", "به دوستت بگو دوستش داری", "یه سلفی بگیر بفرست برای یکی!"]

def get_keyboard(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("امتیاز روزانه 🪙", callback_data='daily_score'),
        InlineKeyboardButton("اطلاعات من 📄", callback_data='my_info'),
        InlineKeyboardButton("خرید اشتراک 💎", callback_data='buy_vip'),
        InlineKeyboardButton("AI CHAT 🤖", callback_data='ai_chat'),
        InlineKeyboardButton("چت ناشناس 🕵️", callback_data='anon_chat'),
        InlineKeyboardButton("بازی جرأت و حقیقت 🎯", callback_data='truth_dare'),
        InlineKeyboardButton("تغییر حالت چت 🔁", callback_data='change_mode')
    )
    if user_id in admins:
        markup.add(
            InlineKeyboardButton("ارسال پیام همگانی 📢", callback_data='broadcast'),
            InlineKeyboardButton("پنل مدیریت 🛠️", callback_data='admin_panel')
        )
    markup.add(InlineKeyboardButton("بستن منو ❌", callback_data='close'))
    return markup

@bot.message_handler(commands=['start'])
def start(message: Message):
    uid = message.from_user.id
    if uid not in users:
        users[uid] = {'score': 0, 'level': 'عادی', 'mode': 'معمولی', 'anon': None, 'last_daily': 0}
    bot.send_message(uid, "سلام عزیز 😄 به ربات خوش آمدی!", reply_markup=get_keyboard(uid))

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = call.from_user.id
    data = call.data

    if uid not in users:
        users[uid] = {'score': 0, 'level': 'عادی', 'mode': 'معمولی', 'anon': None, 'last_daily': 0}

    if data == 'daily_score':
        now = time.time()
        if now - users[uid]['last_daily'] < 86400:
            bot.answer_callback_query(call.id, "⏳ فقط هر ۲۴ ساعت یه‌بار می‌تونی بگیری!")
            return
        level = users[uid]['level']
        amount = 50 if level == 'VIP' else 20 if level == 'حرفه‌ای' else 5
        users[uid]['score'] += amount
        users[uid]['last_daily'] = now
        bot.answer_callback_query(call.id, f"✅ {amount} امتیاز دادی!")

    elif data == 'my_info':
        u = users[uid]
        msg = f"🏷 امتیاز: {u['score']}\n📦 سطح: {u['level']}\n💬 حالت چت: {u['mode']}"
        bot.edit_message_text(chat_id=uid, message_id=call.message.message_id, text=msg, reply_markup=get_keyboard(uid))

    elif data == 'buy_vip':
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("معمولی - ۵🪙", callback_data='buy_normal'),
            InlineKeyboardButton("حرفه‌ای - ۱۰🪙", callback_data='buy_pro'),
            InlineKeyboardButton("VIP - ۲۰🪙", callback_data='buy_vip2')
        )
        bot.edit_message_text(chat_id=uid, message_id=call.message.message_id, text="🎁 اشتراک مورد نظر را انتخاب کن:", reply_markup=markup)

    elif data.startswith("buy_"):
        levels = {'buy_normal': ('عادی', 5), 'buy_pro': ('حرفه‌ای', 10), 'buy_vip2': ('VIP', 20)}
        level, cost = levels[data]
        if users[uid]['score'] >= cost:
            users[uid]['score'] -= cost
            users[uid]['level'] = level
            bot.answer_callback_query(call.id, f"✅ سطح شما به {level} تغییر کرد.")
        else:
            bot.answer_callback_query(call.id, "❌ امتیاز کافی نداری!")

    elif data == 'ai_chat':
        bot.send_message(uid, "🤖 سوالتو بپرس:")
        bot.register_next_step_handler(call.message, simple_ai)

    elif data == 'anon_chat':
        if users[uid]['anon']:
            bot.send_message(uid, "🔴 شما در حال چت ناشناس هستید.")
        elif anon_waiting and anon_waiting[0] != uid:
            partner = anon_waiting.pop(0)
            users[uid]['anon'] = partner
            users[partner]['anon'] = uid
            bot.send_message(uid, "🟢 به یک نفر وصل شدی!")
            bot.send_message(partner, "🟢 یک نفر بهت وصل شد!")
        else:
            anon_waiting.append(uid)
            bot.send_message(uid, "⏳ منتظر طرف مقابل هستی...")

    elif data == 'truth_dare':
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🎯 حقیقت", callback_data='truth'),
            InlineKeyboardButton("🔥 جرأت", callback_data='dare')
        )
        bot.send_message(uid, "چی انتخاب می‌کنی؟", reply_markup=markup)

    elif data == 'truth':
        bot.send_message(uid, "❓ " + random.choice(truths))

    elif data == 'dare':
        bot.send_message(uid, "🔥 " + random.choice(dares))

    elif data == 'change_mode':
        current = users[uid]['mode']
        next_mode = 'شوخی' if current == 'معمولی' else 'عاشقانه' if current == 'شوخی' else 'معمولی'
        users[uid]['mode'] = next_mode
        bot.answer_callback_query(call.id, f"💬 حالت چت تغییر کرد به: {next_mode}")

    elif data == 'broadcast' and uid in admins:
        bot.send_message(uid, "📢 پیام همگانی را ارسال کن:")
        bot.register_next_step_handler(call.message, handle_broadcast)

    elif data == 'admin_panel' and uid in admins:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("📊 لیست کاربران", callback_data='show_users'),
            InlineKeyboardButton("🛠 تغییر امتیاز", callback_data='set_score'),
            InlineKeyboardButton("↩ خروج", callback_data='back')
        )
        bot.edit_message_text(chat_id=uid, message_id=call.message.message_id, text="پنل مدیریت:", reply_markup=markup)

    elif data == 'show_users':
        msg = "\n".join([str(i) for i in users])
        bot.send_message(uid, f"📋 کاربران:\n{msg}")

    elif data == 'set_score':
        bot.send_message(uid, "🔢 بنویس: id امتیاز\nمثال: 123456789 10")
        bot.register_next_step_handler(call.message, set_score)

    elif data == 'back':
        bot.send_message(uid, "↩ بازگشتی به منو", reply_markup=get_keyboard(uid))

    elif data == 'close':
        bot.delete_message(uid, call.message.message_id)

    elif data.startswith("ai_reply:"):
        _, tid, _ = data.split(":")
        tid = int(tid)
        bot.send_message(uid, f"✍ پاسخ برای کاربر {tid}:")
        bot.register_next_step_handler(call.message, lambda m: send_ai_reply(m, tid))

    elif data.startswith("ai_warn:"):
        _, tid = data.split(":")
        tid = int(tid)
        bot.send_message(tid, "⚠️ لطفاً از ارسال کلمات نامفهوم به AI خودداری کنید.")
        bot.answer_callback_query(call.id, "❗ اخطار فرستاده شد.")

@bot.message_handler(func=lambda m: users.get(m.from_user.id, {}).get('anon'))
def handle_anon_chat(message):
    uid = message.from_user.id
    partner = users[uid]['anon']
    if users[uid]['score'] < 1:
        bot.send_message(uid, "❌ برای ارسال پیام ناشناس، حداقل ۱ امتیاز نیاز داری.")
        return
    if partner and partner in users:
        users[uid]['score'] -= 1
        bot.send_message(partner, f"🕵️ پیام ناشناس:\n{message.text}")
    else:
        bot.send_message(uid, "⚠ طرف مقابل قطع شده.")

def simple_ai(message):
    uid = message.from_user.id
    text = message.text.strip().lower()

    # دیکشنری پاسخ‌های کوتاه فارسی (نمونه)
    persian_responses = {
        "سلام": "سلام دوست عزیز! 😊",
        "خوبی": "مرسی، تو چطوری؟",
        "حالت چطوره": "عالی‌ام! تو چطوری؟",
        "اسم تو چیه": "من ربات محمد هستم 🤖",
        "دوستت دارم": "منم دوستت دارم! 😍",
        "خداحافظ": "خداحافظ، به زودی می‌بینمت! 👋",
        "چیکار می‌کنی": "دارم به تو کمک می‌کنم 😊",
        "گشنمه": "یه چیزی بخور 😋",
        "خسته‌ام": "یه استراحت کن 🍵",
        "برو بیرون": "از هوای تازه لذت ببر 🌿",
        # ... ادامه بدید تا ۲۰۰ کلمه فارسی
    }

    # دیکشنری پاسخ‌های کوتاه انگلیسی (نمونه)
    english_responses = {
        "hi": "Hello! 👋",
        "hello": "Hi there! 😊",
        "how are you": "I'm fine, thanks! How about you?",
        "bye": "Goodbye! 👋",
        "thank you": "You're welcome! 😊",
        "i love you": "Love you too! ❤️",
        # ... ادامه بدید تا ۱۰۰ کلمه انگلیسی
    }

    if text in persian_responses:
        if users[uid]['score'] >= 2:
            users[uid]['score'] -= 2
            bot.send_message(uid, persian_responses[text])
        else:
            bot.send_message(uid, "❌ امتیاز کافی برای پاسخ AI نداری!")
    elif text in english_responses:
        if users[uid]['score'] >= 2:
            users[uid]['score'] -= 2
            bot.send_message(uid, english_responses[text])
        else:
            bot.send_message(uid, "❌ امتیاز کافی برای پاسخ AI نداری!")
    else:
        bot.send_message(uid, "📌 این کلمه‌تو بعدش جواب می‌دم 😉")
        for admin in admins:
            bot.send_message(admin, f"📨 پیام ناشناخته از [{uid}](tg://user?id={uid}):\n{text}",
                             parse_mode="Markdown", reply_markup=ai_admin_reply_markup(uid, message.message_id))

def ai_admin_reply_markup(uid, msgid):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔁 پاسخ به کاربر", callback_data=f"ai_reply:{uid}:{msgid}"),
        InlineKeyboardButton("⚠ اخطار", callback_data=f"ai_warn:{uid}")
    )
    return markup

def send_ai_reply(message, tid):
    try:
        bot.send_message(tid, f"📩 پاسخ مدیر:\n{message.text}")
        bot.send_message(message.chat.id, "✅ پاسخ فرستاده شد.")
    except:
        bot.send_message(message.chat.id, "❌ خطا در ارسال.")

def handle_broadcast(message):
    for uid in users:
        try:
            bot.send_message(uid, f"📢 پیام مدیر:\n{message.text}")
        except:
            pass
    bot.send_message(message.chat.id, "✅ پیام برای همه ارسال شد.")

def set_score(message):
    try:
        uid, score = map(int, message.text.split())
        if uid in users:
            users[uid]['score'] = score
            bot.send_message(message.chat.id, "✅ امتیاز تنظیم شد.")
        else:
            bot.send_message(message.chat.id, "❌ کاربر پیدا نشد.")
    except:
        bot.send_message(message.chat.id, "❗ فرمت اشتباهه.")

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.data.decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid', 403

@app.route('/setwebhook')
def setwebhook():
    bot.remove_webhook()
    bot.set_webhook(url="https://mohammad-bot-2.onrender.com/")
    return "Webhook set!"

if __name__ == "__main__":
    app.run
