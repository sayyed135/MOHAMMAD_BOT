import os
import openai
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# ===== تنظیمات =====
BOT_TOKEN = "8271476264:AAHztmtKuFZ-ou-JTr3_wNNRaacvUzgsOnc"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

app = FastAPI()
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# ===== پاسخ هوش مصنوعی =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": user_text}
            ]
        )

        reply = response.choices[0].message.content
        await update.message.reply_text(reply)

    except Exception:
        await update.message.reply_text("خطا در اتصال به هوش مصنوعی!")

telegram_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)

# ===== Webhook Route =====
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}

# ===== راه‌اندازی =====
@app.on_event("startup")
async def startup():
    webhook_url = "https://chatgpt-telegram-bkp1.onrender.com/webhook"
    await telegram_app.bot.set_webhook(webhook_url)
