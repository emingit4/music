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

def download_video(url):
    # yt-dlp parametrləri
    ydl_opts = {
        'format': 'bestaudio/best',  # Yalnız ən yaxşı audio keyfiyyətini seç
        'outtmpl': 'downloads/%(title)s.%(ext)s',  # Faylın adını və yeri
        'noplaylist': True,  # Playlistləri yükləməmək
        'quiet': True,  # Konsolda yalnız zəruri məlumatları göstər
        'nocheckcertificate': True,  # Sertifikat yoxlamasını keç
        'no_warnings': True,  # Xətaları gizlət
        'postprocessors': [{
            'key': 'FFmpegAudio',  # Yalnız audio fayl formatı
            'preferredcodec': 'mp3',  # Audio faylının formatı
            'preferredquality': '192',  # Audio keyfiyyəti
        }],
    }

    # yt-dlp ilə video yükləmək
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

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

    download_video(video_url)  # Musiqi yükləmək üçün əlavə edilib

    # Audio faylı yolunu tapın
    audio_file = f"downloads/{query}.mp3"  # Burada faylın doğru yolda olduğunu təsdiqləyin

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
    app.run()  # Pyrogram-ı başlatmaq və botu işə salmaq üçün bu koda uyğunlaşdir onu
