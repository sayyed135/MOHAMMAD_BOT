import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
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
        markup.add("حساب من", "خرید ارز", "فروش ارز")
    else:
        markup.add("اکانت")
        markup.add(KeyboardButton("ارسال شماره", request_contact=True))
    return markup

def get_user_panel():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("مشاهده امتیاز", callback_data="view_score"))
    markup.add(InlineKeyboardButton("دریافت امتیاز روزانه", callback_data="daily_bonus"))
    markup.add(InlineKeyboardButton("پیام به مدیر", callback_data="msg_to_admin"))
    markup.add(InlineKeyboardButton("تاریخچه تغییرات", callback_data="history"))
    markup.add(InlineKeyboardButton("مشاهده موجودی ارز", callback_data="view_crypto"))
    markup.add(InlineKeyboardButton("خرید ارز", callback_data="buy_crypto"))
    markup.add(InlineKeyboardButton("فروش ارز", callback_data="sell_crypto"))
    return markup

def get_crypto_keyboard(buy=True):
    markup = InlineKeyboardMarkup()
    for crypto in CRYPTO_LIST:
        if buy:
            markup.add(InlineKeyboardButton(f"{crypto} ({CRYPTO_PRICE[crypto]} سکه)", callback_data=f"buy_{crypto}"))
        else:
            markup.add(InlineKeyboardButton(f"{crypto} ({CRYPTO_PRICE[crypto]} سکه)", callback_data=f"sell_{crypto}"))
    return markup

def get_admin_panel():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("مشاهده شماره‌ها", callback_data="view_contacts"),
        InlineKeyboardButton("تعداد کاربران", callback_data="count_users"),
        InlineKeyboardButton("مشاهده امتیازها", callback_data="view_bonus")
    )
    markup.add(
        InlineKeyboardButton("ارسال پیام به کاربران", callback_data="send_msg_multi"),
        InlineKeyboardButton("تغییر امتیاز کاربران", callback_data="change_bonus_multi"),
        InlineKeyboardButton("مدیریت ارز کاربران", callback_data="manage_crypto")
    )
    markup.add(
        InlineKeyboardButton("مشاهده کل ارز کاربران", callback_data="view_all_crypto"),
        InlineKeyboardButton("کاربران آنلاین", callback_data="online_users"),
        InlineKeyboardButton("آمار کامل فعالیت کاربران", callback_data="full_activity")
    )
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

# ------------------- کال‌بک‌ها -------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    acc = accounts.get(user_id)

    # مدیر
    if user_id == ADMIN_ID:
        if call.data == "view_contacts":
            text = "\n".join([f"{info['name']}: {info['phone']}" for info in accounts.values()]) or "هنوز شماره‌ای ثبت نشده."
            bot.send_message(call.message.chat.id, text, reply_markup=get_admin_panel())
        elif call.data == "count_users":
            bot.send_message(call.message.chat.id, f"تعداد کل کاربران: {len(accounts)}", reply_markup=get_admin_panel())
        elif call.data == "view_bonus":
            text = "\n".join([f"{info['name']}: {info['coin']} سکه‌ای" for info in accounts.values()])
            bot.send_message(call.message.chat.id, text, reply_markup=get_admin_panel())
        elif call.data == "send_msg_multi":
            bot.send_message(call.message.chat.id, "آیدی کاربران و پیام را وارد کنید:\nمثال: 123 456 سلام!")
            pending_action[user_id] = "send_msg_multi"
        elif call.data == "change_bonus_multi":
            bot.send_message(call.message.chat.id, "آیدی کاربران و مقدار امتیاز را وارد کنید:\nمثال: 123 456 10")
            pending_action[user_id] = "change_bonus_multi"
        elif call.data == "manage_crypto":
            bot.send_message(call.message.chat.id, "آیدی کاربران و ارز و مقدار را وارد کنید:\nمثال: 123 Bitcoin 2")
            pending_action[user_id] = "manage_crypto"
        elif call.data == "view_all_crypto":
            text = ""
            for uid, info in accounts.items():
                text += f"{info['name']}:\n"
                for c, amt in info['crypto'].items():
                    text += f"  {c}: {amt}\n"
            bot.send_message(call.message.chat.id, text or "هیچ ارزی ثبت نشده.", reply_markup=get_admin_panel())
        elif call.data == "online_users":
            now = datetime.now()
            online_count = sum(1 for u in accounts.values() if u.get("last_bonus") and now - datetime.fromisoformat(u["last_bonus"]) < timedelta(days=1))
            bot.send_message(call.message.chat.id, f"تعداد کاربران فعال ۲۴ ساعت گذشته: {online_count}", reply_markup=get_admin_panel())
        elif call.data == "full_activity":
            text = ""
            for uid, info in accounts.items():
                text += f"{info['name']}:\n"
                for h in info["history"][-10:]:
                    text += f"  {h}\n"
            bot.send_message(call.message.chat.id, f"آخرین فعالیت کاربران:\n{text or 'هیچ فعالیتی وجود ندارد.'}", reply_markup=get_admin_panel())
        return

    # کاربران
    if not acc:
        bot.send_message(call.message.chat.id, "ابتدا شماره خود را ارسال کنید.", reply_markup=get_main_keyboard(user_id))
        return

    if call.data == "view_score":
        bot.send_message(call.message.chat.id,
                         f"امتیاز شما: {acc['coin']}\nآخرین دریافت: {acc['last_bonus']}",
                         reply_markup=get_user_panel())
    elif call.data == "daily_bonus":
        now = datetime.now()
        last = datetime.fromisoformat(acc["last_bonus"]) if acc["last_bonus"] else None
        if not last or now - last >= timedelta(days=1):
            acc["coin"] += 5
            acc["last_bonus"] = str(now)
            acc["history"].append(f"{now} - دریافت ۵ امتیاز روزانه")
            save_data()
            bot.answer_callback_query(call.id, "۵ امتیاز روزانه اضافه شد!")
        else:
            bot.answer_callback_query(call.id, "امتیاز روزانه قبلاً دریافت شده.")
    elif call.data == "msg_to_admin":
        bot.send_message(call.message.chat.id, "پیام خود را برای مدیر ارسال کنید:")
        pending_action[user_id] = "msg_to_admin"
    elif call.data == "history":
        text = "\n".join(acc["history"][-10:]) if acc["history"] else "تاریخچه‌ای وجود ندارد."
        bot.send_message(call.message.chat.id, f"آخرین تغییرات:\n{text}", reply_markup=get_user_panel())
    elif call.data == "view_crypto":
        text = "\n".join([f"{c}: {acc['crypto'][c]}" for c in CRYPTO_LIST])
        bot.send_message(call.message.chat.id, f"موجودی ارزهای شما:\n{text}", reply_markup=get_user_panel())
    elif call.data == "buy_crypto":
        bot.send_message(call.message.chat.id, "ارز مورد نظر را انتخاب کنید:", reply_markup=get_crypto_keyboard(buy=True))
    elif call.data.startswith("buy_"):
        crypto = call.data.split("_")[1]
        price = CRYPTO_PRICE[crypto]
        if acc["coin"] >= price:
            acc["coin"] -= price
            acc["crypto"][crypto] += 1
            acc["history"].append(f"{datetime.now()} - خرید ۱ واحد {crypto} ({price} سکه)")
            save_data()
            bot.send_message(call.message.chat.id, f"یک واحد {crypto} خریداری شد.\n{price} سکه کم شد.", reply_markup=get_user_panel())
        else:
            bot.send_message(call.message.chat.id, f"سکه کافی ندارید! برای خرید {crypto} به {price} سکه نیاز دارید.", reply_markup=get_user_panel())
    elif call.data == "sell_crypto":
        bot.send_message(call.message.chat.id, "ارز مورد نظر را برای فروش انتخاب کنید:", reply_markup=get_crypto_keyboard(buy=False))
    elif call.data.startswith("sell_"):
        crypto = call.data.split("_")[1]
        if acc["crypto"][crypto] > 0:
            acc["crypto"][crypto] -= 1
            acc["coin"] += CRYPTO_PRICE[crypto]
            acc["history"].append(f"{datetime.now()} - فروش ۱ واحد {crypto} ({CRYPTO_PRICE[crypto]} سکه دریافت)")
            save_data()
            bot.send_message(call.message.chat.id, f"یک واحد {crypto} فروخته شد.\n{CRYPTO_PRICE[crypto]} سکه به شما اضافه شد.", reply_markup=get_user_panel())
        else:
            bot.send_message(call.message.chat.id, f"{crypto} کافی ندارید برای فروش.", reply_markup=get_user_panel())

# ------------------- مدیریت پیام‌ها -------------------
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    acc = accounts.get(user_id)

    # مدیر
    if user_id == ADMIN_ID and user_id in pending_action:
        action = pending_action.pop(user_id)
        try:
            parts = message.text.split()
            if action == "send_msg_multi":
                *user_ids, msg = parts[:-1], parts[-1]
                text = " ".join(parts[len(user_ids):])
                for uid_str in user_ids:
                    uid = int(uid_str)
                    if uid in accounts:
                        bot.send_message(uid, f"پیام مدیر: {text}")
                bot.send_message(message.chat.id, "پیام برای همه کاربران ارسال شد.", reply_markup=get_admin_panel())
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
            bot.send_message(message.chat.id, "فرمت اشتباه است. دوباره تلاش کنید.", reply_markup=get_admin_panel())
        return

    # کاربر
    if not acc:
        bot.send_message(message.chat.id, "ابتدا شماره خود را ارسال کنید.", reply_markup=get_main_keyboard(user_id))
        return

    # پیام به مدیر
    if pending_action.get(user_id) == "msg_to_admin":
        msg_text = message.text
        bot.send_message(ADMIN_ID, f"پیام از {acc['name']} ({acc['phone']})\nزمان: {datetime.now()}\nمتن پیام: {msg_text}")
        bot.send_message(message.chat.id, "پیام شما به مدیر ارسال شد.", reply_markup=get_user_panel())
        pending_action.pop(user_id, None)
        return

    bot.send_message(message.chat.id, "لطفاً گزینه مورد نظر را انتخاب کنید:", reply_markup=get_main_keyboard(user_id))

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
