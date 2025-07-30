import telebot
from telebot import types
import json
import os

BOT_TOKEN = "8263363489:AAEOYKHwQRpCoqRlAPSoVlm2A_pFlh2TJAQ"
CHANNEL_USERNAME = "@tyaf90"

bot = telebot.TeleBot(BOT_TOKEN)

SETTINGS_FILE = "settings.json"

# تحميل الإعدادات
if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        group_settings = json.load(f)
else:
    group_settings = {}

# حفظ الإعدادات
def save_settings():
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(group_settings, f, ensure_ascii=False, indent=2)

# التحقق من اشتراك المستخدم في قناة معينة
def is_user_subscribed(channel, user_id):
    try:
        chat_member = bot.get_chat_member(channel, user_id)
        return chat_member.status in ['member', 'creator', 'administrator']
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False

# رسالة الاشتراك في قناة البوت الرسمية
def force_main_subscription_message():
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("اضغط للاشتراك", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
    markup.add(btn)
    return (
        f"🚸 عذرًا، يجب عليك الاشتراك في قناة البوت أولًا: {CHANNEL_USERNAME}\n\n"
        "✅ بعد الاشتراك، أرسل /start",
        markup
    )

# رسالة الاشتراك في قناة المجموعة الخاصة
def force_group_subscription_message(channel):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("اشترك هنا", url=f"https://t.me/{channel[1:]}")
    markup.add(btn)
    return (
        f"🚫 يجب عليك الاشتراك أولًا في: {channel}\nثم أعد المحاولة.",
        markup
    )

# أمر /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not is_user_subscribed(CHANNEL_USERNAME, user_id):
        text, markup = force_main_subscription_message()
        bot.send_message(user_id, text, reply_markup=markup)
    else:
        bot.send_message(user_id, "✅ أهلاً بك، أنت مشترك ويمكنك الآن استخدام البوت.\nأضفني إلى مجموعتك واستخدم الأمر /setchannel")

# أمر /setchannel @channel_name
@bot.message_handler(commands=['setchannel'])
def set_channel(message):
    if message.chat.type in ['group', 'supergroup']:
        try:
            args = message.text.split()
            if len(args) < 2 or not args[1].startswith("@"):
                bot.reply_to(message, "❗️ يرجى استخدام الأمر بهذا الشكل:\n/setchannel @channel_name")
                return
            target_channel = args[1]
            group_id = str(message.chat.id)
            group_settings[group_id] = target_channel
            save_settings()
            bot.reply_to(message, f"✅ تم ضبط قناة الاشتراك الإجباري: {target_channel}")
        except Exception as e:
            print(f"Error in /setchannel: {e}")
            bot.reply_to(message, "❌ حدث خطأ أثناء الحفظ.")
    else:
        bot.reply_to(message, "❗️ يجب استخدام هذا الأمر من داخل مجموعة أو قناة.")

# التعامل مع الأعضاء الجدد
@bot.message_handler(content_types=['new_chat_members'])
def handle_new_members(message):
    group_id = str(message.chat.id)
    if group_id not in group_settings:
        return  # لم يتم ضبط قناة اشتراك لهذه المجموعة

    required_channel = group_settings[group_id]

    for member in message.new_chat_members:
        user_id = member.id
        if not is_user_subscribed(required_channel, user_id):
            try:
                bot.restrict_chat_member(
                    message.chat.id,
                    user_id,
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False
                )
                text, markup = force_group_subscription_message(required_channel)
                bot.send_message(user_id, text, reply_markup=markup)
            except Exception as e:
                print(f"❗️فشل في تقييد العضو: {e}")

if __name__ == "__main__":
    bot.polling(non_stop=True)
