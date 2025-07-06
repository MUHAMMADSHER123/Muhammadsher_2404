import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging sozlamalari
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- BOT TOKEN --- 
# Iltimos, bu yerga BotFather'dan olgan tokeningizni qo'ying
TELEGRAM_BOT_TOKEN = "7824325370:AAGK1GpgoUo_e2rqfE0H2P-AvY2d0tBZgEk"

def search_deezer(query: str) -> list:
    """Berilgan so'rov bo'yicha Deezer'dan qidiradi va treklar ro'yxatini qaytaradi."""
    # Natijalar aniqligini oshirish uchun RANKING bo'yicha saralash
    url = f"https://api.deezer.com/search?q={query}&order=RANKING"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Deezer API bilan xatolik: {e}")
        return []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start buyrug'i uchun salomlashish xabarini yuboradi."""
    user = update.effective_user
    await update.message.reply_html(
        f"Salom {user.mention_html()}! 👋\n\n"
        f"Men sizning veb-saytingiz bilan bir xil musiqa manbasidan (Deezer) foydalanadigan botman. Shunday qilib, biz 'ulanganmiz'! 😉\n\n"
        f"Menga qo'shiq yoki ijrochi nomini yuboring, men darhol qidirishni boshlayman.",
    )

async def search_music(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchi xabari asosida musiqani qidiradi."""
    query = update.message.text
    if not query:
        return

    await update.message.reply_text("Qidirilmoqda...")
    
    tracks = search_deezer(query)

    if not tracks:
        await update.message.reply_text(
            "Ushbu so'rov bo'yicha hech narsa topilmadi. 😕\n"
            "Iltimos, so'rovni aniqroq yozib ko'ring (masalan, 'ijrochi nomi - qo'shiq nomi')."
        )
        return

    # 7 tagacha natijani yuborish
    for track in tracks[:7]:
        title = track.get('title', 'Noma\'lum nom')
        artist = track.get('artist', {}).get('name', 'Noma\'lum ijrochi')
        album_cover = track.get('album', {}).get('cover_small', '')
        preview_url = track.get('preview', '')

        caption = f"🎧 *Nomi:* {title}\n🎤 *Ijrochi:* {artist}"
        
        keyboard = []
        if preview_url:
            keyboard.append([InlineKeyboardButton("🎵 Tinglash (30s)", url=preview_url)])
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

        if album_cover:
            await update.message.reply_photo(
                photo=album_cover,
                caption=caption,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                caption,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

def main() -> None:
    """Botni ishga tushirish."""
    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN" or not TELEGRAM_BOT_TOKEN:
        print("Xatolik: Iltimos, 'music_bot.py' fayliga o'z Telegram Bot Tokeningizni kiriting.")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_music))

    print("Bot ishga tushdi... (To'xtatish uchun Ctrl+C)")
    application.run_polling()
    print("Bot to'xtatildi.")

if __name__ == "__main__":
    main()
