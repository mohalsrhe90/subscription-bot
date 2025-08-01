import telebot
from telebot import types
import json
import os
from keep_alive import keep_alive  # تشغيل السيرفر على Render

# ✅ نستخدم التوكن من متغير بيئة
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = "@tyaf90"  # قناة الاشتراك الإجباري لاستخدام البوت نفسه

bot = telebot.TeleBot(BOT_TOKEN)
SETTINGS_FILE = "settings.json"

# تحميل إعدادات القنوات لكل مجموعة
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

# رسالة الاشتراك في قناة البوت
def force_main_subscription_message():
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("اضغط للاشتراك", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
    markup.add(btn)
    return (
        f"🚸 عذرًا، يجب عليك الاشتراك في قناة البوت أولًا: {CHANNEL_USERNAME}\n\n"
        "✅ بعد الاشتراك، أرسل /start",
        markup
    )

# رسالة الاشتراك في قناة المجموعة
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

# أمر /setchannel لتحديد قناة الاشتراك الإجباري للمجموعة
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
        bot.reply_to(message, "❗️ يجب استخدام هذا الأمر من داخل مجموعة.")

# عند انضمام عضو جديد
@bot.message_handler(content_types=['new_chat_members'])
def handle_new_members(message):
    group_id = str(message.chat.id)
    if group_id not in group_settings:
        return

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

# التحقق من اشتراك الأعضاء عند إرسال رسائل
@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'])
def check_subscription_before_message(message):
    group_id = str(message.chat.id)
    user_id = message.from_user.id

    if group_id not in group_settings:
        return

    required_channel = group_settings[group_id]

    if not is_user_subscribed(required_channel, user_id):
        try:
            bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

            markup = types.InlineKeyboardMarkup()
            btn = types.InlineKeyboardButton("اشترك الآن", url=f"https://t.me/{required_channel[1:]}")
            markup.add(btn)

            bot.send_message(
                message.chat.id,
                f"📛 عذرًا {message.from_user.first_name}، يجب عليك الاشتراك في القناة التالية أولاً للنشر في المجموعة:\n{required_channel}",
                reply_markup=markup
            )
        except Exception as e:
            print(f"❗️فشل في حذف الرسالة أو إرسال التنبيه: {e}")

# ✅ تشغيل البوت والسيرفر
if __name__ == "__main__":
    keep_alive()
    bot.polling(non_stop=True)
