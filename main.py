import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, request
from datetime import datetime, timedelta
import json
import requests

TOKEN = "8207757951:AAHpvqWfbtlZtyigTGN_MYOxZ408u3Q5rgs"
ADMIN_ID = 6994772164
WEBHOOK_URL = f"https://code-ai-0alo.onrender.com/{TOKEN}"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# ------------------- داده‌ها -------------------
accounts = {}
pending_action = {}
DATA_FILE = "accounts.json"

CRYPTO_LIST = ["Bitcoin", "Tuncoin", "Tether", "Euro"]
CRYPTO_PRICE = {"Bitcoin":3, "Tuncoin":0.5, "Tether":1, "Euro":2}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)

def load_data():
    global accounts
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            accounts.update(json.load(f))
    except:
        accounts.clear()

load_data()

# ------------------- دکمه‌ها -------------------
def get_main_keyboard(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    if user_id == ADMIN_ID:
        markup.add("پنل مدیریت")
    elif user_id in accounts and "phone" in accounts[user_id]:
        markup.add("حساب من", "خرید ارز", "فروش ارز", "پیام به مدیر", "تاریخچه")
    else:
        markup.add("اکانت")
        markup.add(KeyboardButton("ارسال شماره", request_contact=True))
    return markup

def get_user_panel():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("مشاهده امتیاز", "دریافت امتیاز روزانه")
    markup.add("مشاهده موجودی ارز", "خرید ارز", "فروش ارز")
    markup.add("پیام به مدیر", "تاریخچه")
    return markup

def get_crypto_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for crypto in CRYPTO_LIST:
        markup.add(f"خرید {crypto} ({CRYPTO_PRICE[crypto]} سکه)", f"فروش {crypto}")
    markup.add("بازگشت")
    return markup

def get_admin_panel():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("مشاهده شماره‌ها", "تعداد کاربران", "مشاهده امتیازها")
    markup.add("ارسال پیام به کاربران", "تغییر امتیاز کاربران")
    markup.add("مدیریت ارز کاربران", "مشاهده کل ارز کاربران")
    markup.add("کاربران آنلاین", "آمار کامل فعالیت کاربران")
    return markup

# ------------------- دریافت شماره -------------------
@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    user_id = message.from_user.id
    phone = message.contact.phone_number
    name = message.from_user.first_name

    if user_id not in accounts:
        accounts[user_id] = {
            "name": name,
            "phone": phone,
            "coin":0,
            "crypto": {c:0 for c in CRYPTO_LIST},
            "last_bonus":None,
            "history":[f"{datetime.now()} - ثبت شماره: {phone}"]
        }
    else:
        accounts[user_id]["phone"] = phone
        accounts[user_id]["history"].append(f"{datetime.now()} - تغییر شماره: {phone}")
    save_data()

    if user_id == ADMIN_ID:
        bot.send_message(message.chat.id, "پنل مدیریت فعال شد:", reply_markup=get_admin_panel())
    else:
        bot.send_message(message.chat.id, f"شماره شما ثبت شد: {phone}", reply_markup=get_user_panel())

# ------------------- پیام‌ها -------------------
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    text = message.text
    acc = accounts.get(user_id)

    # ------------------- مدیر -------------------
    if user_id == ADMIN_ID:
        if text == "پنل مدیریت":
            bot.send_message(message.chat.id, "پنل مدیریت فعال شد:", reply_markup=get_admin_panel())
        elif text == "مشاهده شماره‌ها":
            info = "\n".join([f"{a['name']}: {a['phone']}" for a in accounts.values()])
            bot.send_message(message.chat.id, info or "هیچ شماره‌ای ثبت نشده.", reply_markup=get_admin_panel())
        elif text == "تعداد کاربران":
            bot.send_message(message.chat.id, f"تعداد کاربران: {len(accounts)}", reply_markup=get_admin_panel())
        elif text == "مشاهده امتیازها":
            info = "\n".join([f"{a['name']}: {a['coin']} سکه" for a in accounts.values()])
            bot.send_message(message.chat.id, info or "هیچ امتیازی ثبت نشده.", reply_markup=get_admin_panel())
        elif text == "ارسال پیام به کاربران":
            bot.send_message(message.chat.id, "آیدی کاربران و پیام را وارد کنید:\nمثال: 123 456 سلام")
            pending_action[user_id] = "send_msg_multi"
        elif text == "تغییر امتیاز کاربران":
            bot.send_message(message.chat.id, "آیدی کاربران و مقدار امتیاز را وارد کنید:\nمثال: 123 456 10")
            pending_action[user_id] = "change_bonus_multi"
        elif text == "مدیریت ارز کاربران":
            bot.send_message(message.chat.id, "آیدی کاربران و ارز و مقدار را وارد کنید:\nمثال: 123 Bitcoin 2")
            pending_action[user_id] = "manage_crypto"
        elif text == "مشاهده کل ارز کاربران":
            info = ""
            for uid, a in accounts.items():
                info += f"{a['name']}:\n"
                for c, amt in a["crypto"].items():
                    info += f"  {c}: {amt}\n"
            bot.send_message(message.chat.id, info or "هیچ ارزی ثبت نشده.", reply_markup=get_admin_panel())
        elif text == "کاربران آنلاین":
            now = datetime.now()
            online_count = sum(1 for u in accounts.values() if u.get("last_bonus") and now - datetime.fromisoformat(u["last_bonus"]) < timedelta(days=1))
            bot.send_message(message.chat.id, f"کاربران فعال ۲۴ ساعت گذشته: {online_count}", reply_markup=get_admin_panel())
        elif text == "آمار کامل فعالیت کاربران":
            info = ""
            for uid, a in accounts.items():
                info += f"{a['name']}:\n"
                for h in a["history"][-10:]:
                    info += f"  {h}\n"
            bot.send_message(message.chat.id, f"آخرین فعالیت کاربران:\n{info or 'هیچ فعالیتی وجود ندارد.'}", reply_markup=get_admin_panel())
        elif user_id in pending_action:
            action = pending_action.pop(user_id)
            try:
                parts = text.split()
                if action == "send_msg_multi":
                    *user_ids, msg = parts[:-1], parts[-1]
                    msg_text = " ".join(parts[len(user_ids):])
                    for uid_str in user_ids:
                        uid = int(uid_str)
                        if uid in accounts:
                            bot.send_message(uid, f"پیام مدیر: {msg_text}")
                    bot.send_message(message.chat.id, "پیام ارسال شد.", reply_markup=get_admin_panel())
                elif action == "change_bonus_multi":
                    *user_ids, bonus_str = parts[:-1], parts[-1]
                    bonus = int(bonus_str)
                    for uid_str in user_ids:
                        uid = int(uid_str)
                        if uid in accounts:
                            accounts[uid]["coin"] = bonus
                    save_data()
                    bot.send_message(message.chat.id, "امتیاز کاربران تغییر کرد.", reply_markup=get_admin_panel())
                elif action == "manage_crypto":
                    user_id_target, crypto, amount = parts
                    user_id_target = int(user_id_target)
                    amount = int(amount)
                    if user_id_target in accounts and crypto in CRYPTO_LIST:
                        accounts[user_id_target]["crypto"][crypto] = amount
                        save_data()
                        bot.send_message(message.chat.id, f"{crypto} کاربر {user_id_target} تغییر کرد.", reply_markup=get_admin_panel())
            except:
                bot.send_message(message.chat.id, "فرمت اشتباه است.", reply_markup=get_admin_panel())
        return

    # ------------------- کاربران -------------------
    if not acc:
        bot.send_message(message.chat.id, "ابتدا شماره خود را ارسال کنید.", reply_markup=get_main_keyboard(user_id))
        return

    # دکمه‌های کاربر
    if text == "حساب من":
        bot.send_message(message.chat.id, f"امتیاز: {acc['coin']}\nموجودی ارزها:\n" + "\n".join([f"{c}: {acc['crypto'][c]}" for c in CRYPTO_LIST]), reply_markup=get_user_panel())
    elif text == "مشاهده امتیاز":
        bot.send_message(message.chat.id, f"امتیاز شما: {acc['coin']}", reply_markup=get_user_panel())
    elif text == "دریافت امتیاز روزانه":
        now = datetime.now()
        last = datetime.fromisoformat(acc["last_bonus"]) if acc["last_bonus"] else None
        if not last or now - last >= timedelta(days=1):
            acc["coin"] += 5
            acc["last_bonus"] = str(now)
            acc["history"].append(f"{now} - دریافت ۵ امتیاز روزانه")
            save_data()
            bot.send_message(message.chat.id, "۵ امتیاز روزانه اضافه شد!", reply_markup=get_user_panel())
        else:
            bot.send_message(message.chat.id, "امتیاز روزانه قبلاً دریافت شده.", reply_markup=get_user_panel())
    elif text == "پیام به مدیر":
        bot.send_message(message.chat.id, "پیام خود را برای مدیر ارسال کنید:")
        pending_action[user_id] = "msg_to_admin"
    elif pending_action.get(user_id) == "msg_to_admin":
        bot.send_message(ADMIN_ID, f"پیام از {acc['name']} ({acc['phone']})\nزمان: {datetime.now()}\nمتن پیام: {text}")
        bot.send_message(message.chat.id, "پیام شما به مدیر ارسال شد.", reply_markup=get_user_panel())
        pending_action.pop(user_id, None)
    elif text == "تاریخچه":
        bot.send_message(message.chat.id, "\n".join(acc["history"][-10:]), reply_markup=get_user_panel())
    elif text == "مشاهده موجودی ارز":
        bot.send_message(message.chat.id, "\n".join([f"{c}: {acc['crypto'][c]}" for c in CRYPTO_LIST]), reply_markup=get_user_panel())
    elif text == "خرید ارز":
        bot.send_message(message.chat.id, "ارز مورد نظر را انتخاب کنید:", reply_markup=get_crypto_keyboard())
    elif text.startswith("خرید "):
        crypto = text.split()[1]
        price = CRYPTO_PRICE.get(crypto, 0)
        if acc["coin"] >= price:
            acc["coin"] -= price
            acc["crypto"][crypto] += 1
            acc["history"].append(f"{datetime.now()} - خرید ۱ واحد {crypto} ({price} سکه)")
            save_data()
            bot.send_message(message.chat.id, f"یک واحد {crypto} خریداری شد.", reply_markup=get_user_panel())
        else:
            bot.send_message(message.chat.id, "سکه کافی نیست.", reply_markup=get_user_panel())
    elif text.startswith("فروش "):
        crypto = text.split()[1]
        if acc["crypto"].get(crypto,0) > 0:
            acc["crypto"][crypto] -= 1
            acc["coin"] += CRYPTO_PRICE[crypto]
            acc["history"].append(f"{datetime.now()} - فروش ۱ واحد {crypto} ({CRYPTO_PRICE[crypto]} سکه دریافت)")
            save_data()
            bot.send_message(message.chat.id, f"یک واحد {crypto} فروخته شد.", reply_markup=get_user_panel())
        else:
            bot.send_message(message.chat.id, "ارز کافی نیست.", reply_markup=get_user_panel())
    else:
        bot.send_message(message.chat.id, "لطفاً گزینه مورد نظر را انتخاب کنید.", reply_markup=get_main_keyboard(user_id))

# ------------------- مسیر وب‌هوک -------------------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/")
def index():
    return "Bot is running!", 200

# ------------------- ست کردن Webhook -------------------
try:
    requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")
except:
    print("Webhook not set!")

# ------------------- اجرای Flask -------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
