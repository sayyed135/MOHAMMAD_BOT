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
gift_codes = {}
used_codes = {}

truths = ["آخرین دروغی که گفتی چی بوده؟", "تاحالا حسودی کردی؟", "آخرین بار کی ترسیدی؟"]
dares = ["۵ تا شنا برو", "به دوستت بگو دوستش داری", "یه سلفی بگیر بفرست برای یکی!"]

ai_answers_fa = {
  "سلام": "سلام رفیق 😊", "خوبی": "آره، تو چطوری؟", "چطوری": "قشنگ! تو؟", "دوستت دارم": "منم دوستت دارم 😍",
  "شوخی بگو": "یه شوخی برات دارم: چرا گوجه قرمز شد؟ چون از خجالت سیب رو دید! 😂", "خداحافظ": "فعلاً! مواظب خودت باش!",
  "خسته‌ام": "یه استراحت کوتاه بکن و ادامه بده 💪", "غمگینم": "همه چیز خوب میشه، لبخند بزن 😊",
  "عاشق شدم": "واو! مراقب دلت باش 😄", "بیکارم": "بیا با هم حرف بزنیم 😁"
}

ai_answers_en = {
  "hi": "Hey!", "hello": "Hello there!", "how are you": "I'm fine, thanks!", "bye": "Goodbye!",
  "who are you": "I'm a friendly bot.", "joke": "Why don't scientists trust atoms? Because they make up everything! 😂"
}

def get_main_menu(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("امتیاز روزانه 🪙", callback_data='daily_score'),
        InlineKeyboardButton("اطلاعات من 📄", callback_data='my_info'),
        InlineKeyboardButton("خرید اشتراک 💎", callback_data='buy_vip'),
        InlineKeyboardButton("AI CHAT 🤖", callback_data='ai_chat'),
        InlineKeyboardButton("چت ناشناس 🕵️", callback_data='anon_chat'),
        InlineKeyboardButton("🎁 کد هدیه", callback_data='gift_code'),
        InlineKeyboardButton("📘 راهنما", callback_data='help')
    )
    if user_id in admins:
        markup.add(
            InlineKeyboardButton("ارسال پیام همگانی 📢", callback_data='broadcast'),
            InlineKeyboardButton("پنل مدیریت 🛠️", callback_data='admin_panel')
        )
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    if uid not in users:
        users[uid] = {'score': 0, 'level': 'معمولی', 'mode': 'معمولی', 'anon': None, 'last_daily': 0, 'ai': False}
    bot.send_message(uid, "سلام عزیز 😄 به ربات خوش آمدی!", reply_markup=get_main_menu(uid))

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid = call.from_user.id
    if uid not in users:
        users[uid] = {'score': 0, 'level': 'معمولی', 'mode': 'معمولی', 'anon': None, 'last_daily': 0, 'ai': False}

    data = call.data
    if data == 'daily_score':
        now = time.time()
        if now - users[uid]['last_daily'] < 86400:
            bot.answer_callback_query(call.id, "⏳ فقط هر ۲۴ ساعت یه‌بار می‌تونی بگیری!")
            return
        level = users[uid]['level']
        amount = 50 if level == 'VIP' else 20 if level == 'حرفه‌ای' else 5
        users[uid]['score'] += amount
        users[uid]['last_daily'] = now
        bot.answer_callback_query(call.id, f"✅ {amount} امتیاز گرفتی!")

    elif data == 'my_info':
        u = users[uid]
        msg = f"🏷 امتیاز: {u['score']}\n📦 سطح: {u['level']}\n💬 حالت چت: {u['mode']}"
        bot.edit_message_text(chat_id=uid, message_id=call.message.message_id, text=msg, reply_markup=get_main_menu(uid))

    elif data == 'buy_vip':
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("معمولی - ۵🪙", callback_data='buy_normal'),
            InlineKeyboardButton("حرفه‌ای - ۱۰🪙", callback_data='buy_pro'),
            InlineKeyboardButton("VIP - ۲۰🪙", callback_data='buy_vip2')
        )
        bot.edit_message_text(chat_id=uid, message_id=call.message.message_id, text="🎁 اشتراک مورد نظر را انتخاب کن:", reply_markup=markup)

    elif data.startswith('buy_'):
        levels = {'buy_normal': ('معمولی', 5), 'buy_pro': ('حرفه‌ای', 10), 'buy_vip2': ('VIP', 20)}
        level, cost = levels[data]
        if users[uid]['score'] >= cost:
            users[uid]['score'] -= cost
            users[uid]['level'] = level
            bot.answer_callback_query(call.id, f"✅ سطح شما به {level} تغییر کرد.")
        else:
            bot.answer_callback_query(call.id, "❌ امتیاز کافی نداری!")

    elif data == 'ai_chat':
        users[uid]['ai'] = True
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("❌ پایان چت AI", callback_data='end_ai'))
        bot.send_message(uid, "🤖 سوالت رو بپرس:", reply_markup=markup)

    elif data == 'end_ai':
        users[uid]['ai'] = False
        bot.send_message(uid, "✅ از چت AI خارج شدی.")

    elif data == 'gift_code':
        bot.send_message(uid, "🎁 کد هدیه‌ات رو بفرست:")
        bot.register_next_step_handler(call.message, check_gift_code)

    elif data == 'help':
        bot.send_message(uid,
        "📘 راهنمای ربات:\n\n"
        "1️⃣ امتیاز روزانه: روزی یکبار امتیاز بگیر\n"
        "2️⃣ خرید اشتراک: با امتیازت سطح بگیر (معمولی، حرفه‌ای، VIP)\n"
        "3️⃣ AI Chat: سوال بپرس و هوش مصنوعی پاسخ می‌ده\n"
        "4️⃣ چت ناشناس: با افراد ناشناس گفتگو کن\n"
        "5️⃣ کد هدیه: اگه کد داشتی اینجا وارد کن و امتیاز بگیر")

    elif data == 'broadcast' and uid in admins:
        bot.send_message(uid, "📢 پیام همگانی را بفرست:")
        bot.register_next_step_handler(call.message, broadcast)

    elif data == 'admin_panel' and uid in admins:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🎁 ساخت کد هدیه", callback_data='make_gift'),
            InlineKeyboardButton("📊 تنظیم امتیاز", callback_data='set_score')
        )
        bot.send_message(uid, "🛠️ پنل مدیریت:", reply_markup=markup)

    elif data == 'make_gift':
        bot.send_message(uid, "🆕 بنویس: کد امتیاز (مثال: abc 10)")
        bot.register_next_step_handler(call.message, create_gift)

    elif data == 'set_score':
        bot.send_message(uid, "🧮 بنویس: آیدی امتیاز (مثال: 123 20)")
        bot.register_next_step_handler(call.message, set_score)

def create_gift(message):
    try:
        parts = message.text.split()
        code = parts[0]
        amount = int(parts[1])
        gift_codes[code] = amount
        bot.send_message(message.chat.id, f"🎁 کد {code} ساخته شد با {amount} امتیاز.")
    except:
        bot.send_message(message.chat.id, "❌ فرمت اشتباهه.")

def check_gift_code(message):
    uid = message.from_user.id
    code = message.text.strip()
    if code in used_codes:
        bot.send_message(uid, "❌ این کد قبلاً استفاده شده.")
    elif code in gift_codes:
        amount = gift_codes[code]
        users[uid]['score'] += amount
        used_codes[code] = True
        bot.send_message(uid, f"✅ {amount} امتیاز گرفتی!")
    else:
        bot.send_message(uid, "❌ کد اشتباهه.")

def broadcast(message):
    for uid in users:
        try:
            bot.send_message(uid, f"📢 پیام مدیر:\n{message.text}")
        except:
            pass
    bot.send_message(message.chat.id, "✅ پیام فرستاده شد.")

def set_score(message):
    try:
        parts = message.text.split()
        tid = int(parts[0])
        score = int(parts[1])
        if tid in users:
            users[tid]['score'] = score
            bot.send_message(message.chat.id, "✅ امتیاز تنظیم شد.")
        else:
            bot.send_message(message.chat.id, "❌ کاربر پیدا نشد.")
    except:
        bot.send_message(message.chat.id, "❗ فرمت اشتباهه.")

@bot.message_handler(func=lambda m: True)
def message_handler(message):
    uid = message.from_user.id
    if uid not in users:
        users[uid] = {'score': 0, 'level': 'معمولی', 'mode': 'معمولی', 'anon': None, 'last_daily': 0, 'ai': False}
    if users[uid]['ai']:
        txt = message.text.lower().strip()
        if txt in ai_answers_fa:
            bot.send_message(uid, ai_answers_fa[txt])
            users[uid]['score'] -= 2
        elif txt in ai_answers_en:
            bot.send_message(uid, ai_answers_en[txt])
            users[uid]['score'] -= 2
        else:
            bot.send_message(uid, "🔍 این کلمه بعداً جواب می‌دم.")
            for admin in admins:
                bot.send_message(admin, f"📨 پیام ناشناخته از [{uid}](tg://user?id={uid}):\n{text}", parse_mode="Markdown")

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
    app.run(host="0.0.0.0", port=10000)
