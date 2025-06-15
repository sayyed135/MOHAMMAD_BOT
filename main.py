import telebot, json, random
from telebot import types

bot = telebot.TeleBot('7217912729:AAFuXcRQNl0p-uCQZb64cxakJD15_b414q8')
ADMIN_ID = 6994772164
data = {}

try:
    with open('users.json', 'r') as f:
        data = json.load(f)
except:
    pass

def save(): json.dump(data, open('users.json', 'w'))

cities = ['کابل', 'هرات', 'قندهار', 'مزار شریف']
ai_users = set()

@bot.message_handler(commands=['start'])
def start(m):
    uid = str(m.from_user.id)
    if uid not in data:
        data[uid] = {'name': m.from_user.first_name, 'score': 0, 'level': 'معمولی', 'city': None}
        save()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row('امتیاز روزانه', 'خرید اشتراک')
    kb.row('جرأت یا حقیقت', 'AI-CHAT')
    if m.from_user.id == ADMIN_ID: kb.add('مدیریت')
    bot.send_message(m.chat.id, 'خوش اومدی! 🌟', reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == 'امتیاز روزانه')
def daily(m):
    uid = str(m.from_user.id)
    data[uid]['score'] += 1
    save()
    bot.reply_to(m, 'یک امتیاز گرفتی! 🪙')

@bot.message_handler(func=lambda m: m.text == 'خرید اشتراک')
def buy(m):
    kb = types.InlineKeyboardMarkup()
    for level, price in [('معمولی', 1), ('حرفه‌ای', 3), ('VIP', 5)]:
        kb.add(types.InlineKeyboardButton(f'{level} - {price}🪙', callback_data=f'buy_{level}'))
    bot.send_message(m.chat.id, 'انتخاب کن:', reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith('buy_'))
def buy_cb(c):
    uid = str(c.from_user.id)
    level = c.data[4:]
    cost = {'معمولی': 1, 'حرفه‌ای': 3, 'VIP': 5}[level]
    if data[uid]['score'] >= cost:
        data[uid]['score'] -= cost
        data[uid]['level'] = level
        save()
        bot.answer_callback_query(c.id, f'{level} فعال شد!')
    else:
        bot.answer_callback_query(c.id, 'امتیاز کافی نیست.')

@bot.message_handler(func=lambda m: m.text == 'مدیریت' and m.from_user.id == ADMIN_ID)
def admin(m):
    text = ''
    for uid, info in data.items():
        text += f"👤 [{info['name']}](tg://user?id={uid}) | امتیاز: {info['score']} | سطح: {info['level']} | شهر: {info['city']}\n"
    bot.send_message(m.chat.id, text or 'کاربری نیست', parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == 'جرأت یا حقیقت')
def daretruth(m):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add('تنظیم شهر', 'پیدا کردن یک نفر')
    bot.send_message(m.chat.id, 'یک گزینه رو بزن:', reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == 'تنظیم شهر')
def set_city(m):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for city in cities: kb.add(city)
    bot.send_message(m.chat.id, 'شهر خود را انتخاب کن:', reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in cities)
def save_city(m):
    data[str(m.from_user.id)]['city'] = m.text
    save()
    bot.reply_to(m, f'شهر تنظیم شد: {m.text}')

@bot.message_handler(func=lambda m: m.text == 'پیدا کردن یک نفر')
def find_user(m):
    me = str(m.from_user.id)
    my_city = data[me].get('city')
    if not my_city: return bot.reply_to(m, 'اول شهر را تنظیم کن.')
    for uid, info in data.items():
        if uid != me and info.get('city') == my_city:
            return bot.send_message(m.chat.id, f"👤 [{info['name']}](tg://user?id={uid})", parse_mode='Markdown')
    bot.reply_to(m, 'کسی از شهر تو پیدا نشد.')

@bot.message_handler(func=lambda m: m.text == 'AI-CHAT')
def ai_start(m):
    ai_users.add(m.from_user.id)
    bot.send_message(m.chat.id, 'سلام! با من حرف بزن (برای خروج بنویس /cancel)')

@bot.message_handler(func=lambda m: m.from_user.id in ai_users)
def ai_chat(m):
    if m.text == '/cancel':
        ai_users.remove(m.from_user.id)
        return bot.send_message(m.chat.id, 'خارج شدی از AI-CHAT')
    bot.reply_to(m, random.choice(['اوه جالبه!', 'ادامه بده...', 'واقعا؟', 'نمی‌دونم چی بگم 😅']))

print('✅ ربات فعاله...')
bot.infinity_polling()
