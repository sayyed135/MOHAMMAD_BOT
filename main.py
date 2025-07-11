from flask import Flask, request
import telebot
import json
import os

API_TOKEN = '7217912729:AAE7IXU8LQpwtPLN-BxGDUsF-y7Af36UuQ8'
ADMIN_ID = 6994772164

bot = telebot.TeleBot(API_TOKEN)
bot.remove_webhook()
bot.set_webhook(url='https://mohammad-bot-2.onrender.com/')


app = Flask(__name__)

# ---- ربات همون قبلی ----
def save_user_info(user_id, phone=None, link=None):
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            try:
                data = json.load(f)
            except:
                data = {}
    else:
        data = {}

    if str(user_id) not in data:
        data[str(user_id)] = {}

    if phone:
        data[str(user_id)]["phone"] = phone
    if link:
        data[str(user_id)]["link"] = link

    with open("users.json", "w") as f:
        json.dump(data, f, indent=2)


@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📲 ثبت شماره", "🔗 ثبت لینک")
    if message.from_user.id == ADMIN_ID:
        markup.row("📒 لیست کاربران")
    bot.send_message(message.chat.id, "یکی از گزینه‌ها را انتخاب کن:", reply_markup=markup)


@bot.message_handler(func=lambda m: m.text == "📲 ثبت شماره")
def ask_phone(message):
    msg = bot.send_message(message.chat.id, "شماره‌ات را بفرست:")
    bot.register_next_step_handler(msg, save_phone)

def save_phone(message):
    phone = message.text.strip()
    user_id = message.from_user.id
    save_user_info(user_id, phone=phone)
    bot.send_message(message.chat.id, "✅ شماره ذخیره شد!")


@bot.message_handler(func=lambda m: m.text == "🔗 ثبت لینک")
def ask_link(message):
    msg = bot.send_message(message.chat.id, "لینک پروفایلت را بفرست:")
    bot.register_next_step_handler(msg, save_link)

def save_link(message):
    link = message.text.strip()
    user_id = message.from_user.id
    save_user_info(user_id, link=link)
    bot.send_message(message.chat.id, "✅ لینک ذخیره شد!")


@bot.message_handler(func=lambda m: m.text == "📒 لیست کاربران")
def send_user_list(message):
    if message.from_user.id != ADMIN_ID:
        return

    if not os.path.exists("users.json"):
        bot.send_message(message.chat.id, "هیچ اطلاعاتی ذخیره نشده.")
        return

    with open("users.json", "r") as f:
        data = json.load(f)

    text_lines = []
    for uid, info in data.items():
        phone = info.get("phone", "ندارد")
        link = info.get("link", "ندارد")
        text_lines.append(f"🆔 {uid}\n📞 {phone}\n🔗 {link}\n")

    with open("users.txt", "w", encoding="utf-8") as f:
        f.write("\n------------------\n".join(text_lines))

    with open("users.txt", "rb") as f:
        bot.send_document(message.chat.id, f)

# ---- دریافت پیام‌ها از تلگرام ----
@app.route("/", methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200
