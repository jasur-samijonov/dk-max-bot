import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("telegram-bot\credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key('1DAwKZsTL2d1UwRLhO3pZ9nQK_uYejurG-J72y2MjbCo').sheet1

# Telegram Bot Token
BOT_TOKEN = '6894620110:AAGjj00E36yQK0dNLDO7WonwGzgwnG0OZlQ'

# States
ASK_NAME, ASK_REQUEST_TYPE, ASK_DETAILS = range(3)

# Request types
REQUEST_TYPES = [
    "Missing mile", "Extra stop pay", "Layover", "Detention", 
    "6 weeks on the road bonus", "No violation inspection bonus", "Other"
]

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Welcome! Please enter your name (names should not contain numbers):")
    return ASK_NAME

def ask_request_type(update: Update, context: CallbackContext) -> int:
    name = update.message.text
    if not name.isalpha():
        update.message.reply_text("Invalid name. Please use only letters.")
        return ASK_NAME
    context.user_data['name'] = name
    reply_keyboard = [[request] for request in REQUEST_TYPES]
    update.message.reply_text(
        "Hi, {}! Please choose the type of request:".format(name),
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return ASK_REQUEST_TYPE

def ask_details(update: Update, context: CallbackContext) -> int:
    request_type = update.message.text
    context.user_data['request_type'] = request_type
    if request_type == "Missing mile":
        update.message.reply_text("Please provide the load info and whether it was a deadhead (provide date if so).")
    elif request_type == "Extra stop pay":
        update.message.reply_text("Please provide the load number.")
    elif request_type == "Layover":
        update.message.reply_text("Please provide the date (period from-to).")
    elif request_type == "Detention":
        update.message.reply_text("Please provide the load number.")
    elif request_type == "6 weeks on the road bonus":
        update.message.reply_text("Request submitted!")
        # Store in Google Sheets directly without further details
        store_request(context.user_data['name'], request_type, "N/A")
        return ConversationHandler.END
    elif request_type == "No violation inspection bonus":
        update.message.reply_text("Please provide the date of inspection.")
    elif request_type == "Other":
        update.message.reply_text("Please provide more details about your request.")
    return ASK_DETAILS

def save_request(update: Update, context: CallbackContext) -> int:
    details = update.message.text
    context.user_data['details'] = details
    store_request(context.user_data['name'], context.user_data['request_type'], details)
    update.message.reply_text("Your request has been submitted!")
    return ConversationHandler.END

def store_request(name, request_type, details):
    # Store the data into Google Sheets
    sheet.append_row([name, request_type, details])

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Request canceled.")
    return ConversationHandler.END

def main():
    # Create the Updater and pass it your bot's token
    updater = Updater(BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Define the conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_NAME: [MessageHandler(Filters.text & ~Filters.command, ask_request_type)],
            ASK_REQUEST_TYPE: [MessageHandler(Filters.text & ~Filters.command, ask_details)],
            ASK_DETAILS: [MessageHandler(Filters.text & ~Filters.command, save_request)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Add conversation handler to dispatcher
    dp.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you send a signal to stop (Ctrl+C)
    updater.idle()

if __name__ == '__main__':
    main()
