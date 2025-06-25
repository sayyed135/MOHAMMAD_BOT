import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from flask import Flask, request
import time
import random

API_TOKEN = '7217912729:AAHGslCoRLKfVm1VEZ0qG7riZ3fiGMQ1t7I'
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

admins = [6994772164]
users = {}  # user_id: {score, level, mode, anon_partner, last_daily, ai_active}
gift_codes = {}  # code: score
used_codes = set()  # code-userid used

truths = [
    "آخرین دروغی که گفتی چی بوده؟",
    "تاحالا حسودی کردی؟",
    "آخرین بار کی ترسیدی؟",
    "بزرگ‌ترین ترست چیه؟",
    "یه راز برام بگو.",
]
dares = [
    "۵ تا شنا برو",
    "به دوستت بگو دوستش داری",
    "یه سلفی بگیر و بفرست برای یکی",
    "یه جوک تعریف کن",
    "با یه غریبه صحبت کن",
]

def get_keyboard(uid):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("امتیاز روزانه 🪙", callback_data='daily_score'),
        InlineKeyboardButton("اطلاعات من 📄", callback_data='my_info'),
        InlineKeyboardButton("خرید اشتراک 💎", callback_data='buy_vip'),
        InlineKeyboardButton("AI CHAT 🤖", callback_data='ai_chat_start'),
        InlineKeyboardButton("چت ناشناس 🕵️", callback_data='anon_chat'),
        InlineKeyboardButton("🎁 کد هدیه", callback_data='gift_code')
    )
    if uid in admins:
        markup.add(
            InlineKeyboardButton("ارسال پیام همگانی 📢", callback_data='broadcast'),
            InlineKeyboardButton("پنل مدیریت 🛠️", callback_data='admin_panel')
        )
    return markup

def get_anon_chat_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("جرأت و حقیقت 🎯", callback_data='start_truth_dare'),
        InlineKeyboardButton("قطع چت ❌", callback_data='end_anon_chat')
    )
    return markup

def get_truth_dare_buttons():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("حقیقت", callback_data='truth'),
        InlineKeyboardButton("جرأت", callback_data='dare'),
        InlineKeyboardButton("پایان بازی ⏹️", callback_data='end_truth_dare')
    )
    return markup

def get_ai_chat_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("پایان AI CHAT ⏹️", callback_data='end_ai_chat')
    )
    return markup

def get_admin_panel_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📋 لیست کاربران", callback_data='show_users'),
        InlineKeyboardButton("🛠 تغییر امتیاز", callback_data='set_score'),
        InlineKeyboardButton("🎁 ساخت کد هدیه", callback_data='make_gift'),
        InlineKeyboardButton("📋 لیست کدهای هدیه", callback_data='gift_list'),
        InlineKeyboardButton("↩️ خروج", callback_data='back_to_main')
    )
    return markup

@bot.message_handler(commands=['start'])
def start(message: Message):
    uid = message.from_user.id
    if uid not in users:
        users[uid] = {
            'score': 0,
            'level': 'معمولی',
            'mode': 'معمولی',
            'anon_partner': None,
            'last_daily': 0,
            'ai_active': False,
            'truth_dare': False,
            'truth_dare_turn': None,
            'truth_dare_waiting_answer': False,
            'truth_dare_player_msgs': []
        }
    bot.send_message(uid, "سلام! به ربات خوش آمدی!", reply_markup=get_keyboard(uid))

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = call.from_user.id
    data = call.data

    if uid not in users:
        users[uid] = {
            'score': 0,
            'level': 'معمولی',
            'mode': 'معمولی',
            'anon_partner': None,
            'last_daily': 0,
            'ai_active': False,
            'truth_dare': False,
            'truth_dare_turn': None,
            'truth_dare_waiting_answer': False,
            'truth_dare_player_msgs': []
        }

    # روزانه
    if data == 'daily_score':
        now = time.time()
        last = users[uid]['last_daily']
        if now - last < 86400:
            bot.answer_callback_query(call.id, "⏳ فقط هر ۲۴ ساعت یکبار می‌توانید امتیاز بگیرید!")
            return
        level = users[uid]['level']
        if level == 'VIP':
            amt = 50
        elif level == 'حرفه‌ای':
            amt = 20
        else:
            amt = 5
        users[uid]['score'] += amt
        users[uid]['last_daily'] = now
        bot.answer_callback_query(call.id, f"✅ {amt} امتیاز به شما داده شد!")

    # اطلاعات من
    elif data == 'my_info':
        u = users[uid]
        txt = f"🏷 امتیاز: {u['score']}\nسطح اشتراک: {u['level']}\nحالت چت: {u['mode']}"
        bot.edit_message_text(txt, uid, call.message.message_id, reply_markup=get_keyboard(uid))

    # خرید اشتراک
    elif data == 'buy_vip':
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("معمولی - ۵ امتیاز", callback_data='buy_normal'),
            InlineKeyboardButton("حرفه‌ای - ۱۰ امتیاز", callback_data='buy_pro'),
            InlineKeyboardButton("VIP - ۲۰ امتیاز", callback_data='buy_vip2')
        )
        bot.edit_message_text("🎁 سطح اشتراک را انتخاب کنید:", uid, call.message.message_id, reply_markup=markup)

    elif data.startswith('buy_'):
        lv_cost = {
            'buy_normal': ('معمولی', 5),
            'buy_pro': ('حرفه‌ای', 10),
            'buy_vip2': ('VIP', 20)
        }
        level, cost = lv_cost.get(data, ('معمولی', 5))
        if users[uid]['score'] >= cost:
            users[uid]['score'] -= cost
            users[uid]['level'] = level
            bot.answer_callback_query(call.id, f"✅ سطح شما به {level} تغییر کرد.")
        else:
            bot.answer_callback_query(call.id, "❌ امتیاز کافی ندارید!")

    # AI chat شروع
    elif data == 'ai_chat_start':
        if users[uid]['ai_active']:
            bot.answer_callback_query(call.id, "شما قبلا وارد چت AI شده‌اید.")
        else:
            users[uid]['ai_active'] = True
            bot.send_message(uid, "🤖 به چت هوش مصنوعی خوش آمدید! پیام بفرستید، برای پایان روی دکمه پایین بزنید.", reply_markup=get_ai_chat_keyboard())

    # پایان AI chat
    elif data == 'end_ai_chat':
        users[uid]['ai_active'] = False
        bot.send_message(uid, "⏹️ چت هوش مصنوعی پایان یافت.", reply_markup=get_keyboard(uid))

    # چت ناشناس
    elif data == 'anon_chat':
        if users[uid]['anon_partner'] is not None:
            bot.send_message(uid, "🔴 شما در حال چت ناشناس هستید.", reply_markup=get_anon_chat_keyboard())
        else:
            # جستجو برای همتا
            waiting = [u for u, d in users.items() if d['anon_partner'] is None and u != uid]
            if waiting:
                partner = waiting[0]
                users[uid]['anon_partner'] = partner
                users[partner]['anon_partner'] = uid
                bot.send_message(uid, "🟢 به یک نفر وصل شدی!", reply_markup=get_anon_chat_keyboard())
                bot.send_message(partner, "🟢 یک نفر بهت وصل شد!", reply_markup=get_anon_chat_keyboard())
            else:
                bot.send_message(uid, "⏳ منتظر طرف مقابل هستی...")

    # قطع چت ناشناس
    elif data == 'end_anon_chat':
        partner = users[uid]['anon_partner']
        if partner is not None:
            users[uid]['anon_partner'] = None
            users[partner]['anon_partner'] = None
            bot.send_message(uid, "🔴 چت ناشناس قطع شد.", reply_markup=get_keyboard(uid))
            bot.send_message(partner, "🔴 طرف مقابل چت را قطع کرد.", reply_markup=get_keyboard(partner))
        else:
            bot.answer_callback_query(call.id, "❌ در چت ناشناس نیستید.")

    # بازی جرأت و حقیقت شروع (در چت ناشناس)
    elif data == 'start_truth_dare':
        partner = users[uid]['anon_partner']
        if partner is None:
            bot.answer_callback_query(call.id, "❌ ابتدا به یک نفر وصل شوید.")
            return
        # ارسال درخواست به طرف مقابل
        bot.send_message(partner, f"📩 کاربر ناشناس درخواست بازی جرأت و حقیقت با شما داده. قبول می‌کنید؟",
                         reply_markup=InlineKeyboardMarkup().add(
                             InlineKeyboardButton("✅ قبول", callback_data=f"accept_truth_dare:{uid}"),
                             InlineKeyboardButton("❌ رد", callback_data=f"decline_truth_dare:{uid}")
                         ))
        bot.send_message(uid, "⏳ منتظر پاسخ طرف مقابل هستید...")

    elif data.startswith("accept_truth_dare:"):
        initiator = int(data.split(":")[1])
        if users[uid]['anon_partner'] != initiator:
            bot.answer_callback_query(call.id, "❌ این درخواست معتبر نیست.")
            return
        # شروع بازی
        for player in (uid, initiator):
            users[player]['truth_dare'] = True
            users[player]['truth_dare_turn'] = initiator  # نفر اول نوبت دارد
            users[player]['truth_dare_waiting_answer'] = False
            users[player]['truth_dare_player_msgs'] = []
        bot.send_message(initiator, "🎯 بازی جرأت و حقیقت شروع شد! شما نوبت اول را دارید.")
        bot.send_message(uid, "🎯 بازی جرأت و حقیقت شروع شد! نوبت منتظر است.")
        send_truth_or_dare_question(initiator)

    elif data.startswith("decline_truth_dare:"):
        initiator = int
