# main.py — برای وب‌هوک روی Render  
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
from datetime import datetime, timedelta
import json, os, traceback, requests

# ---------------- CONFIG ----------------
TOKEN = "8207757951:AAHpvqWfbtlZtyigTGN_MYOxZ408u3Q5rgs"  
ADMIN_ID = 6994772164
WEBHOOK_URL = "https://code-ai-0alo.onrender.com/" + TOKEN
DATA_FILE = "accounts.json"
POLL_THRESHOLD = 10
# ----------------------------------------

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"users": {}, "task_link": "", "polls": {}},
                  f, ensure_ascii=False, indent=2)

def load(): return json.load(open(DATA_FILE, "r", encoding="utf-8"))
def save(d): json.dump(d, open(DATA_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

DATA = load()

CRYPTO_LIST = ["Bitcoin", "Tuncoin", "Tether", "Euro"]
CRYPTO_PRICE = {"Bitcoin":3.0, "Tuncoin":0.5, "Tether":1.0, "Euro":2.0}
PENDING = {}

def ensure_user(uid, first_name=None):
    key = str(uid)
    if key not in DATA["users"]:
        DATA["users"][key] = {
            "name": first_name or "",
            "phone": None,
            "credit": 0.0,
            "crypto": {c:0.0 for c in CRYPTO_LIST},
            "last_bonus": None,
            "history": [],
            "tasks_seen": ""
        }
        save(DATA)
    return DATA["users"][key]

def admin_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("مشاهده کاربران", "مشاهده موجودی همه")
    kb.add("ارسال همگانی", "ارسال پیام به کاربران")
    kb.add("ایجاد نظر سنجی", "بروزرسانی TASK لینک")
    kb.add("آمار کامل فعالیت کاربران", "راهنما")
    kb.add("بازگشت")
    return kb

def user_panel():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("مشاهده کریدت", "دریافت کریدت روزانه")
    kb.add("مشاهده موجودی ارز", "خرید ارز")
    kb.add("فروش ارز", "TASKS")
    kb.add("INFORMATION", "تاریخچه")
    kb.add("ارسال پیام به مدیر")
    return kb

def main_keyboard(uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if uid == ADMIN_ID:
        kb.add("پنل مدیریت")
    else:
        u = DATA["users"].get(str(uid))
        if u and u.get("phone"):
            kb.add("حساب من", "خرید ارز")
            kb.add("فروش ارز", "TASKS")
            kb.add("INFORMATION", "تاریخچه")
            kb.add("ارسال پیام به مدیر")
        else:
            kb.add(KeyboardButton("ارسال شماره", request_contact=True))
    return kb

def crypto_buy_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for c in CRYPTO_LIST: kb.add(f"خرید {c} ({CRYPTO_PRICE[c]} کریدت)")
    kb.add("بازگشت")
    return kb

def crypto_sell_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for c in CRYPTO_LIST: kb.add(f"فروش {c}")
    kb.add("بازگشت")
    return kb

@bot.message_handler(commands=["start"])
def start_cmd(m):
    ensure_user(m.chat.id, m.from_user.first_name)
    if m.chat.id == ADMIN_ID:
        bot.send_message(m.chat.id, "پنل مدیریت فعال شد:", reply_markup=admin_keyboard())
    else:
        bot.send_message(m.chat.id, "Welcome to QuantumEdge🧩", reply_markup=main_keyboard(m.chat.id))

@bot.message_handler(content_types=["contact"])
def contact_handler(m):
    u = ensure_user(m.chat.id, m.from_user.first_name)
    u["phone"] = m.contact.phone_number
    u["history"].append(f"{datetime.now()} - ثبت شماره: {u['phone']}")
    save(DATA)
    bot.send_message(m.chat.id, "شماره ثبت شد.", reply_markup=user_panel())

@bot.message_handler(func=lambda m: True)
def on_text(m):
    uid = m.chat.id
    txt = (m.text or "").strip()
    if uid == ADMIN_ID:
        return handle_admin_text(m, txt)

    user = ensure_user(uid, m.from_user.first_name)
    pend = PENDING.get(uid)

    if pend and pend.get("action") == "user_prepare_message_to_admin":
        text = txt
        PENDING[uid] = {"action":"user_prepare_message_to_admin", "meta":{"text":text}}
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("✅ بله — ارسال + 1 کریدت", callback_data="user_send_admin_confirm"))
        kb.add(InlineKeyboardButton("❌ انصراف", callback_data="user_send_admin_cancel"))
        bot.send_message(uid, f"آیا مایلید پیام زیر با پرداخت 1 کریدت به مدیر ارسال شود؟\n\n{text}", reply_markup=kb)
        return

    if txt == "ارسال پیام به مدیر":
        bot.send_message(uid, "پیام خود را بنویسید:", reply_markup=None)
        PENDING[uid] = {"action":"user_prepare_message_to_admin"}
        return

    # ... بقیه logic هم مثل نسخه قبلی ادامه داره ...
    bot.send_message(uid, "از منو انتخاب کن.", reply_markup=main_keyboard(uid))

# ---------- inline & admin callbacks + بقیه کد مثل قبل ----------

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode("utf-8"))])
    return "ok", 200

@app.route("/")
def index():
    return "QuantumEdge🧩 bot running", 200

def set_webhook():
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")
        print("Webhook set:", WEBHOOK_URL)
    except Exception as e:
        print("Webhook failed:", e)

if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
