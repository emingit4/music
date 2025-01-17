from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped
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

@app.on_message(filters.command("play"))
async def play(_, message):
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
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        audio_file = ydl.prepare_filename(info)

    # Səsli söhbətə qoşulun
    await vc.join_group_call(
        message.chat.id,
        AudioPiped(audio_file)  # Burada AudioPiped modulu istifadə olunur
    )
    await message.reply("Mahnı oynanır.")

@app.on_message(filters.command("stop"))
async def stop(_, message):
    await vc.leave_group_call(message.chat.id)
    await message.reply("Mahnı dayandırıldı.")

vc.start()
app.run()
