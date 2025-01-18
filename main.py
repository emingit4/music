from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from googleapiclient.discovery import build
import yt_dlp
import logging
import os

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot parameters
api_id = "28603118"
api_hash = "35a400855835510c0a926f1e965aa12d"
bot_token = "5357718486:AAG3bxaqLvPUBxPvvv46DQYfBCj7aQuwDTE"

app = Client("music_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
vc = PyTgCalls(app)

# YouTube API key
API_KEY = 'AIzaSyA8rNaOWHqOfPW2_EVnzKBhCkc2dIJ5tX8'

# Create YouTube Data API client
youtube = build('youtube', 'v3', developerKey=API_KEY)

def search_youtube(query):
    request = youtube.search().list(
        part="snippet",
        maxResults=1,
        q=query
    )
    response = request.execute()

    if 'items' in response and len(response['items']) > 0:
        video_id = response['items'][0]['id']['videoId']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        return video_url
    return None

def download_video(video_url):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/%(id)s.%(ext)s",  # Yüklənmiş musiqinin fayl yolu
        "quiet": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            audio_file = ydl.prepare_filename(info)
            return audio_file
    except Exception as e:
        logger.error(f"Yükləmə zamanı səhv baş verdi: {e}")
        return None

@app.on_message(filters.command("play"))
async def play(_, message):
    if len(message.command) < 2:
        await message.reply("Zəhmət olmasa, mahnının adını yazın.")
        return

    query = " ".join(message.command[1:])
    video_url = search_youtube(query)
    if not video_url:
        await message.reply("Mahnı tapılmadı.")
        return

    audio_file = download_video(video_url)
    if not audio_file:
        await message.reply("Mahnı yüklənərkən səhv baş verdi.")
        return

    if not vc.is_connected(message.chat.id):
        try:
            await vc.join_group_call(
                message.chat.id,
                MediaStream(audio_file)  # Audio faylı ilə MediaStream əlavə edilir
            )
            await message.reply("Mahnı oynanır.")
        except Exception as e:
            logger.error(f"Səsli söhbətə qoşulma zamanı səhv baş verdi: {e}")
            await message.reply("Səsli söhbətə qoşulma zamanı səhv baş verdi.")
            return
    else:
        await message.reply("Zatən səsli söhbətə qoşulmusunuz.")

@app.on_message(filters.command("stop"))
async def stop(_, message):
    await vc.leave_group_call(message.chat.id)
    await message.reply("Mahnı dayandırıldı.")
    logger.info("Bot səsli söhbəti tərk etdi.")

async def start_bot():
    try:
        await app.start()  # Pyrogram-a qoşulma
        await vc.start()   # PyTgCalls-ı başlatma
        logger.info("Bot başladı.")
        await app.idle()  # Botun dayanmaması üçün
    except Exception as e:
        logger.error(f"Botun başlaması zamanı səhv baş verdi: {e}")

# Botu başlat
if __name__ == "__main__":
    app.run(start_bot())
