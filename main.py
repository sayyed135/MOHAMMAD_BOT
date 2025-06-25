import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, request
import time, random

API_TOKEN = '7217912729:AAHGslCoRLKfVm1VEZ0qG7riZ3fiGMQ1t7I'
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

admins = [6994772164]
users = {}
anon_waiting = []
gift_codes = {}

def get_keyboard(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("امتیاز روزانه 🪙", callback_data='daily_score'),
        InlineKeyboardButton("اطلاعات من 📄", callback_data='my_info'),
        InlineKeyboardButton("خرید اشتراک 💎", callback_data='buy_vip'),
        InlineKeyboardButton("AI CHAT 🤖", callback_data='ai_chat'),
        InlineKeyboardButton("چت ناشناس 🕵️", callback_data='anon_chat'),
        InlineKeyboardButton("🎁 کد هدیه", callback_data='gift_code'),
        InlineKeyboardButton("🧾 راهنمای ربات", callback_data='help'),
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
        users[uid] = {'score': 0, 'level': 'معمولی', 'mode': 'معمولی', 'anon': None, 'last_daily': 0, 'bio': '', 'phone': ''}
    bot.send_message(uid, "سلام عزیز 😄 به ربات خوش آمدی!", reply_markup=get_keyboard(uid))

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = call.from_user.id
    data = call.data

    if uid not in users:
        users[uid] = {'score': 0, 'level': 'معمولی', 'mode': 'معمولی', 'anon': None, 'last_daily': 0, 'bio': '', 'phone': ''}

    if data == 'daily_score':
        now = time.time()
        if now - users[uid]['last_daily'] < 86400:
            bot.answer_callback_query(call.id, "⏳ فقط هر ۲۴ ساعت یک‌بار می‌تونی بگیری!")
            return
        level = users[uid]['level']
        amount = 50 if level == 'VIP' else 20 if level == 'حرفه‌ای' else 5
        users[uid]['score'] += amount
        users[uid]['last_daily'] = now
        bot.answer_callback_query(call.id, f"✅ {amount} امتیاز گرفتی!")

    elif data == 'my_info':
        u = users[uid]
        name = call.from_user.first_name
        username = f"@{call.from_user.username}" if call.from_user.username else "ندارد"
        phone = u.get("phone", "ثبت نشده")
        bio = u.get("bio", "ندارد")
        last_daily = time.strftime('%Y-%m-%d %H:%M', time.localtime(u['last_daily'])) if u['last_daily'] else "هنوز نگرفته"
        anon_status = "وصل است" if u.get("anon") else "قطع است"
        msg = (
            f"👤 نام: {name}\n"
            f"🔖 نام‌کاربری: {username}\n"
            f"🆔 آیدی: {uid}\n"
            f"📱 شماره: {phone}\n"
            f"📝 بیوگرافی: {bio}\n"
            f"🏷 امتیاز: {u['score']}\n"
            f"💎 سطح: {u['level']}\n"
            f"💬 حالت چت: {u['mode']}\n"
            f"⏰ آخرین امتیاز روزانه: {last_daily}\n"
            f"🕵️ چت ناشناس: {anon_status}"
        )
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✏️ تنظیم بیو", callback_data="set_bio"),
            InlineKeyboardButton("☎️ ارسال شماره", callback_data="ask_phone"),
            InlineKeyboardButton("🔙 بازگشت", callback_data="back")
        )
        bot.edit_message_text(chat_id=uid, message_id=call.message.message_id, text=msg, reply_markup=markup)

    elif data == 'set_bio':
        bot.send_message(uid, "📝 بیو خود را بفرست:")
        bot.register_next_step_handler(call.message, save_bio)

    elif data == 'ask_phone':
        kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.add(KeyboardButton("📱 ارسال شماره من", request_contact=True))
        bot.send_message(uid, "برای ثبت شماره‌ات دکمه زیر را بزن:", reply_markup=kb)

    elif data == 'gift_code':
        bot.send_message(uid, "🎁 کد هدیه خود را بفرست:")
        bot.register_next_step_handler(call.message, redeem_gift)

    elif data == 'help':
        text = (
            "🤖 راهنمای ربات:\n\n"
            "🪙 امتیاز روزانه: هر ۲۴ ساعت یکبار امتیاز بگیر\n"
            "💎 خرید اشتراک: سطح کاربرتو ارتقاء بده\n"
            "🤖 AI CHAT: چت هوشمند با ربات (هر پیام ۲ امتیاز)\n"
            "🕵️ چت ناشناس: وصل شدن به کاربر دیگر و گفت‌و‌گو\n"
            "🎁 کد هدیه: با زدن کد جایزه بگیر\n"
            "📄 اطلاعات من: مشاهده اطلاعات کامل حساب\n"
            "🔁 تغییر حالت چت: بین شوخی، عاشقانه و معمولی تغییر بده"
        )
        bot.send_message(uid, text)

    elif data == 'ai_chat':
        if users[uid]['score'] < 2:
            bot.send_message(uid, "❌ برای چت با AI حداقل ۲ امتیاز لازم داری.")
            return
        users[uid]['in_ai'] = True
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("❌ پایان چت AI", callback_data='exit_ai'))
        bot.send_message(uid, "🤖 سوالت رو بپرس:", reply_markup=markup)

    elif data == 'exit_ai':
        users[uid]['in_ai'] = False
        bot.send_message(uid, "✅ چت AI پایان یافت.", reply_markup=get_keyboard(uid))

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
            InlineKeyboardButton("🎁 ساخت کد هدیه", callback_data='create_gift')
        )
        bot.send_message(uid, "🛠 پنل مدیریت:", reply_markup=markup)

    elif data == 'show_users':
        if not users:
            bot.send_message(uid, "❌ هیچ کاربری ثبت نشده.")
            return
        msg = "📋 لیست کاربران:\n"
        for uid2, info in users.items():
            phone = info.get("phone", "ندارد")
            msg += f"🆔 {uid2} | 📱 {phone}\n"
        bot.send_message(uid, msg)

    elif data == 'create_gift':
        bot.send_message(uid, "🎁 کدی که می‌خوای بسازی رو بفرست (مثال: test123):")
        bot.register_next_step_handler(call.message, save_gift_code)

    elif data == 'close':
        bot.delete_message(uid, call.message.message_id)

def save_bio(message):
    uid = message.from_user.id
    users[uid]['bio'] = message.text
    bot.send_message(uid, "✅ بیو ذخیره شد.", reply_markup=get_keyboard(uid))

def redeem_gift(message):
    uid = message.from_user.id
    code = message.text.strip()
    if code in gift_codes and gift_codes[code] != 'used':
        users[uid]['score'] += 2
        gift_codes[code] = 'used'
        bot.send_message(uid, "✅ ۲ امتیاز دریافت شد!", reply_markup=get_keyboard(uid))
    else:
        bot.send_message(uid, "❌ این کد نامعتبر یا استفاده‌شده است.")

def save_gift_code(message):
    code = message.text.strip()
    gift_codes[code] = 'valid'
    bot.send_message(message.chat.id, f"✅ کد {code} ساخته شد.")

@bot.message_handler(content_types=['contact'])
def save_phone(message):
    uid = message.from_user.id
    users[uid]['phone'] = message.contact.phone_number
    bot.send_message(uid, "✅ شماره ثبت شد.", reply_markup=get_keyboard(uid))

@bot.message_handler(func=lambda m: users.get(m.from_user.id, {}).get('in_ai'))
def ai_chat(message):
    uid = message.from_user.id
    text = message.text.lower()
    users[uid]['score'] -= 2
    fa_words = {
        "سلام": "سلام عزیزم 😊", "خوبی": "خوبم، تو چطوری؟", "دوستت دارم": "منم دوستت دارم 😍",
        "خداحافظ": "فعلاً عزیز!", "اسم": "من هوش مصنوعی محمدم!"
    }
    en_words = {
        "hi": "Hello!", "how are you": "I'm good, thanks!", "bye": "Goodbye!", "name": "I'm Mohammad's AI bot."
    }
    for word in fa_words:
        if word in text:
            bot.send_message(uid, fa_words[word])
            return
    for word in en_words:
        if word in text:
            bot.send_message(uid, en_words[word])
            return
    bot.send_message(uid, "📌 این کلمه‌تو بعدش جواب می‌دم 😉")

def handle_broadcast(message):
    for uid in users:
        try:
            bot.send_message(uid, f"📢 پیام مدیر:\n{message.text}")
        except:
            pass
    bot.send_message(message.chat.id, "✅ پیام برای همه ارسال شد.")

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
