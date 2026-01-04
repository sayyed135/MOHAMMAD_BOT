import asyncio
import aiosqlite
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# ================== تنظیمات ==================
API_TOKEN = '8207165361:AAGTMHAXitLwyrjFch0jwQ4PtigSlGHDHbw'
ADMIN_ID = 6994772164
CHANNEL_USERNAME = 'MOHAMMADVOLTPROCH'
CHANNEL_LINK = 'https://t.me/MOHAMMADVOLTPROCH'

WEBHOOK_HOST = 'https://code-ai-0alo.onrender.com'  # لینک خودت
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

DB_FILE = 'voltbot.db'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, parse_mode='HTML')
dp = Dispatcher()

# ================== دیتابیس ==================
async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                phone TEXT,
                credit INTEGER DEFAULT 0,
                referrals INTEGER DEFAULT 0,
                last_daily TEXT
            )
        ''')
        await db.commit()

# ================== منو اصلی ==================
def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("📊 اطلاعات اکانت", "🎁 کریدت روزانه")
    kb.add("👥 دعوت دوستان", "⚠️ گزارش مشکل")
    kb.add("💸 انتقال کریدت", "💎 عضویت VIP")
    kb.add("📱 ارسال شماره تماس")
    return kb

# ================== /start ==================
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("عضویت در کانال ⚡", url=CHANNEL_LINK))
    kb.add(InlineKeyboardButton("بررسی عضویت ✅", callback_data="check"))
    await message.answer(
        "⚡ به ربات MOHAMMADVOLTPRO خوش آمدید.\n"
        "لطفاً در کانال عضو شوید و شماره تماس ارسال کنید.",
        reply_markup=kb
    )

@dp.callback_query_handler(text="check")
async def check(call: types.CallbackQuery):
    await call.message.edit_text("✅ تست موفق!\nربات زنده است ⚡", reply_markup=main_menu())

# ================== تست ساده ==================
@dp.message_handler()
async def echo(message: types.Message):
    await message.answer("ربات کار می‌کنه! ⚡\nمنو رو ببین:", reply_markup=main_menu())

# ================== Webhook Setup ==================
app = web.Application()

async def on_startup(app):
    await init_db()
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook set to {WEBHOOK_URL}")

async def on_shutdown(app):
    await bot.delete_webhook()
    logging.info("Webhook removed")

app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
setup_application(app, dp, bot=bot)

# ================== اجرا ==================
if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=int(__import__('os').environ.get('PORT', 8000)))
