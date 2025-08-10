import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    Dispatcher
)
from flask import Flask, request
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Bot configuration
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
PREMIUM_COST = 100  # Cost in your currency

# Database simulation
users_db = {}
keys_db = {}
redeem_requests = {}

# Initialize bot
updater = Updater(TOKEN, use_context=True)
dispatcher = updater.dispatcher

def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id not in users_db:
        users_db[user_id] = {
            'is_premium': False,
            'premium_until': None,
            'redeem_used': False,
            'banned': False
        }
    
    keyboard = [
        [InlineKeyboardButton("1. Redeem Request", callback_data='redeem')],
        [InlineKeyboardButton("2. Buy Premium", callback_data='buy_premium')],
        [InlineKeyboardButton("3. Services", callback_data='services')],
        [InlineKeyboardButton("4. Dev", callback_data='dev')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        text="🌟 Welcome to Premium Bot 🌟\n\n"
             "Please select an option:",
        reply_markup=reply_markup
    )

def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    
    if users_db.get(user_id, {}).get('banned', False):
        query.edit_message_text(text="🚫 You are banned from using this bot.")
        return
    
    if query.data == 'redeem':
        handle_redeem(query, user_id)
    elif query.data == 'buy_premium':
        handle_buy_premium(query, user_id)
    elif query.data == 'services':
        handle_services(query)
    elif query.data == 'dev':
        handle_dev(query)
    elif query.data.startswith('service_'):
        handle_service_selection(query)
    elif query.data == 'back_to_main':
        start(update, context)

def handle_redeem(query, user_id):
    user_data = users_db.get(user_id, {})
    
    if user_data.get('banned', False):
        query.edit_message_text(text="🚫 You are banned from using this bot.")
        return
    
    if not user_data.get('is_premium', False) and user_data.get('redeem_used', False):
        query.edit_message_text(
            text="❌ You've already used your free redeem request.\n"
                 "Upgrade to premium for unlimited redeems."
        )
        return
    
    query.edit_message_text(
        text="📝 Please enter your redeem details in the format:\n\n"
             "<b>Service Name</b>\n"
             "<b>Account Details</b>\n\n"
             "Example:\n"
             "Netflix\n"
             "Email: example@mail.com | Password: 12345",
        parse_mode='HTML'
    )

def handle_buy_premium(query, user_id):
    keyboard = [
        [InlineKeyboardButton("Back", callback_data='back_to_main')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        text=f"💎 Premium Membership\n\n"
             f"• Unlimited redeem requests\n"
             f"• Priority support\n"
             f"• Special features\n\n"
             f"Cost: ₹{PREMIUM_COST}\n\n"
             f"Contact admin for payment details.",
        reply_markup=reply_markup
    )

def handle_services(query):
    keyboard = [
        [InlineKeyboardButton("1. Prime Video", callback_data='service_prime')],
        [InlineKeyboardButton("2. Spotify", callback_data='service_spotify')],
        [InlineKeyboardButton("3. Crunchyroll", callback_data='service_crunchyroll')],
        [InlineKeyboardButton("4. Turbo VPN", callback_data='service_turbovpn')],
        [InlineKeyboardButton("5. Hotspot Shield VPN", callback_data='service_hotspot')],
        [InlineKeyboardButton("Back", callback_data='back_to_main')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        text="📡 Available Services\n\n"
             "Please select a service:",
        reply_markup=reply_markup
    )

def handle_service_selection(query):
    service = query.data.split('_')[1]
    service_names = {
        'prime': 'Prime Video',
        'spotify': 'Spotify',
        'crunchyroll': 'Crunchyroll',
        'turbovpn': 'Turbo VPN',
        'hotspot': 'Hotspot Shield VPN'
    }
    
    query.edit_message_text(
        text=f"ℹ️ {service_names[service]} Information\n\n"
             f"• Premium accounts available\n"
             f"• 99% uptime\n"
             f"• 24/7 support\n\n"
             f"Use the main menu to request this service."
    )

def handle_dev(query):
    query.edit_message_text(
        text="👨‍💻 Developer Contact:\n\n"
             "@YourAizen"
    )

# Admin commands
def admin_broadcast(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        update.message.reply_text("❌ Admin only command.")
        return
    
    if not context.args:
        update.message.reply_text("Usage: /broadcast Your message here")
        return
    
    message = ' '.join(context.args)
    for user_id in users_db:
        try:
            context.bot.send_message(chat_id=user_id, text=f"📢 Admin Broadcast:\n\n{message}")
        except Exception as e:
            logger.error(f"Failed to send to {user_id}: {e}")
    
    update.message.reply_text(f"✅ Broadcast sent to {len(users_db)} users.")

def admin_gen_key(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        update.message.reply_text("❌ Admin only command.")
        return
    
    if len(context.args) != 1 or not context.args[0].isdigit():
        update.message.reply_text("Usage: /genk DAYS")
        return
    
    days = int(context.args[0])
    key = os.urandom(8).hex()
    expiry = datetime.now() + timedelta(days=days)
    
    keys_db[key] = {
        'days': days,
        'expiry': expiry.strftime('%Y-%m-%d'),
        'used': False,
        'used_by': None
    }
    
    update.message.reply_text(
        f"🔑 Premium Key Generated\n\n"
        f"Key: <code>{key}</code>\n"
        f"Validity: {days} days\n"
        f"Expires: {expiry.strftime('%Y-%m-%d')}\n\n"
        f"Share this with the user.",
        parse_mode='HTML'
    )

def admin_ban(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        update.message.reply_text("❌ Admin only command.")
        return
    
    if len(context.args) < 1:
        update.message.reply_text("Usage: /ban USER_ID")
        return
    
    try:
        user_id = int(context.args[0])
        users_db[user_id]['banned'] = True
        update.message.reply_text(f"✅ User {user_id} has been banned.")
    except (ValueError, KeyError):
        update.message.reply_text("❌ Invalid user ID.")

def admin_unban(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        update.message.reply_text("❌ Admin only command.")
        return
    
    if len(context.args) < 1:
        update.message.reply_text("Usage: /unban USER_ID")
        return
    
    try:
        user_id = int(context.args[0])
        users_db[user_id]['banned'] = False
        update.message.reply_text(f"✅ User {user_id} has been unbanned.")
    except (ValueError, KeyError):
        update.message.reply_text("❌ Invalid user ID.")

# Flask route for webhook
@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), updater.bot)
    dispatcher.process_update(update)
    return 'ok'

@app.route('/')
def index():
    return "Bot is running!"

# Set up handlers
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CallbackQueryHandler(button_handler))
dispatcher.add_handler(CommandHandler('broadcast', admin_broadcast))
dispatcher.add_handler(CommandHandler('genk', admin_gen_key))
dispatcher.add_handler(CommandHandler('ban', admin_ban))
dispatcher.add_handler(CommandHandler('unban', admin_unban))

def main():
    # For production with webhook
    updater.bot.set_webhook(url=f'https://your-render-app-name.onrender.com/{TOKEN}')
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))

if __name__ == '__main__':
    # For local testing
    updater.start_polling()
    updater.idle()
