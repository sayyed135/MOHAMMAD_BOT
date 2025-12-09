import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from DATA import load_data, save_data, ensure_user, update_user

TOKEN = "8207757951:AAHpvqWfbtlZtyigTGN_MYOxZ408u3Q5rgs"
ADMIN_ID = 6994772164
WEBHOOK_URL = "https://code-ai-0alo.onrender.com/"  # آدرس سرور شما روی Render

bot = telebot.TeleBot(TOKEN)

# Load data
data = load_data()

# دکمه‌ها برای کاربران بعد از ثبت نام
def user_menu(user_id):
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
        ensure_user(data, user_id, message.from_user.first_name)
        save_data(data)
        if "phone" in data["users"][str(user_id)]:
            bot.send_message(user_id, "سلام! منوی کاربری شما:", reply_markup=user_menu(user_id))
        else:
            bot.send_message(user_id, "لطفاً شماره خود را ارسال کنید:", reply_markup=contact_keyboard())

@bot.message_handler(content_types=["contact"])
def contact_handler(message):
    user_id = message.from_user.id
    if message.contact is not None:
        phone = message.contact.phone_number
        update_user(data, user_id, phone=phone)
        save_data(data)
        bot.send_message(user_id, f"شماره شما ثبت شد: {phone}\nمنوی کاربری شما فعال شد.", reply_markup=user_menu(user_id))
        bot.send_message(ADMIN_ID, f"کاربر {data['users'][str(user_id)]['name']} شماره‌شو فرستاد: {phone}")

# مدیریت پیام‌ها
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    user_str = str(user_id)
    if user_id == ADMIN_ID:
        # مدیریت
        if message.text == "مشاهده کاربران":
            text = "\n".join([f"{u['name']} - {u.get('phone', 'شماره ثبت نشده')}" for u in data["users"].values()])
            bot.send_message(user_id, text or "هیچ کاربری ثبت نشده.")
        elif message.text == "ارسال پیام همگانی":
            bot.send_message(user_id, "پیام خود را برای ارسال همگانی تایپ کنید:")
            data["pending_action"] = {"type": "broadcast"}
            save_data(data)
        elif message.text == "تغییر کریدت":
            bot.send_message(user_id, "اسم کاربر و مقدار کریدت را وارد کنید:\nمثال: Ali 10")
            data["pending_action"] = {"type": "change_credit"}
            save_data(data)
        elif message.text == "تغییر ارز":
            bot.send_message(user_id, "اسم کاربر و نوع ارز و مقدار را وارد کنید:\nمثال: Ali BTC 1")
            data["pending_action"] = {"type": "change_coin"}
            save_data(data)
        elif message.text == "چت شخصی":
            bot.send_message(user_id, "آیدی یا اسم کاربر برای چت شخصی را وارد کنید:")
            data["pending_action"] = {"type": "private_chat"}
            save_data(data)
        elif message.text == "پیام فوری":
            bot.send_message(user_id, "ارسال پیام فوری (۱۰ کریدت کم می‌شود) برای همه کاربران. پیام را وارد کنید:")
            data["pending_action"] = {"type": "quick_msg"}
            save_data(data)
        elif message.text == "کاربران آنلاین":
            online_users = [u['name'] for u in data["users"].values() if u.get("online")]
            bot.send_message(user_id, "کاربران آنلاین:\n" + ("\n".join(online_users) or "هیچ کاربری آنلاین نیست."))
        else:
            # پردازش اعمال pending
            if "pending_action" in data:
                action = data.pop("pending_action")
                save_data(data)
                if action["type"] == "broadcast":
                    for uid in data["users"]:
                        bot.send_message(int(uid), f"پیام همگانی مدیر:\n{message.text}")
                    bot.send_message(user_id, "پیام همگانی ارسال شد.")
                elif action["type"] == "change_credit":
                    try:
                        name, amount = message.text.split()
                        amount = int(amount)
                        for uid, u in data["users"].items():
                            if u["name"] == name:
                                u["credit"] = amount
                        save_data(data)
                        bot.send_message(user_id, f"کریدت {name} به {amount} تغییر کرد.")
                    except:
                        bot.send_message(user_id, "فرمت اشتباه است.")
                elif action["type"] == "change_coin":
                    try:
                        name, coin, amount = message.text.split()
                        amount = float(amount)
                        for uid, u in data["users"].items():
                            if u["name"] == name:
                                u["coins"][coin] = amount
                        save_data(data)
                        bot.send_message(user_id, f"{coin} {name} به {amount} تغییر کرد.")
                    except:
                        bot.send_message(user_id, "فرمت اشتباه است.")
                elif action["type"] == "private_chat":
                    bot.send_message(user_id, "قابلیت چت شخصی در این نسخه آماده است.")
                elif action["type"] == "quick_msg":
                    for uid in data["users"]:
                        if int(uid) != ADMIN_ID:
                            bot.send_message(int(uid), f"پیام فوری:\n{message.text}")
                    bot.send_message(user_id, "پیام فوری ارسال شد.")
    else:
        # کاربران
        ensure_user(data, user_id, message.from_user.first_name)
        save_data(data)
        if message.text == "حساب من":
            u = data["users"][user_str]
            coins = ", ".join([f"{k}: {v}" for k, v in u.get("coins", {}).items()])
            bot.send_message(user_id, f"نام: {u['name']}\nکریدت: {u.get('credit',0)}\nارزها: {coins}")
        elif message.text == "خرید ارز":
            bot.send_message(user_id, "قابلیت خرید ارز آماده است.")
        elif message.text == "ارسال پیام به مدیر":
            bot.send_message(user_id, "ارسال پیام به مدیر (۱ کریدت کم می‌شود). پیام خود را تایپ کنید:")
            data["pending_action_user"] = {"type": "to_admin"}
            save_data(data)
        elif message.text == "دریافت کریدت روزانه":
            u = data["users"][user_str]
            if not u.get("daily"):
                u["credit"] = u.get("credit",0)+1
                u["daily"] = True
                save_data(data)
                bot.send_message(user_id, "۱ کریدت روزانه دریافت شد.")
            else:
                bot.send_message(user_id, "شما امروز کریدت دریافت کرده‌اید.")
        elif "pending_action_user" in data:
            action = data.pop("pending_action_user")
            save_data(data)
            if action["type"] == "to_admin":
                u = data["users"][user_str]
                if u.get("credit",0)>=1:
                    u["credit"] -= 1
                    save_data(data)
                    bot.send_message(ADMIN_ID, f"پیام از {u['name']}:\n{message.text}")
                    bot.send_message(user_id, "پیام با موفقیت ارسال شد و ۱ کریدت کم شد.")
                else:
                    bot.send_message(user_id, "کریدت کافی ندارید.")
        else:
            bot.send_message(user_id, "گزینه نامعتبر است.", reply_markup=user_menu(user_id))

# Set webhook
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

bot.infinity_polling()
