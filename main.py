import telebot
import sqlite3

TOKEN = '7217912729:AAF5rYAR073MlBLoFBc9-ik8r9M0MdyXMds'
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 6994772164

# اتصال به دیتابیس
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

# ایجاد جدول کاربران
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        phone TEXT
    )
''')
conn.commit()

# منوی کاربر
def user_menu():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton("📞 ثبت شماره")
    btn2 = telebot.types.KeyboardButton("✉️ ارسال پیام به مدیریت")
    keyboard.add(btn1)
    keyboard.add(btn2)
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        show_admin_panel(message)
        return

    cursor.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
    if cursor.fetchone():
        bot.send_message(message.chat.id, "به منوی کاربر خوش آمدید 👇", reply_markup=user_menu())
    else:
        bot.send_message(message.chat.id, "سلام! لطفاً اسم خود را وارد کنید:")
        bot.register_next_step_handler(message, get_name)

def get_name(message):
    user_id = message.from_user.id
    name = message.text
    bot.user_step = getattr(bot, 'user_step', {})
    bot.user_step[user_id] = name

    # دکمه برای ارسال شماره
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = telebot.types.KeyboardButton("📞 ارسال شماره من", request_contact=True)
    keyboard.add(button)

    bot.send_message(message.chat.id, "حالا روی دکمه زیر بزن تا شماره‌ت ثبت بشه:", reply_markup=keyboard)

@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    user_id = message.from_user.id
    phone = message.contact.phone_number

    if hasattr(bot, 'user_step') and user_id in bot.user_step:
        name = bot.user_step[user_id]
        cursor.execute('INSERT OR REPLACE INTO users (user_id, name, phone) VALUES (?, ?, ?)',
                       (user_id, name, phone))
        conn.commit()
        del bot.user_step[user_id]
        bot.send_message(message.chat.id, "✅ ثبت‌نام کامل شد", reply_markup=user_menu())
    else:
        bot.send_message(message.chat.id, "لطفاً ابتدا /start را بزن و اسم را وارد کن.")

# عملکرد دکمه‌های کاربر
@bot.message_handler(func=lambda m: m.text == "📞 ثبت شماره")
def ask_phone_again(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = telebot.types.KeyboardButton("📞 ارسال شماره من", request_contact=True)
    keyboard.add(button)
    bot.send_message(message.chat.id, "روی دکمه زیر بزن برای ثبت یا ویرایش شماره:", reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == "✉️ ارسال پیام به مدیریت")
def ask_message_to_admin(message):
    bot.send_message(message.chat.id, "لطفاً پیام خود را برای مدیریت بنویس:")
    bot.register_next_step_handler(message, forward_to_admin)

def forward_to_admin(message):
    user_id = message.from_user.id
    cursor.execute('SELECT name, phone FROM users WHERE user_id=?', (user_id,))
    row = cursor.fetchone()
    name, phone = row if row else ('نامشخص', 'نامشخص')

    text = f"📩 پیام جدید از کاربر:\n\n🆔 {user_id}\n👤 {name}\n📞 {phone}\n\n📨 متن پیام:\n{message.text}"
    bot.send_message(ADMIN_ID, text)
    bot.send_message(message.chat.id, "✅ پیام شما برای مدیریت ارسال شد.")

# پنل مدیریت
def show_admin_panel(message):
    markup = telebot.types.InlineKeyboardMarkup()
    btn_info = telebot.types.InlineKeyboardButton("📋 اطلاعات کاربران", callback_data="user_info")
    markup.add(btn_info)
    bot.send_message(message.chat.id, "پنل مدیریت 🛠️", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "user_info")
def send_user_info(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "شما دسترسی ندارید.")
        return

    cursor.execute('SELECT * FROM users')
    rows = cursor.fetchall()

    if not rows:
        bot.send_message(call.message.chat.id, "هیچ کاربری ثبت نشده.")
        return

    text = "📄 لیست کاربران:\n\n"
    for row in rows:
        uid, name, phone = row
        text += f"🆔 {uid}\n👤 {name}\n📞 {phone}\n\n"

    bot.send_message(call.message.chat.id, text)

bot.infinity_polling()
