# ================================================
#   ربات MOHAMMADVOLTPRO ⚡ - نسخه ساده و مرتب
#   هر دکمه یک بخش جدا دارد - راحت ویرایش کن!
# ================================================

import asyncio
import aiosqlite
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# ================== 1. تنظیمات اصلی (اینجا تغییر بده) ==================
API_TOKEN = '8207165361:AAGTMHAXitLwyrjFch0jwQ4PtigSlGHDHbw'  # توکن ربات
ADMIN_ID = 6994772164                                           # آیدی عددی خودت (ادمین)
CHANNEL_USERNAME = 'MOHAMMADVOLTPROCH'                           # یوزرنیم کانال بدون @
CHANNEL_LINK = 'https://t.me/MOHAMMADVOLTPROCH'                  # لینک کانال

WEBHOOK_HOST = 'https://code-ai-0alo.onrender.com'              # لینک سرویس Render تو
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

DB_FILE = 'voltbot.db'                                          # اسم دیتابیس

# جایزه و جریمه زیرمجموعه
REFERRAL_BONUS = 2      # کریدت جایزه برای دعوت
REFERRAL_PENALTY = 10   # کسر کریدت اگر زیرمجموعه خارج شد

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, parse_mode='HTML')
dp = Dispatcher()

# ================== 2. دکمه‌های منوی اصلی (اینجا اضافه/کم کن) ==================
BUTTON_ACCOUNT   = "📊 اطلاعات اکانت"
BUTTON_DAILY     = "🎁 کریدت روزانه"
BUTTON_INVITE    = "👥 دعوت دوستان"
BUTTON_REPORT    = "⚠️ گزارش مشکل"
BUTTON_TRANSFER  = "💸 انتقال کریدت"
BUTTON_VIP       = "💎 عضویت VIP"
BUTTON_CONTACT   = "📱 ارسال شماره تماس"

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(BUTTON_ACCOUNT, BUTTON_DAILY)
    kb.add(BUTTON_INVITE, BUTTON_REPORT)
    kb.add(BUTTON_TRANSFER, BUTTON_VIP)
    kb.add(BUTTON_CONTACT)
    return kb

# ================== 3. دیتابیس - ساخت جدول کاربران ==================
async def create_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                phone TEXT,
                credit INTEGER DEFAULT 0,
                referrals INTEGER DEFAULT 0,
                referrer_id INTEGER,
                last_daily TEXT,
                vip INTEGER DEFAULT 0,
                banned INTEGER DEFAULT 0
            )
        ''')
        await db.commit()

# ================== 4. چک عضویت در کانال ==================
async def is_member(user_id):
    try:
        member = await bot.get_chat_member(f'@{CHANNEL_USERNAME}', user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# ================== 5. بخش: شروع ربات (/start) ==================
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    referrer_id = None
    if message.get_args().isdigit():
        referrer_id = int(message.get_args())

    # ثبت کاربر جدید
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (message.from_user.id,)) as cursor:
            if not await cursor.fetchone():
                await db.execute("INSERT INTO users (user_id, username, first_name, referrer_id) VALUES (?, ?, ?, ?)",
                                 (message.from_user.id, message.from_user.username, message.from_user.first_name, referrer_id))
                await db.commit()

                if referrer_id:
                    await db.execute("UPDATE users SET referrals = referrals + 1, credit = credit + ? WHERE user_id = ?",
                                     (REFERRAL_BONUS, referrer_id))
                    await db.commit()
                    try:
                        await bot.send_message(referrer_id, f"✅ یک نفر با لینک شما وارد شد! +{REFERRAL_BONUS} کریدت")
                    except:
                        pass

    # پیام خوش‌آمدگویی
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("عضویت در کانال ⚡", url=CHANNEL_LINK))
    kb.add(InlineKeyboardButton("بررسی عضویت ✅", callback_data="check_join"))
    
    await message.answer(
        "⚡ به ربات MOHAMMADVOLTPRO خوش آمدید.\n"
        "برای استفاده، ابتدا در کانال عضو شوید و شماره تماس خود را ارسال کنید.",
        reply_markup=kb
    )

# ================== 6. بخش: بررسی عضویت و شماره ==================
@dp.callback_query_handler(text="check_join")
async def check_join(call: types.CallbackQuery):
    user_id = call.from_user.id

    # چک شماره تماس
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT phone FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            has_phone = row and row[0] is not None

    if not has_phone:
        await call.message.edit_text("لطفاً شماره تماس خود را ارسال کنید:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton(BUTTON_CONTACT, request_contact=True)))
        return

    # چک عضویت کانال
    if not await is_member(user_id):
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("عضویت در کانال ⚡", url=CHANNEL_LINK))
        kb.add(InlineKeyboardButton("بررسی مجدد", callback_data="check_join"))
        await call.message.edit_text("⚠️ هنوز در کانال عضو نشده‌اید. لطفاً عضو شوید و دوباره بررسی کنید.", reply_markup=kb)
        return

    # همه چیز اوکی شد → منوی اصلی
    await call.message.edit_text("✅ عالی! همه مراحل کامل شد.\nحالا از ربات استفاده کنید:", reply_markup=main_menu())

# ================== 7. بخش: ارسال شماره تماس ==================
@dp.message_handler(content_types=['contact'])
async def get_contact(message: types.Message):
    if message.contact.user_id != message.from_user.id:
        await message.answer("⚠️ فقط شماره خودتان را ارسال کنید.")
        return

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("UPDATE users SET phone = ? WHERE user_id = ?", (message.contact.phone_number, message.from_user.id))
        await db.commit()

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("عضویت در کانال ⚡", url=CHANNEL_LINK))
    kb.add(InlineKeyboardButton("بررسی عضویت ✅", callback_data="check_join"))
    await message.answer("✅ شماره ثبت شد. حالا در کانال عضو شوید:", reply_markup=kb)

# ================== 8. بخش: دکمه اطلاعات اکانت ==================
@dp.message_handler(text=BUTTON_ACCOUNT)
async def account_info(message: types.Message):
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT first_name, phone, credit, referrals, vip, username FROM users WHERE user_id = ?", (message.from_user.id,)) as cursor:
            row = await cursor.fetchone()

    name, phone, credit, refs, vip, username = row
    username = f"@{username}" if username else "ندارد"
    phone = phone or "ثبت نشده"

    text = f"""📊 اطلاعات اکانت شما

نام: {name}
شماره: {phone}
کریدت: {credit}
زیرمجموعه: {refs}
VIP: {'بله' if vip else 'خیر'}
یوزرنیم: {username}"""

    await message.answer(text, reply_markup=main_menu())

# ================== 9. بخش: دکمه کریدت روزانه ==================
@dp.message_handler(text=BUTTON_DAILY)
async def daily_reward(message: types.Message):
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT last_daily, credit FROM users WHERE user_id = ?", (message.from_user.id,)) as cursor:
            row = await cursor.fetchone()
            last_daily, credit = row

        today = datetime.now().date()
        if last_daily and datetime.fromisoformat(last_daily).date() == today:
            await message.answer("⚠️ امروز قبلاً کریدت روزانه گرفتید. فردا دوباره بیایید.")
            return

        new_credit = credit + 1
        await db.execute("UPDATE users SET credit = ?, last_daily = ? WHERE user_id = ?",
                         (new_credit, datetime.now().isoformat(), message.from_user.id))
        await db.commit()

        await message.answer(f"✅ +1 کریدت روزانه!\nموجودی جدید: {new_credit} کریدت", reply_markup=main_menu())

# ================== 10. بخش: دکمه دعوت دوستان ==================
@dp.message_handler(text=BUTTON_INVITE)
async def invite_link(message: types.Message):
    bot_username = (await bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={message.from_user.id}"

    text = f"""🔗 لینک دعوت اختصاصی شما:
{link}

با هر زیرمجموعه جدید: +{REFERRAL_BONUS} کریدت جایزه!

متن آماده برای ارسال:
«ربات حرفه‌ای MOHAMMADVOLTPRO ⚡ کریدت رایگان و امکانات خفن!
لینک: {link}»"""

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("اشتراک‌گذاری لینک 🔗", url=f"https://t.me/share/url?url={link}"))
    await message.answer(text, reply_markup=kb)

# ================== 11. بخش: دکمه گزارش مشکل ==================
@dp.message_handler(text=BUTTON_REPORT)
async def report_problem(message: types.Message):
    await message.answer("مشکل یا پیشنهادتون رو بنویسید. مستقیم برای مدیریت ارسال می‌شه.")
    # منتظر پیام بعدی کاربر می‌مونیم
    dp.register_message_handler(send_report, lambda m: m.from_user.id == message.from_user.id, state=None)

async def send_report(message: types.Message):
    try:
        await bot.forward_message(ADMIN_ID, message.from_user.id, message.message_id)
        await message.answer("✅ گزارش با موفقیت ارسال شد.")
    except:
        await message.answer("❌ خطا در ارسال گزارش.")
    # دوباره منو اصلی
    await message.answer("منوی اصلی:", reply_markup=main_menu())

# ================== 12. بخش: دکمه انتقال کریدت ==================
# (این بخش در پیام بعدی می‌دم چون طولانی‌تره)

# ================== 13. بخش: دکمه VIP ==================
@dp.message_handler(text=BUTTON_VIP)
async def vip_button(message: types.Message):
    await message.answer("⚠️ بخش VIP در حال توسعه است. به زودی فعال می‌شه!", reply_markup=main_menu())

# ================== 14. پنل ادمین (فقط برای تو) ==================
# (در صورت نیاز بعداً اضافه می‌کنیم)

# ================== 15. راه‌اندازی Webhook برای Render ==================
app = web.Application()

async def on_startup(app):
    await create_db()
    await bot.set_webhook(WEBHOOK_URL)
    print("ربات با Webhook فعال شد!")

async def on_shutdown(app):
    await bot.delete_webhook()

app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
setup_application(app, dp, bot=bot)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8000)
