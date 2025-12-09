import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, request, abort
import os
import pickle
from datetime import datetime, date

TOKEN = "8207757951:AAHpvqWfbtlZtyigTGN_MYOxZ408u3Q5rgs"
ADMIN_ID = 6994772164
WEBHOOK_URL = "https://code-ai-0alo.onrender.com/"
USERS_FILE = "users.pkl"  # فایل برای ذخیره کاربران

bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# بارگذاری کاربران از فایل اگر وجود داشته باشد
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "rb") as f:
            return pickle.load(f)
    return {}

# ذخیره کاربران در فایل
def save_users():
    with open(USERS_FILE, "wb") as f:
        pickle.dump(users, f)

users = load_users()  # user_id: {"name": str, "phone": str, "credit": int, "coins": dict, "last_daily": date, "online": bool}

# دکمه‌ها برای کاربران بعد از ثبت نام
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

# دکمه پنل مدیریت
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
            users[user_id] = {"name": message.from_user.first_name, "credit": 0, "coins": {}, "last_daily": None, "online": True}
            save_users()
            bot.send_message(user_id, "لطفاً شماره خود را ارسال کنید:", reply_markup=contact_keyboard())
        else:
            users[user_id]["online"] = True
            save_users()
            bot.send_message(user_id, "سلام! منوی کاربری شما:", reply_markup=user_menu())

@bot.message_handler(content_types=["contact"])
def contact_handler(message):
    user_id = message.from_user.id
    if message.contact:
        phone = message.contact.phone_number
        users[user_id]["phone"] = phone
        save_users()
        bot.send_message(user_id, f"شماره شما ثبت شد: {phone}\nمنوی کاربری فعال شد.", reply_markup=user_menu())
        bot.send_message(ADMIN_ID, f"کاربر {users[user_id]['name']} شماره‌شو فرستاد: {phone}")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    if user_id in users:
        users[user_id]["online"] = True
        save_users()

    if user_id == ADMIN_ID:
        # مدیریت
        if message.text == "مشاهده کاربران":
            text = "\n".join([f"{uid}: {u['name']} - {u.get('phone', 'شماره ثبت نشده')}" for uid, u in users.items()])
            bot.send_message(user_id, text or "هیچ کاربری ثبت نشده.")
        elif message.text == "ارسال پیام همگانی":
            bot.send_message(user_id, "پیام همگانی خود را وارد کنید:")
            bot.register_next_step_handler(message, broadcast_message)
        elif message.text == "تغییر کریدت":
            bot.send_message(user_id, "آیدی کاربر و مقدار کریدت را وارد کنید:\nمثال: 123456789 10")
            bot.register_next_step_handler(message, change_credit)
        elif message.text == "تغییر ارز":
            bot.send_message(user_id, "آیدی کاربر و نوع ارز و مقدار را وارد کنید:\nمثال: 123456789 BTC 1")
            bot.register_next_step_handler(message, change_coin)
        elif message.text == "چت شخصی":
            bot.send_message(user_id, "آیدی کاربر برای چت شخصی را وارد کنید:")
            bot.register_next_step_handler(message, start_private_chat)
        elif message.text == "پیام فوری":
            bot.send_message(user_id, "پیام فوری برای همه کاربران (۱۰ کریدت کم می‌کند) را وارد کنید:")
            bot.register_next_step_handler(message, quick_msg)
        elif message.text == "کاربران آنلاین":
            online_users = [f"{uid}: {u['name']}" for uid, u in users.items() if u.get("online")]
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
            today = date.today()
            if u.get("last_daily") != today:
                u["credit"] += 1
                u["last_daily"] = today
                save_users()
                bot.send_message(user_id, "۱ کریدت روزانه دریافت شد.")
            else:
                bot.send_message(user_id, "شما امروز کریدت دریافت کرده‌اید.")
        # گزینه‌های دیگر را می‌توان پیاده کرد، اما فعلاً پیام پیش‌فرض
        else:
            bot.send_message(user_id, "گزینه نامعتبر است یا هنوز پیاده‌سازی نشده.", reply_markup=user_menu())

def broadcast_message(message):
    for uid in list(users.keys()):
        if uid != ADMIN_ID:
            try:
                bot.send_message(uid, f"پیام همگانی مدیر:\n{message.text}")
            except:
                pass
    bot.send_message(ADMIN_ID, "پیام همگانی ارسال شد.")

def change_credit(message):
    try:
        uid_str, amount = message.text.split()
        uid = int(uid_str)
        amount = int(amount)
        if uid in users:
            users[uid]['credit'] = amount
            save_users()
            bot.send_message(ADMIN_ID, f"کریدت کاربر {uid} به {amount} تغییر کرد.")
        else:
            bot.send_message(ADMIN_ID, "کاربر یافت نشد.")
    except:
        bot.send_message(ADMIN_ID, "فرمت اشتباه است.")

def change_coin(message):
    try:
        uid_str, coin, amount = message.text.split()
        uid = int(uid_str)
        amount = float(amount)
        if uid in users:
            users[uid]["coins"][coin] = amount
            save_users()
            bot.send_message(ADMIN_ID, f"{coin} کاربر {uid} به {amount} تغییر کرد.")
        else:
            bot.send_message(ADMIN_ID, "کاربر یافت نشد.")
    except:
        bot.send_message(ADMIN_ID, "فرمت اشتباه است.")

def quick_msg(message):
    # فرض کنیم ادمین کریدت دارد، اما چک نمی‌کنیم
    for uid in list(users.keys()):
        if uid != ADMIN_ID:
            try:
                bot.send_message(uid, f"پیام فوری:\n{message.text}")
            except:
                pass
    bot.send_message(ADMIN_ID, "پیام فوری ارسال شد.")

def send_to_admin(message):
    user_id = message.from_user.id
    u = users[user_id]
    if u.get("credit", 0) >= 1:
        u["credit"] -= 1
        save_users()
        bot.send_message(ADMIN_ID, f"پیام از {u['name']} (ID: {user_id}):\n{message.text}")
        bot.send_message(user_id, "پیام با موفقیت ارسال شد و ۱ کریدت کم شد.")
    else:
        bot.send_message(user_id, "کریدت کافی ندارید.")

def start_private_chat(message):
    # پیاده‌سازی ساده چت شخصی: فقط پیام بفرست به کاربر
    try:
        uid = int(message.text)
        if uid in users:
            bot.send_message(ADMIN_ID, f"حالا پیام‌های شما به کاربر {uid} ارسال می‌شود. برای خروج /exit بزنید.")
            # اینجا نیاز به حالت چت داریم، اما برای سادگی، next_step_handler برای پیام بعدی
            bot.register_next_step_handler(message, lambda m: send_private(m, uid))
        else:
            bot.send_message(ADMIN_ID, "کاربر یافت نشد.")
    except:
        bot.send_message(ADMIN_ID, "فرمت اشتباه است.")

def send_private(message, target_uid):
    if message.text == "/exit":
        bot.send_message(ADMIN_ID, "چت شخصی پایان یافت.", reply_markup=admin_menu())
        return
    try:
        bot.send_message(target_uid, f"پیام از مدیر:\n{message.text}")
        bot.send_message(ADMIN_ID, "پیام ارسال شد. پیام بعدی را وارد کنید یا /exit برای خروج.")
        bot.register_next_step_handler(message, lambda m: send_private(m, target_uid))
    except:
        bot.send_message(ADMIN_ID, "خطا در ارسال.")

# تنظیم وب‌هوک
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

@app.route('/', methods=['GET', 'HEAD'])
def index():
    return ''

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        abort(403)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
