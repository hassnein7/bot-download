import yt_dlp
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import re
import os # Import the os module

# Read the bot token from an environment variable for security
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables")

def download_video(update, context, url, output_path=".", message_id=None):
    try:
        ydl_opts = {
            'outtmpl': f'{output_path}/%(title)s-%(id)s.%(ext)s',
            'format': 'bestvideo+bestaudio/best',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=message_id, text="Video downloaded successfully!")
    except Exception as e:
        context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=message_id, text=f"Error downloading video: {e}")


def download_audio(update, context, url, output_path=".", message_id=None):
    try:
        ydl_opts = {
            'outtmpl': f'{output_path}/%(title)s-%(id)s.%(ext)s',
            'extract_audio': True,
            'format': 'bestaudio/best',
            'audioformat': 'mp3',
            'audioquality': '0',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=message_id, text="Audio downloaded successfully!")
    except Exception as e:
        context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=message_id, text=f"Error downloading audio: {e}")


def start(update, context):
    update.message.reply_text("Welcome to the video downloader bot! Send me a link to download a video or audio.")

def help_command(update, context):
    update.message.reply_text("Send me a link from any website to download the video. If it's a YouTube link, I'll ask if you want video or audio.")



# Basic URL validation regex
URL_REGEX = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"

def handle_message(update, context):
    text = str(update.message.text)
    match = re.search(URL_REGEX, text)
    if match:
        url = match.group(0)
        context.user_data['url'] = url # Store URL for callback
        if "youtube.com" in url or "youtu.be" in url:
            keyboard = [
                [InlineKeyboardButton("Video", callback_data='video')],
                [InlineKeyboardButton("Audio", callback_data='audio')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text('Choose download format for YouTube link:', reply_markup=reply_markup)
        else:
            # Directly download video for non-YouTube links
            sent_message = update.message.reply_text("Starting video download...")
            download_video(update, context, url, message_id=sent_message.message_id)
    else:
        update.message.reply_text("Please send a valid link.")

def button_handler(update, context):
    query = update.callback_query
    query.answer()
    choice = query.data
    url = context.user_data.get('url')

    if not url:
        query.edit_message_text(text="Sorry, I couldn't find the URL. Please send it again.")
        return

    # Edit the original message to show processing status
    query.edit_message_text(text=f"Starting {choice} download...")
    message_id = query.message.message_id

    if choice == 'video':
        download_video(update, context, url, message_id=message_id)
    elif choice == 'audio':
        download_audio(update, context, url, message_id=message_id)

    # Clear the stored URL after processing
    if 'url' in context.user_data:
        del context.user_data['url']

if __name__ == '__main__':
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    # Use MessageHandler with regex filter for URLs first
    dp.add_handler(MessageHandler(filters.text & filters.entity("url") | filters.text & filters.entity("text_link"), handle_message))
    # Add a handler for button clicks
    dp.add_handler(CallbackQueryHandler(button_handler))
    # Fallback for non-URL text messages
    dp.add_handler(MessageHandler(filters.text & ~filters.command, handle_message))

    updater.start_polling()
    updater.idle()