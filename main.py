# main.py — QuantumEdge🧩 (clean rewrite, TASK removed)
# Webhook preset for: https://code-ai-0alo.onrender.com/<TOKEN>
# Requirements: pyTelegramBotAPI, Flask, requests

import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
from datetime import datetime, timedelta
import json, os, traceback, requests, time

# ========== CONFIG ==========
TOKEN = "8207757951:AAHpvqWfbtlZtyigTGN_MYOxZ408u3Q5rgs"   # حتماً چک کن
ADMIN_ID = 6994772164
WEBHOOK_URL = "https://code-ai-0alo.onrender.com/" + TOKEN
DATA_FILE = "accounts.json"
# ============================

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# ---------- DATA INIT ----------
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"users": {}}, f, ensure_ascii=False, indent=2)

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

DATA = load_data()

# ---------- CONSTANTS ----------
CRYPTO_LIST = ["Bitcoin", "Tuncoin", "Tether", "Euro"]
CRYPTO_PRICE = {"Bitcoin":3.0, "Tuncoin":0.5, "Tether":1.0, "Euro":2.0}

# ---------- PENDING (flow control) ----------
# key: chat_id (int) -> {"action": str, "meta": dict}
PENDING = {}

# ---------- HELPERS ----------
def ensure_user(uid, first_name=None):
    k = str(uid)
    if k not in DATA["users"]:
        DATA["users"][k] = {
            "name": first_name or "",
            "phone": None,
            "credit": 0.0,
            "crypto": {c:0.0 for c in CRYPTO_LIST},
            "last_bonus": None,
            "history": []
        }
        save_data(DATA)
    return DATA["users"][k]

def safe_send(uid, text, reply_markup=None):
    try:
        bot.send_message(int(uid), text, reply_markup=reply_markup)
        return True
    except Exception:
        return False

# ---------- KEYBOARDS (simple reply keyboards) ----------
def admin_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("مشاهده لیست کاربران", "ارسال همگانی")
    kb.add("ارسال پیام به یک کاربر", "مشاهده موجودی کل کاربران")
    kb.add("بازگشت")
    return kb

def user_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("حساب من", "مشاهده کریدت")
    kb.add("دریافت کریدت روزانه", "مشاهده موجودی ارز")
    kb.add("خرید ارز", "فروش ارز")
    kb.add("INFORMATION", "تاریخچه")
    kb.add("ارسال پیام به مدیر")
    return kb

def crypto_buy_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for c in CRYPTO_LIST:
        kb.add(f"خرید {c} ({CRYPTO_PRICE[c]} کریدت)")
    kb.add("بازگشت")
    return kb

def crypto_sell_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for c in CRYPTO_LIST:
        kb.add(f"فروش {c}")
    kb.add("بازگشت")
    return kb

# ---------- START / CONTACT ----------
@bot.message_handler(commands=["start"])
def cmd_start(m):
    ensure_user(m.chat.id, m.from_user.first_name)
    if m.chat.id == ADMIN_ID:
        bot.send_message(m.chat.id, "پنل مدیریت فعال شد.", reply_markup=admin_keyboard())
    else:
        bot.send_message(m.chat.id, "خوش اومدی به QuantumEdge🧩 — از منو استفاده کن.", reply_markup=user_keyboard())

@bot.message_handler(content_types=["contact"])
def handle_contact(m):
    try:
        u = ensure_user(m.chat.id, m.from_user.first_name)
        if m.contact and m.contact.phone_number:
            u["phone"] = m.contact.phone_number
            u["history"].append(f"{datetime.now()} - ثبت شماره: {u['phone']}")
            save_data(DATA)
            bot.send_message(m.chat.id, "شماره ثبت شد.", reply_markup=user_keyboard())
        else:
            bot.send_message(m.chat.id, "شماره معتبر نیست. دوباره تلاش کن.", reply_markup=user_keyboard())
    except Exception:
        bot.send_message(m.chat.id, "خطا در ثبت شماره.", reply_markup=user_keyboard())

# ---------- USER MESSAGE HANDLER ----------
@bot.message_handler(func=lambda m: True)
def handle_text(m):
    try:
        uid = m.chat.id
        txt = (m.text or "").strip()

        # admin routed separately
        if uid == ADMIN_ID:
            return handle_admin(m, txt)

        # ensure user
        ensure_user(uid, m.from_user.first_name)
        user = DATA["users"][str(uid)]

        # if waiting for user->admin text
        pend = PENDING.get(uid)
        if pend and pend.get("action") == "user_prepare_message_to_admin":
            # store text then ask for confirm (yes/no via inline)
            text = txt
            PENDING[uid] = {"action":"user_prepare_message_to_admin", "meta":{"text": text}}
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("✅ بله — پرداخت 1 کریدت و ارسال", callback_data="user_confirm_send"))
            kb.add(InlineKeyboardButton("❌ انصراف", callback_data="user_cancel_send"))
            bot.send_message(uid, f"آیا با پرداخت 1 کریدت مایل به ارسال پیام به مدیر هستید؟\n\nمتن:\n{text}", reply_markup=kb)
            return

        # user commands
        if txt == "حساب من":
            bot.send_message(uid, f"نام: {user.get('name','')}\nشماره: {user.get('phone')}\nکریدت: {user.get('credit',0)}", reply_markup=user_keyboard())
            return

        if txt == "مشاهده کریدت":
            bot.send_message(uid, f"کریدت شما: {user.get('credit',0)}", reply_markup=user_keyboard())
            return

        if txt == "دریافت کریدت روزانه":
            last = user.get("last_bonus")
            now = datetime.now()
            if last:
                try:
                    last_dt = datetime.fromisoformat(last)
                    if now - last_dt < timedelta(days=1):
                        bot.send_message(uid, "شما امروز کریدت گرفتید. فردا دوباره.", reply_markup=user_keyboard())
                        return
                except:
                    pass
            user["credit"] = float(user.get("credit",0)) + 1.0
            user["last_bonus"] = now.isoformat()
            user["history"].append(f"{now} - دریافت 1 کریدت روزانه")
            save_data(DATA)
            bot.send_message(uid, "۱ کریدت روزانه اضافه شد.", reply_markup=user_keyboard())
            return

        if txt == "مشاهده موجودی ارز":
            bot.send_message(uid, "موجودی شما:\n" + "\n".join([f"{c}: {user['crypto'].get(c,0)}" for c in CRYPTO_LIST]), reply_markup=user_keyboard())
            return

        if txt == "خرید ارز":
            bot.send_message(uid, "کدام ارز؟", reply_markup=crypto_buy_kb())
            return

        if txt == "فروش ارز":
            bot.send_message(uid, "کدام ارز؟", reply_markup=crypto_sell_kb())
            return

        if txt.startswith("خرید "):
            parts = txt.split()
            if len(parts) >= 2:
                crypto = parts[1]
                if crypto in CRYPTO_PRICE:
                    price = float(CRYPTO_PRICE[crypto])
                    if float(user.get("credit",0)) >= price:
                        user["credit"] = float(user.get("credit",0)) - price
                        user["crypto"][crypto] = float(user["crypto"].get(crypto,0)) + 1.0
                        user["history"].append(f"{datetime.now()} - خرید 1 {crypto} ({price} کریدت)")
                        save_data(DATA)
                        bot.send_message(uid, f"خرید موفق: 1 {crypto}. {price} کریدت کم شد.", reply_markup=user_keyboard())
                    else:
                        bot.send_message(uid, f"کریدت کافی نیست. نیاز به {price} کریدت.", reply_markup=user_keyboard())
                else:
                    bot.send_message(uid, "ارز نامشخص.", reply_markup=user_keyboard())
            return

        if txt.startswith("فروش "):
            parts = txt.split()
            if len(parts) >= 2:
                crypto = parts[1]
                if crypto in CRYPTO_PRICE:
                    if float(user["crypto"].get(crypto,0)) >= 1.0:
                        user["crypto"][crypto] = float(user["crypto"].get(crypto,0)) - 1.0
                        user["credit"] = float(user.get("credit",0)) + float(CRYPTO_PRICE[crypto])
                        user["history"].append(f"{datetime.now()} - فروش 1 {crypto} ({CRYPTO_PRICE[crypto]} کریدت اضافه)")
                        save_data(DATA)
                        bot.send_message(uid, f"فروش موفق: 1 {crypto}. {CRYPTO_PRICE[crypto]} کریدت اضافه شد.", reply_markup=user_keyboard())
                    else:
                        bot.send_message(uid, "موجودی کافی ندارید.", reply_markup=user_keyboard())
                else:
                    bot.send_message(uid, "ارز نامشخص.", reply_markup=user_keyboard())
            return

        if txt == "INFORMATION":
            info = (
                "ربات: QuantumEdge🧩\n"
                "سیستم کریدت و مدیریت ساده.\n"
                "هر ۲۰ کریدت = ۵ کریدت واقعی.\n"
                "ساخته شده توسط تیم SMMH_TEAM"
            )
            bot.send_message(uid, info, reply_markup=user_keyboard())
            return

        if txt == "تاریخچه":
            hist = user.get("history", [])[-10:]
            bot.send_message(uid, "\n".join(hist) if hist else "تاریخچه‌ای وجود ندارد.", reply_markup=user_keyboard())
            return

        if txt == "ارسال پیام به مدیر":
            # start flow: user writes message, then confirm with inline (handled above)
            PENDING[uid] = {"action":"user_prepare_message_to_admin"}
            bot.send_message(uid, "پیامت را بنویس (بعد از ارسال، گزینه تأیید نمایش داده می‌شود).", reply_markup=None)
            return

        # fallback
        bot.send_message(uid, "لطفاً گزینه‌ای از منو انتخاب کن.", reply_markup=user_keyboard())

    except Exception:
        traceback.print_exc()
        try:
            bot.send_message(m.chat.id, "خطا در پردازش پیام. دوباره تلاش کن.", reply_markup=user_keyboard())
        except:
            pass

# ---------- ADMIN HANDLER ----------
def handle_admin(m, txt):
    uid = m.chat.id
    txt = (txt or "").strip()

    if txt == "پنل مدیریت":
        bot.send_message(uid, "پنل مدیریت:", reply_markup=admin_keyboard())
        return

    if txt == "مشاهده لیست کاربران":
        lines = []
        for k,v in DATA["users"].items():
            lines.append(f"{k} — {v.get('name','')} — {v.get('phone','')}")
        bot.send_message(uid, "\n".join(lines) if lines else "هیچ کاربری ثبت نشده.", reply_markup=admin_keyboard())
        return

    if txt == "ارسال همگانی":
        bot.send_message(uid, "متن پیام همگانی را ارسال کن:", reply_markup=None)
        PENDING[uid] = {"action":"admin_broadcast"}
        return

    if txt == "ارسال پیام به یک کاربر":
        kb = InlineKeyboardMarkup(row_width=1)
        for k,v in DATA["users"].items():
            display = f"{v.get('name','')} — {k}"
            kb.add(InlineKeyboardButton(display, callback_data=f"admin_select_user|{k}"))
        kb.add(InlineKeyboardButton("انصراف", callback_data="admin_select_cancel"))
        bot.send_message(uid, "روی اسم کاربر بزن تا براش پیام بفرستی (یا انصراف).", reply_markup=kb)
        return

    if txt == "مشاهده موجودی کل کاربران":
        lines = []
        for k,v in DATA["users"].items():
            crypt = ", ".join([f"{c}:{v['crypto'].get(c,0)}" for c in CRYPTO_LIST])
            lines.append(f"{k} — {v.get('name','')} — کریدت:{v.get('credit',0)} — {crypt}")
        bot.send_message(uid, "\n".join(lines) if lines else "هیچ کاربری ثبت نشده.", reply_markup=admin_keyboard())
        return

    if txt == "بازگشت":
        bot.send_message(uid, "بازگشت به منوی اصلی.", reply_markup=admin_keyboard())
        return

    # pending admin actions
    if uid in PENDING:
        act = PENDING.pop(uid)
        if act["action"] == "admin_broadcast":
            text = txt
            ok = fail = 0
            for k in list(DATA["users"].keys()):
                try:
                    bot.send_message(int(k), f"📣 پیام همگانی از مدیر:\n\n{text}")
                    ok += 1
                except:
                    fail += 1
            bot.send_message(uid, f"ارسال همگانی انجام شد — موفق: {ok} — ناموفق: {fail}", reply_markup=admin_keyboard())
            return
        if act["action"] == "admin_send_to_user":
            target = act["meta"]["target"]
            ok = safe_send(target, f"📨 پیام از مدیر:\n\n{txt}")
            if ok:
                kb = ReplyKeyboardMarkup(resize_keyboard=True)
                kb.add("قطع چت")
                kb.add("بازگشت")
                bot.send_message(ADMIN_ID, f"پیام به {target} ارسال شد.", reply_markup=kb)
            else:
                bot.send_message(ADMIN_ID, f"ارسال به {target} ناموفق بود.", reply_markup=admin_keyboard())
            return

    bot.send_message(uid, "از منوی مدیریت استفاده کن.", reply_markup=admin_keyboard())

# ---------- INLINE CALLBACKS ----------
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        uid = call.from_user.id
        data = call.data

        # user confirm send to admin
        if data == "user_confirm_send":
            pend = PENDING.get(uid)
            if not pend or pend.get("action") != "user_prepare_message_to_admin":
                bot.answer_callback_query(call.id, "مسیر ارسال نامعتبر است.")
                return
            user = DATA["users"].get(str(uid))
            if not user:
                bot.answer_callback_query(call.id, "ابتدا شماره ثبت کن.")
                PENDING.pop(uid, None)
                return
            text = pend["meta"]["text"]
            if float(user.get("credit",0)) < 1.0:
                bot.answer_callback_query(call.id, "کریدت کافی نداری!", show_alert=True)
                PENDING.pop(uid, None)
                return
            # deduct & send
            user["credit"] = float(user.get("credit",0)) - 1.0
            now = datetime.now()
            user["history"].append(f"{now} - پرداخت 1 کریدت و ارسال پیام به مدیر")
            save_data(DATA)
            meta = f"📩 پیام از {user.get('name','')} ({user.get('phone','')})\nزمان: {now}\n\n{str(text)}"
            bot.send_message(ADMIN_ID, meta)
            bot.send_message(uid, "پیام با موفقیت به مدیر ارسال شد.", reply_markup=user_keyboard())
            PENDING.pop(uid, None)
            bot.answer_callback_query(call.id, "ارسال شد")
            return

        if data == "user_cancel_send":
            # cancel user pending and return to menu
            PENDING.pop(uid, None)
            bot.send_message(uid, "ارسال لغو شد.", reply_markup=user_keyboard())
            bot.answer_callback_query(call.id, "لغو شد")
            return

        # admin selecting user
        if data.startswith("admin_select_user|"):
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "فقط مدیر می‌تواند این کار را انجام دهد.")
                return
            target = data.split("|",1)[1]
            # set pending so next admin message will be sent to target
            PENDING[ADMIN_ID] = {"action":"admin_send_to_user", "meta":{"target": target}}
            bot.send_message(ADMIN_ID, f"پیام خود را بنویس تا برای کاربر {target} ارسال کنم.")
            bot.answer_callback_query(call.id, "متن را ارسال کن.")
            return

        if data == "admin_select_cancel":
            bot.edit_message_text("انصراف ثبت شد.", call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, "انصراف")
            return

        bot.answer_callback_query(call.id, "عملیات نامشخص.")
    except Exception:
        traceback.print_exc()
        try:
            bot.answer_callback_query(call.id, "خطا در پردازش درخواست.")
        except:
            pass

# ---------- ADMIN PENDING PROCESSOR (separate) ----------
@bot.message_handler(func=lambda m: True)
def admin_pending_processor(m):
    uid = m.chat.id
    txt = (m.text or "").strip()

    # admin pending actions handled in handle_admin above via PENDING entries
    # Here we also handle admin "قطع چت"
    if uid == ADMIN_ID and txt == "قطع چت":
        bot.send_message(ADMIN_ID, "چت قطع شد — برگشت به پنل مدیریت.", reply_markup=admin_keyboard())
        return

    # otherwise do nothing here; main handlers already manage flows
    return

# ---------- WEBHOOK (Flask) ----------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        upd = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
        bot.process_new_updates([upd])
    except Exception:
        traceback.print_exc()
    return "ok", 200

@app.route("/")
def index():
    return "QuantumEdge🧩 bot is running", 200

def set_webhook():
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")
        print("Webhook set:", WEBHOOK_URL)
    except Exception as e:
        print("Failed to set webhook:", e)

# ---------- RUN ----------
if __name__ == "__main__":
    # set webhook if WEBHOOK_URL configured; otherwise fall back to polling for local testing
    if "your-render-app" in WEBHOOK_URL or WEBHOOK_URL.strip() == "":
        print("WEBHOOK placeholder — running with polling.")
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    else:
        set_webhook()
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
