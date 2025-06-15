import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = '7217912729:AAGwbJSodBzOzhOf0Yh6VwNrRs2XACld1gA'
bot = telebot.TeleBot(TOKEN)

# داده ها را در حافظه موقت ذخیره می‌کنیم (برای ذخیره دائمی باید فایل یا دیتابیس استفاده شود)
users = {}

ADMIN_ID = 123456789  # آیدی تلگرام مدیر را اینجا بگذار

def main_keyboard(is_admin=False):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('احراز هویت')
    keyboard.add('جرأت یا حقیقت')
    if is_admin:
        keyboard.add('مدیریت')
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users[user_id] = {
        'first_name': message.from_user.first_name,
        'last_name': message.from_user.last_name,
        'username': message.from_user.username,
        'phone': None
    }
    is_admin = (user_id == ADMIN_ID)
    bot.send_message(message.chat.id,
                     "سلام! به ربات خوش آمدید.",
                     reply_markup=main_keyboard(is_admin))

@bot.message_handler(func=lambda m: m.text == 'احراز هویت')
def request_contact(message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = KeyboardButton('ارسال شماره تلفن', request_contact=True)
    keyboard.add(button)
    bot.send_message(message.chat.id, 'لطفاً شماره تلفن خود را ارسال کنید:', reply_markup=keyboard)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    if message.contact and message.contact.user_id == user_id:
        phone = message.contact.phone_number
        if user_id in users:
            users[user_id]['phone'] = phone
        else:
            users[user_id] = {
                'first_name': message.from_user.first_name,
                'last_name': message.from_user.last_name,
                'username': message.from_user.username,
                'phone': phone
            }
        bot.send_message(message.chat.id, 'شماره تلفن شما با موفقیت ثبت شد.', reply_markup=main_keyboard(user_id==ADMIN_ID))
    else:
        bot.send_message(message.chat.id, 'شماره تلفن باید از طرف خود شما ارسال شود.')

@bot.message_handler(func=lambda m: m.text == 'مدیریت')
def admin_panel(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, 'شما اجازه دسترسی به این بخش را ندارید.')
        return
    text = "اطلاعات کاربران ثبت شده:\n\n"
    for uid, info in users.items():
        uname = info['username'] if info['username'] else 'ندارد'
        phone = info['phone'] if info['phone'] else 'ندارد'
        name = f"{info['first_name'] or ''} {info['last_name'] or ''}".strip()
        text += f"آیدی: {uid}\nنام: {name}\nیوزرنیم: @{uname}\nشماره: {phone}\n\n"
    bot.send_message(message.chat.id, text or "هیچ کاربری ثبت نشده.")

@bot.message_handler(func=lambda m: m.text == 'جرأت یا حقیقت')
def dare_or_truth(message):
    bot.send_message(message.chat.id, "این بخش فعلاً در دست ساخت است.")

bot.infinity_polling()
