import telebot
from flask import Flask, request
import os
from datetime import datetime

TOKEN = '7217912729:AAHEug-znb_CGJTXlITt3Zrjp2dJan0a9Gs'
WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com/'
ADMIN_ID = 6994772164

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

connected_users = {}  # user_id: partner_id
blocked_users = set()
chat_logs = {}  # (user1, user2): [(sender_id, msg, time)]
chat_enabled = True
chat_start_times = {}
command_history_map = {}  # برای نگهداری کد دستور تاریخچه چت


@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.data.decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid content type', 403


@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📊 پنل مدیریت")
        bot.send_message(user_id, "سلام مدیر عزیز! به پنل خوش آمدی.", reply_markup=markup)
    else:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("💬 شروع چت ناشناس")
        if user_id in connected_users:
            markup.add("❌ قطع چت ناشناس")
        bot.send_message(user_id, "سلام! به چت ناشناس خوش آمدی.", reply_markup=markup)


@bot.message_handler(func=lambda m: m.text == "📊 پنل مدیریت" and m.from_user.id == ADMIN_ID)
def admin_panel(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🕒 زمان شروع چت کاربران", "📈 آمار کلی", "🔍 بررسی کاربر")
    markup.add("🛠 اتصال دستی", "🚫 لیست مسدودها", "✅ رفع مسدودی", "📁 تاریخچه چت")
    markup.add("⚙️ فعال/غیرفعال‌سازی چت", "📣 هشدار به دو طرف", "❌ بستن پنل")
    bot.send_message(message.chat.id, "پنل مدیریت:", reply_markup=markup)


@bot.message_handler(func=lambda m: m.text == "💬 شروع چت ناشناس")
def start_anonymous_chat(message):
    user_id = message.from_user.id
    if not chat_enabled:
        return bot.send_message(user_id, "❌ چت ناشناس در حال حاضر غیرفعال است.")
    if user_id in blocked_users:
        return bot.send_message(user_id, "🚫 شما از چت ناشناس مسدود شده‌اید.")
    if user_id in connected_users:
        return bot.send_message(user_id, "ℹ️ شما در حال حاضر در یک چت هستید.")
    for uid in connected_users:
        if connected_users[uid] is None and uid != user_id:
            connected_users[uid] = user_id
            connected_users[user_id] = uid
            now = datetime.now()
            chat_start_times[(user_id, uid)] = now
            bot.send_message(uid, "✅ شما به یک کاربر متصل شدید. پیام بده!")
            bot.send_message(user_id, "✅ شما به یک کاربر متصل شدید. پیام بده!")
            return
    connected_users[user_id] = None
    bot.send_message(user_id, "⏳ در حال جستجوی یک کاربر...")


@bot.message_handler(func=lambda m: m.from_user.id in connected_users and connected_users[m.from_user.id] is not None)
def relay_message(message):
    sender = message.from_user.id
    receiver = connected_users[sender]
    if receiver not in connected_users or connected_users[receiver] != sender:
        return bot.send_message(sender, "❌ خطا! ارتباط قطع شده.")
    bot.send_message(receiver, message.text)
    log_key = tuple(sorted([sender, receiver]))
    chat_logs.setdefault(log_key, []).append((sender, message.text, datetime.now().strftime('%H:%M:%S')))


@bot.message_handler(func=lambda m: m.text == "❌ قطع چت ناشناس")
def disconnect(message):
    user_id = message.from_user.id
    partner_id = connected_users.get(user_id)
    bot.send_message(user_id, "❌ چت شما قطع شد.")
    if partner_id:
        bot.send_message(partner_id, "❌ طرف مقابل چت را قطع کرد.")
        connected_users.pop(partner_id, None)
    connected_users.pop(user_id, None)


@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID)
def handle_admin_commands(message):
    if message.text == "🕒 زمان شروع چت کاربران":
        response = ""
        for (u1, u2), t in chat_start_times.items():
            response += f"{u1} ↔️ {u2} : {t.strftime('%Y-%m-%d %H:%M:%S')}\n"
        bot.send_message(ADMIN_ID, response or "هیچ چتی فعال نیست.")

    elif message.text == "📈 آمار کلی":
        total = len(chat_logs)
        active = len([1 for pair in connected_users.items() if pair[1] is not None])
        blocked = len(blocked_users)
        bot.send_message(ADMIN_ID, f"📊 کل چت‌ها: {total}\n🔴 فعال: {active}\n🚫 مسدود: {blocked}")

    elif message.text == "📁 تاریخچه چت":
        bot.send_message(ADMIN_ID, "لطفا آیدی عددی کاربر را بفرستید تا چت‌های او نمایش داده شود:")
        bot.register_next_step_handler(message, show_user_chat_history)

    elif message.text == "📣 هشدار به دو طرف":
        for uid in connected_users:
            if connected_users[uid]:
                bot.send_message(uid, "⚠️ هشدار: لطفاً قوانین را رعایت کنید!")

    elif message.text == "⚙️ فعال/غیرفعال‌سازی چت":
        global chat_enabled
        chat_enabled = not chat_enabled
        status = "فعال" if chat_enabled else "غیرفعال"
        bot.send_message(ADMIN_ID, f"✅ چت ناشناس اکنون {status} است.")

    elif message.text == "🚫 لیست مسدودها":
        if blocked_users:
            bot.send_message(ADMIN_ID, "🔒 کاربران مسدود:\n" + '\n'.join(map(str, blocked_users)))
        else:
            bot.send_message(ADMIN_ID, "🔓 هیچ کاربری مسدود نیست.")

    elif message.text == "✅ رفع مسدودی":
        bot.send_message(ADMIN_ID, "آی‌دی عددی کاربر رو بفرست تا رفع بشه:")
        bot.register_next_step_handler(message, unblock_user)

    elif message.text == "🔍 بررسی کاربر":
        bot.send_message(ADMIN_ID, "آی‌دی عددی کاربر رو بفرست:")
        bot.register_next_step_handler(message, check_user_status)

    elif message.text == "🛠 اتصال دستی":
        bot.send_message(ADMIN_ID, "دو آی‌دی عددی رو با فاصله بفرست (مثلاً: 123 456):")
        bot.register_next_step_handler(message, manual_connect)

    elif message.text == "❌ بستن پنل":
        bot.send_message(ADMIN_ID, "✅ پنل بسته شد.")


def unblock_user(message):
    try:
        uid = int(message.text)
        blocked_users.discard(uid)
        bot.send_message(ADMIN_ID, f"✅ کاربر {uid} رفع مسدودیت شد.")
    except:
        bot.send_message(ADMIN_ID, "❌ خطا در ورود آی‌دی.")


def check_user_status(message):
    try:
        uid = int(message.text)
        status = "🔴 متصل نیست"
        for u1, u2 in connected_users.items():
            if u1 == uid or u2 == uid:
                status = f"🟢 در حال چت با {u2 if u1 == uid else u1}"
                break
        if uid in blocked_users:
            status += "\n🚫 کاربر مسدود است."
        bot.send_message(ADMIN_ID, status)
    except:
        bot.send_message(ADMIN_ID, "❌ خطا در بررسی کاربر.")


def manual_connect(message):
    try:
        ids = list(map(int, message.text.split()))
        if len(ids) == 2:
            connected_users[ids[0]] = ids[1]
            connected_users[ids[1]] = ids[0]
            bot.send_message(ids[0], "✅ به یک کاربر متصل شدید.")
            bot.send_message(ids[1], "✅ به یک کاربر متصل شدید.")
            chat_start_times[(ids[0], ids[1])] = datetime.now()
            bot.send_message(ADMIN_ID, "🛠 اتصال با موفقیت انجام شد.")
        else:
            raise Exception()
    except:
        bot.send_message(ADMIN_ID, "❌ خطا! دو آی‌دی عددی وارد کن.")


def show_user_chat_history(message):
    try:
        user_id = int(message.text)
        user_chats = []
        for (u1, u2), logs in chat_logs.items():
            if user_id in (u1, u2):
                other_id = u2 if u1 == user_id else u1
                code = f"/history{str(abs(hash((u1, u2))))[:6]}"
                user_chats.append((other_id, logs[0][2], code))

        if not user_chats:
            bot.send_message(ADMIN_ID, "هیچ چتی برای این کاربر یافت نشد.")
            return

        text = "لیست چت‌های کاربر:\n\n"
        for idx, (other_id, start_time, code) in enumerate(user_chats, 1):
            text += f"{idx}. کاربر {other_id} در ساعت {start_time} با این کاربر چت داشته است. اگر روی {code} کلیک کنید، تاریخچه چت نمایش داده می‌شود.\n"
        bot.send_message(ADMIN_ID, text)

        for _, (u1, u2) in enumerate(chat_logs.keys()):
            key_code = f"/history{str(abs(hash((u1, u2))))[:6]}"
            command_history_map[key_code] = (u1, u2)

    except ValueError:
        bot.send_message(ADMIN_ID, "آیدی وارد شده معتبر نیست. لطفا یک عدد صحیح ارسال کنید.")


@bot.message_handler(func=lambda m: m.text in command_history_map and m.from_user.id == ADMIN_ID)
def send_chat_history(message):
    u1, u2 = command_history_map[message.text]
    logs = chat_logs.get(tuple(sorted([u1, u2])), [])
    if not logs:
        bot.send_message(ADMIN_ID, "هیچ تاریخچه‌ای برای این چت موجود نیست.")
        return
    text = f"تاریخچه چت بین {u1} و {u2}:\n\n"
    for sender, msg, time in logs:
        text += f"[{time}] {sender}: {msg}\n"
    bot.send_message(ADMIN_ID, text)


@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(message.chat.id, "دستور ناشناس است.")


if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
