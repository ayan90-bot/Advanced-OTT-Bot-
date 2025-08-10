import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
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
PREMIUM_COST = 100

# Database simulation
users_db = {}
keys_db = {}
redeem_requests = {}

# Initialize bot
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    
    await update.message.reply_text(
        text="🌟 Welcome to Premium Bot 🌟\n\nPlease select an option:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if users_db.get(user_id, {}).get('banned', False):
        await query.edit_message_text(text="🚫 You are banned from using this bot.")
        return
    
    if query.data == 'redeem':
        await handle_redeem(query, user_id)
    elif query.data == 'buy_premium':
        await handle_buy_premium(query)
    elif query.data == 'services':
        await handle_services(query)
    elif query.data == 'dev':
        await handle_dev(query)
    elif query.data.startswith('service_'):
        await handle_service_selection(query)
    elif query.data == 'back_to_main':
        await start(update, context)

async def handle_redeem(query, user_id):
    user_data = users_db.get(user_id, {})
    
    if user_data.get('banned', False):
        await query.edit_message_text(text="🚫 You are banned from using this bot.")
        return
    
    if not user_data.get('is_premium', False) and user_data.get('redeem_used', False):
        await query.edit_message_text(
            text="❌ You've already used your free redeem request.\nUpgrade to premium for unlimited redeems."
        )
        return
    
    await query.edit_message_text(
        text="📝 Please enter your redeem details in the format:\n\n<b>Service Name</b>\n<b>Account Details</b>\n\nExample:\nNetflix\nEmail: example@mail.com | Password: 12345",
        parse_mode='HTML'
    )

async def handle_buy_premium(query):
    keyboard = [[InlineKeyboardButton("Back", callback_data='back_to_main')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=f"💎 Premium Membership\n\n• Unlimited redeem requests\n• Priority support\n• Special features\n\nCost: ₹{PREMIUM_COST}\n\nContact admin for payment details.",
        reply_markup=reply_markup
    )

async def handle_services(query):
    keyboard = [
        [InlineKeyboardButton("1. Prime Video", callback_data='service_prime')],
        [InlineKeyboardButton("2. Spotify", callback_data='service_spotify')],
        [InlineKeyboardButton("3. Crunchyroll", callback_data='service_crunchyroll')],
        [InlineKeyboardButton("4. Turbo VPN", callback_data='service_turbovpn')],
        [InlineKeyboardButton("5. Hotspot Shield VPN", callback_data='service_hotspot')],
        [InlineKeyboardButton("Back", callback_data='back_to_main')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="📡 Available Services\n\nPlease select a service:",
        reply_markup=reply_markup
    )

async def handle_service_selection(query):
    service = query.data.split('_')[1]
    service_names = {
        'prime': 'Prime Video',
        'spotify': 'Spotify',
        'crunchyroll': 'Crunchyroll',
        'turbovpn': 'Turbo VPN',
        'hotspot': 'Hotspot Shield VPN'
    }
    await query.edit_message_text(
        text=f"ℹ️ {service_names[service]} Information\n\n• Premium accounts available\n• 99% uptime\n• 24/7 support\n\nUse the main menu to request this service."
    )

async def handle_dev(query):
    await query.edit_message_text(text="👨‍💻 Developer Contact:\n\n@YourAizen")

# Flask route
@app.route('/')
def index():
    return "Bot is running!"

@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    webhook_url = f'https://{os.getenv("RENDER_EXTERNAL_HOSTNAME")}/{TOKEN}'
    application.bot.set_webhook(webhook_url)
    return "Webhook set successfully"

# Register handlers
application.add_handler(CommandHandler('start', start))
application.add_handler(CallbackQueryHandler(button_handler))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
else:
    application.run_webhook(
        listen='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        webhook_url=f'https://{os.getenv("RENDER_EXTERNAL_HOSTNAME")}/{TOKEN}'
    )
