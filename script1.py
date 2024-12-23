import asyncio
import nest_asyncio
import requests
from bs4 import BeautifulSoup  # BeautifulSoup for parsing HTML
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ConversationHandler, 
    ContextTypes
)

# Apply nest_asyncio to allow asyncio event loop inside Jupyter notebooks or similar environments.
nest_asyncio.apply()

# Define the states for the conversation
USERNAME, MESSAGE = range(2)

# Function to simulate generating a link
def generate_telegram_link(username, message=""):
    base_url = "https://telegram.koyeb.app/"  # Replace with the actual URL of the service
    params = {
        "username": username,
        "message": message
    }

    # Simulate sending a POST request to generate the link
    response = requests.post(base_url, data=params)

    if response.status_code == 200:
        # Parse the HTML content and extract the shortened link
        soup = BeautifulSoup(response.text, "html.parser")
        link_tag = soup.find("a", {"id": "shortLink"})  # Extract the link from <a id="shortLink">
        
        if link_tag:
            return link_tag.get("href")  # Return the href attribute which is the shortened link
        else:
            return "Failed to extract the link from the response."
    else:
        return "Failed to generate the link."

# /start command to show the keyboard button options
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [KeyboardButton("Create Link 🔗")]  # This creates the button on the keyboard
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Welcome! Press 'Create Link 🔗' to start generating a link.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

# Function to handle "Create Link 🔗" button click (this is now a message handler, not a callback)
async def create_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Show a message asking for the username and add a cancel button to the keyboard
    keyboard = [
        [KeyboardButton("❌Cancel❌")]  # Button to cancel the operation
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "Please send your Telegram username.",
        reply_markup=reply_markup
    )
    return USERNAME

# Function to handle the username input
async def username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Ignore the "❌Cancel❌" message input in the username step
    if update.message.text == "❌Cancel❌":
        return await cancel(update, context)  # If it's cancel, stop the process

    # Remove "@" from the username if it exists
    username = update.message.text.strip()
    if username.startswith('@'):
        username = username[1:]  # Remove the '@' symbol

    context.user_data["username"] = username  # Save the cleaned username
    keyboard = [
        [KeyboardButton("❌Cancel❌"), KeyboardButton("Get Link 🔗")]  # Add Get Link button
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "Got it! Now, please send your message (optional). Or click 'Get Link 🔗' to create the link without a message.",
        reply_markup=reply_markup
    )
    return MESSAGE

# Function to handle the message input and generate the link
async def message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Ignore the "❌Cancel❌" message input in the message step
    if update.message.text == "❌Cancel❌":
        return await cancel(update, context)  # If it's cancel, stop the process
    
    username = context.user_data["username"]
    message = update.message.text

    # If the user clicks "Get Link 🔗" without sending a message
    if message == "Get Link 🔗":
        generated_link = generate_telegram_link(username)
        # Send the link as an inline button as well
        inline_keyboard = [[InlineKeyboardButton("Open Link", url=generated_link)]]
        inline_markup = InlineKeyboardMarkup(inline_keyboard)
        await update.message.reply_text(f"Here is your generated link: {generated_link}", reply_markup=inline_markup)
        
        # After sending the link, show the "Create Link 🔗" button again
        await show_create_link_button(update)
        return ConversationHandler.END

    # Otherwise, generate the link with the message
    generated_link = generate_telegram_link(username, message)

    # Check if the generated link is too long (max length 4096 characters)
    if len(generated_link) > 4096:
        # Split the message into chunks if it exceeds 4096 characters
        await send_long_message(update, generated_link)
    else:
        # Send the generated link normally and as an inline button
        inline_keyboard = [[InlineKeyboardButton("Open Link", url=generated_link)]]
        inline_markup = InlineKeyboardMarkup(inline_keyboard)
        await update.message.reply_text(f"Here is your generated link: {generated_link}", reply_markup=inline_markup)

    # After sending the link, show the "Create Link 🔗" button again
    await show_create_link_button(update)
    return ConversationHandler.END

# Function to send a long message in chunks
async def send_long_message(update: Update, long_message: str) -> None:
    # Split the message into chunks of 4096 characters
    chunk_size = 4096
    for i in range(0, len(long_message), chunk_size):
        await update.message.reply_text(long_message[i:i + chunk_size])

# Function to show "Create Link 🔗" button again after link generation or cancellation
async def show_create_link_button(update: Update) -> None:
    keyboard = [
        [KeyboardButton("Create Link 🔗")]  # This creates the button again
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Press 'Create Link 🔗' to generate another link.",
        reply_markup=reply_markup
    )

# Function to handle cancellation of the conversation
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Inform the user that the action was cancelled
    await update.message.reply_text("Conversation cancelled. No link was generated.")
    
    # Show the "Create Link 🔗" button again after cancellation
    await show_create_link_button(update)

    # End the conversation and stop listening
    return ConversationHandler.END
