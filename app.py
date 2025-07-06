import os
import logging
import telebot
from telebot import types
import yt_dlp
from pathlib import Path
import sys
import threading
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# --- Basic Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- Flask App Setup ---
# Serve static files from the root directory where index.html is located
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # Allow cross-origin requests for our API

# --- Telegram Bot Configuration ---
TOKEN = "7824325370:AAEbGsu2AGhlbbGpn4NIk06XJ-vRJAoTEpI"
DOWNLOAD_DIR = "downloads"
OWNER_ID = 7157577190

bot = telebot.TeleBot(TOKEN, parse_mode='HTML')
Path(DOWNLOAD_DIR).mkdir(exist_ok=True)

# --- Hardcoded Movie Database (API-siz yechim) ---
LOCAL_MOVIES_DB = [
    {
        "title": "Shum Bola",
        "release_date": "1977-01-01",
        "vote_average": 8.5,
        "poster_path": "/z3t5mO3IKM5M2y2G6wzYQz4A4Q4.jpg"
    },
    {
        "title": "Baron",
        "release_date": "2016-01-15",
        "vote_average": 7.8,
        "poster_path": "/lAmX1tV3iVfA1i1lS3C2gq9sT5y.jpg"
    },
    {
        "title": "Avatar: The Way of Water",
        "release_date": "2022-12-14",
        "vote_average": 7.7,
        "poster_path": "/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
    },
    {
        "title": "Scorpion",
        "release_date": "2018-12-01",
        "vote_average": 6.9,
        "poster_path": "/5V2885wX2O50Yp2g6b7a5h5g.jpg"
    },
    {
        "title": "The Avengers",
        "release_date": "2012-04-25",
        "vote_average": 7.7,
        "poster_path": "/RYMX2wcKCBAr24UyPD7xwmjaTn.jpg"
    }
]

# --- Web API Endpoint for Movie Search (Local Version) ---
@app.route('/api/search_movie')
def api_search_movie():
    query = request.args.get('q', '').lower()
    logger.info(f"Lokal kino qidiruvi: {query}")

    if not query:
        # Agar so'rov bo'sh bo'lsa, barcha kinolarni qaytarish
        return jsonify({"data": LOCAL_MOVIES_DB})

    # Sarlavhadan qidirish
    results = [
        movie for movie in LOCAL_MOVIES_DB
        if query in movie['title'].lower()
    ]
    
    return jsonify({"data": results})


# --- Web API Endpoint for Music Search ---
@app.route('/api/search')
def api_search():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    logger.info(f"API Search for: {query}")
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'default_search': 'ytsearch15',
            'noplaylist': True,
            'skip_download': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch15:{query}", download=False)
            entries = result.get('entries', [])

            if not entries:
                return jsonify({"data": []})

            tracks = []
            for entry in entries:
                if not entry:
                    continue
                
                # yt-dlp provides the direct URL in 'url' for the best audio format
                stream_url = entry.get('url')
                
                if stream_url:
                    tracks.append({
                        "title": entry.get('title', 'Noma’lum'),
                        "artist": {"name": entry.get('uploader', 'Noma’lum')},
                        "album": {"cover_medium": entry.get('thumbnail')},
                        "preview": stream_url
                    })

            return jsonify({"data": tracks})

    except Exception as e:
        logger.error(f"API Search error: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch search results"}), 500

# --- Main HTML Serving ---
@app.route('/')
def index():
    # Serves the main index.html file
    return send_from_directory('.', 'index.html')

# --- Telegram Bot Functions ---
@bot.message_handler(commands=['start'])
def start(message):
    # Simplified start message for the combined service
    bot.send_message(message.chat.id, 
                     "👋 Assalomu alaykum!\n\n" 
                     "Bu bot endi veb-sayt bilan birga ishlaydi. "
                     "Musiqa qidirish va tinglash uchun, iltimos, veb-saytimizga tashrif buyuring: https://kino-app-d2pl.onrender.com/",
                     disable_web_page_preview=True) # Replace [HAVOLA] with your actual website link

# --- Main Execution ---
def run_bot():
    logger.info("Starting Telegram bot polling...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logger.critical(f"Bot polling failed: {e}", exc_info=True)

if __name__ == '__main__':
    # Bot is temporarily disabled to resolve conflict
    # bot_thread = threading.Thread(target=run_bot)
    # bot_thread.daemon = True
    # bot_thread.start()

    # Run the Flask app
    # Use port 8000 as it's common for development
    logger.info("Starting Flask web server on http://127.0.0.1:8000")
    # Setting debug=False is important for production or when running with threads
    app.run(host='0.0.0.0', port=8000, debug=False)