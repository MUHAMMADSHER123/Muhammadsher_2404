# Telegram Bot API (telebot) konfiguratsiyasi va ishlatilishi
import telebot
from telebot import types

# Bot tokeni va ob'ekti
TOKEN = "7824325370:AAGc8WNdkwcvhOlDrwySz7fty_OWz80HruM"
bot = telebot.TeleBot(TOKEN)

# Telegram komanda handlerlari
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🎵 Musiqa yuklash", "📹 Video yuklash", "🔍 Nom bo‘yicha qidirish", "ℹ️ Yordam")
    bot.send_message(chat_id, "👋 Assalomu alaykum! Men YouTube’dan musiqa va video yuklab beruvchi botman.\n"
                              "Quyidagi tugmalardan birini tanlang:", reply_markup=markup)

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id in {7157577190}:  # Admin ID
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add("📊 Statistika ko'rish", "🔄 Botni qayta yuklash", "📂 Yuklangan fayllar", "⬅️ Bosh menyu")
        bot.send_message(message.chat.id, "🔑 Admin paneliga xush kelibsiz!", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "❌ Siz admin emassiz!")

# Callback query handler
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    data = call.data
    if data.startswith("delete"):
        _, chat_id, msg_id = data.split("_")
        bot.delete_message(int(chat_id), int(msg_id))
    # Boshqa callback'lar...

# YouTube API (yt_dlp) konfiguratsiyasi va ishlatilishi
import yt_dlp

# Musiqa yuklash uchun yt_dlp sozlamalari
def download_audio(chat_id, url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', 'audio').replace('<', '_').replace('>', '_')  # Fayl nomini tozalash
        audio_file = Path(ydl.prepare_filename(info)).with_suffix('.mp3')
        return audio_file, title

# Video yuklash uchun yt_dlp sozlamalari
def download_video(chat_id, url, quality):
    ydl_opts = {
        'format': f'bestvideo[height<={quality}]+bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', 'video').replace('<', '_').replace('>', '_')
        video_file = Path(ydl.prepare_filename(info))
        return video_file, title

# Ma'lumot olish uchun yt_dlp
def show_audio_info(chat_id, url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get('title', 'Noma’lum')
        uploader = info.get('uploader', 'Noma’lum')
        duration = info.get('duration', 0)
        duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else 'Noma’lum'
        views = info.get('view_count', 'Noma’lum')
        upload_date = info.get('upload_date', 'Noma’lum')
        return f"🎵 Musiqa ma'lumotlari:\n📌 Sarlavha: {title}\n👤 Muallif: {uploader}\n⏱ Davomiylik: {duration_str}\n👀 Ko‘rishlar: {views}\n📅 Yuklangan sana: {upload_date}"

# Botni ishga tushirish
if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
