import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "7217912729:AAG0fXedfzX59DuvMHmHky2RS3JiMxlB7II"
ADMIN_ID = 6994772164  # آیدی عددی مدیر را اینجا بگذار

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    if message.from_user.id == ADMIN_ID:
        markup.add(InlineKeyboardButton("🔧 مدیریت", callback_data="admin_menu"))
    markup.add(
        InlineKeyboardButton("🛒 خرید اشتراک", callback_data="buy_sub"),
        InlineKeyboardButton("ℹ️ اطلاعات من", callback_data="my_info")
    )
    bot.send_message(message.chat.id, "Welcome! Choose an option:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "admin_menu":
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "این بخش فقط برای مدیر است.")
            return
        admin_markup = InlineKeyboardMarkup()
        admin_markup.add(
            InlineKeyboardButton("👤 کاربران", callback_data="users"),
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings"),
            InlineKeyboardButton("💎 اشتراک", callback_data="subscriptions")
        )
        bot.edit_message_text("مدیریت:", call.message.chat.id, call.message.message_id, reply_markup=admin_markup)

    elif call.data == "buy_sub":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "💳 برای خرید اشتراک با مدیر در ارتباط باشید.")

    elif call.data == "my_info":
        user = call.from_user
        info = f"👤 Name: {user.first_name}\n"
        if user.last_name:
            info += f"🧾 Last Name: {user.last_name}\n"
        if user.username:
            info += f"📛 Username: @{user.username}\n"
        info += f"🆔 ID: {user.id}"
        bot.send_message(call.message.chat.id, info)

    elif call.data == "users":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📋 لیست کاربران به‌زودی اضافه می‌شود.")

    elif call.data == "settings":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "⚙️ تنظیمات در حال توسعه است.")

    elif call.data == "subscriptions":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "💎 بخش اشتراک هنوز کامل نشده.")

if __name__ == "__main__":
    print("Bot running...")
    bot.infinity_polling()
