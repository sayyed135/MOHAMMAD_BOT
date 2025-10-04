from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
)

# توکن و آیدی مدیر
TOKEN = "7961151930:AAGiq4-yqNpMc3aZ1F1k8DpNqjHqFKmpxyY"
ADMIN_ID = 6994772164  # آیدی عددی تو

# دیتای کاربران
users = {}

# /start
async def start(update: Update, context: CallbackContext):
    keyboard = [
        [KeyboardButton("Verify Identity", request_contact=True)]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Welcome! Please verify your identity.", reply_markup=reply_markup)

# گرفتن شماره تلفن
async def contact_handler(update: Update, context: CallbackContext):
    user = update.message.from_user
    phone = update.message.contact.phone_number
    users[user.id] = {
        "name": user.first_name,
        "phone": phone,
        "points": users.get(user.id, {}).get("points", 0)
    }
    await update.message.reply_text("✅ Your identity has been verified!")

# دکمه مدیریت
async def management(update: Update, context: CallbackContext):
    if update.message.from_user.id == ADMIN_ID:
        if not users:
            await update.message.reply_text("No users registered yet.")
            return
        text = "📊 Users Stats:\n\n"
        for uid, info in users.items():
            text += f"👤 ID: {uid}\n📞 Phone: {info['phone']}\n⭐ Points: {info['points']}\n\n"
        await update.message.reply_text(text)
    else:
        await update.message.reply_text("⛔ You are not authorized!")

# پاسخ به پیام خاص
async def message_handler(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "علی خوبی":
        await update.message.reply_text("خوبم داداش، تو چطوری؟ 😊")

# دستور برای مدیر
async def admin_panel(update: Update, context: CallbackContext):
    if update.message.from_user.id == ADMIN_ID:
        keyboard = [[InlineKeyboardButton("📊 MANAGEMENT", callback_data="management")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Admin Panel:", reply_markup=reply_markup)

# کلیک روی دکمه مدیریت
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == "management":
        if not users:
            await query.edit_message_text("No users registered yet.")
            return
        text = "📊 Users Stats:\n\n"
        for uid, info in users.items():
            text += f"👤 ID: {uid}\n📞 Phone: {info['phone']}\n⭐ Points: {info['points']}\n\n"
        await query.edit_message_text(text)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
