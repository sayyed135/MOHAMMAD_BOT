import telebot
from flask import Flask, request
from DATA import load_data, save_data, ensure_user, update_user
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8207757951:AAHpvqWfbtlZtyigTGN_MYOxZ408u3Q5rgs"
WEBHOOK_URL = "https://code-ai-0alo.onrender.com/"
ADMIN_ID = 6994772164

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

pending_admin_action = {}
active_chats = {}

# ---------------- کیبورد کاربر ----------------
def get_user_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("ارسال شماره", request_contact=True))
    markup.add(KeyboardButton("حساب"), KeyboardButton("Information"))
    markup.add(KeyboardButton("خرید ارز"))
    return markup

# ---------------- کیبورد مدیر ----------------
def get_admin_panel():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("مشاهده کاربران", callback_data="view_users"),
        InlineKeyboardButton("ارسال پیام همگانی", callback_data="send_all_msg"),
        InlineKeyboardButton("مدیریت کریدت", callback_data="manage_credit"),
        InlineKeyboardButton("مدیریت ارزها", callback_data="manage_crypto"),
        InlineKeyboardButton("چت شخصی", callback_data="personal_chat"),
        InlineKeyboardButton("ارسال پیام فوری", callback_data="send_instant")
    )
    return markup

# ---------------- شروع ربات ----------------
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    if uid == ADMIN_ID:
        bot.send_message(uid, "پنل مدیریت فعال شد:", reply_markup=get_admin_panel())
    else:
        ensure_user(uid, message.from_user.first_name)
        bot.send_message(uid, "سلام! خوش آمدید.", reply_markup=get_user_keyboard())

# ---------------- دریافت شماره ----------------
@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    uid = message.from_user.id
    if uid != ADMIN_ID:
        user = ensure_user(uid, message.from_user.first_name)
        user["phone"] = message.contact.phone_number
        update_user(uid, user)
        bot.send_message(uid, f"شماره شما ثبت شد: {user['phone']}")
        bot.send_message(ADMIN_ID, f"کاربر {user['name']} شماره خود را فرستاد: {user['phone']}")

# ---------------- کال‌بک‌ها ----------------
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = call.from_user.id
    data = call.data
    user = ensure_user(uid, call.from_user.first_name)

    if uid == ADMIN_ID:
        if data == "view_users":
            users = load_data()["users"]
            if not users:
                bot.send_message(uid, "هیچ کاربری ثبت نشده.", reply_markup=get_admin_panel())
                return
            markup = InlineKeyboardMarkup()
            for u_id, info in users.items():
                markup.add(InlineKeyboardButton(info['name'], callback_data=f"msg_{u_id}"))
            bot.send_message(uid, "انتخاب کاربر برای ارسال پیام:", reply_markup=markup)

        elif data.startswith("msg_"):
            target_id = int(data.split("_")[1])
            pending_admin_action[uid] = ("send_msg", target_id)
            bot.send_message(uid, f"پیام خود را به {ensure_user(target_id,'Unknown')['name']} بنویسید:")

        elif data == "send_all_msg":
            pending_admin_action[uid] = ("send_all", None)
            bot.send_message(uid, "پیام همگانی خود را بنویسید:")

        elif data == "send_instant":
            pending_admin_action[uid] = ("send_instant", None)
            bot.send_message(uid, "پیام فوری خود را بنویسید (10 کریدت کم می‌کند):")

        elif data == "manage_credit":
            pending_admin_action[uid] = ("manage_credit", None)
            bot.send_message(uid, "برای تغییر کریدت کاربران، نام کاربر و مقدار را وارد کنید:\nمثال: Ali 5")

        elif data == "manage_crypto":
            pending_admin_action[uid] = ("manage_crypto", None)
            bot.send_message(uid, "برای تغییر ارز کاربران، نام کاربر و ارز و مقدار را وارد کنید:\nمثال: Ali BTC 2")

# ---------------- پیام‌ها ----------------
@bot.message_handler(func=lambda message: True)
def messages(message):
    uid = message.from_user.id
    text = message.text
    user = ensure_user(uid, message.from_user.first_name)

    # مدیر
    if uid in pending_admin_action:
        action, target_id = pending_admin_action.pop(uid)
        if action == "send_msg":
            bot.send_message(target_id, f"پیام مدیر: {text}")
            bot.send_message(uid, "پیام ارسال شد.")
        elif action == "send_all":
            users = load_data()["users"]
            for u_id in users:
                bot.send_message(int(u_id), f"پیام همگانی: {text}")
            bot.send_message(uid, "پیام همگانی ارسال شد.")
        elif action == "send_instant":
            if user["credit"] >= 10:
                user["credit"] -= 10
                update_user(uid, user)
                users = load_data()["users"]
                for u_id in users:
                    bot.send_message(int(u_id), f"پیام فوری: {text}")
                bot.send_message(uid, "پیام فوری ارسال شد و 10 کریدت کم شد.")
            else:
                bot.send_message(uid, "کریدت کافی نیست.")
        elif action == "manage_credit":
            parts = text.split()
            name, amount = parts[0], int(parts[1])
            users = load_data()["users"]
            for u_id, info in users.items():
                if info['name'] == name:
                    info['credit'] += amount
                    update_user(int(u_id), info)
                    bot.send_message(uid, f"کریدت {name} تغییر کرد.")
        elif action == "manage_crypto":
            parts = text.split()
            name, currency, amount = parts[0], parts[1], float(parts[2])
            users = load_data()["users"]
            for u_id, info in users.items():
                if info['name'] == name:
                    info['crypto'][currency] += amount
                    update_user(int(u_id), info)
                    bot.send_message(uid, f"{currency} {name} تغییر کرد.")
        return

    # کاربران
    if uid != ADMIN_ID:
        if text == "حساب":
            bot.send_message(uid, f"نام: {user['name']}\nکریدت: {user['credit']}\nارزها: {user['crypto']}")
        elif text == "Information":
            bot.send_message(uid, "این ربات ساخته شده توسط تیم SMMH_TEAM است.\nلینک ربات: https://t.me/YourBotLink")
        elif text == "خرید ارز":
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("Bitcoin - 3 سکه", callback_data="buy_BTC"),
                InlineKeyboardButton("TonCoin - 0.5 سکه", callback_data="buy_TonCoin"),
                InlineKeyboardButton("Tether - 1 سکه", callback_data="buy_Tether"),
                InlineKeyboardButton("Euro - 2 سکه", callback_data="buy_EUR")
            )
            bot.send_message(uid, "ارز مورد نظر را انتخاب کنید:", reply_markup=markup)
        else:
            # ارسال پیام به مدیر با 1 کریدت
            if user["credit"] >=1:
                user["credit"] -= 1
                update_user(uid, user)
                bot.send_message(ADMIN_ID, f"پیام از {user['name']}: {text}")
                bot.send_message(uid, "پیام شما به مدیر ارسال شد و 1 کریدت کم شد.")
            else:
                bot.send_message(uid, "برای ارسال پیام به مدیر نیاز به 1 کریدت دارید.")

# ---------------- خرید ارز ----------------
@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def buy_crypto(call):
    uid = call.from_user.id
    currency = call.data.split("_")[1]
    user = ensure_user(uid, call.from_user.first_name)
    prices = {"BTC":3,"TonCoin":0.5,"Tether":1,"EUR":2}
    price = prices[currency]
    if user["credit"] >= price:
        user["credit"] -= price
        user["crypto"][currency] += 1
        update_user(uid, user)
        bot.answer_callback_query(call.id, f"{currency} خریداری شد.")
        bot.send_message(uid, f"شما 1 {currency} خریدید و {price} کریدت کم شد.")
    else:
        bot.answer_callback_query(call.id, "کریدت کافی نیست.")

# ---------------- وبهوک ----------------
@app.route("/", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
