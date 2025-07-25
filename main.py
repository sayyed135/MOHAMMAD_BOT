import os
import sqlite3
from flask import Flask, request
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = '7217912729:AAGXxp8wDSX1dSpWrRw5RhAY8zDIV1QLvIo'  # توکن جدیدت
WEBHOOK_URL = 'https://mohammad-bot-2.onrender.com'  # آدرس ربات روی Render
ADMIN_ID = 6994772164  # آیدی مدیر جدید

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DB_PATH = "bot_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        in_chat INTEGER DEFAULT 0,
        partner_id INTEGER,
        score INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS blocks (
        user_id INTEGER,
        blocked_user_id INTEGER,
        PRIMARY KEY(user_id, blocked_user_id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS reports (
        reporter_id INTEGER,
        reported_id INTEGER,
        reason TEXT
    )''')
    conn.commit()
    conn.close()

def db_connect():
    return sqlite3.connect(DB_PATH)

def add_user_if_not_exists(user_id, username):
    conn = db_connect()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users(user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def set_in_chat(user_id, partner_id):
    conn = db_connect()
    c = conn.cursor()
    c.execute("UPDATE users SET in_chat=1, partner_id=? WHERE user_id=?", (partner_id, user_id))
    conn.commit()
    conn.close()

def set_not_in_chat(user_id):
    conn = db_connect()
    c = conn.cursor()
    c.execute("UPDATE users SET in_chat=0, partner_id=NULL WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def get_partner(user_id):
    conn = db_connect()
    c = conn.cursor()
    c.execute("SELECT partner_id FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else None

def block_user(user_id, blocked_user_id):
    conn = db_connect()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO blocks(user_id, blocked_user_id) VALUES (?, ?)", (user_id, blocked_user_id))
    conn.commit()
    conn.close()

def is_blocked(user1, user2):
    conn = db_connect()
    c = conn.cursor()
    c.execute("SELECT 1 FROM blocks WHERE user_id=? AND blocked_user_id=?", (user1, user2))
    res = c.fetchone()
    conn.close()
    return res is not None

def add_report(reporter_id, reported_id, reason):
    conn = db_connect()
    c = conn.cursor()
    c.execute("INSERT INTO reports(reporter_id, reported_id, reason) VALUES (?, ?, ?)", (reporter_id, reported_id, reason))
    conn.commit()
    conn.close()

def get_score(user_id):
    conn = db_connect()
    c = conn.cursor()
    c.execute("SELECT score FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else 0

def update_score(user_id, delta):
    conn = db_connect()
    c = conn.cursor()
    c.execute("UPDATE users SET score = score + ? WHERE user_id=?", (delta, user_id))
    conn.commit()
    conn.close()

def set_score(user_id, score):
    conn = db_connect()
    c = conn.cursor()
    c.execute("UPDATE users SET score = ? WHERE user_id=?", (score, user_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = db_connect()
    c = conn.cursor()
    c.execute("SELECT user_id, username, score, in_chat FROM users")
    res = c.fetchall()
    conn.close()
    return res

def disconnect_chat(user_id):
    partner = get_partner(user_id)
    if partner:
        set_not_in_chat(user_id)
        set_not_in_chat(partner)
        return partner
    return None

def user_menu(in_chat):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if in_chat:
        kb.row(KeyboardButton("❌ قطع چت"), KeyboardButton("🚫 بلاک"), KeyboardButton("📢 گزارش"))
    else:
        kb.row(KeyboardButton("🎭 شروع چت ناشناس"))
    return kb

def admin_main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("مدیریت"))
    return kb

def admin_panel():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("📊 آمار کاربران"), KeyboardButton("👥 مدیریت چت‌ها"))
    kb.row(KeyboardButton("⚙️ تنظیم امتیاز کاربران"))
    kb.row(KeyboardButton("🔐 خروج از مدیریت"))
    return kb

def report_reasons():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("اسپم"))
    kb.row(KeyboardButton("رفتار نامناسب"))
    kb.row(KeyboardButton("کلمات توهین‌آمیز"))
    kb.row(KeyboardButton("اخلال در چت"))
    kb.row(KeyboardButton("لغو گزارش"))
    return kb

@bot.message_handler(commands=['start'])
def start_handler(m):
    add_user_if_not_exists(m.chat.id, m.from_user.username)
    if m.chat.id == ADMIN_ID:
        bot.send_message(m.chat.id, "سلام مدیر عزیز!", reply_markup=admin_main_menu())
    else:
        bot.send_message(m.chat.id, "سلام! به چت ناشناس خوش آمدی.", reply_markup=user_menu(False))

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.text == "مدیریت")
def admin_panel_handler(m):
    bot.send_message(m.chat.id, "پنل مدیریت باز شد.", reply_markup=admin_panel())

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.text == "📊 آمار کاربران")
def admin_stats(m):
    users = get_all_users()
    txt = "📊 آمار کاربران:\n"
    for u in users:
        txt += f"ID: {u[0]} - Username: {u[1]} - امتیاز: {u[2]} - در چت: {'بله' if u[3] else 'خیر'}\n"
    bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.text == "⚙️ تنظیم امتیاز کاربران")
def admin_score_set_start(m):
    bot.send_message(m.chat.id, "آی‌دی کاربری که می‌خواهید امتیازش را تغییر دهید را بفرستید:")

    @bot.message_handler(func=lambda mm: mm.chat.id == ADMIN_ID and mm.text.isdigit())
    def admin_receive_user_id(msg):
        user_id = int(msg.text)
        bot.send_message(msg.chat.id, "مقدار امتیاز جدید را (مثبت یا منفی) وارد کنید:")

        @bot.message_handler(func=lambda mmm: mmm.chat.id == ADMIN_ID)
        def admin_receive_score(msg_score):
            try:
                delta = int(msg_score.text)
                update_score(user_id, delta)
                bot.send_message(msg_score.chat.id, f"امتیاز کاربر {user_id} به اندازه {delta} تغییر کرد.")
            except Exception as e:
                bot.send_message(msg_score.chat.id, "مقدار نامعتبر است.")
            bot.register_next_step_handler_by_chat_id(msg_score.chat.id, admin_score_set_start)

@bot.message_handler(func=lambda m: m.chat.id != ADMIN_ID)
def user_text_handler(m):
    add_user_if_not_exists(m.chat.id, m.from_user.username)
    user = m.chat.id

    conn = db_connect()
    c = conn.cursor()
    c.execute("SELECT in_chat FROM users WHERE user_id=?", (user,))
    in_chat = c.fetchone()[0]
    conn.close()

    if m.text == "🎭 شروع چت ناشناس" and not in_chat:
        conn = db_connect()
        c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE in_chat=0")
        waiting = [row[0] for row in c.fetchall()]
        conn.close()

        for uid in waiting:
            if uid != user and not is_blocked(uid, user) and not is_blocked(user, uid):
                set_in_chat(user, uid)
                set_in_chat(uid, user)
                bot.send_message(user, "✅ متصل شدید. حالا می‌توانید چت کنید.", reply_markup=user_menu(True))
                bot.send_message(uid, "✅ متصل شدید. حالا می‌توانید چت کنید.", reply_markup=user_menu(True))
                return
        bot.send_message(user, "منتظر اتصال به کاربر دیگر هستید...", reply_markup=user_menu(False))
    elif in_chat:
        partner = get_partner(user)
        if m.text == "❌ قطع چت":
            partner = disconnect_chat(user)
            if partner:
                bot.send_message(partner, "🔌 چت توسط طرف مقابل قطع شد.", reply_markup=user_menu(False))
            bot.send_message(user, "🔌 چت پایان یافت.", reply_markup=user_menu(False))
        elif m.text == "🚫 بلاک":
            partner = get_partner(user)
            if partner:
                block_user(user, partner)
                disconnect_chat(user)
                bot.send_message(user, "🚫 کاربر بلاک شد و چت پایان یافت.", reply_markup=user_menu(False))
            else:
                bot.send_message(user, "شما در چت نیستید.", reply_markup=user_menu(False))
        elif m.text
