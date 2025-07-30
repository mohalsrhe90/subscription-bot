import telebot
from telebot import types

# توكن البوت من BotFather
BOT_TOKEN = "8263363489:AAEOYKHwQRpCoqRlAPSoVlm2A_pFlh2TJAQ"
bot = telebot.TeleBot(BOT_TOKEN)

# اسم قناة الاشتراك الإجباري
CHANNEL_USERNAME = "@tyaf90"

# دالة التحقق من الاشتراك في القناة
def is_user_subscribed(user_id):
    try:
        chat_member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status in ['member', 'creator', 'administrator']
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False

# رسالة الاشتراك الإجباري
def force_subscription_message():
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("يجب عليك الاشتراك في قناة البوت لاستخدامه", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
    markup.add(btn)
    return (
        "📢 يعمل هذا البوت على زيادة الاشتراكات وتعزيز التفاعل في القنوات والمجموعات من خلال الاشتراك الإجباري.\n\n"
        "🚸| عذراً عزيزي .\n"
        f"🔰| عليك الاشتراك في قناة البوت لتتمكن من استخدامه: {CHANNEL_USERNAME}\n"
        "‼️| اشترك ثم ارسل /start"
    , markup)

# أمر /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not is_user_subscribed(user_id):
        text, markup = force_subscription_message()
        bot.send_message(user_id, text, reply_markup=markup)
    else:
        bot.send_message(user_id, "✅ أهلاً بك! أنت مشترك في القناة ويمكنك استخدام البوت الآن.")

# التحقق من رسائل المستخدمين في المجموعات
@bot.message_handler(func=lambda message: True, content_types=['text'])
def check_subscription_in_groups(message):
    if message.chat.type in ['group', 'supergroup']:
        user_id = message.from_user.id
        if not is_user_subscribed(user_id):
            text, markup = force_subscription_message()
            bot.reply_to(message, text, reply_markup=markup)
            try:
                bot.delete_message(message.chat.id, message.message_id)
            except:
                pass  # في حال لم يكن للبوت صلاحية حذف الرسائل

bot.polling()
