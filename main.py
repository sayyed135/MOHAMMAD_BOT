import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import json
import os

TOKEN = '7217912729:AAFuXcRQNl0p-uCQZb64cxakJD15_b414q8'
bot = telebot.TeleBot(TOKEN)

DATA_FILE = 'users.json'
ADMIN_ID = 123456789  # آیدی مدیر را اینجا بگذار

def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users(users):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

users = load_users()

def start_keyboard(user_id):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    if user_id == ADMIN_ID:
        keyboard.add(KeyboardButton('مدیریت'))
    keyboard.add(KeyboardButton('احراز هویت', request_contact=True))
    return keyboard

def admin_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('اطلاعات'))
    keyboard.add(KeyboardButton('بازگشت'))
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    keyboard = start_keyboard(message.from_user.id)
    bot.send_message(message.chat.id, "سلام! برای احراز هویت دکمه زیر را بزنید.", reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == 'مدیریت' and m.from_user.id == ADMIN_ID)
def admin_panel(message):
    bot.send_message(message.chat.id, "به بخش مدیریت خوش آمدید.", reply_markup=admin_keyboard())

@bot.message_handler(func=lambda m: m.text == 'بازگشت')
def back_to_main(message):
    keyboard = start_keyboard(message.from_user.id)
    bot.send_message(message.chat.id, "بازگشت به منوی اصلی.", reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == 'اطلاعات' and m.from_user.id == ADMIN_ID)
def send_users_info(message):
    if not users:
        bot.send_message(message.chat.id, "هیچ کاربری هنوز احراز هویت نکرده است.")
        return
    text = "لیست کاربران احراز هویت شده:\n\n"
    for user_id, info in users.items():
        username = info.get('username', 'ندارد')
        phone = info.get('phone', 'ندارد')
        text += f"ID: {user_id}\nUsername: @{username}\nشماره: {phone}\n\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    if message.contact is not None:
        user_id = str(message.from_user.id)
        users[user_id] = {
            'phone': message.contact.phone_number,
            'username': message.from_user.username or '',
        }
        save_users(users)
        bot.send_message(message.chat.id, "احراز هویت با موفقیت انجام شد.", reply_markup=ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, "لطفاً شماره تماس خود را ارسال کنید.")

if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling()
