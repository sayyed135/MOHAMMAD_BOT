import telebot
import random

bot = telebot.TeleBot("7217912729:AAG0fXedfzX59DuvMHmHky2RS3JiMxlB7II")
admin_id = 6994772164
users_points = {}
user_current_question = {}
user_asked_questions = {}

questions = [
    {"id": 1, "q": "پایتخت افغانستان چیست؟", "a": ["کابل", "کابل افغانستان"]},
    {"id": 2, "q": "رنگ پرچم افغانستان چیست؟", "a": ["سیاه قرمز سبز", "سبز قرمز سیاه", "پرچم سه رنگ"]},
    {"id": 3, "q": "چه دینی در افغانستان بیشترین پیرو دارد؟", "a": ["اسلام", "مسلمان", "دین اسلام"]},
]

@bot.message_handler(commands=['start'])
def start(msg):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🎯 جواب دادن")
    bot.send_message(msg.chat.id, "سلام! یکی از گزینه‌ها را انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🎯 جواب دادن")
def send_question(msg):
    chat_id = msg.chat.id
    if chat_id not in user_asked_questions:
        user_asked_questions[chat_id] = set()

    available = [q for q in questions if q['id'] not in user_asked_questions[chat_id]]
    
    if not available:
        bot.send_message(chat_id, "✅ شما همه سوالات را پاسخ داده‌اید.")
        return

    q = random.choice(available)
    user_current_question[chat_id] = q
    user_asked_questions[chat_id].add(q['id'])

    bot.send_message(chat_id, f"❓ سوال:\n{q['q']}\n\n✏️ جواب را بنویس:")

@bot.message_handler(func=lambda m: True)
def handle_answer(msg):
    chat_id = msg.chat.id
    if chat_id in user_current_question:
        question = user_current_question[chat_id]
        correct_answers = question['a']
        user_answer = msg.text.lower()

        if any(ans in user_answer for ans in correct_answers):
            users_points[chat_id] = users_points.get(chat_id, 0) + 1
            bot.send_message(chat_id, f"✅ آفرین! جواب درست بود.\nامتیاز شما: {users_points[chat_id]}")
        else:
            bot.send_message(chat_id, "❌ متاسفم، جواب درست نبود.")

        del user_current_question[chat_id]

bot.infinity_polling()
