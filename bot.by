import telebot
import os

API_TOKEN = os.getenv("API_TOKEN")
BOT_MAIN_CHANNEL = os.getenv("BOT_MAIN_CHANNEL")  # قناة البوت الأساسية مثل @tyaf90

bot = telebot.TeleBot(API_TOKEN)

# تحقق من الاشتراك في القناة
def is_user_subscribed(user_id):
    try:
        member = bot.get_chat_member(BOT_MAIN_CHANNEL, user_id)
        return member.status in ['member', 'creator', 'administrator']
    except:
        return False

@bot.message_handler(commands=['start'])
def start(message):
    if not is_user_subscribed(message.from_user.id):
        markup = telebot.types.InlineKeyboardMarkup()
        btn = telebot.types.InlineKeyboardButton("🟢 يجب عليك الاشتراك في قناة البوت لاستخدامه", url=f"https://t.me/{BOT_MAIN_CHANNEL.strip('@')}")
        check = telebot.types.InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check")
        markup.add(btn)
        markup.add(check)
        bot.send_message(message.chat.id,
                         "🚸| عذراً عزيزي.\n🔰| عليك الاشتراك في قناة البوت لتتمكن من استخدامه.\n‼️| اشترك ثم أرسل /start",
                         reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "✅ تم التحقق من الاشتراك، يمكنك الآن استخدام البوت أو إضافته إلى مجموعتك.")

@bot.callback_query_handler(func=lambda call: call.data == "check")
def check_subscription(call):
    if is_user_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ تم التحقق من الاشتراك.")
        bot.send_message(call.message.chat.id, "✅ يمكنك الآن استخدام البوت.")
    else:
        bot.answer_callback_query(call.id, "🚫 لم يتم الاشتراك بعد.")

bot.polling()
