import logging
import os
import threading
import asyncio
import re
import yt_dlp
from flask import Flask, jsonify, request, redirect, send_file, after_this_request
from flask_cors import CORS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from werkzeug.middleware.proxy_fix import ProxyFix
import secrets
import string
from functools import wraps

# --- Configuration ---
class Config:
    # Generate a random secret key for Flask
    SECRET_KEY = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7824325370:AAGrIvQXA-DXN_NmEA68FtCVMOtkSpl-m6M')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max download size
    DOWNLOAD_FOLDER = 'downloads'
    ALLOWED_DOMAINS = {
        'youtube.com', 'youtu.be', 
        'instagram.com', 'fb.watch',
        'soundcloud.com', 'tiktok.com'
    }
    RATE_LIMIT = 5  # requests per minute per IP

# --- Basic Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"), 
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure download directory exists
os.makedirs(Config.DOWNLOAD_FOLDER, exist_ok=True)

# --- Flask App Setup ---
app = Flask(__name__)
app.config.from_object(Config)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
CORS(app)

# --- Rate Limiting ---
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[f"{Config.RATE_LIMIT} per minute"]
)

# --- Security Helpers ---
def validate_url(url):
    """Validate URL format and domain."""
    if not url:
        return False
        
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if not parsed.scheme in ('http', 'https'):
            return False
            
        domain = '.'.join(parsed.netloc.split('.')[-2:])
        if domain not in Config.ALLOWED_DOMAINS:
            return False
            
        return True
    except:
        return False

def sanitize_filename(filename):
    """Sanitize filenames to prevent directory traversal."""
    filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
    filename = filename[:100]  # limit length
    return filename

def cleanup_old_files():
    """Remove files older than 1 hour from downloads folder."""
    try:
        now = time.time()
        for f in os.listdir(Config.DOWNLOAD_FOLDER):
            fpath = os.path.join(Config.DOWNLOAD_FOLDER, f)
            if os.path.isfile(fpath) and (now - os.stat(fpath).st_mtime) > 3600:
                try:
                    os.remove(fpath)
                    logger.info(f"Cleaned up old file: {fpath}")
                except Exception as e:
                    logger.error(f"Error cleaning up file {fpath}: {e}")
    except Exception as e:
        logger.error(f"Error in cleanup_old_files: {e}")

# --- Async Helpers ---
def async_route(f):
    """Decorator to run Flask routes in a thread."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

# --- HTML Content (Frontend) ---
html_content = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Music & Movie App</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🎵</text></svg>">
    <style>
        :root {
            --primary-color: #1DB954;
            --primary-color-hover: #1ed760;
            --background-color: #121212;
            --card-color: #181818;
            --card-hover-color: #282828;
            --text-color: #FFFFFF;
            --text-secondary-color: #B3B3B3;
            --player-bar-height: 80px;
        }
        body {
            font-family: 'Poppins', sans-serif;
            background-color: var(--background-color);
            color: var(--text-color);
            margin: 0;
        }
        main {
            padding: 2rem;
            padding-bottom: calc(var(--player-bar-height) + 2rem);
        }
        .search-container {
            display: flex;
            justify-content: center;
            margin-bottom: 2rem;
        }
        #search-input {
            width: 60%;
            max-width: 500px;
            padding: 0.8rem 1.2rem;
            border-radius: 50px 0 0 50px;
            border: 1px solid #282828;
            background-color: #282828;
            color: white;
            font-size: 1rem;
        }
        #search-button {
            padding: 0.8rem 1.5rem;
            border: none;
            background-color: var(--primary-color);
            color: white;
            cursor: pointer;
            border-radius: 0 50px 50px 0;
        }
        #results-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 1.5rem;
        }
        .track {
            background-color: var(--card-color);
            border-radius: 8px;
            overflow: hidden;
            cursor: pointer;
        }
        .track img {
            width: 100%;
            display: block;
        }
        .track-info {
            padding: 1rem;
        }
        #player-bar {
            position: fixed;
            bottom: 0;
            width: 100%;
            background-color: #181818;
            padding: 1rem;
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        .download-card {
            background-color: var(--card-color);
            border-radius: 8px;
            padding: 2rem;
            text-align: center;
            grid-column: 1 / -1;
        }
        .download-buttons {
            margin-top: 1rem;
            display: flex;
            justify-content: center;
            gap: 1rem;
        }
        .btn-download {
            padding: 0.8rem 1.5rem;
            border: none;
            background-color: var(--primary-color);
            color: white;
            cursor: pointer;
            border-radius: 50px;
            font-size: 1rem;
            transition: background-color 0.2s;
        }
        .btn-download:hover {
            background-color: var(--primary-color-hover);
        }
        .error-message {
            color: #ff3333;
            text-align: center;
            padding: 1rem;
        }
    </style>
</head>
<body>
    <main>
        <h1>Music & Movie Search</h1>
        <div class="search-container">
            <input type="text" id="search-input" placeholder="Qo'shiq nomini yoki havolani kiriting...">
            <button id="search-button">Qidirish</button>
        </div>
        <div id="results-container"></div>
    </main>
    <div id="player-bar" style="display: none;">
        <img id="now-playing-cover" src="" width="56" height="56">
        <div id="now-playing-info">
            <h4 style="margin: 0;"></h4>
            <p style="margin: 0; color: #B3B3B3;"></p>
        </div>
        <audio id="audio-player" controls style="width: 50%;"></audio>
    </div>
    <script>
        const searchButton = document.getElementById('search-button');
        const searchInput = document.getElementById('search-input');
        const resultsContainer = document.getElementById('results-container');
        const playerBar = document.getElementById('player-bar');
        const audioPlayer = document.getElementById('audio-player');
        const nowPlayingCover = document.getElementById('now-playing-cover');
        const nowPlayingInfo = document.getElementById('now-playing-info').children;

        searchButton.addEventListener('click', handleSearch);
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleSearch();
            }
        });

        async function handleSearch() {
            const query = searchInput.value.trim();
            if (!query) return;

            resultsContainer.innerHTML = '<p>Qidirilmoqda...</p>';

            try {
                const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                if (!response.ok) {
                    throw new Error(await response.text());
                }
                const result = await response.json();

                if (result.type === 'link') {
                    displayDownloadOptions(result.url);
                } else if (result.type === 'search') {
                    displayMusicResults(result.data);
                } else {
                    resultsContainer.innerHTML = `<p class="error-message">Xatolik: ${result.error || 'Noma'lum xato'}</p>`;
                }
            } catch (error) {
                resultsContainer.innerHTML = `<p class="error-message">Xatolik: ${error.message || 'Server bilan bog'lanishda xatolik'}</p>`;
                console.error('Search error:', error);
            }
        }

        function displayDownloadOptions(url) {
            resultsContainer.innerHTML = `
                <div class="download-card">
                    <h3>Faylni yuklab olish</h3>
                    <p style="word-break: break-all;">${url}</p>
                    <div class="download-buttons">
                        <button class="btn-download" onclick="triggerDownload('${url}', 'audio')">🎵 Audio yuklash</button>
                        <button class="btn-download" onclick="triggerDownload('${url}', 'video')">🎬 Video yuklash</button>
                    </div>
                </div>
            `;
        }

        function triggerDownload(url, format) {
            window.location.href = `/api/download?url=${encodeURIComponent(url)}&format=${format}`;
        }

        function displayMusicResults(tracks) {
            resultsContainer.innerHTML = '';
            if (!tracks || tracks.length === 0) {
                resultsContainer.innerHTML = '<p>Hech narsa topilmadi.</p>';
                return;
            }
            tracks.forEach(track => {
                const trackElement = document.createElement('div');
                trackElement.className = 'track';
                trackElement.innerHTML = `
                    <img src="${track.thumbnail || 'https://via.placeholder.com/200x200?text=No+Image'}" alt="${track.title}">
                    <div class="track-info">
                        <h3 style="margin:0; font-size: 1rem;">${track.title}</h3>
                        <p style="margin:0; color: #B3B3B3; font-size: 0.9rem;">${track.uploader || 'Noma'lum'}</p>
                    </div>
                `;
                trackElement.addEventListener('click', () => {
                    playTrack(track.webpage_url, track.title, track.uploader, track.thumbnail);
                });
                resultsContainer.appendChild(trackElement);
            });
        }

        function playTrack(videoUrl, title, artist, imageUrl) {
            playerBar.style.display = 'flex';
            nowPlayingCover.src = imageUrl || 'https://via.placeholder.com/56x56?text=No+Image';
            nowPlayingInfo[0].textContent = title;
            nowPlayingInfo[1].textContent = artist || 'Noma'lum';
            audioPlayer.src = `/api/get_audio_stream?url=${encodeURIComponent(videoUrl)}`;
            audioPlayer.play();
        }
    </script>
</body>
</html>
"""

# --- Web API Endpoints ---
@app.route('/')
def index():
    return html_content

@app.route('/api/search')
@limiter.limit("5 per minute")
def api_search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    if validate_url(query):
        logger.info(f"API Link detected: {query}")
        return jsonify({"type": "link", "url": query})

    logger.info(f"API Search for: {query}")
    try:
        ydl_opts = {
            'format': 'worstaudio/worst',
            'quiet': True,
            'default_search': 'ytsearch10',
            'noplaylist': True,
            'skip_download': True,
            'extract_flat': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch10:{query}", download=False)
            entries = result.get('entries', [])
            tracks = [{
                "title": e.get('title', 'Noma'lum'),
                "uploader": e.get('uploader', 'Noma'lum'),
                "thumbnail": e.get('thumbnail'),
                "webpage_url": e.get('url') or f"https://youtube.com/watch?v={e.get('id')}"
            } for e in entries if e]
            return jsonify({"type": "search", "data": tracks})
    except Exception as e:
        logger.error(f"API Search error: {e}", exc_info=True)
        return jsonify({"type": "error", "error": "Qidirish natijalarini olib bo'lmadi"}), 500

@app.route('/api/download')
@limiter.limit("3 per minute")
def api_download():
    media_url = request.args.get('url')
    media_format = request.args.get('format', 'audio')
    
    if not media_url or not validate_url(media_url):
        return "Xato: To'g'ri URL manzilini taqdim eting.", 400
    if media_format not in ['audio', 'video']:
        return "Xato: Format 'audio' yoki 'video' bo'lishi kerak.", 400

    logger.info(f"API Download request for URL: {media_url}, Format: {media_format}")

    try:
        info, filename = download_media_sync(media_url, media_format)

        @after_this_request
        def cleanup(response):
            try:
                if os.path.exists(filename):
                    os.remove(filename)
                    logger.info(f"Vaqtinchalik fayl o'chirildi: {filename}")
            except Exception as error:
                logger.error(f"Faylni o'chirishda xatolik: {error}")
            return response

        return send_file(
            filename,
            as_attachment=True,
            download_name=sanitize_filename(os.path.basename(filename))
    except yt_dlp.DownloadError as e:
        logger.error(f"Download error: {e}")
        return "Uzr, bu kontentni yuklab bo'lmadi. Boshqa havolani sinab ko'ring.", 400
    except Exception as e:
        logger.error(f"API Download error: {e}", exc_info=True)
        return "Faylni yuklab bo'lmadi. Iltimos, keyinroq urinib ko'ring.", 500

@app.route('/api/get_audio_stream')
@limiter.limit("10 per minute")
def get_audio_stream():
    video_url = request.args.get('url')
    if not video_url or not validate_url(video_url):
        return jsonify({"error": "To'g'ri URL parametri talab qilinadi"}), 400
        
    logger.info(f"Audio oqimini olinmoqda: {video_url}")
    try:
        ydl_opts = {
            'format': 'worstaudio/worst',
            'quiet': True,
            'noplaylist': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            if not info or not info.get('url'):
                raise ValueError("Audio stream URL not found")
            return redirect(info['url'])
    except Exception as e:
        logger.error(f"Audio stream error: {e}", exc_info=True)
        return jsonify({"error": "Audio oqimini olishda xatolik"}), 500

# --- Media Download Functions ---
def download_media_sync(media_url, media_format='audio'):
    """Synchronous media download function with enhanced error handling."""
    cleanup_old_files()
    
    ydl_opts = {
        'outtmpl': os.path.join(Config.DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'quiet': True,
        'noplaylist': True,
        'max_filesize': Config.MAX_CONTENT_LENGTH,
    }

    if media_format == 'video':
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    else:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(media_url, download=True)
        filename = ydl.prepare_filename(info)
        
        if media_format == 'audio' and not filename.endswith('.mp3'):
            base, _ = os.path.splitext(filename)
            filename = base + '.mp3'
            
        return info, filename

# --- Telegram Bot Functions ---
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        'Assalomu alaykum! Menga qoʻshiq nomi yoki YouTube/Instagram havolasini yuboring.\n\n'
        'Botdan foydalanish uchun quyidagilardan birini yuboring:\n'
        '1. Qoʻshiq nomi (qidirish uchun)\n'
        '2. YouTube/Instagram/SoundCloud havolasi (yuklab olish uchun)'
    )

async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        'Yordam:\n'
        '1. Musiqa topish uchun nomini yuboring\n'
        '2. Yuklab olish uchun havolani yuboring\n\n'
        'Bot faqat YouTube, Instagram, SoundCloud platformalarini qoʻllab-quvvatlaydi.'
    )

async def handle_message(update: Update, context: CallbackContext):
    query = update.message.text.strip()
    if not query:
        await update.message.reply_text("Iltimos, qidirish uchun matn yoki havola yuboring.")
        return

    if validate_url(query):
        logger.info(f"Telegram link detected: {query}")
        context.user_data['download_url'] = query
        keyboard = [
            [InlineKeyboardButton("🎵 Audio yuklash", callback_data="dl_audio")],
            [InlineKeyboardButton("🎬 Video yuklash", callback_data="dl_video")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"Havola qabul qilindi. Qaysi formatda yuklab olmoqchisiz?",
            reply_markup=reply_markup
        )
        return

    await update.message.reply_text(f'\"{query}\" uchun qidirilmoqda...')
    logger.info(f"Telegram search for: {query}")
    
    try:
        result = await asyncio.to_thread(search_music_sync, query)
        entries = result.get('entries', [])
        if not entries:
            await update.message.reply_text("Hech narsa topilmadi.")
            return

        keyboard = []
        for entry in entries[:5]:  # Limit to 5 results
            title = entry.get('title', 'Noma'lum')[:64]  # Truncate long titles
            video_id = entry.get('id')
            if video_id:
                keyboard.append([InlineKeyboardButton(title, callback_data=f"download_{video_id}")])

        if not keyboard:
            await update.message.reply_text("Natijalar topildi, lekin ularni tugma sifatida ko'rsatib bo'lmadi.")
            return

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Topilgan natijalar:', reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Telegram search error: {e}", exc_info=True)
        await update.message.reply_text("Qidirishda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")

async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    callback_data = query.data

    try:
        if callback_data in ["dl_audio", "dl_video"]:
            media_url = context.user_data.get('download_url')
            if not media_url:
                await query.edit_message_text(text="Xatolik: Yuklash havolasi topilmadi. Iltimos, havolani qayta yuboring.")
                return

            media_format = 'audio' if callback_data == "dl_audio" else 'video'
            await query.edit_message_text(text=f"{media_format.capitalize()} yuklanmoqda, iltimos kuting...")

            try:
                info, filename = await asyncio.to_thread(download_media_sync, media_url, media_format)
                caption = info.get('title', 'Yuklab olindi')[:1000]  # Truncate long captions

                if media_format == 'audio':
                    await context.bot.send_audio(
                        chat_id=query.message.chat_id,
                        audio=open(filename, 'rb'),
                        caption=caption,
                        timeout=120
                    )
                else:
                    await context.bot.send_video(
                        chat_id=query.message.chat_id,
                        video=open(filename, 'rb'),
                        caption=caption,
                        timeout=120
                    )

                os.remove(filename)
                await query.delete_message()

            except Exception as e:
                logger.error(f"Telegram download error: {e}", exc_info=True)
                await query.edit_message_text(text="Faylni yuklashda xatolik yuz berdi. Iltimos, boshqa formatda urinib ko'ring.")

        elif callback_data.startswith("download_"):
            video_id = callback_data.split('_', 1)[1]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            await query.edit_message_text(text="Musiqa (audio) yuklab olinmoqda, iltimos kuting...")

            try:
                info, filename = await asyncio.to_thread(download_media_sync, video_url, 'audio')
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=open(filename, 'rb'),
                    caption=info.get('title', 'Musiqa')[:1000],
                    timeout=120
                )
                os.remove(filename)
                await query.delete_message()

            except Exception as e:
                logger.error(f"Telegram download error: {e}", exc_info=True)
                await query.edit_message_text(text="Faylni yuklashda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")

    except Exception as e:
        logger.error(f"Callback error: {e}", exc_info=True)
        await query.edit_message_text(text="Amalni bajarishda xatolik yuz berdi.")

def search_music_sync(search_query):
    """Synchronous music search with error handling."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch5',
        'noplaylist': True,
        'quiet': True,
        'extract_flat': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(search_query, download=False)

# --- Bot Setup ---
def setup_bot():
    """Configure and return the Telegram bot application."""
    if not Config.TELEGRAM_BOT_TOKEN:
        raise ValueError("Telegram bot token not configured")

    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))

    return application

# --- Main Execution ---
if __name__ == '__main__':
    # Run cleanup on startup
    cleanup_old_files()

    # Start the Telegram bot in a separate thread
    try:
        bot_app = setup_bot()
        bot_thread = threading.Thread(
            target=bot_app.run_polling,
            kwargs={'stop_signals': []}  # Don't handle signals in thread
        )
        bot_thread.daemon = True
        bot_thread.start()
        logger.info("Telegram bot started in background thread")
    except Exception as e:
        logger.error(f"Failed to start Telegram bot: {e}")

    # Run the Flask web server
    logger.info("Starting Flask web server on http://0.0.0.0:8000")
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=False,
        use_reloader=False  # Disable reloader in production
    )
