import yt_dlp
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
import re
import os
import logging
from urllib.parse import urlparse

# إعداد التسجيل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# قراءة رمز البوت من متغيرات البيئة
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("لم يتم العثور على BOT_TOKEN في متغيرات البيئة")

# تعبير منتظم للتحقق من صحة الروابط
URL_REGEX = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"

def is_youtube_url(url):
    """التحقق مما إذا كان الرابط من يوتيوب"""
    parsed_url = urlparse(url)
    return 'youtube.com' in parsed_url.netloc or 'youtu.be' in parsed_url.netloc

def is_audio_url(url):
    """التحقق مما إذا كان الرابط يشير إلى ملف صوتي"""
    audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac']
    parsed_url = urlparse(url)
    path = parsed_url.path.lower()
    return any(path.endswith(ext) for ext in audio_extensions)

def download_content(update, context, url, is_audio=False, message_obj=None):
    """تحميل المحتوى من الرابط"""
    try:
        # إنشاء رسالة حالة إذا لم يتم توفيرها
        if not message_obj:
            message_obj = update.message.reply_text("جاري التحميل... ⏳")
        
        # تكوين خيارات التحميل
        ydl_opts = {
            'outtmpl': './downloads/%(title)s-%(id)s.%(ext)s',
            'format': 'bestaudio/best' if is_audio else 'bestvideo+bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if is_audio else [],
            'progress_hooks': [lambda d: progress_hook(d, message_obj)],
        }
        
        # إنشاء مجلد التنزيلات إذا لم يكن موجودًا
        os.makedirs('./downloads', exist_ok=True)
        
        # تحميل المحتوى
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # تعديل اسم الملف إذا كان صوتًا
            if is_audio and not filename.endswith('.mp3'):
                filename = os.path.splitext(filename)[0] + '.mp3'
            
            # إرسال الملف
            message_obj.edit_text("جاري إرسال الملف... 📤")
            
            if os.path.exists(filename):
                if is_audio:
                    context.bot.send_audio(
                        chat_id=update.effective_chat.id,
                        audio=open(filename, 'rb'),
                        title=info.get('title', 'Audio'),
                        caption=f"🎵 {info.get('title', 'Audio')}",
                    )
                else:
                    context.bot.send_video(
                        chat_id=update.effective_chat.id,
                        video=open(filename, 'rb'),
                        caption=f"🎬 {info.get('title', 'Video')}",
                        supports_streaming=True,
                    )
                
                # حذف الملف بعد الإرسال
                os.remove(filename)
                message_obj.edit_text("✅ تم التحميل والإرسال بنجاح!")
            else:
                message_obj.edit_text("❌ لم يتم العثور على الملف بعد التحميل.")
    except Exception as e:
        logger.error(f"خطأ في التحميل: {str(e)}")
        message_obj.edit_text(f"❌ حدث خطأ أثناء التحميل: {str(e)}")

def progress_hook(d, message_obj):
    """تحديث حالة التقدم"""
    if d['status'] == 'downloading':
        try:
            percent = d.get('_percent_str', 'غير معروف')
            speed = d.get('_speed_str', 'غير معروف')
            eta = d.get('_eta_str', 'غير معروف')
            message_obj.edit_text(
                f"جاري التحميل... ⏳\n"
                f"التقدم: {percent}\n"
                f"السرعة: {speed}\n"
                f"الوقت المتبقي: {eta}"
            )
        except Exception as e:
            logger.error(f"خطأ في تحديث التقدم: {str(e)}")

def start(update: Update, context: CallbackContext):
    """التعامل مع أمر البدء"""
    update.message.reply_text(
        "👋 مرحبًا بك في بوت التحميل!\n\n"
        "🔹 أرسل لي رابط فيديو أو صوت من أي موقع وسأقوم بتحميله لك.\n"
        "🔹 إذا كان الرابط من يوتيوب، سأسألك إذا كنت تريد تحميله كفيديو أو صوت.\n\n"
        "جرب الآن! 🚀"
    )

def handle_message(update: Update, context: CallbackContext):
    """التعامل مع الرسائل الواردة"""
    text = update.message.text
    match = re.search(URL_REGEX, text)
    
    if match:
        url = match.group(0)
        
        if is_youtube_url(url):
            # إذا كان الرابط من يوتيوب، اعرض خيارات التحميل
            keyboard = [
                [InlineKeyboardButton("🎬 فيديو", callback_data='video')],
                [InlineKeyboardButton("🎵 صوت", callback_data='audio')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text('اختر صيغة التحميل:', reply_markup=reply_markup)
            context.user_data['url'] = url
        else:
            # إذا كان الرابط من موقع آخر، حدد نوع المحتوى تلقائيًا
            if is_audio_url(url):
                message_obj = update.message.reply_text("جاري تحميل الصوت... ⏳")
                download_content(update, context, url, is_audio=True, message_obj=message_obj)
            else:
                message_obj = update.message.reply_text("جاري تحميل الفيديو... ⏳")
                download_content(update, context, url, is_audio=False, message_obj=message_obj)
    else:
        update.message.reply_text("❌ الرابط غير صالح. يرجى إرسال رابط صحيح.")

def button_handler(update: Update, context: CallbackContext):
    """التعامل مع الأزرار المضمنة"""
    query = update.callback_query
    query.answer()
    
    url = context.user_data.get('url')
    if not url:
        query.edit_message_text(text="❌ لم يتم العثور على الرابط. يرجى إرساله مرة أخرى.")
        return
    
    is_audio = query.data == 'audio'
    message_text = "جاري تحميل الصوت... ⏳" if is_audio else "جاري تحميل الفيديو... ⏳"
    message_obj = query.edit_message_text(text=message_text)
    
    download_content(update, context, url, is_audio=is_audio, message_obj=message_obj)

def error_handler(update, context):
    """التعامل مع الأخطاء"""
    logger.error(f"حدث خطأ: {context.error}")
    try:
        if update and update.effective_message:
            update.effective_message.reply_text("❌ حدث خطأ أثناء معالجة طلبك. يرجى المحاولة مرة أخرى لاحقًا.")
    except:
        pass

def main():
    """تشغيل البوت"""
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # إضافة معالجات الأوامر والرسائل
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(button_handler))
    
    # إضافة معالج الأخطاء
    dp.add_error_handler(error_handler)

    # بدء البوت
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()