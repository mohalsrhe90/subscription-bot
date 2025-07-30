import telebot
from telebot import types
from flask import Flask, request
import json
import os

# إعدادات البوت
BOT_TOKEN = "YOUR_BOT_TOKEN"
bot = telebot.TeleBot(BOT_TOKEN)
WEBHOOK_URL = "https://your-render-url.onrender.com/"  # عدّل هذا حسب رابط مشروعك على Render
CHANNEL_USERNAME = "@yourchannel"

SETTINGS_FILE = "settings.json"

# تحميل إعدادات القنوات الخاصة بالمجموعات
if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        group_settings = json.load(f)
else:
    group_settings = {}

def save_settings():
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(group_settings, f, ensure_ascii=False, indent=2)

# التحقق من الاشتراك
def is_user_subscribed(channel, user_id):
    try:
        chat_member = bot.get_chat_member(channel, user_id)
        return chat_member.status in ['member', 'creator', 'administrator']
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False

def force_group_subscription_message(channel, user):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("اشترك الآن", url=f"https://t.me/{channel[1:]}")
    markup.add(btn)
    return (
        f"📛 [{user.first_name}](tg://user?id={user.id})، اشترك أولاً في القناة:\n{channel}",
        markup
    )

# /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not is_user_subscribed(CHANNEL_USERNAME, user_id):
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("اضغط للاشتراك", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
        markup.add(btn)
        bot.send_message(user_id, f"🚸 يجب عليك الاشتراك في القناة: {CHANNEL_USERNAME}", reply_markup=markup)
    else:
        bot.send_message(user_id, "✅ تم التحقق من اشتراكك!")

# /setchannel
@bot.message_handler(commands=['setchannel'])
def set_channel(message):
    if message.chat.type in ['group', 'supergroup']:
        args = message.text.split()
        if len(args) < 2 or not args[1].startswith("@"):
            bot.reply_to(message, "❗️ استخدم: /setchannel @channel_name")
            return
        group_id = str(message.chat.id)
        group_settings[group_id] = args[1]
        save_settings()
        bot.reply_to(message, f"✅ تم ضبط قناة الاشتراك: {args[1]}")
    else:
        bot.reply_to(message, "❗️ استخدم هذا الأمر داخل مجموعة فقط.")

# لا تقييد تلقائي — فقط تحقق عند أول رسالة
@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'])
def check_subscription_before_message(message):
    group_id = str(message.chat.id)
    user_id = message.from_user.id

    if group_id not in group_settings:
        return

    required_channel = group_settings[group_id]

    if not is_user_subscribed(required_channel, user_id):
        try:
            bot.delete_message(message.chat.id, message.message_id)
            text, markup = force_group_subscription_message(required_channel, message.from_user)
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
        except Exception as e:
            print(f"Error: {e}")

# إعداد Flask
app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return 'Bot is running!'

@app.route('/', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

# إعداد Webhook عند التشغيل
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
