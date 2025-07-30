import telebot
from telebot import types
import json
import os
from keep_alive import keep_alive  # لتشغيل السيرفر على Render

BOT_TOKEN = "8263363489:AAEOYKHwQRpCoqRlAPSoVlm2A_pFlh2TJAQ"
CHANNEL_USERNAME = "@tyaf90"

bot = telebot.TeleBot(BOT_TOKEN)
SETTINGS_FILE = "settings.json"

# تحميل إعدادات القنوات الخاصة بالمجموعات
if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        group_settings = json.load(f)
else:
    group_settings = {}

# حفظ الإعدادات
def save_settings():
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(group_settings, f, ensure_ascii=False, indent=2)

# التحقق من الاشتراك في قناة
def is_user_subscribed(channel, user_id):
    try:
        chat_member = bot.get_chat_member(channel, user_id)
        return chat_member.status in ['member', 'creator', 'administrator']
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False

# رسالة الاشتراك الإجباري
def force_group_subscription_message(channel, user):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("اشترك الآن", url=f"https://t.me/{channel[1:]}")
    markup.add(btn)
    return (
        f"📛 عذرًا [{user.first_name}](tg://user?id={user.id})، يجب عليك الاشتراك في القناة التالية أولاً:\n{channel}",
        markup
    )

# أمر /start (تحقق من الاشتراك في القناة العامة)
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not is_user_subscribed(CHANNEL_USERNAME, user_id):
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("اضغط للاشتراك", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
        markup.add(btn)
        bot.send_message(user_id, f"🚸 عذرًا، يجب عليك الاشتراك في قناة البوت أولًا: {CHANNEL_USERNAME}\n\n✅ بعد الاشتراك، أرسل /start", reply_markup=markup)
    else:
        bot.send_message(user_id, "✅ أهلاً بك، أنت مشترك ويمكنك الآن استخدام البوت.\nأضفني إلى مجموعتك واستخدم الأمر /setchannel")

# أمر /setchannel لتحديد قناة الاشتراك الخاصة بالمجموعة
@bot.message_handler(commands=['setchannel'])
def set_channel(message):
    if message.chat.type in ['group', 'supergroup']:
        args = message.text.split()
        if len(args) < 2 or not args[1].startswith("@"):
            bot.reply_to(message, "❗️ يرجى استخدام الأمر بهذا الشكل:\n/setchannel @channel_name")
            return
        target_channel = args[1]
        group_id = str(message.chat.id)
        group_settings[group_id] = target_channel
        save_settings()
        bot.reply_to(message, f"✅ تم ضبط قناة الاشتراك الإجباري: {target_channel}")
    else:
        bot.reply_to(message, "❗️ يجب استخدام هذا الأمر من داخل مجموعة.")

# 🔄 عدم تقييد الأعضاء الجدد عند انضمامهم
@bot.message_handler(content_types=['new_chat_members'])
def handle_new_members(message):
    pass  # لا نفعل شيئًا عند دخول عضو جديد

# ✅ عندما يرسل أي عضو رسالة داخل مجموعة
@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'])
def check_subscription_before_message(message):
    group_id = str(message.chat.id)
    user_id = message.from_user.id

    if group_id not in group_settings:
        return

    required_channel = group_settings[group_id]

    if not is_user_subscribed(required_channel, user_id):
        try:
            # حذف الرسالة
            bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

            # إرسال رسالة داخل المجموعة تطلب الاشتراك
            text, markup = force_group_subscription_message(required_channel, message.from_user)
            bot.send_message(
                message.chat.id,
                text,
                reply_markup=markup,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"❗️فشل في حذف الرسالة أو إرسال التنبيه: {e}")

# تشغيل البوت والسيرفر
if __name__ == "__main__":
    keep_alive()
    bot.polling(non_stop=True)
