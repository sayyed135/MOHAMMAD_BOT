‌from flask import Flask, request
import requests
import os
from openai import OpenAI

app = Flask(__name__)

# گرفتن توکن و کلید از Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_KEY")

client = OpenAI(api_key=OPENAI_KEY)

# صفحه اصلی برای تست
@app.route("/")
def home():
    return "AI Bot is Running"

# Webhook تلگرام
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.get_json()

    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"]["text"]

        try:
            # درخواست به OpenAI
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": user_text}
                ]
            )
            ai_reply = response.choices[0].message.content
        except Exception:
            ai_reply = "خطا در ارتباط با هوش مصنوعی."

        # ارسال پاسخ به تلگرام
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": ai_reply
            }
        )

    return "ok", 200
