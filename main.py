import telebot

TOKEN = '7217912729:AAHXuGAtqSfYkXQeVg4fY1mZ_aBEKqknqsA'
ADMIN_ID = 6994772164
bot = telebot.TeleBot(TOKEN)

users = set()

@bot.message_handler(commands=['start'])
def start(message):
    users.add(message.from_user.id)
    bot.send_message(message.chat.id, "سلام! به ربات خوش آمدی.\nدستورات:\n📢 /sendall پیام\n👥 /users\n🎮 /daretotruth آیدی")

@bot.message_handler(commands=['users'])
def show_users(message):
    if message.from_user.id == ADMIN_ID:
        user_list = '\n'.join(str(u) for u in users)
        bot.send_message(message.chat.id, f"لیست کاربران ({len(users)}):\n{user_list}")
    else:
        bot.send_message(message.chat.id, "فقط مدیر به این بخش دسترسی دارد.")

@bot.message_handler(commands=['sendall'])
def send_all(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "فقط مدیر می‌تواند پیام همگانی بفرستد.")
    text = message.text.replace('/sendall', '').strip()
    if not text:
        return bot.send_message(message.chat.id, "متن پیام را بعد از /sendall بنویس.")
    count = 0
    for uid in users:
        try:
            bot.send_message(uid, f"📢 پیام مدیریت:\n{text}")
            count += 1
        except:
            continue
    bot.send_message(message.chat.id, f"پیام برای {count} نفر ارسال شد.")

@bot.message_handler(commands=['daretotruth'])
def dare_truth(message):
    parts = message.text.split()
    if len(parts) != 2:
        return bot.send_message(message.chat.id, "مثال درست:\n/daretotruth 123456789")
    try:
        target_id = int(parts[1])
        bot.send_message(target_id, f"🎮 کاربری با آیدی {message.from_user.id} می‌خواهد با شما بازی کند.\nآیا قبول می‌کنید؟ (فعلاً پاسخ دستی دهید)")
        bot.send_message(message.chat.id, f"درخواست ارسال شد به آیدی {target_id}.")
    except:
        bot.send_message(message.chat.id, "خطا در ارسال آیدی.")

bot.infinity_polling()
