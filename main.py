import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os

TOKEN = '8077313575:AAFUdCtWJ7A4b7nqiP59hEMXRw98hjfsX28'
CHANNEL_USERNAME = '@SAYYED_AMFUN'
ADMIN_ID = 6994772164

bot = telebot.TeleBot(TOKEN)

DATA_FILE = 'data.json'

# بارگذاری داده‌ها از فایل
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
else:
    data = {
        "user_points": {},
        "user_invites": {}
    }

user_points = data["user_points"]
user_invites = data["user_invites"]

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump({
            "user_points": user_points,
            "user_invites": user_invites
        }, f)

def is_member(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return False

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    args = message.text.split()

    if user_id not in user_points:
        user_points[user_id] = 0
        user_invites[user_id] = 0
        save_data()

    if len(args) > 1:
        inviter_id = args[1]
        if inviter_id != user_id and is_member(message.from_user.id):
            user_points[inviter_id] = user_points.get(inviter_id, 0) + 5
            user_invites[inviter_id] = user_invites.get(inviter_id, 0) + 1
            save_data()
            try:
                bot.send_message(int(inviter_id), f"🎉 یه نفر با دعوتت عضو شد!\nامتیاز جدید: {user_points[inviter_id]}")
            except:
                pass

    invite_link = f"https://t.me/SAYYED_AMFUN?start={user_id}"

    text = f"""👋 سلام {message.from_user.first_name}!

⭐ امتیاز شما: {user_points[user_id]}
👥 دعوت‌شده‌ها: {user_invites[user_id]}

👇 لینک اختصاصی دعوت شما:
{invite_link}
"""

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📢 عضویت در کانال", url="https://t.me/SAYYED_AMFUN"))
    bot.send_message(message.chat.id, text, reply_markup=keyboard)

@bot.message_handler(commands=['points'])
def points(message):
    user_id = str(message.from_user.id)
    pts = user_points.get(user_id, 0)
    inv = user_invites.get(user_id, 0)
    bot.send_message(message.chat.id, f"⭐ امتیاز: {pts}\n👥 دعوت‌شده‌ها: {inv}")

@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("📄 لیست کاربران", callback_data="list"))
        kb.add(InlineKeyboardButton("➕ تنظیم امتیاز", callback_data="set"))
        kb.add(InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data="send"))
        bot.send_message(message.chat.id, "🔐 پنل مدیریت:", reply_markup=kb)
    else:
        bot.send_message(message.chat.id, "🚫 دسترسی نداری!")

@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    if c.from_user.id != ADMIN_ID:
        return

    if c.data == "list":
        if not user_points:
            bot.send_message(c.message.chat.id, "❌ لیستی نیست.")
        else:
            txt = "👥 کاربران:\n"
            for uid, pts in user_points.items():
                txt += f"{uid} — {pts} امتیاز\n"
            bot.send_message(c.message.chat.id, txt)

    elif c.data == "set":
        bot.send_message(c.message.chat.id, "فرمت: `آیدی امتیاز` (مثال: 12345 10)")
        bot.register_next_step_handler(c.message, set_pts)

    elif c.data == "send":
        bot.send_message(c.message.chat.id, "پیامتو بفرست:")
        bot.register_next_step_handler(c.message, send_all)

def set_pts(msg):
    try:
        parts = msg.text.split()
        uid = parts[0]
        pts = int(parts[1])
        user_points[uid] = pts
        save_data()
        bot.send_message(msg.chat.id, "✅ تنظیم شد.")
    except:
        bot.send_message(msg.chat.id, "❌ خطا! فرمت نادرسته.")

def send_all(msg):
    count = 0
    for uid in user_points.keys():
        try:
            bot.send_message(int(uid), f"📢 پیام مدیر:\n\n{msg.text}")
            count += 1
        except:
            continue
    bot.send_message(msg.chat.id, f"✅ پیام به {count} نفر ارسال شد.")

bot.infinity_polling()
