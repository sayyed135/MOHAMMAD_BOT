import telebot
from telebot import types
import json
import os

TOKEN = '7217912729:AAFuXcRQNl0p-uCQZb64cxakJD15_b414q8'
bot = telebot.TeleBot(TOKEN)

user_data = {}
USERS_FILE = "users.json"
ADMIN_ID = 6994772164  # آی‌دی خودت رو بزار

cities_afghanistan = [
    "کابل", "هرات", "مزار شریف", "قندهار", "جلال‌آباد",
    "بامیان", "غزنی", "بدخشان", "نیمروز", "فراه",
    "سمنگان", "بلخ", "بادغیس", "پکتیا", "لوگر"
]

interests_list = ["🎮 بازی", "🎵 موسیقی", "🎬 فیلم", "📖 مطالعه", "💻 تکنولوژی"]

# Load users
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        all_users = json.load(f)
else:
    all_users = {}

@bot.message_handler(commands=["start"])
def send_welcome(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("📝 ثبت اطلاعات من", "📊 اطلاعات من")
    if message.chat.id == ADMIN_ID:
        keyboard.row("📋 اطلاعات کاربران")
    bot.send_message(message.chat.id, "سلام! یکی از گزینه‌ها رو انتخاب کن:", reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == "📝 ثبت اطلاعات من")
def ask_name(message):
    user_data[message.chat.id] = {}
    bot.send_message(message.chat.id, "نامت رو بنویس:")
    bot.register_next_step_handler(message, ask_age)

def ask_age(message):
    user_data[message.chat.id]["name"] = message.text
    bot.send_message(message.chat.id, "چند سالته؟")
    bot.register_next_step_handler(message, ask_gender)

def ask_gender(message):
    user_data[message.chat.id]["age"] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("پسر", "دختر")
    bot.send_message(message.chat.id, "جنسیتت رو انتخاب کن:", reply_markup=markup)
    bot.register_next_step_handler(message, ask_city)

def ask_city(message):
    user_data[message.chat.id]["gender"] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for city in cities_afghanistan:
        markup.add(city)
    bot.send_message(message.chat.id, "شهر خودت رو انتخاب کن:", reply_markup=markup)
    bot.register_next_step_handler(message, ask_interests)

def ask_interests(message):
    user_data[message.chat.id]["city"] = message.text
    markup = types.InlineKeyboardMarkup()
    for interest in interests_list:
        markup.add(types.InlineKeyboardButton(text=interest, callback_data=f"int_{interest}"))
    markup.add(types.InlineKeyboardButton(text="✅ ثبت نهایی", callback_data="done"))
    user_data[message.chat.id]["interests"] = []
    bot.send_message(message.chat.id, "علاقه‌مندی‌هاتو انتخاب کن:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("int_"))
def select_interest(call):
    interest = call.data[4:]
    uid = call.from_user.id
    if interest not in user_data[uid]["interests"]:
        user_data[uid]["interests"].append(interest)
        bot.answer_callback_query(call.id, text=f"{interest} اضافه شد.")
    else:
        bot.answer_callback_query(call.id, text=f"{interest} قبلاً انتخاب شده.")

@bot.callback_query_handler(func=lambda call: call.data == "done")
def finish_registration(call):
    uid = call.from_user.id
    user = user_data.get(uid, {})
    user["level"] = "معمولی"
    user["id"] = uid
    all_users[str(uid)] = user
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_users, f, ensure_ascii=False, indent=2)
    bot.send_message(uid, "ثبت‌نام با موفقیت انجام شد ✅")

@bot.message_handler(func=lambda m: m.text == "📊 اطلاعات من")
def show_user_info(message):
    uid = str(message.chat.id)
    if uid in all_users:
        u = all_users[uid]
        info = f"👤 نام: {u['name']}\n🎂 سن: {u['age']}\n🚻 جنسیت: {u['gender']}\n🏙 شهر: {u['city']}\n🎯 علاقه‌مندی‌ها: {', '.join(u['interests'])}\n⭐ سطح: {u['level']}"
    else:
        info = "شما هنوز ثبت‌نام نکردید."
    bot.send_message(message.chat.id, info)

@bot.message_handler(func=lambda m: m.text == "📋 اطلاعات کاربران" and m.chat.id == ADMIN_ID)
def show_all_users(message):
    text = ""
    for uid, u in all_users.items():
        text += f"👤 {u['name']} | ID: {uid}\n"
        text += f"🎂 سن: {u['age']} | 🚻 جنسیت: {u['gender']}\n🏙 شهر: {u['city']} | ⭐ سطح: {u['level']}\n🎯 علاقه‌مندی‌ها: {', '.join(u['interests'])}\n\n"
    if not text:
        text = "هیچ کاربری ثبت‌نام نکرده."
    bot.send_message(message.chat.id, text)

print("ربات فعال شد...")
bot.infinity_polling()
