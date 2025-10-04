import os import sqlite3 from datetime import datetime, date from flask import Flask, request, abort import telebot from telebot import types import threading import requests

TOKEN = os.getenv('TOKEN', '7961151930:AAEMibfYlZJ6hr5Ji9k-3lMY8Hf0ZU0Dvrc') WEB_SERVICE_URL = os.getenv('WEB_SERVICE_URL', 'https://code-ai-0alo.onrender.com') SUPER_ADMIN_ID = int(os.getenv('SUPER_ADMIN_ID', '6994772164')) DB_PATH = os.getenv('DB_PATH', 'bot_data.db') BACKUP_DIR = os.getenv('BACKUP_DIR', 'backups')

bot = telebot.TeleBot(TOKEN, threaded=False) app = Flask(name)

def init_db(): os.makedirs(BACKUP_DIR, exist_ok=True) conn = sqlite3.connect(DB_PATH, check_same_thread=False) cur = conn.cursor() cur.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points_diamond INTEGER DEFAULT 0, points_gold INTEGER DEFAULT 0, points_coin INTEGER DEFAULT 0, last_daily TEXT DEFAULT NULL)''') cur.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''') cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('lang', 'en')") cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('service_link', ?)" , (WEB_SERVICE_URL,)) conn.commit() return conn

conn = init_db() lock = threading.Lock()

def get_setting(key): cur = conn.cursor() cur.execute('SELECT value FROM settings WHERE key=?', (key,)) r = cur.fetchone() return r[0] if r else None

def set_setting(key, value): with lock: cur = conn.cursor() cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, str(value))) conn.commit() backup_db()

def ensure_user(user_id): with lock: cur = conn.cursor() cur.execute('SELECT user_id FROM users WHERE user_id=?', (user_id,)) if not cur.fetchone(): cur.execute('INSERT INTO users (user_id) VALUES (?)', (user_id,)) conn.commit() backup_db()

def add_points(user_id, diamond=0, gold=0, coin=0): with lock: ensure_user(user_id) cur = conn.cursor() cur.execute('''UPDATE users SET points_diamond = points_diamond + ?, points_gold = points_gold + ?, points_coin = points_coin + ? WHERE user_id = ?''', (diamond, gold, coin, user_id)) conn.commit() backup_db()

def get_user_stats(user_id): cur = conn.cursor() cur.execute('SELECT points_diamond, points_gold, points_coin, last_daily FROM users WHERE user_id=?', (user_id,)) r = cur.fetchone() if not r: return (0,0,0,None) return r

def set_last_daily(user_id, iso_date): with lock: cur = conn.cursor() cur.execute('UPDATE users SET last_daily=? WHERE user_id=?', (iso_date, user_id)) conn.commit() backup_db()

def backup_db(): try: ts = datetime.utcnow().strftime('%Y%m%d%H%M%S') backup_file = os.path.join(BACKUP_DIR, f'bot_data_{ts}.db') with open(DB_PATH, 'rb') as src, open(backup_file, 'wb') as dst: dst.write(src.read()) try: files = {'file': open(backup_file, 'rb')} requests.post(WEB_SERVICE_URL.rstrip('/') + '/backup', files=files, timeout=5) except Exception: pass except Exception: pass

TEXTS = { 'en': {'welcome': "Welcome!", 'support': "For support contact: {}", 'daily_already': "You've already taken today's daily point.", 'daily_success': "You received 1 coin for today's check-in!", 'admin_only': "This is an admin-only command.", 'language_changed': "Bot language changed to {}.", 'stats_title': "Statistics", 'service_link': "Service link: {}", 'language_button': "Language", 'admin_panel': "Admin Panel"}, 'fa': {'welcome': "خوش آمدید!", 'support': "برای پشتیبانی تماس بگیرید: {}", 'daily_already': "امروز قبلا امتیاز روزانه را گرفتید.", 'daily_success': "شما ۱ سکه بابت امتیاز روزانه دریافت کردید!", 'admin_only': "این دستور فقط برای مدیر است.", 'language_changed': "زبان ربات به {} تغییر کرد.", 'stats_title': "آمار", 'service_link': "لینک سرویس: {}", 'language_button': "Language", 'admin_panel': "پنل مدیریت"} }

def t(key): lang = get_setting('lang') or 'en' return TEXTS.get(lang, TEXTS['en']).get(key, key)

def user_keyboard(): kb = types.InlineKeyboardMarkup() kb.add(types.InlineKeyboardButton('Support', callback_data='support')) kb.add(types.InlineKeyboardButton('Daily Points', callback_data='daily')) return kb

@bot.message_handler(commands=['start']) def handle_start(m): user_id = m.from_user.id ensure_user(user_id) bot.send_message(user_id, t('welcome'), reply_markup=user_keyboard())

@bot.message_handler(commands=['admin']) def handle_admin(m): user_id = m.from_user.id if user_id != SUPER_ADMIN_ID: bot.send_message(user_id, t('admin_only')) return kb = types.InlineKeyboardMarkup() kb.add(types.InlineKeyboardButton(t('stats_title'), callback_data='admin_stats')) kb.add(types.InlineKeyboardButton(t('language_button'), callback_data='admin_language')) bot.send_message(user_id, t('admin_panel'), reply_markup=kb)

@bot.callback_query_handler(func=lambda call: True) def callback_query(call): user_id = call.from_user.id data = call.data if data == 'support': link = get_setting('service_link') or WEB_SERVICE_URL bot.answer_callback_query(call.id) bot.send_message(user_id, t('support').format(link)) elif data == 'daily': ensure_user(user_id) pd, pg, pc, last_daily = get_user_stats(user_id) today_iso = date.today().isoformat() if last_daily == today_iso: bot.answer_callback_query(call.id, text=t('daily_already')) return add_points(user_id, diamond=0, gold=0, coin=1) set_last_daily(user_id, today_iso) bot.answer_callback_query(call.id, text=t('daily_success')) elif data == 'admin_stats' and user_id == SUPER_ADMIN_ID: cur = conn.cursor() cur.execute('SELECT COUNT(*), SUM(points_diamond), SUM(points_gold), SUM(points_coin) FROM users') r = cur.fetchone() total_users = r[0] or 0 sum_d = r[1] or 0 sum_g = r[2] or 0 sum_c = r[3] or 0 service_link = get_setting('service_link') text = f"{t('stats_title')}:\n\nUsers: {total_users}\nDiamonds: {sum_d}\nGolds: {sum_g}\nCoins: {sum_c}\n\n{t('service_link').format(service_link)}" bot.answer_callback_query(call.id) bot.send_message(user_id, text) elif data == 'admin_language' and user_id == SUPER_ADMIN_ID: kb = types.InlineKeyboardMarkup() kb.add(types.InlineKeyboardButton('فارسی', callback_data='set_lang_fa')) kb.add(types.InlineKeyboardButton('English', callback_data='set_lang_en')) bot.answer_callback_query(call.id) bot.send_message(user_id, 'Choose language / زبان را انتخاب کنید:', reply_markup=kb) elif data in ['set_lang_fa', 'set_lang_en'] and user_id == SUPER_ADMIN_ID: new_lang = 'fa' if data == 'set_lang_fa' else 'en' set_setting('lang', new_lang) bot.answer_callback_query(call.id, text=TEXTS[new_lang]['language_changed'].format('فارسی' if new_lang=='fa' else 'English'))

@app.route('/' + TOKEN, methods=['POST']) def webhook(): if request.headers.get('content-type') == 'application/json': json_str = request.get_data().decode('utf-8') update = telebot.types.Update.de_json(json_str) bot.process_new_updates([update]) return '', 200 else: abort(403)

@app.route('/') def index(): return 'Bot is running.'

def set_webhook(): url = WEB_SERVICE_URL.rstrip('/') + '/' + TOKEN bot.remove_webhook() bot.set_webhook(url=url)

if name == 'main': try: set_webhook() except: pass app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

