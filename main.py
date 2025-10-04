import json
import os
from datetime import datetime, timedelta
from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
)

TOKEN = "7961151930:AAGiq4-yqNpMc3aZ1F1k8DpNqjHqFKmpxyY"
ADMIN_ID = 6994772164
DATA_FILE = "data.json"

# بارگذاری داده‌ها
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {"users": {}, "settings": {"language": "EN", "daily_points": 1, "daily_time": 24}}

# ذخیره داده‌ها
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ساخت کیبورد کاربر
def user_keyboard():
    kb = [
        [KeyboardButton("Verify Identity", request_contact=True)],
        ["Daily Points", "Support"],
        ["Subscription", "Guide"]
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

# /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Welcome! Please choose an option.", reply_markup=user_keyboard()
    )

# گرفتن شماره تلفن
async def contact_handler(update: Update, context: CallbackContext):
    user = update.message.from_user
    phone = update.message.contact.phone_number
    if str(user.id) not in data["users"]:
        data["users"][str(user.id)] = {
            "name": user.first_name,
            "phone": phone,
            "points": 0,
            "subscription": None,
            "referrals": [],
            "last_daily": None
        }
    else:
        data["users"][str(user.id)]["phone"] = phone
    save_data()
    await update.message.reply_text("✅ Your identity has been verified!")

# Daily Points
async def daily_points(update: Update, context: CallbackContext):
    uid = str(update.message.from_user.id)
    if uid not in data["users"]:
        await update.message.reply_text("❌ You must verify first.")
        return
    last = data["users"][uid].get("last_daily")
    now = datetime.now()
    allowed_time = timedelta(hours=data["settings"]["daily_time"])
    if last:
        last_time = datetime.fromisoformat(last)
        if now - last_time < allowed_time:
            await update.message.reply_text("⏳ You have already claimed your daily points.")
            return
    data["users"][uid]["points"] += data["settings"]["daily_points"]
    data["users"][uid]["last_daily"] = now.isoformat()
    save_data()
    await update.message.reply_text(f"✅ You received {data['settings']['daily_points']} points!")

# Support
async def support(update: Update, context: CallbackContext):
    uid = str(update.message.from_user.id)
    if uid not in data["users"]:
        await update.message.reply_text("❌ Verify first.")
        return
    await update.message.reply_text("✉️ Send your message, it will be forwarded to admin.")
    context.user_data["support"] = True

async def support_message(update: Update, context: CallbackContext):
    uid = str(update.message.from_user.id)
    if context.user_data.get("support"):
        text = update.message.text
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 Support Message from {data['users'][uid]['name']} (ID: {uid}):\n{text}"
        )
        # دکمه قطع ارتباط
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("Disconnect", callback_data=f"disconnect_{uid}")]])
        await context.bot.send_message(chat_id=ADMIN_ID, text="Manage this support chat:", reply_markup=kb)
        await update.message.reply_text("✅ Your message sent to admin.")
        context.user_data["support"] = False

# پنل مدیر
async def admin_panel(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ You are not authorized!")
        return
    kb = [
        [InlineKeyboardButton("📊 MANAGEMENT", callback_data="management")],
        [InlineKeyboardButton("🛠 Settings", callback_data="settings")]
    ]
    await update.message.reply_text("🔐 Admin Panel:", reply_markup=InlineKeyboardMarkup(kb))

# دکمه‌ها
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data_id = query.data

    # مدیریت کاربران
    if data_id == "management":
        text = "📊 Users Stats:\n\n"
        for uid, info in data["users"].items():
            text += f"👤 ID: {uid}\n📞 Phone: {info['phone']}\n⭐ Points: {info['points']}\n🔹 Subs: {len(info['referrals'])}\nSubscription: {info['subscription']}\n\n"
        await query.edit_message_text(text)

    # Settings
    elif data_id == "settings":
        kb = [
            [InlineKeyboardButton("Language: EN/FA", callback_data="toggle_language")],
            [InlineKeyboardButton("Set Daily Points", callback_data="set_daily_points")]
        ]
        await query.edit_message_text("⚙️ Admin Settings:", reply_markup=InlineKeyboardMarkup(kb))

    elif data_id == "toggle_language":
        current = data["settings"]["language"]
        data["settings"]["language"] = "FA" if current == "EN" else "EN"
        save_data()
        await query.edit_message_text(f"Language switched to {data['settings']['language']}")

# پیام راهنما
async def guide(update: Update, context: CallbackContext):
    msg = (
        "📘 Guide / راهنما\n\n"
        "1. Verify Identity: Send your contact.\n"
        "2. Daily Points: Claim your daily points.\n"
        "3. Support: Send messages to admin.\n"
        "4. Subscription: Get benefits with referrals.\n"
        "5. Transfer points to others (future).\n\n"
        "🎯 Full guide will be expanded here for English & Persian..."
    )
    await update.message.reply_text(msg)

# پیام‌های متنی
async def text_handler(update: Update, context: CallbackContext):
    if context.user_data.get("support"):
        await support_message(update, context)
    elif update.message.text == "Daily Points":
        await daily_points(update, context)
    elif update.message.text == "Support":
        await support(update, context)
    elif update.message.text == "Subscription":
        await update.message.reply_text("⚡ Subscription system coming soon...")
    elif update.message.text == "Guide":
        await guide(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
