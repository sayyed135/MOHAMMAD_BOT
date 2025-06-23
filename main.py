import telebot
from flask import Flask, request

bot = telebot.TeleBot("7217912729:AAEbbFfenQJrBOTSEJYsVWmcVJOmZTOuWuU")
app = Flask(__name__)
admin_id = 6994772164  # آیدی عددی مدیر

# دستورات کاربر
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "خوش آمدی.")

@bot.message_handler(commands=['info'])
def info(message):
    bot.reply_to(message, f"نام: {message.from_user.first_name}\nآیدی: {message.from_user.id}")

@bot.message_handler(commands=['score'])
def score(message):
    bot.reply_to(message, "امتیاز: 0")

@bot.message_handler(commands=['daily'])
def daily(message):
    bot.reply_to(message, "امتیاز روزانه دریافت شد.")

@bot.message_handler(commands=['buy'])
def buy(message):
    bot.reply_to(message, "برای خرید اشتراک، پیام بده.")

@bot.message_handler(commands=['renew'])
def renew(message):
    bot.reply_to(message, "اشتراک تمدید شد.")

@bot.message_handler(commands=['level'])
def level(message):
    bot.reply_to(message, "سطح شما: معمولی")

@bot.message_handler(commands=['truthordare'])
def tod(message):
    bot.reply_to(message, "بازی شروع شد.")

@bot.message_handler(commands=['chat'])
def chat(message):
    bot.reply_to(message, "درحال یافتن چت...")

@bot.message_handler(commands=['mode'])
def mode(message):
    bot.reply_to(message, "حالت چت تغییر کرد.")

@bot.message_handler(commands=['block'])
def block(message):
    bot.reply_to(message, "کاربر بلاک شد.")

@bot.message_handler(commands=['ai'])
def ai(message):
    bot.reply_to(message, "پرسش خود را بنویس.")

@bot.message_handler(commands=['google'])
def google(message):
    bot.reply_to(message, "چه چیزی جستجو شود؟")

@bot.message_handler(commands=['faq'])
def faq(message):
    bot.reply_to(message, "سوالات متداول در حال آماده شدن است.")

@bot.message_handler(commands=['rules'])
def rules(message):
    bot.reply_to(message, "قوانین رعایت شود.")

@bot.message_handler(commands=['support'])
def support(message):
    bot.reply_to(message, "در حال اتصال به پشتیبانی...")

@bot.message_handler(commands=['report'])
def report(message):
    bot.reply_to(message, "گزارش ثبت شد.")

@bot.message_handler(commands=['contactadmin'])
def contactadmin(message):
    bot.reply_to(message, "در حال ارتباط با مدیر.")

@bot.message_handler(commands=['invite'])
def invite(message):
    bot.reply_to(message, "لینک دعوت ارسال شد.")

@bot.message_handler(commands=['reward'])
def reward(message):
    bot.reply_to(message, "جایزه داده شد.")

@bot.message_handler(commands=['about'])
def about(message):
    bot.reply_to(message, "این ربات توسط محمد ساخته شده.")

# دستورات مدیر
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id == admin_id:
        bot.reply_to(message, "پیام همگانی بنویس.")
    else:
        bot.reply_to(message, "دسترسی ندارید.")

@bot.message_handler(commands=['users'])
def users(message):
    if message.from_user.id == admin_id:
        bot.reply_to(message, "تعداد کاربران: 1")
    else:
        bot.reply_to(message, "دسترسی ندارید.")

@bot.message_handler(commands=['manualconnect'])
def connect(message):
    bot.reply_to(message, "دو کاربر وصل شدند.")

@bot.message_handler(commands=['limit'])
def limit(message):
    bot.reply_to(message, "محدودیت تنظیم شد.")

@bot.message_handler(commands=['setscore'])
def setscore(message):
    bot.reply_to(message, "امتیاز تنظیم شد.")

@bot.message_handler(commands=['setlevel'])
def setlevel(message):
    bot.reply_to(message, "سطح تنظیم شد.")

@bot.message_handler(commands=['blockuser'])
def blockuser(message):
    bot.reply_to(message, "کاربر مسدود شد.")

@bot.message_handler(commands=['unblock'])
def unblock(message):
    bot.reply_to(message, "کاربر آزاد شد.")

@bot.message_handler(commands=['warn'])
def warn(message):
    bot.reply_to(message, "هشدار ارسال شد.")

@bot.message_handler(commands=['chats'])
def chats(message):
    bot.reply_to(message, "آمار چت‌ها: 0 فعال")

# webhook
@app.route("/", methods=["POST"])
def receive():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return ""

@app.route("/", methods=["GET"])
def check():
    return "ربات روشن است."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
