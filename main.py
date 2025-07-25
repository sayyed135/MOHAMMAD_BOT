import json
import time
import os
from datetime import datetime
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

TOKEN = "7217912729:AAGXxp8wDSX1dSpWrRw5RhAY8zDIV1QLvIo"
ADMIN_ID = 6994772164
DATA_FILE = "users_data.json"

app = Flask(__name__)
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def init_user(user_id, username=None):
    data = load_data()
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {
            "username": username or "",
            "crypto": 0.0,
            "diamond": 0.0,
            "role": "user",  # user, vip, gold, special
            "refs": [],
            "ref_by": None,
            "earned_daily": 0.0,
            "earned_ref": 0.0,
            "spent": 0.0,
            "last_daily": 0,
            "subs_count": 0
        }
        save_data(data)
    return data[user_id]

def update_user(user_id, info):
    data = load_data()
    data[str(user_id)] = info
    save_data(data)

def calculate_role(subs_count):
    if subs_count >= 50:
        return "special"
    elif subs_count >= 10:
        return "gold"
    elif subs_count >= 5:
        return "vip"
    else:
        return "user"

def add_crypto(user_id, amount, source=None):
    data = load_data()
    uid = str(user_id)
    if uid not in data:
        return
    data[uid]["crypto"] += amount
    if source == "daily":
        data[uid]["earned_daily"] += amount
    elif source == "ref":
        data[uid]["earned_ref"] += amount
    save_data(data)

def add_diamond(user_id, amount):
    data = load_data()
    uid = str(user_id)
    if uid not in data:
        return
    data[uid]["diamond"] += amount
    save_data(data)

def spend_crypto(user_id, amount):
    data = load_data()
    uid = str(user_id)
    if uid not in data or data[uid]["crypto"] < amount:
        return False
    data[uid]["crypto"] -= amount
    data[uid]["spent"] += amount
    save_data(data)
    return True

def check_daily(user_id):
    data = load_data()
    uid = str(user_id)
    last = data.get(uid, {}).get("last_daily", 0)
    now = time.time()
    if now - last >= 86400:
        data[uid]["last_daily"] = now
        save_data(data)
        return True
    return False

def get_role_bonus(role):
    if role == "user":
        return 5
    elif role == "vip":
        return 8
    elif role == "gold":
        return 12
    elif role == "special":
        return 20
    return 5

def generate_main_keyboard(user_info):
    kb = [
        [InlineKeyboardButton("🏅 امتیاز من", callback_data="show_score")],
        [InlineKeyboardButton("📥 زیرمجموعه‌گیری", callback_data="show_ref")],
        [InlineKeyboardButton("🎁 پاداش روزانه", callback_data="daily_reward")],
        [InlineKeyboardButton("🛒 خرید اشتراک", callback_data="buy_subscription")],
        [InlineKeyboardButton("👤 پروفایل", callback_data="profile")],
    ]
    if user_info["role"] in ["vip", "gold", "special"]:
        kb.append([InlineKeyboardButton("💬 چت با مدیر", callback_data="chat_admin")])
    kb.append([InlineKeyboardButton("💎 تبدیل الماس به Crypto", callback_data="convert_diamond")])
    kb.append([InlineKeyboardButton("🔄 تبدیل Crypto به الماس", callback_data="convert_crypto")])
    if user_info.get("is_admin"):
        kb.append([InlineKeyboardButton("📊 اطلاعات کاربران", callback_data="admin_user_info")])
        kb.append([InlineKeyboardButton("📢 پیام همگانی", callback_data="admin_broadcast")])
    return InlineKeyboardMarkup(kb)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_info = init_user(user.id, user.username)
    user_info["is_admin"] = (user.id == ADMIN_ID)
    update_user(user.id, user_info)
    update.message.reply_text("به ربات خوش آمدید!", reply_markup=generate_main_keyboard(user_info))

def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    user_info = init_user(user_id, query.from_user.username)
    user_info["is_admin"] = (user_id == ADMIN_ID)

    data = query.data

    if data == "show_score":
        text = (f"🏅 امتیاز Crypto شما: {user_info['crypto']:.2f}\n"
                f"💎 تعداد الماس: {user_info['diamond']:.2f}\n"
                f"🧾 زیرمجموعه‌ها: {user_info['subs_count']}\n"
                f"🔰 سطح اشتراک: {user_info['role'].capitalize()}")
        query.answer()
        query.edit_message_text(text, reply_markup=generate_main_keyboard(user_info))

    elif data == "show_ref":
        ref_link = f"https://t.me/YourBotUsername?start={user_id}"
        text = f"لینک زیرمجموعه‌گیری شما:\n{ref_link}\n\nتعداد زیرمجموعه‌ها: {user_info['subs_count']}"
        query.answer()
        query.edit_message_text(text, reply_markup=generate_main_keyboard(user_info))

    elif data == "daily_reward":
        if check_daily(user_id):
            add_crypto(user_id, 0.5, source="daily")
            query.answer("🎉 پاداش روزانه ۰.۵ Crypto به حساب شما اضافه شد!")
        else:
            query.answer("⚠️ شما امروز قبلاً پاداش روزانه را گرفته‌اید!")
        query.edit_message_reply_markup(reply_markup=generate_main_keyboard(user_info))

    elif data == "buy_subscription":
        query.answer()
        query.edit_message_text("این بخش هنوز در دست توسعه است.", reply_markup=generate_main_keyboard(user_info))

    elif data == "profile":
        text = (f"👤 پروفایل شما:\n\n"
                f"نام کاربری: @{user_info['username']}\n"
                f"امتیاز Crypto: {user_info['crypto']:.2f}\n"
                f"المــاس: {user_info['diamond']:.2f}\n"
                f"زیرمجموعه‌ها: {user_info['subs_count']}\n"
                f"سطح اشتراک: {user_info['role'].capitalize()}")
        query.answer()
        query.edit_message_text(text, reply_markup=generate_main_keyboard(user_info))

    elif data == "chat_admin":
        query.answer()
        query.edit_message_text("💬 این قابلیت در نسخه فعلی غیرفعال است.", reply_markup=generate_main_keyboard(user_info))

    elif data == "convert_diamond":
        if user_info["diamond"] >= 1:
            user_info["diamond"] -= 1
            user_info["crypto"] += 5
            update_user(user_id, user_info)
            query.answer("💎 یک الماس به 5 Crypto تبدیل شد!")
        else:
            query.answer("❌ شما الماس کافی ندارید!")
        query.edit_message_reply_markup(reply_markup=generate_main_keyboard(user_info))

    elif data == "convert_crypto":
        if user_info["crypto"] >= 5:
            user_info["crypto"] -= 5
            user_info["diamond"] += 1
            update_user(user_id, user_info)
            query.answer("💰 5 Crypto به یک الماس تبدیل شد!")
        else:
            query.answer("❌ امتیاز Crypto کافی ندارید!")
        query.edit_message_reply_markup(reply_markup=generate_main_keyboard(user_info))

    elif data == "admin_user_info" and user_info["is_admin"]:
        data_all = load_data()
        text = "📊 اطلاعات کاربران:\n\n"
        for uid, info in data_all.items():
            text += (f"👤 [{info['username']}](tg://user?id={uid})\n"
                     f"امتیاز Crypto: {info['crypto']:.2f}\n"
                     f"المــاس: {info['diamond']:.2f}\n"
                     f"زیرمجموعه‌ها: {info['subs_count']}\n"
                     f"کل هزینه‌ها: {info['spent']:.2f}\n"
                     f"-----------------------\n")
        query.answer()
        bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="Markdown")

    elif data == "admin_broadcast" and user_info["is_admin"]:
        query.answer()
        query.edit_message_text("📢 لطفاً پیام همگانی خود را ارسال کنید.")
        context.user_data["waiting_broadcast"] = True

def handle_broadcast(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID and context.user_data.get("waiting_broadcast"):
        context.user_data["waiting_broadcast"] = False
        data_all = load_data()
        count = 0
        for uid in data_all.keys():
            try:
                bot.send_message(chat_id=int(uid), text=update.message.text)
                count += 1
            except:
                continue
        update.message.reply_text(f"پیام به {count} کاربر ارسال شد.")

def handle_start(update: Update, context: CallbackContext):
    user = update.effective_user
    args = context.args
    user_info = init_user(user.id, user.username)
    if args:
        ref_id = args[0]
        if ref_id != str(user.id) and user_info["ref_by"] is None:
            data_all = load_data()
            if ref_id in data_all:
                # اضافه کردن زیرمجموعه
                data_all[ref_id]["refs"].append(user.id)
                data_all[ref_id]["subs_count"] += 1
                # آپدیت سطح اشتراک
                data_all[ref_id]["role"] = calculate_role(data_all[ref_id]["subs_count"])
                # دادن امتیاز بر اساس سطح
                bonus = get_role_bonus(data_all[ref_id]["role"])
                data_all[ref_id]["crypto"] += bonus
                data_all[ref_id]["earned_ref"] += bonus
                # ثبت معرف
                user_info["ref_by"] = ref_id
                update_user(user.id, user_info)
                save_data(data_all)
                bot.send_message(int(ref_id), f"🎉 یک زیرمجموعه جدید به شما اضافه شد! +{bonus} Crypto")
    update_user(user.id, user_info)
    bot.send_message(user.id, "به ربات خوش آمدید!", reply_markup=generate_main_keyboard(user_info))

def main():
    dispatcher.add_handler(CommandHandler("start", handle_start))
    dispatcher.add_handler(CallbackQueryHandler(handle_callback))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_broadcast))
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
