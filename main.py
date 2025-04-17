import yt_dlp
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, filters

TOKEN = "7749906128:AAGTgDeEWm_jNmv8IaCLZmijexwZBJM83Pg"

def download_video(update, context, url, output_path="."):
    try:
        ydl_opts = {
            'outtmpl': f'{output_path}/%(title)s-%(id)s.%(ext)s',
            'format': 'bestvideo+bestaudio/best',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        update.message.reply_text("Video downloaded successfully!")
    except Exception as e:
        update.message.reply_text(f"Error downloading video: {e}")

def download_audio(update, context, url, output_path="."):
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
        update.message.reply_text("Audio downloaded successfully!")
    except Exception as e:
        update.message.reply_text(f"Error downloading audio: {e}")

def start(update, context):
    update.message.reply_text("Welcome to the video downloader bot! Send me a link to download a video or audio.")

def help_command(update, context):
    update.message.reply_text("Send me a link to download a video or audio. Use /video to download video, /audio to download audio.")

def video_command(update, context):
    url = update.message.text.split(' ')[1]
    download_video(update, context, url)

def audio_command(update, context):
    url = update.message.text.split(' ')[1]
    download_audio(update, context, url)

def handle_message(update, context):
    text = str(update.message.text)
    if "youtube.com" in text or "youtu.be" in text:
        update.message.reply_text("Choose an option: /video [url] to download video, /audio [url] to download audio.")
    else:
        update.message.reply_text("Please send a valid YouTube link.")

if __name__ == '__main__':
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("video", video_command))
    dp.add_handler(CommandHandler("audio", audio_command))
    dp.add_handler(MessageHandler(filters.text, handle_message))

    updater.start_polling()
    updater.idle()