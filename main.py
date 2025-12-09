import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8207757951:AAHY2nfBaP-tUlojzevhzTNEKjVJc-H49IU"
ADMIN_ID = 6994772164
WEBHOOK_URL = "https://code-ai-0alo.onrender.com/"

bot = telebot.TeleBot(TOKEN)

# دیتای کاربران داخل کد
users = {}  # user_id: {"name": str, "phone": str, "credit": int, "coins": dict, "online": bool}

# دکمه‌ها ساده برای کاربران بعد از ثبت نام
def user_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("حساب من", "خرید ارز", "ارسال پیام به مدیر")
    markup.row("دریافت کریدت روزانه", "تاریخچه تراکنش", "تبدیل ارز به کریدت")
    markup.row("اطلاعات ربات", "گزینه سرگرمی", "راهنما و لینک ربات")
    markup.row("گزینه ۱۰", "گزینه ۱۱", "گزینه ۱۲")
    markup.row("گزینه ۱۳", "گزینه ۱۴", "گزینه ۱۵")
    return markup

# دکمه ارسال شماره قبل از ثبت نام
def contact_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("ارسال شماره", request_contact=True))
    return markup

# دکمه پنل مدیریت ساده
def admin_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("مشاهده کاربران", "ارسال پیام همگانی", "چت شخصی")
    markup.row("پیام فوری", "تغییر کریدت", "تغییر ارز")
    markup.row("کاربران آنلاین")
    return markup

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        bot.send_message(user_id, "پنل مدیریت فعال شد:", reply_markup=admin_menu())
    else:
        if user_id not in users:
            users[user_id] = {"name": message.from_user.first_name, "credit": 0, "coins": {}, "online": False}
            bot.send_message(user_id, "لطفاً شماره خود را ارسال کنید:", reply_markup=contact_keyboard())
        else:
            bot.send_message(user_id, "سلام! منوی کاربری شما:", reply_markup=user_menu())

@bot.message_handler(content_types=["contact"])
def contact_handler(message):
    user_id = message.from_user.id
    if message.contact:
        phone = message.contact.phone_number
        users[user_id]["phone"] = phone
        users[user_id]["online"] = True
        bot.send_message(user_id, f"شماره شما ثبت شد: {phone}\nمنوی کاربری فعال شد.", reply_markup=user_menu())
        bot.send_message(ADMIN_ID, f"کاربر {users[user_id]['name']} شماره‌شو فرستاد: {phone}")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        # مدیریت
        if message.text == "مشاهده کاربران":
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            for u in users.values():
                markup.add(KeyboardButton(u['name']))
            bot.send_message(user_id, "روی اسم کاربر بزنید:", reply_markup=markup)
        elif message.text == "ارسال پیام همگانی":
            bot.send_message(user_id, "پیام همگانی خود را وارد کنید:")
            bot.register_next_step_handler(message, broadcast_message)
        elif message.text == "تغییر کریدت":
            bot.send_message(user_id, "روی اسم کاربر بزنید:")
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            for u in users.values():
                markup.add(KeyboardButton(u['name']))
            bot.send_message(user_id, "انتخاب کاربر برای تغییر کریدت:", reply_markup=markup)
            bot.register_next_step_handler(message, change_credit)
        elif message.text == "تغییر ارز":
            bot.send_message(user_id, "روی اسم کاربر بزنید:")
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            for u in users.values():
                markup.add(KeyboardButton(u['name']))
            bot.send_message(user_id, "انتخاب کاربر برای تغییر ارز:", reply_markup=markup)
            bot.register_next_step_handler(message, change_coin)
        elif message.text == "پیام فوری":
            bot.send_message(user_id, "پیام فوری برای همه کاربران (۱۰ کریدت کم می‌کند) را وارد کنید:")
            bot.register_next_step_handler(message, quick_msg)
        elif message.text == "چت شخصی":
            bot.send_message(user_id, "آیدی یا اسم کاربر برای چت شخصی را وارد کنید:")
        elif message.text == "کاربران آنلاین":
            online_users = [u['name'] for u in users.values() if u.get("online")]
            bot.send_message(user_id, "کاربران آنلاین:\n" + ("\n".join(online_users) or "هیچ کاربری آنلاین نیست."))
    else:
        # کاربران
        if message.text == "حساب من":
            u = users[user_id]
            coins = ", ".join([f"{k}: {v}" for k, v in u.get("coins", {}).items()])
            bot.send_message(user_id, f"نام: {u['name']}\nکریدت: {u.get('credit',0)}\nارزها: {coins}")
        elif message.text == "خرید ارز":
            bot.send_message(user_id, "قابلیت خرید ارز آماده است.")
        elif message.text == "ارسال پیام به مدیر":
            bot.send_message(user_id, "ارسال پیام به مدیر (۱ کریدت کم می‌شود). پیام خود را تایپ کنید:")
            bot.register_next_step_handler(message, send_to_admin)
        elif message.text == "دریافت کریدت روزانه":
            u = users[user_id]
            if not u.get("daily"):
                u["credit"] += 1
                u["daily"] = True
                bot.send_message(user_id, "۱ کریدت روزانه دریافت شد.")
            else:
                bot.send_message(user_id, "شما امروز کریدت دریافت کرده‌اید.")
        else:
            bot.send_message(user_id, "گزینه نامعتبر است.", reply_markup=user_menu())

def broadcast_message(message):
    for uid in users:
        if uid != ADMIN_ID:
            bot.send_message(uid, f"پیام همگانی مدیر:\n{message.text}")
    bot.send_message(ADMIN_ID, "پیام همگانی ارسال شد.")

def change_credit(message):
    try:
        user_name = message.text
        bot.send_message(ADMIN_ID, f"کریدت جدید برای {user_name} را وارد کنید:")
        bot.register_next_step_handler(message, lambda msg: set_credit(user_name, msg))
    except:
        bot.send_message(ADMIN_ID, "خطا در انتخاب کاربر.")

def set_credit(user_name, message):
    try:
        amount = int(message.text)
        for u in users.values():
            if u['name'] == user_name:
                u['credit'] = amount
        bot.send_message(ADMIN_ID, f"کریدت {user_name} به {amount} تغییر کرد.")
    except:
        bot.send_message(ADMIN_ID, "فرمت اشتباه است.")

def change_coin(message):
    try:
        user_name = message.text
        bot.send_message(ADMIN_ID, f"ارز و مقدار جدید برای {user_name} را وارد کنید (مثال: BTC 1.5):")
        bot.register_next_step_handler(message, lambda msg: set_coin(user_name, msg))
    except:
        bot.send_message(ADMIN_ID, "خطا در انتخاب کاربر.")

def set_coin(user_name, message):
    try:
        coin, amount = message.text.split()
        amount = float(amount)
        for u in users.values():
            if u['name'] == user_name:
                u["coins"][coin] = amount
        bot.send_message(ADMIN_ID, f"{coin} {user_name} به {amount} تغییر کرد.")
    except:
        bot.send_message(ADMIN_ID, "فرمت اشتباه است.")

def quick_msg(message):
    for uid in users:
        if uid != ADMIN_ID:
            bot.send_message(uid, f"پیام فوری:\n{message.text}")
    bot.send_message(ADMIN_ID, "پیام فوری ارسال شد.")

def send_to_admin(message):
    user_id = message.from_user.id
    u = users[user_id]
    if u.get("credit",0) >= 1:
        u["credit"] -= 1
        bot.send_message(ADMIN_ID, f"پیام از {u['name']}:\n{message.text}")
        bot.send_message(user_id, "پیام با موفقیت ارسال شد و ۱ کریدت کم شد.")
    else:
        bot.send_message(user_id, "کریدت کافی ندارید.")

# حذف webhook قبلی و ست کردن وبهوک جدید
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

bot.infinity_polling()
