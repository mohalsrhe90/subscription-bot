import telebot
from telebot import types
from flask import Flask, request
import json
import os

# بيانات البوت
BOT_TOKEN = "8263363489:AAEOYKHwQRpCoqRlAPSoVlm2A_pFlh2TJAQ"
CHANNEL_USERNAME = "@tyaf90"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
WEBHOOK_URL = "https://subscription-bot-85rq.onrender.com/"

SETTINGS_FILE = "settings.json"

# تحميل الإعدادات
if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        group_settings = json.load(f)
else:
    group_settings = {}

def save_settings():
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(group_settings, f, ensure_ascii=False, indent=2)

def is_user_subscribed(channel, user_id):
    try:
        chat_member = bot.get_chat_member(channel, user_id)
        return chat_member.status in ['member', 'creator', 'administrator']
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False

def force_main_subscription_message():
    markup = types.InlineKeyboardMarkup()
    btn_sub = types.InlineKeyboardButton("📢 اضغط هنا للاشتراك", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
    btn_check = types.InlineKeyboardButton("✅ تحقّقت من الاشتراك", callback_data="check_main_subscription")
    markup.add(btn_sub)
    markup.add(btn_check)
    return (
        f"🚸 عذرًا، يجب عليك الاشتراك في قناة البوت أولًا:\n{CHANNEL_USERNAME}\n\n"
        "🧭 اضغط على الزر للاشتراك.\n"
        "✅ بعد الاشتراك، اضغط على زر (تحقّقت من الاشتراك) بالأسفل.",
        markup
    )

# عند الضغط على زر "تحققت من الاشتراك" في الخاص
@bot.callback_query_handler(func=lambda call: call.data == "check_main_subscription")
def callback_check_subscription(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if is_user_subscribed(CHANNEL_USERNAME, user_id):
        bot.edit_message_text(
            "✅ تم التحقق بنجاح! أنت الآن مشترك ويمكنك استخدام البوت.",
            chat_id=chat_id,
            message_id=call.message.message_id
        )
    else:
        bot.answer_callback_query(
            call.id,
            "❗️ لم يتم العثور على اشتراكك بعد. تأكد من أنك مشترك بالفعل، ثم حاول مجددًا.",
            show_alert=True
        )

# أوامر البوت
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if not is_user_subscribed(CHANNEL_USERNAME, user_id):
        text, markup = force_main_subscription_message()
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "✅ أهلاً بك، أنت مشترك ويمكنك الآن استخدام البوت.\nأضفني إلى مجموعتك واستخدم الأمر /setchannel")

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

# التحقق من الاشتراك داخل المجموعة
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
            btn_sub = types.InlineKeyboardButton("📢 اضغط للاشتراك", url=f"https://t.me/{required_channel[1:]}")
            btn_check = types.InlineKeyboardButton("✅ تحقّقت من الاشتراك", callback_data=f"check_group_subscription:{required_channel}:{message.chat.id}")
            markup.add(btn_sub)
            markup.add(btn_check)

            bot.send_message(
                message.chat.id,
                f"📛 عذرًا {message.from_user.first_name}، يجب عليك الاشتراك في القناة التالية أولاً للنشر في المجموعة:\n{required_channel}\n\n"
                "🧭 اضغط على (الاشتراك)، ثم اضغط (تحقّقت من الاشتراك).",
                reply_markup=markup
            )
        except Exception as e:
            print(f"❗️فشل في حذف الرسالة أو إرسال التنبيه: {e}")

# عند الضغط على "تحققت من الاشتراك" داخل المجموعة
@bot.callback_query_handler(func=lambda call: call.data.startswith("check_group_subscription"))
def callback_check_group_subscription(call):
    try:
        _, channel, group_id = call.data.split(":")
        user_id = call.from_user.id

        if is_user_subscribed(channel, user_id):
            bot.edit_message_text(
                f"✅ تم التحقق من اشتراكك في {channel} بنجاح!\nيمكنك الآن النشر في المجموعة.",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )
        else:
            bot.answer_callback_query(
                call.id,
                "❗️أنت لم تشترك بعد.\nيرجى الاشتراك في القناة ثم الضغط مجددًا.",
                show_alert=True
            )
    except Exception as e:
        print(f"خطأ في التحقق اليدوي من الاشتراك في المجموعة: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ، حاول مجددًا لاحقًا.", show_alert=True)

# Webhook endpoint
@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == "POST":
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return "Bot is running and webhook is set!", 200

# تشغيل السيرفر وضبط Webhook
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host='0.0.0.0', port=8080)
