import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from DATA import load_data, save_data, ensure_user, update_user

TOKEN = "8207757951:AAHpvqWfbtlZtyigTGN_MYOxZ408u3Q5rgs"
ADMIN_ID = 6994772164
bot = telebot.TeleBot(TOKEN)

# بارگذاری دیتا
DATA = load_data()

# دکمه های کاربران
def user_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("حساب من"), KeyboardButton("ارزها"))
    markup.add(KeyboardButton("ارسال پیام به مدیر"), KeyboardButton("اطلاعات ربات"))
    return markup

# دکمه های مدیر
def admin_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("مشاهده کاربران", callback_data="view_users"))
    markup.add(InlineKeyboardButton("مدیریت کریدت/ارزها", callback_data="manage_credit"))
    markup.add(InlineKeyboardButton("پیام خصوصی به کاربر", callback_data="msg_user"))
    markup.add(InlineKeyboardButton("پیام همگانی", callback_data="msg_all"))
    return markup

# دکمه ارسال شماره
def get_contact_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("ارسال شماره", request_contact=True))
    return markup

# start handler
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    if uid == ADMIN_ID:
        bot.send_message(uid, "پنل مدیریت فعال شد:", reply_markup=admin_keyboard())
    else:
        user = ensure_user(uid, message.from_user.first_name)
        if not user.get("phone"):
            bot.send_message(uid, "سلام! لطفاً شماره خودت را ارسال کن:", reply_markup=get_contact_keyboard())
        else:
            bot.send_message(uid, "خوش آمدید!", reply_markup=user_keyboard())

# contact handler
@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    uid = message.from_user.id
    phone = message.contact.phone_number
    user = ensure_user(uid, message.from_user.first_name)
    user["phone"] = phone
    update_user(uid, user)
    bot.send_message(uid, f"شماره شما ثبت شد: {phone}", reply_markup=user_keyboard())
    bot.send_message(ADMIN_ID, f"کاربر {user['name']} شماره‌اش را ثبت کرد: {phone}")

# پیام کاربر
@bot.message_handler(func=lambda message: True)
def user_message(message):
    uid = message.from_user.id
    user = ensure_user(uid, message.from_user.first_name)
    
    if uid != ADMIN_ID:
        # ارسال پیام فوری به مدیر
        if message.text == "ارسال پیام به مدیر":
            if user["credit"] >= 10:
                msg = bot.send_message(uid, "پیام خود را بنویسید (۱۰ کریدت کم می‌شود):")
                bot.register_next_step_handler(msg, send_to_admin)
            else:
                bot.send_message(uid, "کریدت کافی ندارید!")
        elif message.text == "حساب من":
            bot.send_message(uid, f"نام: {user['name']}\nکریدت: {user['credit']}")
        elif message.text == "ارزها":
            crypto_text = "\n".join([f"{c}: {v}" for c, v in user["crypto"].items()])
            bot.send_message(uid, f"موجودی ارزها:\n{crypto_text}")
        elif message.text == "اطلاعات ربات":
            bot.send_message(uid, "ربات ساخته شده توسط تیم SMMH_TEAM\nهر ۲۰ کریدت = ۵ کریدت واقعی\nلینک ربات: https://t.me/YourBotUsername")
        else:
            bot.send_message(uid, "از دکمه‌های منو استفاده کنید.", reply_markup=user_keyboard())

# ارسال پیام فوری به مدیر
def send_to_admin(message):
    uid = message.from_user.id
    user = ensure_user(uid, message.from_user.first_name)
    text = message.text
    user["credit"] -= 10
    update_user(uid, user)
    bot.send_message(uid, "پیام شما به مدیر ارسال شد و ۱۰ کریدت کم شد.")
    bot.send_message(ADMIN_ID, f"پیام فوری از {user['name']}:\n{text}")

# callback handler مدیر
active_chats = {}  # uid کاربر: True یعنی مدیر در حال چت

@bot.callback_query_handler(func=lambda call: True)
def callback_admin(call):
    if call.from_user.id != ADMIN_ID:
        return
    data = load_data()
    if call.data == "view_users":
        users = data["users"]
        if not users:
            bot.send_message(ADMIN_ID, "هیچ کاربری ثبت نشده.")
            return
        markup = InlineKeyboardMarkup()
        for uid_str, info in users.items():
            if int(uid_str) == ADMIN_ID:
                continue
            markup.add(InlineKeyboardButton(info["name"], callback_data=f"chat_{uid_str}"))
        bot.send_message(ADMIN_ID, "لیست کاربران:", reply_markup=markup)
    elif call.data.startswith("chat_"):
        target_id = int(call.data.split("_")[1])
        active_chats[target_id] = True
        bot.send_message(ADMIN_ID, f"شما وارد چت با {DATA['users'][str(target_id)]['name']} شدید.\nبرای قطع چت، /endchat را بزنید.")
    elif call.data == "msg_all":
        msg = bot.send_message(ADMIN_ID, "پیام همگانی خود را بنویسید:")
        bot.register_next_step_handler(msg, broadcast_msg)

# قطع چت شخصی مدیر
@bot.message_handler(commands=['endchat'])
def end_chat(message):
    uid = message.from_user.id
    for user_id in list(active_chats.keys()):
        if active_chats[user_id]:
            active_chats[user_id] = False
            bot.send_message(ADMIN_ID, f"چت با {DATA['users'][str(user_id)]['name']} قطع شد.")

# ارسال پیام از مدیر به کاربر در چت شخصی
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID)
def admin_chat_message(message):
    for user_id, active in active_chats.items():
        if active:
            bot.send_message(user_id, f"پیام مدیر:\n{message.text}")
            bot.send_message(ADMIN_ID, f"پیام به {DATA['users'][str(user_id)]['name']} ارسال شد.")
            break

# پیام همگانی
def broadcast_msg(message):
    text = message.text
    data = load_data()
    for uid_str, info in data["users"].items():
        if int(uid_str) != ADMIN_ID:
            bot.send_message(int(uid_str), f"پیام همگانی مدیر:\n{text}")
    bot.send_message(ADMIN_ID, "پیام همگانی ارسال شد.")

bot.polling()
