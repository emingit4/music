from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from youtube_search import YoutubeSearch
import yt_dlp
import logging

# Logging konfiqurasiyası
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot parametrləri
api_id = "28603118"
api_hash = "35a400855835510c0a926f1e965aa12d"
bot_token = "5347650033:AAHANE4nPgPOP_SqWo1BtajRea6zyBORwJ4"

app = Client("music_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
vc = PyTgCalls(app)

# YouTube-dan link əldə etmək üçün funksiya
def search_youtube(query):
    results = YoutubeSearch(query, max_results=1).to_dict()
    if results:
        video_url = f"https://www.youtube.com{results[0]['url_suffix']}"
        return video_url
    return None

@app.on_message(filters.command("start"))
async def start(_, message):
    await message.reply("Bot başlatıldı və hazırdır!")
    logger.info("Start əmri alındı və bot başlatıldı.")  # Start əmri alındıqda loq mesajı

@app.on_message(filters.command("play"))
async def play(_, message):
    logger.info("Play əmri alındı.")  # Loq mesajı əlavə etdim
    if not message.chat.type in ["supergroup", "group"]:
        await message.reply("Bu əmri yalnız qrupda istifadə edə bilərsiniz.")
        return

    if len(message.command) < 2:
        await message.reply("Zəhmət olmasa, mahnının adını yazın.")
        return

    query = " ".join(message.command[1:])
    video_url = search_youtube(query)
    if not video_url:
        await message.reply("Mahnı tapılmadı.")
        return

    # Mahnını yükləyin
    await message.reply(f"Mahnı tapıldı: {video_url}. Yüklənir...")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "quiet": True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            audio_file = ydl.prepare_filename(info)
    except Exception as e:
        logger.error(f"Yükləmə zamanı səhv baş verdi: {e}")
        await message.reply("Mahnı yüklənərkən səhv baş verdi.")
        return

    # Səsli söhbətə qoşulun, əlaqə artıq varsa, qoşulmaya cəhd etməyin
    if not vc.is_connected(message.chat.id):
        try:
            await vc.join_group_call(
                message.chat.id,
                MediaStream(audio_file)  # AudioPiped -> MediaStream
            )
        except Exception as e:
            logger.error(f"Səsli söhbətə qoşulma zamanı səhv baş verdi: {e}")
            await message.reply("Səsli söhbətə qoşulma zamanı səhv baş verdi.")
            return
    else:
        await message.reply("Zatən səsli söhbətə qoşulmusunuz.")
    await message.reply("Mahnı oynanır.")
    logger.info("Mahnı oynanmağa başladı.")  # Mahnı başladı mesajı

@app.on_message(filters.command("stop"))
async def stop(_, message):
    await vc.leave_group_call(message.chat.id)
    await message.reply("Mahnı dayandırıldı.")
    logger.info("Bot səsli söhbəti tərk etdi.")  # Stop əmri işlədiyi zaman loq mesajı

# `app.run()` yalnız bir dəfə çağırılmalıdır
async def start_bot():
    await app.start()  # Pyrogram-a qoşulma
    await vc.start()   # PyTgCalls-ı başlatma
    logger.info("Bot başladı.")  # Bot başlatma loqu

# Botu başlat
app.run(start_bot())  # Bu üsul əlaqəni düzgün idarə edəcək
