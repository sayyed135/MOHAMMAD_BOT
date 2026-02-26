import os
from openai import AsyncOpenAI
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# ===== تنظیمات =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-domain.com/webhook")

if not BOT_TOKEN or not OPENAI_API_KEY:
    raise ValueError("BOT_TOKEN or OPENAI_API_KEY not set")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)
app = FastAPI()
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# ===== پاسخ هوش مصنوعی =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": user_text}
            ]
        )
        reply = response.choices[0].message.content
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"خطا: {str(e)}")

telegram_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)

# ===== Webhook =====
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}

@app.on_event("startup")
async def startup():
    await telegram_app.bot.set_webhook(WEBHOOK_URL)