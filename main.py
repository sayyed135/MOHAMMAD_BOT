import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import datetime
import re

TOKEN = '7217912729:AAEejn42bw2U9AB7SmcUYwt9tdpqvKYcJR0'
bot = telebot.TeleBot(TOKEN)

users = {}
blocked_users = set()
admin_id = 6994772164

prices = {
    'normal': 5,
    'pro': 10,
    'vip': 20
}

daily_reward = 1

levels_fa = {
    'normal': 'معمولی',
    'pro': 'حرفه‌ای',
    'vip': 'VIP'
}

def get_main_menu(user_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🎁 امتیاز روزانه", callback_data="daily"))
    keyboard.add(InlineKeyboardButton("💎 خرید اشتراک", callback_data="buy_sub"))
    if user_id == admin_id:
        keyboard.add(InlineKeyboardButton("پنل مدیریت", callback_data="admin_panel"))
    return keyboard

def get_sub_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("اشتراک معمولی", callback_data="sub_normal"),
        InlineKeyboardButton("حرفه‌ای", callback_data="sub_pro"),
        InlineKeyboardButton("VIP", callback_data="sub_vip")
    )
    return keyboard

def get_admin_panel():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("🛠 تنظیمات اشتراک و امتیاز", callback_data="settings"),
        InlineKeyboardButton("📢 پیام همگانی", callback_data="broadcast")
    )
    return keyboard

def get_user_control_menu(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ افزودن ۱۰ امتیاز", callback_data=f"add10_{user_id}")],
        [InlineKeyboardButton("⛔ بلاک", callback_data=f"block_{user_id}")],
        [InlineKeyboardButton("💬 پیام به کاربر", callback_data=f"message_{user_id}")]
    ])

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id in blocked_users:
        return
    if user_id not in users:
        users[user_id] = {'score': 0, 'level': 'عادی', 'last_daily': None}
    bot.send_message(user_id, "به ربات خوش آمدید!", reply_markup=get_main_menu(user_id))

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.from_user.id
    if user_id in blocked_users:
        return

    if call.data == "daily":
        today = datetime.date.today()
        last = users[user_id].get('last_daily')
        if last == today:
            bot.answer_callback_query(call.id, "امروز قبلاً امتیاز گرفته‌اید.")
        else:
            users[user_id]['score'] += daily_reward
            users[user_id]['last_daily'] = today
            bot.answer_callback_query(call.id, f"{daily_reward} امتیاز دریافت شد.")

    elif call.data == "buy_sub":
        bot.edit_message_text("نوع اشتراک را انتخاب کنید:", call.message.chat.id, call.message.message_id, reply_markup=get_sub_menu())

    elif call.data.startswith("sub_"):
        sub = call.data.split("_")[1]
        cost = prices[sub]
        if users[user_id]['score'] >= cost:
            users[user_id]['score'] -= cost
            users[user_id]['level'] = sub
            bot.answer_callback_query(call.id, f"اشتراک {levels_fa[sub]} فعال شد.")
        else:
            bot.answer_callback_query(call.id, "امتیاز کافی ندارید.")

    elif call.data == "admin_panel" and user_id == admin_id:
        bot.edit_message_text("پنل مدیریت:", call.message.chat.id, call.message.message_id, reply_markup=get_admin_panel())

    elif call.data == "settings" and user_id == admin_id:
        bot.send_message(user_id, f"مقادیر فعلی:\n\n🔹 قیمت‌ها:\nمعمولی: {prices['normal']}\nحرفه‌ای: {prices['pro']}\nVIP: {prices['vip']}\n\n🎁 امتیاز روزانه: {daily_reward}\n\nبرای تغییر قیمت‌ها و امتیاز روزانه، پیام را به صورت زیر ارسال کنید:\nset normal 7\nset pro 15\nset vip 30\nset daily 2")

    elif call.data == "broadcast" and user_id == admin_id:
        msg = bot.send_message(user_id, "پیام همگانی را بنویس:")
        bot.register_next_step_handler(msg, broadcast_msg)

    elif call.data.startswith("add10_") and user_id == admin_id:
        uid = int(call.data.split("_")[1])
        if uid in users:
            users[uid]['score'] += 10
            bot.send_message(admin_id, f"۱۰ امتیاز به {uid} اضافه شد.")
            bot.send_message(uid, "✅ مدیر به شما ۱۰ امتیاز داد!")

    elif call.data.startswith("block_") and user_id == admin_id:
        uid = int(call.data.split("_")[1])
        blocked_users.add(uid)
        bot.send_message(uid, "⛔ شما توسط مدیر مسدود شدید.")
        bot.send_message(admin_id, f"کاربر {uid} بلاک شد.")

    elif call.data.startswith("message_") and user_id == admin_id:
        uid = int(call.data.split("_")[1])
        msg = bot.send_message(admin_id, "متن پیام را بنویس:")
        bot.register_next_step_handler(msg, lambda m: send_message_to_user(m, uid))

@bot.message_handler(func=lambda m: str(m.text).isdigit() and m.from_user.id == admin_id)
def watch_user_info(message):
    uid = int(message.text)
    if uid in users:
        u = users[uid]
        bot.send_message(admin_id, f"🔍 کاربر {uid}\nامتیاز: {u['score']}\nاشتراک: {levels_fa.get(u['level'], u['level'])}", reply_markup=get_user_control_menu(uid))
    else:
        bot.send_message(admin_id, "کاربر یافت نشد.")

@bot.message_handler(func=lambda m: m.from_user.id == admin_id)
def handle_admin_text(message):
    text = message.text.strip()
    pattern = r'^set\s+(normal|pro|vip|daily)\s+(\d+)$'
    match = re.match(pattern, text, re.IGNORECASE)
    if match:
        key = match.group(1).lower()
        value = int(match.group(2))
        global daily_reward
        if key in ['normal', 'pro', 'vip']:
            prices[key] = value
            bot.send_message(admin_id, f"قیمت اشتراک {levels_fa[key]} به {value} امتیاز تغییر کرد.")
        elif key == 'daily':
            daily_reward = value
            bot.send_message(admin_id, f"امتیاز روزانه به {value} تغییر کرد.")
    else:
        # میتونی اینجا دستورهای دیگه ادمین رو هم اضافه کنی
        pass

def broadcast_msg(message):
    if message.from_user.id != admin_id:
        return
    for uid in users:
        try:
            bot.send_message(uid, f"📢 پیام مدیر:\n\n{message.text}")
        except:
            pass

def send_message_to_user(message, uid):
    try:
        bot.send_message(uid, f"📬 پیام مدیر:\n\n{message.text}")
        bot.send_message(admin_id, "پیام ارسال شد.")
    except:
        bot.send_message(admin_id, "ارسال پیام با خطا مواجه شد.")

bot.infinity_polling()
